"""
Generic command line interface, usable in the terminal or as a backend
in a GUI application.

How auto-completion works
-------------------------
if completion key is pressed:
    if completion is running:
        (next/prev depends on whether completing forwards or backwards)
        - move to next/prev position in suggestion list
        - change completable text to new suggestion
        if at start/end of suggestion list:
            - wrap around and move to opposite end
    if completion is not running:
        - completion -> running
        - move to next/prev position in suggestion list (aka not the first)
        - change completable text to new suggestion
if any other key is pressed:
    - completion -> not running
"""
import enum
from operator import attrgetter
import re
from typing import Callable, Dict, List, NamedTuple, Optional, Tuple


class ArgumentRules(enum.Enum):
    NONE = enum.auto()
    OPTIONAL = enum.auto()
    REQUIRED = enum.auto()


class AutocompletionPattern(NamedTuple):
    name: str
    get_suggestions: Callable
    prefix: str = ''
    start: str = r'^'
    end: str = r'$'
    illegal_chars: str = ''


class Command(NamedTuple):
    name: str
    help_text: str
    callback: Callable
    args: ArgumentRules = ArgumentRules.OPTIONAL


class AutocompletionState(NamedTuple):
    autocompleting: bool = False
    suggestions: List[str] = []
    suggestion_index: int = 0
    original_text: str = None
    match_start: int = 0
    match_end: int = 0


class CommandLineInterface:
    def __init__(self,
                 get_input: Callable[[], str] = None,
                 set_input: Callable[[str], None] = None,
                 set_output: Callable[[str], None] = None,
                 get_cursor_pos: Callable[[], int] = None,
                 set_cursor_pos: Callable[[int], None] = None) -> None:
        for func in (get_input, set_input, set_output,
                     get_cursor_pos, set_cursor_pos):
            assert func is not None
        self.get_input = get_input
        self.set_input = set_input
        self.set_output = set_output
        self.get_cursor_pos = get_cursor_pos
        self.set_cursor_pos = set_cursor_pos

        self.confirmation_callback: Optional[Tuple[Callable, str]] = None

        self.history: List[str] = ['']
        self.history_index = 0
        self.autocompletion_state = AutocompletionState()

        self.commands: Dict[str, Command] = {
            'help': Command('help', 'Show help about a command',
                            self._help_command, ArgumentRules.REQUIRED)
        }
        self.autocompletion_patterns = [
            AutocompletionPattern(
                'command',
                lambda name, text: _command_suggestions(self.commands,
                                                        name, text),
                end=r'( |$)',
                illegal_chars=' \t'
            ),
            AutocompletionPattern(
                'help',
                lambda name, text: _command_suggestions(self.commands,
                                                        name, text),
                prefix=r'help\s+',
                illegal_chars=' \t'
            )
        ]

    def _help_command(self, text: str) -> None:
        text = text.strip()
        if text in self.commands:
            help_text = self.commands[text].help_text
            if not help_text.strip():
                self.print_(f'No help text for "{text}"')
            else:
                self.print_(help_text)
        else:
            self.error('No such command!')

    # Outside-visible methods
    def add_command(self, command: Command) -> None:
        self.commands[command.name] = command

    def add_autocompletion_pattern(self, pattern: AutocompletionPattern
                                   ) -> None:
        self.autocompletion_patterns.append(pattern)

    def print_(self, text: str) -> None:
        self.set_output(text)

    def error(self, text: str) -> None:
        self.set_output(_error(text))

    def next_autocompletion(self) -> None:
        self._change_autocompletion(reverse=False)

    def previous_autocompletion(self) -> None:
        self._change_autocompletion(reverse=True)

    def _change_autocompletion(self, reverse: bool = False) -> None:
        input_text = self.get_input()
        cursor_pos = self.get_cursor_pos()
        state = self.autocompletion_state
        if not state.suggestions:
            state = _init_autocompletion(input_text, cursor_pos, state,
                                         self.autocompletion_patterns)
        new_input_text, new_cursor_pos, new_autocompletion_state =\
            _run_autocompletion(input_text, cursor_pos, state, reverse=reverse)
        self.set_input(new_input_text)
        self.set_cursor_pos(new_cursor_pos)
        self.autocompletion_state = new_autocompletion_state

    def stop_autocompleting(self) -> None:
        self.autocompletion_state = AutocompletionState()

    def older_history(self) -> None:
        self._traverse_history(back=True)

    def newer_history(self) -> None:
        self._traverse_history()

    def _traverse_history(self, back: bool = False) -> None:
        if len(self.history) <= 1:
            return
        self.autocompletion_state = AutocompletionState()
        new_input_text, self.history_index =\
            _move_in_history(back, self.get_input(), self.history,
                             self.history_index)
        self.set_input(new_input_text)

    def reset_history_travel(self) -> None:
        self.history_index = 0
        self.history[0] = self.get_input()

    def run_command(self) -> None:
        input_text = self.get_input()
        self.set_output('')
        if self.confirmation_callback:
            _handle_confirmation(self.confirmation_callback, self.print_,
                                 input_text == 'y')
            self.confirmation_callback = None
            return
        new_input_text, new_output_text, append_to_history =\
            _run_command(input_text, self.commands)
        self.set_input(new_input_text)
        if new_output_text is not None:
            self.set_output(new_output_text)
        if append_to_history:
            self.history = _add_to_history(self.history, input_text)

    def confirm_command(self, text: str, callback: Callable, arg: str) -> None:
        self.print_('{} Type y to confirm.'.format(text))
        self.set_input('')
        self.confirmation_callback = (callback, arg)


# De-OOP'd functions

def _error(text: str) -> str:
    return f'Error: {text}'


def _init_autocompletion(input_text: str,
                         cursor_pos: int,
                         autocompletion_state: AutocompletionState,
                         autocompletion_patterns: List[AutocompletionPattern]
                         ) -> AutocompletionState:
    suggestions, start, end = _generate_suggestions(
            autocompletion_patterns,
            input_text,
            cursor_pos)
    return autocompletion_state._replace(suggestions=suggestions,
                                         original_text=input_text,
                                         match_start=start,
                                         match_end=end)


def _run_autocompletion(input_text: str,
                        cursor_pos: int,
                        autocompletion_state: AutocompletionState,
                        reverse: bool = False
                        ) -> Tuple[str, int, AutocompletionState]:
    """
    Change to the new autocompletion suggestion.

    Return the new input text, the new cursor position, and the
    new state of the autocompletion.
    """
    def apply_suggestion(num: int) -> Tuple[str, int]:
        state = autocompletion_state
        prefix = state.original_text[:state.match_start]
        suffix = state.original_text[state.match_end:]
        return (prefix + state.suggestions[num] + suffix,
                len(prefix + state.suggestions[num]))

    # If there's only one suggestion, set it and move on
    if len(autocompletion_state.suggestions) == 2:
        new_input_text, new_cursor_pos = apply_suggestion(1)
        return new_input_text, new_cursor_pos, AutocompletionState()
    # Otherwise start scrolling through them
    elif autocompletion_state.suggestions:
        new_suggestion_index = (
                (autocompletion_state.suggestion_index
                    + (-1 if reverse else 1))
                % len(autocompletion_state.suggestions))
        new_input_text, new_cursor_pos = apply_suggestion(new_suggestion_index)
        new_state = autocompletion_state._replace(
                suggestion_index=new_suggestion_index)
        return new_input_text, new_cursor_pos, new_state
    else:
        return input_text, cursor_pos, autocompletion_state


def _command_suggestions(commands: Dict, name: str, text: str) -> List[str]:
    return [cmd.name + (' ' if cmd.args != ArgumentRules.NONE else '')
            for cmd in sorted(commands.values(), key=attrgetter('name'))
            if cmd.name.startswith(text)]


def _generate_suggestions(autocompletion_patterns: List[AutocompletionPattern],
                          rawtext: str, rawpos: int
                          ) -> Tuple[List[str], int, int]:
    # TODO: docstring ffs
    for ac in autocompletion_patterns:
        prefix = re.match(ac.prefix, rawtext)
        if prefix is None:
            continue
        prefix_length = len(prefix.group(0))
        # Dont match anything if the cursor is in the prefix
        if rawpos < prefix_length:
            continue
        pos = rawpos - prefix_length
        text = rawtext[prefix_length:]
        start_matches = [x for x in re.finditer(ac.start, text)
                         if x.end() <= pos]
        # I think this should check the whole string so it can do lookbehinds
        end_matches = next((x for x in re.finditer(ac.end, text)
                           if x.start() >= pos), None)
        if not start_matches or not end_matches:
            continue
        start = start_matches[-1].end()
        end = end_matches.start()
        matchtext = text[start:end]
        # Check if the text includes any invalid characters
        if any(ch for ch in ac.illegal_chars if ch in matchtext):
            continue
        match_start, match_end = (start + prefix_length, end + prefix_length)
        suggestions = [matchtext] + ac.get_suggestions(ac.name, matchtext)
        return suggestions, match_start, match_end
    return [], 0, 0


def _run_command(input_text: str, commands: Dict[str, Command]
                 ) -> Tuple[str, Optional[str], bool]:
    """
    Run a command.

    Return new input text, new output text, and whether or not to append
    the input to history.
    """
    if not input_text.strip():
        return input_text, None, False
    chunks = input_text.split(None, 1)
    arg = chunks[1] if len(chunks) == 2 else None
    command_name = chunks[0]
    if command_name not in commands:
        return input_text, _error(f'Invalid command: {command_name}'), False
    command = commands[command_name]
    if arg and command.args == ArgumentRules.NONE:
        return (input_text, _error(f'This command doesn\'t '
                                   f'take any arguments'), False)
    if not arg and command.args == ArgumentRules.REQUIRED:
        return input_text, _error(f'This command requires an argument'), False
    if command.args != ArgumentRules.NONE:
        command.callback(arg)
    else:
        command.callback()
    return '', None, True


def _handle_confirmation(confirmation_callback: Tuple[Callable, str],
                         print_: Callable[[str], None],
                         confirmed: bool) -> None:
    if confirmed:
        print_('Confirmed')
        callback, arg = confirmation_callback
        callback(arg)
    else:
        print_('Aborted')


def _add_to_history(history: List[str], text: str) -> List[str]:
    return ['', text] + history[1:]


def _move_in_history(back: bool, input_text: str, history: List[str],
                     history_index: int) -> Tuple[str, int]:
    new_history_index = max(0, min(history_index + (1 if back else -1),
                                   len(history) - 1))
    return history[new_history_index], new_history_index

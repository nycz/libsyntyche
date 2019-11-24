import pytest
from unittest.mock import Mock
from typing import Dict, List

from libsyntyche.cli import (_generate_suggestions, _run_command,
                             ArgumentRules, AutocompletionPattern,
                             Command)


def test_generate_suggestions() -> None:
    def getter(name: str, current_text: str) -> List[str]:
        return [x for x in ['abc', 'bcd', 'cde', 'aaa']
                if x.startswith(current_text)]
    ac = AutocompletionPattern('foo', getter)
    result = _generate_suggestions([ac], 'a', 0)
    assert result == (['a', 'abc', 'aaa'], 0, 1)


def test_generate_suggestions_prefix() -> None:
    def getter(name: str, current_text: str) -> List[str]:
        return [x for x in ['abc', 'bcd', 'cde', 'aaa']
                if x.startswith(current_text)]
    ac = AutocompletionPattern('foo', getter, prefix=r'x\s+')
    result = _generate_suggestions([ac], 'x a', 2)
    assert result == (['a', 'abc', 'aaa'], 2, 3)


@pytest.fixture  # type: ignore
def default_commands() -> Dict[str, Command]:
    commands = {
        'f': Command('foo', '', Mock(), short_name='f',
                     args=ArgumentRules.NONE),
        'b': Command('bar', '', Mock(), short_name='b',
                     args=ArgumentRules.REQUIRED),
        'z': Command('baz', '', Mock(), short_name='z'),
        '/': Command('search', '', Mock(), short_name='/',
                     args=ArgumentRules.REQUIRED, strip_input=False),
    }
    return commands


# Run command

def test_run_command_empty(default_commands: Dict[str, Command]) -> None:
    result = _run_command('', default_commands, True, False)
    # new_input, (error, new_output), append_to_history
    assert result == ('', (False, None), False)


def test_run_command_no_args(default_commands: Dict[str, Command]) -> None:
    result = _run_command('f', default_commands, True, False)
    # new_input, (error, new_output), append_to_history
    assert result == ('', (False, None), True)
    default_commands['f'].callback.assert_called_once_with()


@pytest.mark.parametrize('arg', [' foobar', '  stuff', 'lorem ipsum foo baz'])
def test_run_command_req_args(arg: str, default_commands: Dict[str, Command]
                              ) -> None:
    result = _run_command('b' + arg, default_commands, True, True)
    # new_input, (error, new_output), append_to_history
    assert result == ('', (False, None), False)
    default_commands['b'].callback.assert_called_once_with(arg.strip())


@pytest.mark.parametrize('arg', ['', ' foobar'])
def test_run_command_opt_args(arg: str, default_commands: Dict[str, Command]
                              ) -> None:
    result = _run_command('z' + arg, default_commands, True, True)
    # new_input, (error, new_output), append_to_history
    assert result == ('', (False, None), False)
    if arg:
        default_commands['z'].callback.assert_called_once_with(arg.strip())
    else:
        default_commands['z'].callback.assert_called_once_with(None)


def test_run_command_dont_strip_input(default_commands: Dict[str, Command]
                                      ) -> None:
    result = _run_command('/ foobar ', default_commands, True, True)
    # new_input, (error, new_output), append_to_history
    assert result == ('', (False, None), False)
    default_commands['/'].callback.assert_called_once_with(' foobar ')


# Fail run commands

def test_run_unknown_command(default_commands: Dict[str, Command]
                             ) -> None:
    result = _run_command('X', default_commands, True, False)
    # new_input, (error, new_output), append_to_history
    assert result == ('X', (True, 'Invalid command: X'), False)


def test_run_command_no_args_error(default_commands: Dict[str, Command]
                                   ) -> None:
    result = _run_command('f foo', default_commands, True, False)
    # new_input, (error, new_output), append_to_history
    assert result == ('f foo', (True, "This command doesn't "
                                "take any arguments"), False)
    default_commands['f'].callback.assert_not_called()


def test_run_command_req_arg_error(default_commands: Dict[str, Command]
                                   ) -> None:
    result = _run_command('b ', default_commands, True, False)
    # new_input, (error, new_output), append_to_history
    assert result == ('b ', (True, "This command requires an argument"), False)
    default_commands['b'].callback.assert_not_called()

from datetime import datetime
import enum
from pathlib import Path
from typing import Any, Callable, cast, Dict, Iterable, Optional

from PyQt5.QtCore import (Qt, QEasingCurve, QEvent, QObject,
                          QPoint, QPropertyAnimation, QTimer)
from PyQt5.QtGui import QHideEvent, QKeyEvent
from PyQt5.QtWidgets import (QAbstractItemView, QFrame, QGraphicsOpacityEffect,
                             QLabel, QLineEdit, QListWidget, QSizePolicy,
                             QVBoxLayout, QWidget)

from .cli import ArgumentRules, Command, CommandLineInterface
from .widgets import Signal0, mk_signal0, mk_signal3


class MessageType(enum.Enum):
    PRINT = enum.auto()
    ERROR = enum.auto()
    INPUT = enum.auto()


class Terminal(QFrame):
    error_triggered = mk_signal0()
    show_message = mk_signal3(datetime, MessageType, str)

    class InputField(QLineEdit):
        def setFocus(self) -> None:  # type: ignore
            self.parentWidget().show()
            super().setFocus()

    def __init__(self, parent: QWidget,
                 help_command: str = 'h', log_command: str = 'l',
                 history_file: Optional[Path] = None) -> None:
        super().__init__(parent)
        self.input_field = self.InputField(self)
        self.input_field.setObjectName('terminal_input')
        self.output_field = QLineEdit(self)
        self.output_field.setObjectName('terminal_output')
        self.output_field.setDisabled(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.input_field)
        layout.addWidget(self.output_field)
        self.cli = CommandLineInterface(
            get_input=self.input_field.text,
            set_input=self.on_input,
            get_cursor_pos=self.input_field.cursorPosition,
            set_cursor_pos=self.input_field.setCursorPosition,
            set_output=self.on_print,
            show_error=self.on_error,
            history_file=history_file
        )
        self.add_command = self.cli.add_command
        self.add_autocompletion_pattern = self.cli.add_autocompletion_pattern
        self.print_ = self.cli.print_
        self.error = self.cli.error
        self.prompt = self.cli.prompt
        # Help
        self.help_command = help_command
        if help_command:
            self.add_command(Command(
                'toggle-help',
                'Show or hide the help view.',
                self.toggle_extended_help,
                args=ArgumentRules.OPTIONAL,
                short_name=self.help_command,
                arg_help=(('', 'Toggle extended help view.'),
                          ('X', 'Show help for command X, which should be '
                           'one from the list below.'))
            ))
        self.help_view = HelpView(self, self.cli.commands, help_command)
        self.help_view.show_help(help_command)
        layout.insertWidget(0, self.help_view)
        # Log
        self.log_history = LogHistory(self)
        if log_command:
            self.add_command(Command(
                'toggle-terminal-log',
                'Show or hide the log of all input and output in the terminal.',
                self.log_history.toggle_visibility,
                args=ArgumentRules.NONE, short_name=log_command
            ))
        layout.addWidget(self.log_history)
        self.log_history.show_message.connect(self.show_message.emit)
        self.watch_terminal()

    def toggle_extended_help(self, arg: str) -> None:
        if not arg and self.help_view.isVisible():
            self.help_view.hide()
        else:
            success = self.help_view.show_help(arg or self.help_command)
            if success:
                self.help_view.show()
            else:
                self.error('Unknown command')
                self.help_view.hide()

    def on_input(self, text: str) -> None:
        self.input_field.setText(text)
        if text:
            self.log_history.add_input(text)

    def on_print(self, text: str) -> None:
        self.output_field.setText(text)
        if text:
            self.log_history.add(text)

    def on_error(self, text: str) -> None:
        self.error_triggered.emit()
        self.output_field.setText(text)
        self.log_history.add_error(text)

    def watch_terminal(self) -> None:
        class EventFilter(QObject):
            backtab_pressed = mk_signal0()
            tab_pressed = mk_signal0()
            reset_completion = mk_signal0()
            up_pressed = mk_signal0()
            down_pressed = mk_signal0()
            reset_history = mk_signal0()

            def eventFilter(self_, obj: object, event: QEvent) -> bool:
                catch_keys = [
                    (Qt.Key_Backtab, Qt.ShiftModifier, self_.backtab_pressed),
                    (Qt.Key_Tab, Qt.NoModifier, self_.tab_pressed),
                    (Qt.Key_Up, Qt.NoModifier, self_.up_pressed),
                    (Qt.Key_Down, Qt.NoModifier, self_.down_pressed),
                ]
                modkeys = (Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt,
                           Qt.Key_AltGr)
                if event.type() == QEvent.KeyPress:
                    key_event = cast(QKeyEvent, event)
                    if key_event.key() not in modkeys + (Qt.Key_Tab, Qt.Key_Backtab):
                        self_.reset_completion.emit()
                    if key_event.key() not in modkeys + (Qt.Key_Up, Qt.Key_Down):
                        self_.reset_history.emit()
                    for key, mod, signal in catch_keys:
                        if key_event.key() == key and int(key_event.modifiers()) == mod:
                            signal.emit()
                            return True
                return False
        self.term_event_filter = EventFilter()
        self.input_field.installEventFilter(self.term_event_filter)
        self.term_event_filter.tab_pressed.connect(self.cli.next_autocompletion)
        self.term_event_filter.backtab_pressed.connect(self.cli.previous_autocompletion)
        self.term_event_filter.reset_completion.connect(self.cli.stop_autocompleting)
        self.term_event_filter.up_pressed.connect(self.cli.older_history)
        self.term_event_filter.down_pressed.connect(self.cli.newer_history)
        self.term_event_filter.reset_history.connect(self.cli.reset_history_travel)
        cast(Signal0, self.input_field.returnPressed).connect(self.cli.run_command)

    def hideEvent(self, event: QHideEvent) -> None:
        self.output_field.setText('')
        super().hideEvent(event)

    def confirm_command(self, text: str, callback: Callable[[str], Any],
                        arg: str) -> None:
        self.input_field.setFocus()
        self.cli.confirm_command(text, callback, arg)

    def exec_command(self, command_string: str) -> None:
        """
        Parse and run or prompt a command string from the config.

        If command_string starts with a space, set the input field's text to
        command_string (minus the leading space), otherwise run the command.
        """
        if command_string.startswith(' '):
            self.input_field.setText(command_string[1:])
            self.input_field.setFocus()
        else:
            self.cli.run_command(command_string, quiet=True)


class MessageTrayItem(QLabel):
    def __init__(self, text: str, name: str, parent: QWidget) -> None:
        super().__init__(text, parent)
        self.setObjectName(name)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        # Fade out animation
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(1)
        self.setGraphicsEffect(effect)
        a1 = QPropertyAnimation(effect, b'opacity')
        a1.setEasingCurve(QEasingCurve.InOutQuint)
        a1.setDuration(500)
        a1.setStartValue(1)
        a1.setEndValue(0)
        cast(Signal0, a1.finished).connect(self.deleteLater)
        self.fade_animation = a1
        # Move animation
        a2 = QPropertyAnimation(self, b'pos')
        a2.setEasingCurve(QEasingCurve.InQuint)
        a2.setDuration(300)
        self.move_animation = a2

    def kill(self) -> None:
        self.fade_animation.start()
        self.move_animation.setStartValue(self.pos())
        self.move_animation.setEndValue(self.pos() - QPoint(0, 50))
        self.move_animation.start()


class MessageTray(QFrame):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        # TODO: put this in settings
        self.seconds_alive = 5
        layout = QVBoxLayout(self)
        layout.addStretch()
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def add_message(self, timestamp: datetime, msgtype: MessageType, text: str) -> None:
        if msgtype == MessageType.INPUT:
            return
        classes = {
            MessageType.ERROR: 'terminal_error',
            MessageType.PRINT: 'terminal_print',
        }
        lbl = MessageTrayItem(text, classes[msgtype], self)
        self.layout().addWidget(lbl)
        QTimer.singleShot(1000 * self.seconds_alive, lbl.kill)


class LogHistory(QListWidget):
    show_message = mk_signal3(datetime, MessageType, str)

    def __init__(self, parent: Terminal) -> None:
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.hide()

    def toggle_visibility(self) -> None:
        self.setVisible(not self.isVisible())

    def add(self, message: str) -> None:
        self._add_to_log(MessageType.PRINT, message)

    def add_error(self, message: str) -> None:
        self._add_to_log(MessageType.ERROR, message)

    def add_input(self, text: str) -> None:
        self._add_to_log(MessageType.INPUT, text)

    def _add_to_log(self, type_: MessageType, message: str) -> None:
        timestamp = datetime.now()
        self.show_message.emit(timestamp, type_, message)
        if type_ == MessageType.ERROR:
            message = '< [ERROR] ' + message
        elif type_ == MessageType.INPUT:
            message = '> ' + message
        else:
            message = '< ' + message
        self.addItem(f'{timestamp.strftime("%H:%M:%S")} - {message}')


class HelpView(QLabel):
    def __init__(self, parent: QWidget,
                 commands: Dict[str, Command],
                 help_command: str) -> None:
        super().__init__(parent)
        self.commands = commands
        self.help_command = help_command
        self.set_help_text()
        self.setWordWrap(True)
        self.hide()

    def set_help_text(self) -> None:
        def escape(s: str) -> str:
            return s.replace('<', '&lt;').replace('>', '&gt;')
        # TODO: make this into labels and widgets instead maybe?
        main_template = ('<h2 style="margin:0">{command}: {desc}</h2>'
                         '<hr><table>{rows}</table>')
        row_template = ('<tr><td><b>{command}{arg}</b></td>'
                        '<td style="padding-left:10px">{subdesc}</td></tr>')

        def gen_arg_help(cmd: Command) -> Iterable[str]:
            err_template = ('<tr><td colspan="2"><b><i>ERROR: {}'
                            '</i></b></td></tr>')
            if not cmd.arg_help and cmd.args == ArgumentRules.NONE:
                return ["<tr><td>This command doesn't take any arguments."
                        "</td></tr>"]
            elif not cmd.arg_help:
                return [err_template.format('missing help for args')]
            else:
                out = [row_template.format(command=escape(cmd.short_name),
                                           arg=escape(arg),
                                           subdesc=escape(subdesc))
                       for arg, subdesc in cmd.arg_help]
                if cmd.args == ArgumentRules.NONE:
                    out.append(err_template.format(
                        'command takes no arguments but there are still '
                        'help lines!'))
                return out

        self.help_html = {
            id_: main_template.format(
                command=escape(id_),
                desc=cmd.help_text,
                rows=''.join(gen_arg_help(cmd))
            )
            for id_, cmd in self.commands.items()
            if cmd.short_name
        }
        command_template = ('<div style="margin-left:5px">'
                            '<h3>List of {} commands</h3>'
                            '<table style="margin-top:2px">{}</table></div>')
        categories = {cmd.category for cmd in self.commands.values()}
        for group in sorted(categories):
            command_rows = (
                row_template.format(command=escape(cmd), arg='',
                                    subdesc=meta.help_text)
                for cmd, meta in self.commands.items()
                if meta.category == group and cmd
            )
            self.help_html[self.help_command] += command_template.format(
                group or 'misc',
                ''.join(command_rows))

    def show_help(self, arg: str) -> bool:
        self.set_help_text()
        if arg not in self.help_html:
            return False
        self.setText(self.help_html[arg])
        return True

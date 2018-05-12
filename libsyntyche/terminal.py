from typing import cast, Callable

from PyQt5.QtCore import pyqtSignal, Qt, QEvent, QObject
from PyQt5.QtGui import QHideEvent, QKeyEvent
from PyQt5.QtWidgets import QFrame, QLineEdit, QVBoxLayout

from .cli import CommandLineInterface


class Terminal(QFrame):

    class InputField(QLineEdit):
        def setFocus(self) -> None:
            self.parentWidget().show()
            super().setFocus()

    def __init__(self, parent, short_mode: bool = False) -> None:
        super().__init__(parent)
        self.input_field = self.InputField(self)
        self.input_field.setObjectName('terminal_input')
        self.output_field = QLineEdit(self)
        self.output_field.setObjectName('terminal_output')
        self.output_field.setDisabled(True)
        l = QVBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)
        l.addWidget(self.input_field)
        l.addWidget(self.output_field)
        self.cli = CommandLineInterface(
                get_input=self.input_field.text,
                set_input=self.input_field.setText,
                get_cursor_pos=self.input_field.cursorPosition,
                set_cursor_pos=self.input_field.setCursorPosition,
                set_output=self.output_field.setText,
                short_mode=short_mode)
        self.add_command = self.cli.add_command
        self.add_autocompletion_pattern = self.cli.add_autocompletion_pattern
        self.print_ = self.cli.print_
        self.error = self.cli.error
        self.watch_terminal()

    def watch_terminal(self) -> None:
        class EventFilter(QObject):
            backtab_pressed = pyqtSignal()
            tab_pressed = pyqtSignal()
            reset_completion = pyqtSignal()
            up_pressed = pyqtSignal()
            down_pressed = pyqtSignal()
            reset_history = pyqtSignal()
            page_up_pressed = pyqtSignal()
            page_down_pressed = pyqtSignal()

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
                        if key_event.key() == key and key_event.modifiers() == mod:
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
        self.input_field.returnPressed.connect(self.cli.run_command)

    def hideEvent(self, event: QHideEvent) -> None:
        self.output_field.setText('')
        super().hideEvent(event)

    def confirm_command(self, text: str, callback: Callable, arg: str) -> None:
        self.input_field.setFocus()
        self.cli.confirm_command(text, callback, arg)

    def exec_command(self, command_string: str) -> None:
        """
        Parse and run or prompt a command string from the config.

        If command_string starts with a space, set the input field's text to
        command_string (minus the leading space), otherwise run the command.
        """
        if command_string.startswith(' '):
            self.input_field.text = command_string[1:]
            self.input_field.setFocus()
        else:
            self.cli.run_command(command_string)

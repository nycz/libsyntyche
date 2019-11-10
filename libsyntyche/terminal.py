from datetime import datetime
import enum
from pathlib import Path
from typing import cast, Callable, Optional

from PyQt5.QtCore import pyqtSignal, Qt, QEvent, QObject
from PyQt5.QtGui import QHideEvent, QKeyEvent
from PyQt5.QtWidgets import (QAbstractItemView, QFrame, QLineEdit,
                             QListWidget, QVBoxLayout)

from .cli import CommandLineInterface


class MessageType(enum.Enum):
    PRINT = enum.auto()
    ERROR = enum.auto()
    INPUT = enum.auto()


class Terminal(QFrame):
    error_triggered = pyqtSignal()
    show_message = pyqtSignal(datetime, MessageType, str)

    class InputField(QLineEdit):
        def setFocus(self) -> None:
            self.parentWidget().show()
            super().setFocus()

    def __init__(self, parent, short_mode: bool = False,
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
                short_mode=short_mode,
                history_file=history_file)
        self.add_command = self.cli.add_command
        self.add_autocompletion_pattern = self.cli.add_autocompletion_pattern
        self.print_ = self.cli.print_
        self.error = self.cli.error
        self.prompt = self.cli.prompt
        self.log_history = LogHistory(self)
        layout.addWidget(self.log_history)
        self.log_history.show_message.connect(self.show_message)
        self.watch_terminal()

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
            self.input_field.setText(command_string[1:])
            self.input_field.setFocus()
        else:
            self.cli.run_command(command_string, quiet=True)


class LogHistory(QListWidget):
    show_message = pyqtSignal(datetime, MessageType, str)

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

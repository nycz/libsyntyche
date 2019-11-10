from typing import Any, Callable, cast, Generic, List, Union, Type, TypeVar

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QBoxLayout, QLayout, QWidget

from .cli import AutocompletionPattern, CommandLineInterface


# Wrappers for signals for easier type checking

T = TypeVar('T', bound=Callable[..., Any])


_T1 = TypeVar('_T1')
_T2 = TypeVar('_T2')
_T3 = TypeVar('_T3')


class Signal0:
    def __init__(self) -> None: ...

    def emit(self) -> None: ...

    def connect(self, slot: Callable[[], None]) -> None: ...


class Signal1(Generic[_T1]):
    def __init__(self, arg_type: Type[_T1]) -> None: ...

    def emit(self, arg: _T1) -> None: ...

    def connect(self, slot: Callable[[_T1], None]) -> None: ...


class Signal2(Generic[_T1, _T2]):
    def __init__(self, arg1_type: Type[_T1], arg2_type: Type[_T2]) -> None: ...

    def emit(self, arg1: _T1, arg2: _T2) -> None: ...

    def connect(self, slot: Callable[[_T1, _T2], None]) -> None: ...


class Signal3(Generic[_T1, _T2, _T3]):
    def __init__(self, arg1_type: Type[_T1], arg2_type: Type[_T2],
                 arg3_type: Type[_T3]) -> None: ...

    def emit(self, arg1: _T1, arg2: _T2, arg3: _T3) -> None: ...

    def connect(self, slot: Callable[[_T1, _T2, _T3], None]) -> None: ...


# Actual widgets

class ScrolledList(QtWidgets.QScrollArea):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._widget = QtWidgets.QFrame(self)
        self._widget.setObjectName('ScrolledListWidget')
        self.setWidgetResizable(True)
        self.setWidget(self._widget)
        self._vbox = VBoxLayout(self._widget)
        self._vbox.addStretch(1)

    def add_widget(self, widget: QWidget) -> None:
        self._vbox.insertWidget(self._vbox.count() - 1, widget)

    def add_layout(self, layout: QtWidgets.QLayout) -> None:
        self._vbox.insertLayout(self._vbox.count() - 1, layout)

    def clear(self) -> None:
        self._vbox.clear()
        self._vbox.addStretch(1)


class Stretch:
    def __init__(self, *args):
        self.weight = 0
        self.item = None
        for arg in args:
            if isinstance(arg, int):
                self.weight = arg
            elif isinstance(arg, QWidget) or isinstance(arg, QLayout):
                self.item = arg
            else:
                raise TypeError('Invalid argument')


def HBoxLayout(*args, **kwargs) -> QtWidgets.QHBoxLayout:
    return BoxLayout(QtWidgets.QBoxLayout.LeftToRight, *args, **kwargs)


def VBoxLayout(*args, **kwargs) -> QtWidgets.QVBoxLayout:
    return BoxLayout(QtWidgets.QBoxLayout.TopToBottom, *args, **kwargs)


            #   parent: QWidget = None,
            #   widgets: List[Union[QtWidgets.QLabel, QWidget]] = [],
            #   spacing: int = 0) -> QBoxLayout:
def BoxLayout(direction: QBoxLayout.Direction, *args) -> QBoxLayout:
    parent: QWidget = None
    items: List[Union[QtWidgets.QLayout, QWidget, Stretch]] = []
    spacing = 0
    for arg in args:
        if isinstance(arg, QWidget):
            parent = arg
        elif isinstance(arg, list):
            items = arg
        elif isinstance(arg, int):
            spacing = arg
        else:
            raise TypeError('Invalid argument')
    box = QBoxLayout(direction, parent)
    box.setContentsMargins(0, 0, 0, 0)
    box.setSpacing(spacing)
    for item in items:
        stretch = 0
        if isinstance(item, Stretch):
            if item.item is not None:
                stretch = item.weight
                item = item.item
            else:
                box.addStretch(item.weight)
        if isinstance(item, QWidget):
            box.addWidget(item, stretch=stretch)
        elif isinstance(item, QLayout):
            box.addLayout(item, stretch=stretch)
    return box


class Terminal(QtWidgets.QFrame):

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.input_field = QtWidgets.QLineEdit(self)
        self.output_field = QtWidgets.QLineEdit(self)
        self.output_field.setDisabled(True)
        vbox = VBoxLayout(self)
        vbox.addWidget(self.input_field)
        vbox.addWidget(self.output_field)
        self.cli = CommandLineInterface(self.input_field.text,
                                        self.input_field.setText,
                                        self.input_field.cursorPosition,
                                        self.input_field.setCursorPosition,
                                        self.output_field.setText)
        ac = AutocompletionPattern('test', autocomplete_file_path,
                                   'open ')
        self.cli.add_autocompletion_pattern(ac)
        self.init_key_triggers()

    def init_key_triggers(self):
        class EventFilter(QtCore.QObject):
            def eventFilter(self_, obj: object, event: QtCore.QEvent) -> bool:
                catch_keys = [
                    (Qt.Key_Backtab, Qt.ShiftModifier, self.cli.previous_autocompletion),
                    (Qt.Key_Tab, Qt.NoModifier, self.cli.next_autocompletion),
                    (Qt.Key_Up, Qt.NoModifier, self.cli.older_history),
                    (Qt.Key_Down, Qt.NoModifier, self.cli.newer_history),
                ]
                if event.type() == QtCore.QEvent.KeyPress:
                    key_event = cast(QtGui.QKeyEvent, event)
                    # if event.text() or event.key() in (Qt.Key_Left, Qt.Key_Right):
                    #     self.cli.reset_history_travel()
                    #     self.cli.stop_autocompleting()
                    #     return False
                    for key, mod, callback in catch_keys:
                        if key_event.key() == key and key_event.modifiers() == mod:
                            callback()
                            return True
                    else:
                        self.cli.reset_history_travel()
                        self.cli.stop_autocompleting()
                        return False
                return False
        self.term_event_filter = EventFilter()
        self.input_field.installEventFilter(self.term_event_filter)
        self.input_field.returnPressed.connect(self.cli.run_command)

    def focusInEvent(self, event):
        self.input_field.setFocus()


def autocomplete_file_path(name: str, text: str):
    """A convenience autocompletion function for filepaths."""
    import os
    import os.path
    full_path = os.path.abspath(os.path.expanduser(text))
    if text.endswith(os.path.sep):
        dir_path, name_fragment = full_path, ''
    else:
        dir_path, name_fragment = os.path.split(full_path)
    raw_paths = (os.path.join(dir_path, x)
                 for x in os.listdir(dir_path)
                 if x.startswith(name_fragment))
    return sorted(p + ('/' if os.path.isdir(p) else '')
                  for p in raw_paths)

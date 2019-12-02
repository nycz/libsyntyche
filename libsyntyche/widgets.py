from typing import (Any, Callable, cast, Generic, List, Optional,
                    Union, Type, TypeVar)

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QBoxLayout, QLayout, QWidget


# Helper functions

def kill_theming(layout: QtWidgets.QLayout) -> None:
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)


def set_hotkey(key: str, target: QtWidgets.QWidget,
               callback: Callable[[Any], Any]) -> None:
    QtWidgets.QShortcut(QtGui.QKeySequence(key), target, callback)


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


class Stretch:
    def __init__(self, *args: Any) -> None:
        self.weight = 0
        self.item = None
        for arg in args:
            if isinstance(arg, int):
                self.weight = arg
            elif isinstance(arg, QWidget) or isinstance(arg, QLayout):
                self.item = arg
            else:
                raise TypeError('Invalid argument')


def HBoxLayout(*args: Any) -> QtWidgets.QHBoxLayout:
    return cast(QtWidgets.QHBoxLayout,
                BoxLayout(QtWidgets.QBoxLayout.LeftToRight, *args))


def VBoxLayout(*args: Any) -> QtWidgets.QVBoxLayout:
    return cast(QtWidgets.QVBoxLayout,
                BoxLayout(QtWidgets.QBoxLayout.TopToBottom, *args))


def BoxLayout(direction: QBoxLayout.Direction, *args: Any) -> QBoxLayout:
    parent: Optional[QWidget] = None
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

from typing import (Any, Callable, List, Optional, Protocol, Type, TypeVar,
                    Union, cast)

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QBoxLayout, QLayout, QWidget


def kill_theming(layout: QtWidgets.QLayout) -> None:
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)


def set_hotkey(key: Union[str, QtCore.Qt.Key], target: QtWidgets.QWidget,
               callback: Callable[..., Any]) -> None:
    QtWidgets.QShortcut(QtGui.QKeySequence(key), target, callback)


# Wrappers for signals for easier type checking

_T1 = TypeVar('_T1')
_T2 = TypeVar('_T2')
_T3 = TypeVar('_T3')


class Signal0(Protocol):
    def __init__(self) -> None: ...

    def emit(self) -> None: ...

    def connect(self, slot: Callable[[], None]) -> None: ...


class Signal1(Protocol[_T1]):
    def __init__(self, arg_type: Type[_T1]) -> None: ...

    def emit(self, arg: _T1) -> None: ...

    def connect(self, slot: Callable[[_T1], None]) -> None: ...


class Signal2(Protocol[_T1, _T2]):
    def __init__(self, arg1_type: Type[_T1], arg2_type: Type[_T2]) -> None: ...

    def emit(self, arg1: _T1, arg2: _T2) -> None: ...

    def connect(self, slot: Callable[[_T1, _T2], None]) -> None: ...


class Signal3(Protocol[_T1, _T2, _T3]):
    def __init__(self, arg1_type: Type[_T1], arg2_type: Type[_T2],
                 arg3_type: Type[_T3]) -> None: ...

    def emit(self, arg1: _T1, arg2: _T2, arg3: _T3) -> None: ...

    def connect(self, slot: Callable[[_T1, _T2, _T3], None]) -> None: ...


def mk_signal0() -> Signal0:
    return cast(Signal0, QtCore.pyqtSignal())


def mk_signal1(t1: Type[_T1]) -> Signal1[_T1]:
    return cast(Signal1[_T1], QtCore.pyqtSignal(t1))


def mk_signal2(t1: Type[_T1], t2: Type[_T2]) -> Signal2[_T1, _T2]:
    return cast(Signal2[_T1, _T2], QtCore.pyqtSignal(t1, t2))


def mk_signal3(t1: Type[_T1], t2: Type[_T2], t3: Type[_T3]
               ) -> Signal3[_T1, _T2, _T3]:
    return cast(Signal3[_T1, _T2, _T3], QtCore.pyqtSignal(t1, t2, t3))


# Actual widgets

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

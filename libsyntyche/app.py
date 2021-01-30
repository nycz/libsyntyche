import sys
from pathlib import Path
from typing import Any, List, Optional, Type, TypeVar, Union, cast

from PyQt5 import QtCore, QtWidgets

from .widgets import HBoxLayout, VBoxLayout, mk_signal0


class RootWindow(QtWidgets.QFrame):
    """Generic root window, useful for most applications."""
    def __init__(self, title: str = '', horizontal: bool = False) -> None:
        super().__init__()
        self.setWindowTitle(title)
        if horizontal:
            HBoxLayout(self)
        else:
            VBoxLayout(self)


class StackedRootWindow(QtWidgets.QFrame):
    """Generic root window with stack layout."""
    def __init__(self, title: str = '') -> None:
        super().__init__()
        self.setWindowTitle(title)
        self.stack = QtWidgets.QStackedLayout(self)


C = TypeVar('C', bound=QtWidgets.QWidget)


def run_app(css_path: Union[Path, str, None], window_constructor: Type[C],
            args: Optional[List[Any]] = None) -> None:
    app = QtWidgets.QApplication(sys.argv)
    if css_path:
        if isinstance(css_path, str):
            css_path = Path(css_path)
        app.setStyleSheet(css_path.read_text())

        class AppEventFilter(QtCore.QObject):
            activation_event = mk_signal0()

            def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
                if event.type() == QtCore.QEvent.ApplicationActivate:
                    cast(QtWidgets.QApplication, obj).setStyleSheet(
                        cast(Path, css_path).read_text())
                    self.activation_event.emit()
                return False
        event_filter = AppEventFilter()
        setattr(app, 'event_filter', event_filter)
        app.installEventFilter(event_filter)
    if args is None:
        args = []
    window = window_constructor(*args)
    app.setActiveWindow(window)
    sys.exit(app.exec_())

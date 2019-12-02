from pathlib import Path
import sys
from typing import Any, List, Optional, Type, TypeVar, Union

from PyQt5 import QtCore, QtWidgets

from .widgets import HBoxLayout, VBoxLayout


class RootWindow(QtWidgets.QFrame):
    """Generic root window, useful for most applications."""
    def __init__(self, title: str = '', horizontal: bool = False) -> None:
        super().__init__()
        self.setWindowTitle(title)
        box = HBoxLayout(self) if horizontal else VBoxLayout(self)


C = TypeVar('C', bound=QtWidgets.QWidget)


def run_app(css_path: Union[Path, str, None], window_constructor: Type[C],
            args: Optional[List[Any]] = None) -> None:
    app = QtWidgets.QApplication(sys.argv)
    if css_path:
        css_path_ = css_path
        with open(css_path) as f:
            css = f.read()
        app.setStyleSheet(css)

        class AppEventFilter(QtCore.QObject):
            activation_event = QtCore.pyqtSignal()

            def eventFilter(self, obj: QtWidgets.QWidget,
                            event: QtCore.QEvent) -> bool:
                if event.type() == QtCore.QEvent.ApplicationActivate:
                    with open(css_path_) as f:
                        css = f.read()
                    obj.setStyleSheet(css)
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

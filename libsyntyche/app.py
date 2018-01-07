import sys
from typing import Type, TypeVar

from PyQt5 import QtCore, QtWidgets

from .widgets import HBoxLayout, VBoxLayout


class RootWindow(QtWidgets.QFrame):
    """Generic root window, useful for most applications."""
    def __init__(self, title: str = None, horizontal: bool = False) -> None:
        super().__init__()
        self.setWindowTitle(title)
        box = HBoxLayout(self) if horizontal else VBoxLayout(self)


C = TypeVar('C', bound=QtWidgets.QWidget)


def run_app(css_path: str, window_constructor: Type[C], args=None) -> None:
    app = QtWidgets.QApplication(sys.argv)
    if css_path:
        with open(css_path) as f:
            css = f.read()
        app.setStyleSheet(css)

        class AppEventFilter(QtCore.QObject):
            # activation_event = QtCore.pyqtSignal()

            def eventFilter(self, obj, event):
                if event.type() == QtCore.QEvent.ApplicationActivate:
                    with open(css_path) as f:
                        css = f.read()
                    obj.setStyleSheet(css)
                    # self.activation_event.emit()
                return False
        app.event_filter = AppEventFilter()
        app.installEventFilter(app.event_filter)
    if args is None:
        args = []
    window = window_constructor(*args)
    app.setActiveWindow(window)
    sys.exit(app.exec_())

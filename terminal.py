from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal, Qt, QEvent, pyqtBoundSignal

from libsyntyche.common import kill_theming

class GenericTerminalInputBox(QtGui.QLineEdit):
    tab_pressed = pyqtSignal()
    reset_ac_suggestions = pyqtSignal()
    reset_history_travel = pyqtSignal()
    history_up = pyqtSignal()
    history_down = pyqtSignal()

    # This has to be here, keyPressEvent does not capture tab press
    def event(self, event):
        if event.type() == QEvent.KeyPress and\
                    event.modifiers() == Qt.NoModifier:
            if event.key() == Qt.Key_Tab:
                self.tab_pressed.emit()
                return True
        return super().event(event)

    def keyPressEvent(self, event):
        if event.text() or event.key() in (Qt.Key_Left, Qt.Key_Right):
            QtGui.QLineEdit.keyPressEvent(self, event)
            self.reset_ac_suggestions.emit()
            self.reset_history_travel.emit()
        elif event.key() == Qt.Key_Up:
            self.history_up.emit()
        elif event.key() == Qt.Key_Down:
            self.history_down.emit()
        else:
            return super().keyPressEvent(event)

class GenericTerminalOutputBox(QtGui.QLineEdit):
    pass

class GenericTerminal(QtGui.QWidget):
    def __init__(self, parent, input_term_constructor, output_term_constructor):
        super().__init__(parent)

        layout = QtGui.QVBoxLayout(self)
        kill_theming(layout)

        self.input_term = input_term_constructor()
        self.output_term = output_term_constructor()
        self.output_term.setDisabled(True)

        layout.addWidget(self.input_term)
        layout.addWidget(self.output_term)

        self.input_term.setFocus()
        self.input_term.returnPressed.connect(self.parse_command)

        # History
        self.history = ['']
        self.history_index = 0
        self.input_term.reset_history_travel.connect(self.reset_history_travel)
        self.input_term.history_up.connect(self.history_up)
        self.input_term.history_down.connect(self.history_down)

        self.commands = {}

    def setFocus(self):
        self.input_term.setFocus()

    def print_(self, msg):
        self.output_term.setText(str(msg))
        self.show()

    def error(self, msg):
        self.output_term.setText('Error: ' + msg)
        self.show()

    def command_parsing_injection(self, arg):
        pass

    def parse_command(self):
        text = self.input_term.text().strip()
        if not text:
            return
        self.add_history(text)
        self.input_term.setText('')
        self.output_term.setText('')

        abort = self.command_parsing_injection(text)
        if abort:
            return

        command = text[0].lower()
        if command in self.commands:
            arg = text[1:].strip()
            # Run command
            run = self.commands[command][0]
            if isinstance(run, pyqtBoundSignal):
                run.emit(arg)
            else:
                run(arg)
        else:
            self.error('No such command (? for help)')



    # ==== History =============================== #

    def history_up(self):
        if self.history_index < len(self.history)-1:
            self.history_index += 1
        self.input_term.setText(self.history[self.history_index])

    def history_down(self):
        if self.history_index > 0:
            self.history_index -= 1
        self.input_term.setText(self.history[self.history_index])

    def add_history(self, text):
        self.history[0] = text
        self.history.insert(0, '')

    def reset_history_travel(self):
        self.history_index = 0
        self.history[self.history_index] = self.input_term.text()


    # ==== Useful commands ====================== #

    def cmd_help(self, arg):
        if not arg:
            self.print_(' '.join(sorted(self.commands)))
        elif arg in self.commands:
            self.print_(self.commands[arg][1])
        else:
            self.error('No such command')
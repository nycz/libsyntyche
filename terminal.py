from datetime import datetime

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal, Qt, QEvent, pyqtBoundSignal, QTimer

from libsyntyche.common import kill_theming

class GenericTerminalInputBox(QtGui.QLineEdit):
    tab_pressed = pyqtSignal(bool)
    reset_ac_suggestions = pyqtSignal()
    reset_history_travel = pyqtSignal()
    history_up = pyqtSignal()
    history_down = pyqtSignal()

    # This has to be here, keyPressEvent does not capture tab press
    def event(self, ev):
        if ev.type() == QEvent.KeyPress:
            if ev.key() == Qt.Key_Backtab and ev.modifiers() == Qt.ShiftModifier:
                self.tab_pressed.emit(True)
                return True
            elif ev.key() == Qt.Key_Tab and ev.modifiers() == Qt.NoModifier:
                self.tab_pressed.emit(False)
                return True
        return super().event(ev)

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
    def __init__(self):
        super().__init__()
        self.animate = False
        self.timer = QTimer(self)
        self.timer.setInterval(5)
        self.timer.timeout.connect(self._add_character)
        self.buffer = ''

    def set_timer_interval(self, num):
        self.timer.setInterval(num)

    def _add_character(self):
        if not self.buffer:
            self.timer.stop()
            return
        super().setText(self.text() + self.buffer[0])
        self.buffer = self.buffer[1:]

    def setText(self, text):
        if not self.animate or not text:
            super().setText(text)
            return
        super().setText(text[0])
        if len(text) > 1:
            self.buffer = text[1:]
            self.timer.start()

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

        # Log
        self.log = []

        # History
        self.history = ['']
        self.history_index = 0
        self.input_term.reset_history_travel.connect(self.reset_history_travel)
        self.input_term.history_up.connect(self.history_up)
        self.input_term.history_down.connect(self.history_down)

        # Autocomplete
        self.ac_suggestions = []
        self.ac_index = 0
        self.ac_reset_flag = True
        self.input_term.tab_pressed.connect(self.autocomplete)
        self.input_term.reset_ac_suggestions.connect(self.reset_ac_suggestions)

        # Each post in self.commands is (callback/signal, helptext[, options])
        # options is an optional dict with - surprise - options
        self.commands = {}

    def add_to_log(self, msgtype, msg):
        self.log.append((datetime.now(), msgtype, msg))

    def get_log(self):
        return self.log

    def get_formatted_log(self):
        def format_log_entry(msgtype, msg):
            if msgtype == 'cmd':
                return '   >>  ' + msg
            elif msgtype == 'error':
                return '  <<   Error: ' + msg
            else:
                return '  <<   ' + msg
        text = '\n'.join(
            ts.strftime('%H:%M:%S') + format_log_entry(msgtype, msg)
            for ts, msgtype, msg in self.log
        )
        return text if text else '[empty log]'

    def setFocus(self):
        self.input_term.setFocus()

    def clear_input(self):
        self.input_term.setText('')

    def clear_output(self):
        self.output_term.setText('')

    def clear(self):
        self.clear_input()
        self.clear_output()

    def print_(self, msg):
        self.output_term.setText(str(msg))
        self.add_to_log('msg', str(msg))
        self.show()

    def error(self, msg):
        self.output_term.setText('Error: ' + msg)
        self.add_to_log('error', str(msg))
        self.show()

    def prompt(self, msg):
        self.input_term.setText(msg)
        self.input_term.setFocus()
        self.show()

    def command_parsing_injection(self, arg):
        pass

    def parse_command(self):
        text = self.input_term.text().strip()
        if not text:
            return
        self.add_to_log('cmd', text)
        self.add_history(text)
        self.input_term.setText('')
        self.output_term.setText('')

        abort = self.command_parsing_injection(text)
        if abort:
            return

        command = text[0].lower()
        if command in self.commands:
            command_data = self.commands[command]
            # Keep the whitespace if the correct option is present and true
            if len(command_data) == 3 and  command_data[2].get('keep whitespace', False):
                arg = text[1:]
            # Otherwise strip it away
            else:
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


    # ==== Autocomplete ========================== #

    def autocomplete(self, reverse):
        """
        Main autocomplete functions.
        Is called whenever tab is pressed.
        """
        pass

    def run_autocompletion(self, text, reverse):
        # Generate new suggestions if none exist
        if not self.ac_suggestions:
            self.ac_suggestions = self.get_ac_suggestions(text)

        # If there's only one possibility, set it and move on
        if len(self.ac_suggestions) == 1:
            text = self.ac_suggestions[0]
            self.reset_ac_suggestions()
        # Otherwise start scrolling through 'em
        elif self.ac_suggestions:
            if self.ac_reset_flag:
                if reverse:
                    self.ac_index = len(self.ac_suggestions)-1
                self.ac_reset_flag = False
            else:
                if reverse:
                    self.ac_index -= 1
                    if self.ac_index == -1:
                        self.ac_index = len(self.ac_suggestions)-1
                else:
                    self.ac_index += 1
                    if self.ac_index == len(self.ac_suggestions):
                        self.ac_index = 0
            text = self.ac_suggestions[self.ac_index]
        return text

    def get_ac_suggestions(self, prefix):
        return []

    def reset_ac_suggestions(self):
        """
        Reset the list of suggestions if another button than tab
        has been pressed.
        """
        self.ac_suggestions = []
        self.ac_index = 0
        self.ac_reset_flag = True

    # ==== Useful commands ======================= #

    def cmd_help(self, arg):
        if not arg:
            self.print_(' '.join(sorted(self.commands)))
        elif arg in self.commands:
            self.print_(self.commands[arg][1])
        else:
            self.error('No such command')
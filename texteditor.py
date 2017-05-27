import re

from PyQt5.QtGui import QTextCursor, QTextDocument


class SearchAndReplaceable():
    """
    This implements search and replace functions for a QTextEdit,
    QPlaintTextEdit, or another class that defines the following methods:
        textCursor()
        moveCursor(operation)
        setTextCursor(cursor)
        find(exp, options)
    Since QTextEdit and QPlaintTextEdit don't have a common ancestor, this
    class can't inherit from it. Instead: duck typing galore!

    The command syntax is hardcoded.
    """
    def initialize_search_and_replace(self, error, print_):
        """
        Initialize all the stuff needed for searching and replacing.

        error and print_ are functions that take a string and output it in an
        appropriate place, for example in a libsyntyche-style terminal.

        As long as PyQt4 is used, multiple inheritence works kinda crappy.
        For now, this method should be run instead of __init__ before any
        other method in the class is used.
        """
        self.search_buffer = None
        self.error = error
        self.print_ = print_

    def search_and_replace(self, arg):
        """
        Main search and replace function. This is most likely the method you
        will want to use.

        arg is a string with a vim-like s&r syntax (see the regexes below)
        """
        def generate_flags(flagstr):
            # self.search_flags is automatically generated and does not
            # need to be initialized in __init__()
            self.search_flags = QTextDocument.FindFlags()
            if 'b' in flagstr:
                self.search_flags |= QTextDocument.FindBackward
            if 'i' not in flagstr:
                self.search_flags |= QTextDocument.FindCaseSensitively
            if 'w' in flagstr:
                self.search_flags |= QTextDocument.FindWholeWords

        search_rx = re.compile(r'([^/]|\\/)+$')
        search_flags_rx = re.compile(r'([^/]|\\/)*?([^\\]/[biw]*)$')
        replace_rx = re.compile(r"""
            (?P<search>([^/]|\\/)*?[^\\])
            /
            (?P<replace>(([^/]|\\/)*[^\\])?)
            /
            (?P<flags>[abiw]*)
            $
        """, re.VERBOSE)

        if search_rx.match(arg):
            self.search_buffer = search_rx.match(arg).group(0)
            self.search_flags = QTextDocument.FindCaseSensitively
            self.search_next()

        elif search_flags_rx.match(arg):
            self.search_buffer, flags = search_flags_rx.match(arg).group(0).rsplit('/', 1)
            generate_flags(flags)
            self.search_next()

        elif replace_rx.match(arg):
            match = replace_rx.match(arg)
            self.search_buffer = match.group('search')
            generate_flags(match.group('flags'))
            if 'a' in match.group('flags'):
                self._replace_all(match.group('replace'))
            else:
                self._replace_next(match.group('replace'))

        else:
            self.error('Malformed search/replace expression')

    def _searching_backwards(self):
        return QTextDocument.FindBackward & self.search_flags

    def search_next(self):
        """
        Go to the next string found.

        This does the same thing as running the same search-command again.
        """
        if self.search_buffer is None:
            self.error('No previous searches')
            return
        temp_cursor = self.textCursor()
        found = self.find(self.search_buffer, self.search_flags)
        if not found:
            if not self.textCursor().atStart() \
                        or (self._searching_backwards() and not self.textCursor().atEnd()):
                if self._searching_backwards():
                    self.moveCursor(QTextCursor.End)
                else:
                    self.moveCursor(QTextCursor.Start)
                found = self.find(self.search_buffer, self.search_flags)
                if not found:
                    self.setTextCursor(temp_cursor)
                    self.error('Text not found')
            else:
                self.setTextCursor(temp_cursor)
                self.error('Text not found')


    def _replace_next(self, replace_buffer):
        """
        Go to the next string found and replace it with replace_buffer.

        While this technically can be called from outside this class, it is
        not recommended (and most likely needs some modifications of the code.)
        """
        temp_cursor = self.textCursor()
        found = self.find(self.search_buffer, self.search_flags)
        if not found:
            if not self.textCursor().atStart() \
                        or (self._searching_backwards() and not self.textCursor().atEnd()):
                if self._searching_backwards():
                    self.moveCursor(QTextCursor.End)
                else:
                    self.moveCursor(QTextCursor.Start)
                found = self.find(self.search_buffer, self.search_flags)
                if not found:
                    self.setTextCursor(temp_cursor)
        if found:
            t = self.textCursor()
            t.insertText(replace_buffer)
            l = len(replace_buffer)
            t.setPosition(t.position() - l)
            t.setPosition(t.position() + l, QTextCursor.KeepAnchor)
            self.setTextCursor(t)
            self.print_('Replaced on line {}, pos {}'
                             ''.format(t.blockNumber(), t.positionInBlock()))
        else:
            self.error('Text not found')


    def _replace_all(self, replace_buffer):
        """
        Replace all strings found with the replace_buffer.

        As with replace_next, you probably don't want to call this manually.
        """
        temp_cursor = self.textCursor()
        times = 0
        self.moveCursor(QTextCursor.Start)
        while True:
            found = self.find(self.search_buffer, self.search_flags)
            if found:
                self.textCursor().insertText(replace_buffer)
                times += 1
            else:
                break
        if times:
            self.print_('{0} instance{1} replaced'.format(times, 's'*(times>0)))
        else:
            self.error('Text not found')
        self.setTextCursor(temp_cursor)

import enum
import re
from dataclasses import dataclass, field
from typing import Callable, Optional, Set, Union

from PyQt5 import QtWidgets
from PyQt5.QtGui import QTextCursor, QTextDocument

# Flags
_FLAG_BACKWARDS = 'b'
_FLAG_CASE_INSENSITIVE = 'i'
_FLAG_WHOLE_WORDS = 'w'
_FLAG_COUNT = '#'
_FLAG_REPLACE_ALL = 'a'

_SEARCH_FLAGS = ''.join([
    _FLAG_BACKWARDS,
    _FLAG_CASE_INSENSITIVE,
    _FLAG_WHOLE_WORDS,
    _FLAG_COUNT,
])

_REPLACE_FLAGS = ''.join([
    _FLAG_BACKWARDS,
    _FLAG_CASE_INSENSITIVE,
    _FLAG_WHOLE_WORDS,
    _FLAG_REPLACE_ALL,
])


# Regexes
_SEARCH_PAYLOAD = r'(?:\\/|[^/])'
_search_rx = re.compile(fr'{_SEARCH_PAYLOAD}+')
_search_flags_rx = re.compile(fr"""
    (?P<search>{_SEARCH_PAYLOAD}*?[^\\])
    /
    (?P<flags>[{_SEARCH_FLAGS}]*)
""")
_replace_rx = re.compile(fr"""
    (?P<search>{_SEARCH_PAYLOAD}*?[^\\])
    /
    (?P<replace>({_SEARCH_PAYLOAD}*?[^\\])?)
    /
    (?P<flags>[{_REPLACE_FLAGS}]*)
""", re.VERBOSE)


# State
class SearchFlags(enum.Enum):
    backwards = enum.auto()
    case_insensitive = enum.auto()
    whole_words = enum.auto()


@dataclass
class SearchState:
    text: str
    flags: Set[SearchFlags] = field(default_factory=set)

    def find(self, editor: Union[QtWidgets.QPlainTextEdit, QtWidgets.QTextEdit],
             override_flags: Optional[Set[SearchFlags]] = None) -> bool:
        return editor.find(self.text,
                           _encode_flags(override_flags if override_flags is not None
                                         else self.flags))


def _parse_flags(flag_str: str) -> Set[SearchFlags]:
    out = set()
    if _FLAG_BACKWARDS in flag_str:
        out.add(SearchFlags.backwards)
    if _FLAG_CASE_INSENSITIVE in flag_str:
        out.add(SearchFlags.case_insensitive)
    if _FLAG_WHOLE_WORDS in flag_str:
        out.add(SearchFlags.whole_words)
    return out


def _encode_flags(flags: Set[SearchFlags]) -> QTextDocument.FindFlags:
    search_flags = QTextDocument.FindFlags()
    if SearchFlags.backwards in flags:
        search_flags |= QTextDocument.FindBackward  # type: ignore
    if SearchFlags.case_insensitive not in flags:
        search_flags |= QTextDocument.FindCaseSensitively  # type: ignore
    if SearchFlags.whole_words in flags:
        search_flags |= QTextDocument.FindWholeWords  # type: ignore
    return QTextDocument.FindFlags(search_flags)


class Searcher:
    def __init__(self, editor: Union[QtWidgets.QPlainTextEdit, QtWidgets.QTextEdit],
                 error: Callable[[str], None],
                 log: Callable[[str], None]) -> None:
        self._editor = editor
        self._search_state: Optional[SearchState] = None
        self.error = error
        self.log = log

    def search_or_replace(self, cmd: str) -> None:
        """
        Search or replace, depending on how the cmd looks.
        """
        if (match := _search_rx.fullmatch(cmd)):
            self._search_state = SearchState(match[0])
            self.search_next()
        elif (match := _search_flags_rx.fullmatch(cmd)):
            search_buffer, flags = match['search'], match['flags']
            if _FLAG_COUNT in flags:
                self._count_hits(search_buffer, _parse_flags(flags))
            else:
                self._search_state = SearchState(search_buffer, _parse_flags(flags))
                self.search_next()
        elif (match := _replace_rx.fullmatch(cmd)):
            self._search_state = SearchState(match['search'], _parse_flags(match['flags']))
            if _FLAG_REPLACE_ALL in match['flags']:
                self._replace_all(match['replace'])
            else:
                self._replace_next(match['replace'])
        else:
            self.error('Malformed search/replace expression')

    @property
    def _is_searching_backwards(self) -> bool:
        return bool(self._search_state and SearchFlags.backwards in self._search_state.flags)

    def _replace_next(self, replace_buffer: str) -> None:
        """
        Go to the next string found and replace it with replace_buffer.
        """
        if self._search_state is None:
            self.error('No previous searches')
            return
        temp_cursor = self._editor.textCursor()
        found = self._search_state.find(self._editor)
        searching_backwards = self._is_searching_backwards
        if not found and \
                (not self._editor.textCursor().atStart()
                 or (searching_backwards and not self._editor.textCursor().atEnd())):
            self._editor.moveCursor(QTextCursor.End if searching_backwards
                                    else QTextCursor.Start)
            found = self._search_state.find(self._editor)
            if not found:
                self._editor.setTextCursor(temp_cursor)
        if found:
            t = self._editor.textCursor()
            t.insertText(replace_buffer)
            replace_len = len(replace_buffer)
            t.setPosition(t.position() - replace_len)
            t.setPosition(t.position() + replace_len, QTextCursor.KeepAnchor)
            self._editor.setTextCursor(t)
            self.log(f'Replaced on line {t.blockNumber()}, pos {t.positionInBlock()}')
        else:
            self.error('Text not found')

    def search_next(self, in_reverse: bool = False) -> None:
        """
        Go to the next string found.
        """
        if self._search_state is None:
            self.error('No previous searches')
            return
        search_flags = self._search_state.flags.copy()
        if in_reverse != self._is_searching_backwards:
            searching_backwards = True
            search_flags.add(SearchFlags.backwards)
        else:
            searching_backwards = False
            search_flags.discard(SearchFlags.backwards)
        temp_cursor = self._editor.textCursor()
        found = self._search_state.find(self._editor, search_flags)
        if not found and \
                (not self._editor.textCursor().atStart()
                 or (searching_backwards and not self._editor.textCursor().atEnd())):
            self._editor.moveCursor(QTextCursor.End if searching_backwards
                                    else QTextCursor.Start)
            found = self._search_state.find(self._editor, search_flags)
        if not found:
            self._editor.setTextCursor(temp_cursor)
            self.error('Text not found')

    def _count_hits(self, target: str, flags: Set[SearchFlags]) -> None:
        """
        Count how many times a term (word/sentence, etc.) has been used.
        """
        times = 0
        cursor = QTextCursor(self._editor.document())
        # Don't use the backwards flag
        flags = flags - {SearchFlags.backwards}
        while True:
            cursor = self._editor.document().find(target, cursor, _encode_flags(flags))
            if not cursor.isNull():
                times += 1
            else:
                break
        if times:
            self.log(f'The word "{target}" is used {times} times')
        else:
            self.log(f'The word "{target}" is not used')

    def _replace_all(self, replace_buffer: str) -> None:
        """
        Replace all strings found with the replace_buffer.

        As with replace_next, you probably don't want to call this manually.
        """
        if self._search_state is None:
            return
        temp_cursor = self._editor.textCursor()
        times = 0
        self._editor.moveCursor(QTextCursor.Start)
        while True:
            found = self._search_state.find(self._editor)
            if found:
                self._editor.textCursor().insertText(replace_buffer)
                times += 1
            else:
                break
        if times:
            self.log(f'{times} instance{"" if times == 1 else "s"} replaced')
        else:
            self.error('Text not found')
        self._editor.setTextCursor(temp_cursor)

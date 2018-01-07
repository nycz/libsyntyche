# © nycz 2013
# Licenced under MIT.

import json
import os
import os.path
import re
import shutil
import sys
import traceback

from typing import Any, Callable

# ============= IO/file handling ====================
def read_json(path: str) -> str:
    return json.loads(read_file(path))

def write_json(path: str, data: Any, sort_keys: bool = True, default=None) -> None:
    write_file(path, json.dumps(data, ensure_ascii=False,
                                indent=2,
                                sort_keys=sort_keys,
                                default=default))

def read_file(path: str) -> str:
    with open(path, encoding='utf-8') as f:
        data = f.read()
    return data

def write_file(path: str, data: str) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(data)

def local_path(path: str) -> str:
    return os.path.join(sys.path[0], path)

def make_sure_config_exists(config: str, defconfig: str) -> None:
    """
    Check if the file exists, otherwise copy the default
    file to the path instead, creating directories if needded
    """
    if not os.path.exists(config):
        path = os.path.dirname(config)
        if not os.path.exists(path):
            os.makedirs(path, mode=0o755, exist_ok=True)
        shutil.copyfile(defconfig, config)
        print('No config found, copied the default to {}.'.format(config))
# ===================================================


# ============= Misc functions ======================
def print_traceback() -> None:
    traceback.print_exc(file=sys.stdout)
# ===================================================


# ============= Qt Specific =========================
def kill_theming(layout) -> None:
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

def set_hotkey(key: str, target: Any, callback: Callable[[Any], Any]) -> None:
    from PyQt5 import QtWidgets, QtGui
    QtWidgets.QShortcut(QtGui.QKeySequence(key), target, callback)
# ===================================================


# ============= Enhanced CSS ========================
# DEPRECATED AS FUCK
def parse_stylesheet(data):
    """
    Return a valid CSS or Qt CSS stylesheet.

    The path can be a valid CSS/QSS file or a SASS-like CSS/QSS file, that
    will then be parsed to conform to CSS/QSS standards.

    Basically this is a metaparser that adds variables to the stylesheet,
    using the following syntax:

    /* Declaration */
    $variable_name: value;
    /* Usage */
    $variable_name anywhere in the stylesheet
    """

    allowed_chars = 'a-zA-Z0-9_'

    variable_declaration_rx = re.compile(r"""^
        \$(?P<key>[{legal_chars}]+?)
        \s*
        :
        \s*
        (?P<value>.+?);?
    $""".format(legal_chars=allowed_chars), re.MULTILINE | re.VERBOSE)

    stylesheet = '\n'.join([l for l in data.splitlines()
                            if not l.startswith('$')])

    find_str = r'\${varname}(?=[^{legal_char}]|$)'

    for key, value in variable_declaration_rx.findall(data):
        searchterm = find_str.format(varname=key, legal_char=allowed_chars)
        stylesheet, subs = re.subn(searchterm, value, stylesheet)
        if not subs:
            print('[stylesheet] warning: ${} is never used'.format(key))

    return stylesheet
# ===================================================

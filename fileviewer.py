import html
import os.path
try:
    import markdown
except ImportError:
    markdown_available = False
else:
    markdown_available = True

from PyQt4 import QtCore, QtGui, QtWebKit

from typing import Optional

from libsyntyche.common import read_file

html_boilerplate = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style type="text/css">{css}</style>
</head>
<body>{body}</body>
</html>"""

default_css = """
body {
  font-family: Helvetica, arial, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  background-color: #222;
  color: #ddd;
  width: 950px;
  margin: 0px auto;
}

h1 {
  border-bottom: 1px solid #505050;
}

h2 {
  border-bottom: 1px solid #333;
}

code, tt {
  background-color: #333;
  border: 1px solid #505050;
  border-radius: 3px;
  font-family: Consolas, "Liberation Mono", Menlo, Courier, monospace;
  font-size: 12px;
  padding: 1px 4px;
}

pre {
  background-color: #333;
  border: 1px solid #505050;
/*  font-size: 13px;*/
  line-height: 19px;
  overflow: auto;
  padding: 6px 10px;
  border-radius: 3px;
}

pre code, pre tt {
  background-color: transparent;
  border: none;
  padding: 0px;
}
::-webkit-scrollbar {
    background-color: #222;
    height: 15px;
    width: 15px;
}
::-webkit-scrollbar-button {
    display: none;
}
::-webkit-scrollbar-thumb {
    background-color: #111;
}
::-webkit-scrollbar-corner {
    background-color: #222;
}
"""


class FileViewer(QtWebKit.QWebView):

    def __init__(self, parent: QtGui.QWidget) -> None:
        super().__init__(parent)

    def set_page(self,
                 text: Optional[str] = None,
                 fname: Optional[str] = None,
                 css: Optional[str] = default_css,
                 format: str = 'auto') -> None:
        assert (text and not fname) or (fname and not text)
        if not css:
            css = default_css
        if not text:
            text = read_file(fname)
        page = generate_page(text, fname, css, format)
        self.setHtml(page)


def generate_page(text: str, fname: str, css: str, format: str) -> str:
    formats = ('rawtext', 'markdown', 'html')
    fallback = 'rawtext'
    # Figure out the format
    if format == 'auto':
        if fname:
            ext = os.path.splitext(fname)[1].lower()
            if ext == '.md':
                format = 'markdown'
            elif ext in ('.html', '.htm', '.xhtml', '.xht'):
                format = 'html'
            elif ext == '.txt':
                format = 'rawtext'
            else:
                format = fallback
        else:
            format = fallback
    # Check to see if the markdown lib exists
    if format == 'markdown' and not markdown_available:
        format = fallback
    # Check if format is supported at all
    if format not in formats:
        format = fallback
    # Parse the shit
    if format == 'rawtext':
        body = html.escape(text).replace('\n', '<br>')
        return html_boilerplate.format(body='<pre>{}</pre>'.format(body), css=css)
    elif format == 'markdown':
        body = markdown.markdown(text)
        return html_boilerplate.format(body=body, css=css)
    elif format == 'html':
        return text


if __name__ == '__main__':
    from libsyntyche.common import write_file
    fname = '/home/nycz/gitprojects/sapfo/README.md'
    text = read_file(fname)
    page = generate_page(text, fname, '', 'auto')
    write_file('/home/nycz/gitprojects/libsyntyche/test.html', page)
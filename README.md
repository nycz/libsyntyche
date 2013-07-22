libsyntyche
===========
Common functions for my Python/PyQt programs


Installation
------------
1. Clone the repo to a location of your liking. 
2. `# ln -s /path/to/gitprojects/libsyntyche/ /usr/lib/pythonX.Y/site-packages/`


Is that CSS or are you just happy to see me
-------------------------------------------

The language used in `read_stylesheet()` is a modified version of Qt's CSS:
http://qt-project.org/doc/qt-4.8/stylesheet-reference.html
that adds variables.

###Variables###
A line beginning with `$` is interpreted as a variable definition and should have the syntax `$variable: value`.

A variable's name consists of A-Z, a-z, 0-9 and underscore.

All valid defined variables are replaced with their respective values before Qt parses the stylesheet.
Variables that have not been declared will not be replaced but instead make Qt cry. Don't make Qt cry.

Invalid variable definitions are ignored, and will very likely also make Qt cry. Do not make Qt cry.

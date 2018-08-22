# GRAIDE: GRAphite Integrated Development Environment

Graide is an integrated development envrionment that can be used
to develop fonts with Graphite features.
[Graphite](http://graphite.sil.org) is a "smart font" system
developed specifically to handle the complexities of lesser-known
languages of the world.

## Installation

Graide uses [GrCompiler](https://github.com/silnrsi/grcompiler).
Please install it.
Alternatively you can bundle it with this Python package.
Either set the environment variable `GRCOMPILER_BUNDLE`
to a git reference (e.g. master) and be sure to have its build
toolchain installed or set the variable to any other value and
the builtin version is copied to the package.

You can install graide from from this directory with pip:
`pip install -e .`

Additionally, run 1 (with Qt4) or 2 (with Qt5):
1. `pip install PySide`
2. `pip install PySide2`

You will then have the Python script `graide` installed.

## Development

The build dependencies are listed in setup.py's `install_requires`.
Graide uses [QtPy](https://pypi.org/project/QtPy/) to abstract its
Qt bindings. Therefore [PySide](https://pypi.org/project/PySide/)
or [PySide2](https://pypi.org/project/PySide2/) is needed as an
additional runtime dependency. Using any PyQt version is not
supported.

For those wanting to add images to the lib/graide/images directory.
Make sure you update the pyresources.qrc and run:
```
pyside2-rcc -o pyresources.py pyresources.qrc
sed -i -e 's/PySide2/qtpy/' pyresources.py
```
so that you can see the images from the program.

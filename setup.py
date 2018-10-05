#!/usr/bin/python

import os
from setuptools import setup
from io import open

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

PKG_ROOT = 'lib'
bundle = os.environ.get('GRCOMPILER_BUNDLE')
if bundle:
    import grcompiler
    PKG_DATA = grcompiler.build(PKG_ROOT, bundle)
else:
    PKG_DATA = {}

setup(  name = 'graide',
        version = '0.8',
        description = 'Graphite Integrated Development Environment',
        author = 'Martin Hosken',
        author_email = 'martin_hosken@sil.org',
        license = 'LGPL-2.1+',
        url = 'https://github.com/silnrsi/graide',
        package_dir = {'' : PKG_ROOT},
        packages = ['graide', 'graide/makegdl'],
        package_data = PKG_DATA,
        install_requires = ['future', 'configparser', 'QtPy', 'FontTools', 'graphite2', 'freetype-py'],
        extras_require = {'qt4': ['PySide'], 'qt5': ['PySide2']},
        scripts = ['graide'],
        zip_safe = False,
        long_description = long_description,
        long_description_content_type = 'text/markdown',
        classifiers = [
            'Development Status :: 3 - Alpha',
            'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3'
        ]
)

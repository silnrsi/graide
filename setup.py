#!/usr/bin/python

import os
from setuptools import setup

if os.environ.get('GRCOMPILER_BUNDLE_VERSION'):
    import grcompiler
    BIN = ['grcompiler/*']
    CMDCLASS = {'bdist_wheel':grcompiler.BuildBdistWheel}
else:
    BIN = []
    CMDCLASS = {}

setup(  name = 'graphite-graide',
        version = '0.8',
        description = 'Graphite Integrated Development Environment',
        author = 'M. Hosken',
        package_dir = {'' : 'lib'},
        packages = ['graide', 'graide/makegdl', 'ttfrename'],
        package_data = {'graide' : BIN},
        install_requires = ['future', 'configparser', 'QtPy', 'fontTools', 'graphite2', 'freetype-py'],
        scripts = ['graide', 'ttfrename'],
        cmdclass = CMDCLASS,
        zip_safe = False
)

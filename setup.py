#!/usr/bin/python

from sys import platform
from setuptools import setup

BIN = []
if platform == 'win32':
    BIN.append('grcompiler_win/*')
elif platform == 'darwin':
    BIN.append('grcompiler_mac/*')

setup(  name = 'graphite-graide',
        version = '0.8',
        description = 'Graphite Integrated Development Environment',
        author = 'M. Hosken',
        package_dir = {'' : 'lib'},
        packages = ['graide', 'graide/makegdl', 'ttfrename'],
        package_data = {'graide' : BIN},
        install_requires = ['future', 'configparser', 'QtPy', 'fontTools', 'graphite2', 'freetype-py'],
        scripts = ['graide', 'ttfrename'],
        zip_safe = False
)

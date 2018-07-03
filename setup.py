#!/usr/bin/python

from setuptools import setup
import sys
from glob import glob

kw = {}
scripts = ['graide', 'ttfrename']

setup(  name = 'graphite-graide',
        version = '0.8',
        description = 'Graphite Integrated Development Environment',
        author = 'M. Hosken',
        package_dir = {'' : 'lib'},
        packages = ['graide', 'graide/makegdl', 'ttfrename'],
        install_requires = ['future', 'configparser', 'QtPy', 'fontTools', 'graphite2', 'freetype-py'],
        scripts = scripts,
        **kw
)


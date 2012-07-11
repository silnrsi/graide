#!/usr/bin/python

from distutils.core import setup
import sys

kw = {}
if sys.platform == "win32" :
    kw['package_data'] = {'graide' : 'dll/*.dll'}

setup(  name = 'graide',
        version = '0.0.1',
        description = 'Graphite Integrated Development Environment',
        author = 'M. Hosken',
        package_dir = {'' : 'lib'},
        packages = ['graide', 'graide/freetype', 'graide/makegdl'],
        scripts = ['graide'],
        **kw
)


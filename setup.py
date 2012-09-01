#!/usr/bin/python

from distutils.core import setup
import sys
from glob import glob

kw = {}
scripts = ['graide', 'ttfrename']
if sys.platform == "win32" :
    scripts += glob('lib/graide/dll/*.dll')

setup(  name = 'graide',
        version = '0.0.1',
        description = 'Graphite Integrated Development Environment',
        author = 'M. Hosken',
        package_dir = {'' : 'lib'},
        packages = ['graide', 'graide/freetype', 'graide/makegdl', 'ttfrename'],
        scripts = scripts,
        **kw
)


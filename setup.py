#!/usr/bin/python

from distutils.core import setup

setup(  name = 'graide',
        version = '0.0.1',
        description = 'Graphite Integrated Development Environment',
        author = 'M. Hosken',
        package_dir = {'' : 'lib'},
        packages = ['graide', 'graide/freetype'],
        scripts = ['graide']
)


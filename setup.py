#!/usr/bin/python

import os
from setuptools import setup
from io import open

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

if os.environ.get('GRCOMPILER_BUNDLE_VERSION'):
    from distutils.command.bdist import bdist
    from wheel.bdist_wheel import bdist_wheel
    from grcompiler import build

    class BuildBdist(bdist):
        def run(self):
            build()
            bdist.run(self)

    class BuildBdistWheel(bdist_wheel):
        def run(self):
            build()
            bdist_wheel.run(self)

    BIN = ['grcompiler/*']
    CMDCLASS = {'bdist':BuildBdist, 'bdist_wheel':BuildBdistWheel}
else:
    BIN = []
    CMDCLASS = {}

setup(  name = 'graide',
        version = '0.8',
        description = 'Graphite Integrated Development Environment',
        author = 'Martin Hosken',
        author_email = 'martin_hosken@sil.org',
        license = 'LGPL-2.1+',
        url = 'https://github.com/silnrsi/graide',
        package_dir = {'' : 'lib'},
        packages = ['graide', 'graide/makegdl', 'ttfrename'],
        package_data = {'graide' : BIN},
        install_requires = ['future', 'configparser', 'QtPy', 'fontTools', 'graphite2', 'freetype-py'],
        scripts = ['graide', 'ttfrename'],
        cmdclass = CMDCLASS,
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

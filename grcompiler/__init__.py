#    Copyright 2018, Bastian Germann
#    All rights reserved.
#
#    This library is free software; you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation; either version 2.1 of License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should also have received a copy of the GNU Lesser General Public
#    License along with this library in the file named "LICENSE".
#    If not, write to the Free Software Foundation, 51 Franklin Street,
#    suite 500, Boston, MA 02110-1335, USA or visit their web page on the
#    internet at http://www.fsf.org/licenses/lgpl.html.

import os
import shutil
import tempfile
from glob import glob
from subprocess import check_call
from sys import platform
from zipfile import ZipFile
try:
    from urllib.request import urlretrieve
    from urllib.error import HTTPError
except ImportError:
    from urllib import urlretrieve
    from urllib2 import HTTPError

def build(root, version):
    origdir = os.getcwd()
    tmpdir = tempfile.mkdtemp()

    try:
        urlretrieve('https://github.com/silnrsi/grcompiler/archive/' + version + '.zip', tmpdir + '/grc.zip')
        os.chdir(tmpdir)
        grcz = ZipFile('grc.zip')
        grcz.extractall()
        grcz.close()

        os.chdir('grcompiler-' + version)
        if platform == 'win32':
            # possible improvement: check for 64 bit compiler and download a 64 bit version
            urlretrieve('http://download.icu-project.org/files/icu4c/56.1/icu4c-56_1-Win32-msvc10.zip', 'icu.zip')
            icuz = ZipFile('icu.zip')
            icuz.extractall()
            icuz.close()

            # the make file expects an icu source package to find the headers
            os.chdir('icu')
            os.mkdir('source')
            shutil.move('include', 'source/common')

            os.chdir('../preprocessor')
            check_call(['nmake', '-f', 'gdlpp.mak'])

            os.chdir('..')
            check_call(['nmake', '-f', 'makefile.mak'])
            binaries = glob('release/*')
        else:
            check_call(['autoreconf', '-i'])
            check_call(['./configure'])
            check_call(['make'])
            binaries = ['compiler/grcompiler', 'preprocessor/gdlpp']

    except HTTPError as e:
        if os.path.exists('grcompiler/' + platform):
            binaries = glob('grcompiler/' + platform + '/*')
        else:
            raise e

    dst = os.path.join(origdir, root, 'graide', 'grcompiler')
    if binaries and not os.path.exists(dst):
        os.mkdir(dst)
    for f in binaries:
        shutil.copy(f, dst)

    os.chdir(origdir)
    shutil.rmtree(tmpdir)
    return {'graide' : ['grcompiler/*']}

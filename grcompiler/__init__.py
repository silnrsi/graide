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

        os.chdir(glob('grcompiler-*')[0])
        check_call(['cmake', '-DCMAKE_BUILD_TYPE=Release', '.'])
        check_call(['cmake', '--build', '.'])
        # include binaries and license texts
        binaries = glob('compiler/icud*') + glob('compiler/icuu*') + glob('compiler/grcompiler*') + ['compiler/stddef.gdh']
        binaries += glob('license/*') + glob('preprocessor/gdlpp*')

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

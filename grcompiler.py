try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve
import os
import shutil
import tempfile
from subprocess import check_call
from zipfile import ZipFile
from wheel.bdist_wheel import bdist_wheel

class BuildBdistWheel(bdist_wheel):
    def run(self):
        origdir = os.getcwd()
        tmpdir = tempfile.mkdtemp()

        os.chdir(tmpdir)
        version = os.environ.get('GRCOMPILER_BUNDLE_VERSION')
        urlretrieve('https://github.com/silnrsi/grcompiler/archive/' + version + '.zip', 'grc.zip')
        grcz = ZipFile('grc.zip')
        grcz.extractall()

        os.chdir('grcompiler-' + version)
        if os.name == 'nt':
            # possible improvement: check for 64 bit compiler and download a 64 bit version
            urlretrieve('http://download.icu-project.org/files/icu4c/56.1/icu4c-56_1-Win32-msvc10.zip', 'icu.zip')
            icuz = ZipFile('icu.zip')
            icuz.extractall()

            # the make file expects an icu source package to find the headers
            os.chdir('icu')
            os.mkdir('source')
            shutil.move('include', 'source/common')

            os.chdir('../preprocessor')
            check_call(['nmake', '-f', 'gdlpp.mak'])

            os.chdir('..')
            check_call(['nmake', '-f', 'makefile.mak'])
            binaries = ['release/*']
        else:
            check_call(['autoreconf', '-i'])
            check_call(['./configure'])
            check_call(['make'])
            binaries = ['compiler/grcompiler', 'preprocessor/gdlpp']
        dst = os.path.join(origdir, 'lib', 'graide', 'grcompiler')
        os.mkdir(dst)
        for f in binaries:
            shutil.copy(f, dst)

        os.chdir(origdir)
        shutil.rmtree(tmpdir)

        bdist_wheel.run(self)

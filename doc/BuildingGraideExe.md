This document describes building graide.exe using 64-bit Python 3.9 on Windows 10. This process includes installing graide into a Python virtual environment, which may be desirable even if not building a Windows exe

**Gather the pieces**

Acquire a 64-bit graphite2.dll either by building a release version from source using the graphite repo or by downloading it from Team City using the guest login.
https://github.com/silnrsi/graphite
https://build.palaso.org/viewType.html?buildTypeId=Graphite_Windows64bitProduction

Clone the graide and graphite repos.
https://github.com/silnrsi/graide
https://github.com/silnrsi/graphite

The graide repo includes a bundled Graphite compiler. If a newer version is desired, install the Graphite compiler using an installer from its repo or build a release version from source. Then, update the files in the graide\grcompiler\win32 folder from the Graphite compiler (e.g. grcompiler.exe, icudt66.dll, icuuc66.dll, gdlpp.exe, stddef.gdh).
https://github.com/silnrsi/grcompiler/releases
https://github.com/silnrsi/grcompiler

**Create a Python virual environment for graide**

The following describes how to install graide in a Python virtual enviroment (venv). Such environments provide a way to install a Python-based application with all its dependencies in a way that isolates it from any Python system already present on a system. The application thus does not interfere with the system Python and is not affected by subsequent changes to the system Python. 

Python 3.9 (64-bit) needs to be installed. At a command prompt, the following will create the virtual environment in a folder called graide in the current directory.

python -m venv graide

Activate the venv. The command prompt will change. All subsequent steps assume the venv is active. This is what causes the isolated Python in the venv to be used instead of the system Python. (Basically, the PATH has been changed so the Python in the venv comes before other Python interpreters, and several Python environment variables have been set so packages in the venv will be used.)

cd graide
Scripts\activate

FYI, the venv can be deactivated using 'deactivate'.

By default the venv includes the pip and setuptools packages. Pip should be upgraded from PyPI using:

python -m pip install --upgrade pip

Graide depends on the Qt GUI toolkit and its Python bindings. Install this in the venv from PyPI using:

pip install PySide2

The Python graphite bindings and graide itself need to be installed in the venv. Several other packages will be installed when this is done. In order to include the Graphite compiler in the graide repo, the GRCOMPILER_BUNDLE environment variable needs to be set before installing graide. 

set GRCOMPILER_BUNDLE=1
in the graphite repo, run 'python setup.py build' and 'python setup.py install'
in the graide repo, run 'python setup.py build' and 'python setup.py install'

The graphite2.dll acquired previously needs to be copied to the graide\Scripts folder in the venv, so it's in the PATH that is set when the venv is active and can be found by the Python graphite bindings.

The graide installation can be tested by running 'python Scripts\graide' in the venv

**Build graide.exe**

To build a Windows exe, PyInstaller can be used. Install it from PyPI in the active venv:

pip install PyInstaller

The command line to build the exe is:
pyinstaller --onefile --icon <path to icon file in graide repo> <path to graide script in graide venv> 

The icon file can be found in the graide repo at 
<path repo folder>\graide\lib\graide\images\graide.ico 

The path to the graide script in the venv must be used. This is NOT the same thing as the launcher in graide\Scripts that was used to run graide previously. The script can be found at something like:

<path to graide venv>\graide\Lib\site-packages\graide-1.1-py3.9.egg\EGG-INFO\scripts\graide

This will produce 'graide.exe' in the venv 'graide\dist' folder. It will also produce a 'graide.spec' file in the venv graide folder. To build the exe again, you can run the following instead of the previous command:

pyinstaller --clean graide.spec 

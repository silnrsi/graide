# Building a Graphite IDE Windows application #

This document describes building graide.exe using 64-bit Python 3.9 on Windows 10. This process includes installing graide into a Python virtual environment, which may be desirable even if not building a Windows exe. Graide.exe can be copied to a Windows system and used without installing Python.

## Gather the pieces ##

Acquire a 64-bit `graphite2.dll` either by building a release version from source using the graphite [repo](https://github.com/silnrsi/graphite) or by downloading it from [Team City](https://build.palaso.org/viewType.html?buildTypeId=Graphite_Windows64bitProduction) using the guest login provided there.

Clone the [graide](https://github.com/silnrsi/graide) and [graphite](https://github.com/silnrsi/graphite) repos.

The graide repo includes a bundled Graphite compiler. If a newer version is desired, install the Graphite compiler using an installer from its [repo](https://github.com/silnrsi/grcompiler/releases) or build a release version from [source](https://github.com/silnrsi/grcompiler). Then, update the files in the `graide` repo at `graide\grcompiler\win32` from the Graphite compiler installation or build (e.g. `grcompiler.exe`, `icudt66.dll`, `icuuc66.dll`, `gdlpp.exe`, `stddef.gdh`).

## Install graide in a Python virtual environment ##

The following describes how to install graide in a Python virtual environment (venv). Such environments provide a way to install a Python-based application with all its dependencies in a way that isolates it from any Python system already present on a system. The application thus does not interfere with the system Python and is not affected by subsequent changes to the system Python. 

Python 3.9 (64-bit) needs to be installed. At a command prompt, the following will create the virtual environment in a folder called graide in the current directory.

    python -m venv graide

Activate the venv. The command prompt will change. **All subsequent steps assume the venv is active.** This is what causes the isolated Python in the venv to be used instead of the system Python. (Basically, the Windows `PATH` has been changed so the Python in the venv comes before other Python interpreters, and several Python environment variables have been set so packages in the venv will be used.)

    cd graide
    Scripts\activate

FYI, the venv can be deactivated using `deactivate`.

By default the venv includes the `pip` and `setuptools` packages. Pip should be upgraded from PyPI using:

    python -m pip install --upgrade pip

Graide uses Qt and Python bindings for its GUI. Install this in the venv from PyPI using:

    pip install PySide2

The Python graphite bindings and graide itself need to be built and installed in the venv using the respective `setup.py` scripts in the repos cloned above. (Several other packages will be installed when this is done.) To use the Graphite compiler from the graide repo, the `GRCOMPILER_BUNDLE` environment variable needs to be set before installing graide. 

    set GRCOMPILER_BUNDLE=1
    cd <graphite repo>
    python setup.py build
    python setup.py install
    cd <graide repo>
    python setup.py build
    python setup.py install

The `graphite2.dll` acquired previously needs to be copied to the `graide\Scripts` folder in the venv, so it's in the PATH that is set when the venv is active and can be found by the Python graphite bindings.

The graide installation can be tested by running `python Scripts\graide` in the venv

    cd <graide venv>
    python Scripts\graide

## Build graide.exe ##

To build a Windows executable, `PyInstaller` can be used. Install it from PyPI in the active venv:

    pip install PyInstaller

The command line to build the exe is:

    pyinstaller --onefile --icon <path to icon file in graide repo> <path to graide script in graide venv> 

The icon file can be found in the graide repo at `<path to repo folder>\graide\lib\graide\images\graide.ico`

The path to the graide script in the venv must be used. This is NOT the same thing as the launcher in graide\Scripts that was used to run graide previously. The script can be found at something like: `<path to graide venv>\graide\Lib\site-packages\graide-1.1-py3.9.egg\EGG-INFO\scripts\graide`

This will produce `graide.exe` in the venv `graide\dist` folder. It will also produce a `graide.spec` file in the venv `graide` folder. To build the exe again, you can run the following instead of the previous command:

    pyinstaller --clean graide.spec 

The `graide.exe` file should run on a Windows system without the need to install Python, or if Python is installed there, without affecting it. It includes a Python interpreter, all the dependent packages, and the graide code, which will be unpacked into a temporary folder and executed when `graide.exe` is ran.

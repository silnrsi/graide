# -*- mode: python -*-
import sys, platform, glob, os

macfixup='''
import sys
import os

for t in ('QtCore', 'QtGui', 'QtSvg', 'QtXml') :
    s = os.path.join(sys._MEIPASS, t)
    f = os.path.join(sys._MEIPASS, 'lib' + t + '.4.dylib')
    if not os.path.exists(s) : continue
    if os.path.exists(f) : os.unlink(f)
    os.symlink(s, f)
'''
#''' to keep vim happy

versionSuffix = '0_8_75'
showConsole = False
consoleSuffix = '_console' if showConsole else ''

def toc_remove(atoc, *anames) :
    atoc.data = filter(lambda x: x[0] not in anames, atoc.data)

libdir = 'lib'
ext = ''
if sys.platform.startswith('linux') :
    libdir += '-linux-' + platform.machine() + '-2.7'

pathex=[os.path.dirname(sys.argv[0]), 'build/' + libdir]

if sys.platform == 'win32' :
    pydir = os.path.dirname(sys.executable)
    pth = os.path.join(pydir, 'Lib\\site-packages\\pyside')
    pathex.append(pth)
    ext = '.exe'

a = Analysis(['build/scripts-2.7/graide'],
             pathex=pathex,
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
bins = a.binaries
if sys.platform == 'win32' :
    for d in ('zlib1', 'freetype6', 'graphite2', 'msvcr100') :
        bins += [(d + '.dll', 'build/scripts-2.7/' + d + '.dll', 'BINARY')]
    for d in glob.glob('grcompiler_win/*.*') :
        bins += [(d[15:], d, 'BINARY')]
    pydir = os.path.dirname(sys.executable)
    pth = os.path.join(pydir, 'Lib\\site-packages\\pyside')
    for d in ('QtSvg', 'QtXml') :
        bins += [(d+'4.dll', os.path.join(pth, d+'4.dll'), 'BINARY')]
    pth = os.path.join(pth, 'plugins')
    for d in glob.glob(os.path.join(pth, 'imageformats/*')) :
        if os.path.exists(d) :
            bins += [(d[len(pth):], d, 'BINARY')]
#    import pdb; pdb.set_trace()
elif sys.platform == 'darwin' :
    pth = '/opt/local/Library/Frameworks/QtGui.framework/Versions/4/Resources/'
    for d in glob.glob(pth + 'qt_menu.nib/*') :
        a.datas.append((d[len(pth):], d, 'DATA'))
    for d in glob.glob('grcompiler_mac/*') :
        bins += [(d[15:], d, 'BINARY')]
    pth = '/opt/local/lib/'
    for d in ('QtSvg', 'QtXml') :
        rname = '/opt/local/Library/Frameworks/{0}.framework/Versions/4/{0}'.format(d)
        if os.path.exists(rname) :
            bins += [(d, rname, 'BINARY')]
    pth = '/opt/local/share/qt4/plugins/'
    for d in glob.glob(pth + 'imageformats/*') :
        if os.path.exists(d) :
            bins += [(d[len(pth):], d, 'BINARY')]
    for d in ('freetype.6', 'graphite2', 'icui18n.48', 'icuuc.48', 'icudata.48') :
        fn = 'lib' + d + '.dylib'
        for pth in ('/usr/local/lib', '/opt/local/lib') :
            if os.path.exists(os.path.join(pth, fn)) :
                bins += [(fn, os.path.join(pth, fn), 'BINARY')]
    f = file("build/myrthook", "w")
    f.write(macfixup)
    f.close()
    a.scripts.insert(-1, ("myrthook", "build/myrthook", "PYSOURCE"))
    bins.append(('QtGui', '/opt/local/Library/Frameworks/QtGui.framework/Versions/4/QtGui', 'BINARY'))
    toc_remove(bins, 'libQtCore.4.dylib', 'libQtGui.4.dylib')

exe = EXE(pyz,
          a.scripts,
          bins,
          a.zipfiles,
          a.datas,
          name=os.path.join('build', 'graide' + versionSuffix + consoleSuffix + ext),
          debug=False,
          strip=None,
          upx=True,
          icon=os.path.join('lib', 'graide', 'images', ('graide.ico' if sys.platform == 'win32' else 'graide.icns')),
          console=showConsole)

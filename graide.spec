# -*- mode: python -*-
import sys, platform, glob, os

macfixup='''
import sys
import os

f = os.path.join(sys._MEIPASS, 'libqtcore.4.dylib')
os.unlink(f)
os.symlink(os.path.join(sys._MEIPASS, 'QtCore'), f)
'''

libdir = 'lib'
ext = ''
if sys.platform == 'linux2' :
    libdir += '-linux-' + platform.machine() + '-2.7'
elif sys.platform == 'win32' :
    ext = '.exe'

a = Analysis(['build/scripts-2.7/graide'],
             pathex=[os.path.dirname(sys.argv[0]), 'build/' + libdir],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
bins = a.binaries
if sys.platform == 'win32' :
    for d in ('zlib1', 'freetype6', 'graphite2', 'msvcr100') :
        bins += [(d + '.dll', 'build/scripts-2.7/' + d + '.dll', 'BINARY')]
    for d in glob.glob('grcompiler_win/*.*') :
        bins += [(d[15:], d, 'BINARY')]
#    import pdb; pdb.set_trace()
#    grdeps = bindepend.Dependencies([('graphite2.dll', 'build/scripts-2.7/graphite2.dll', 'BINARY')])
#    bins += grdeps
#    print grdeps
elif sys.platform == 'darwin' :
    pth = '/opt/local/Library/Frameworks/QtGui.framework/Versions/4/Resources/'
    for d in glob.glob(pth + 'qt_menu.nib/*') :
        a.datas.append((d[len(pth):], d, 'DATA'))
#    pth = '/opt/local/lib/'
#    for d in ('QtSvg', 'QtXml') :
#        lname = 'lib'+d+'.4.dylib'
#        rname = os.path.realpath(os.path.join(pth, lname))
#        if os.path.exists(rname) :
#            bins += [(lname, rname, 'BINARY')]
#    pth = '/opt/local/share/qt4/plugins/'
#    for d in glob.glob(pth + 'imageformats/*') :
#        if os.path.exists(d) :
#            bins += [(d[len(pth):], d, 'BINARY')]
    for d in ('freetype.6', 'graphite2') :
        fn = 'lib' + d + '.dylib'
        for pth in ('/usr/local/lib', '/opt/local/lib') :
            if os.path.exists(os.path.join(pth, fn)) :
                bins += [(fn, os.path.join(pth, fn), 'BINARY')]
    f = file("build/myrthook", "w")
    f.write(macfixup)
    f.close()
    a.scripts.insert(-1, ("myrthook", "build/myrthook", "PYSOURCE"))

exe = EXE(pyz,
          a.scripts,
          bins,
          a.zipfiles,
          a.datas,
          name=os.path.join('build', 'graide' + ext),
          debug=False,
          strip=None,
          upx=True,
          icon=os.path.join('lib', 'graide', 'images', ('graide.ico' if sys.platform == 'win32' else 'graide.icns')),
          console=False)

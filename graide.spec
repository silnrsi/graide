# -*- mode: python -*-
import sys, platform
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
#    import pdb; pdb.set_trace()
#    grdeps = bindepend.Dependencies([('graphite2.dll', 'build/scripts-2.7/graphite2.dll', 'BINARY')])
#    bins += grdeps
#    print grdeps

exe = EXE(pyz,
          a.scripts,
          bins,
          a.zipfiles,
          a.datas,
          name=os.path.join('build', 'graide' + ext),
          debug=False,
          strip=None,
          upx=True,
          console=True )

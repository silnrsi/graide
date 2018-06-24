# -*- mode: python -*-
import sys, platform, glob

libdir = 'lib'
ext = ''
if sys.platform == 'linux2' :
    libdir += '-linux-' + platform.machine() + '-2.7'
elif sys.platform == 'win32' :
    ext = '.exe'

a = Analysis(['build/scripts-2.7/ttfrename'],
             pathex=[os.path.dirname(sys.argv[0]), 'build/' + libdir],
             hiddenimports=['fontTools.ttLib.tables._p_o_s_t'],
	     excludes=['win32com', 'numpy.test', 'tcl', 'tk', '_tkinter'],
             hookspath=None)
pyz = PYZ(a.pure)
bins = a.binaries
if sys.platform == 'win32' :
    for d in ('zlib1', 'freetype6') :
        bins += [(d + '.dll', 'build/scripts-2.7/' + d + '.dll', 'BINARY')]
#    for d in glob.glob('grcompiler_win/*.*') :
#        bins += [(d[15:], d, 'BINARY')]
#    import pdb; pdb.set_trace()
#    grdeps = bindepend.Dependencies([('graphite2.dll', 'build/scripts-2.7/graphite2.dll', 'BINARY')])
#    bins += grdeps
#    print(grdeps)

exe = EXE(pyz,
          a.scripts,
          bins,
          a.zipfiles,
          a.datas,
          name=os.path.join('build', 'ttfrename' + ext),
          debug=False,
          strip=None,
          upx=True,
          console=True )

from graide.graphite import gr2
from ctypes import cdll
from ctypes.util import find_library
import os, sys, subprocess
from tempfile import mktemp
from shutil import copyfile

libc = cdll.LoadLibrary(find_library("msvcrt" if sys.platform == "win32" else "c"))

class ModelSuper(object) :
    pass

def configval(config, section, option) :
    if config.has_option(section, option) :
        return config.get(section, option)
    else :
        return None

def copyobj(src, dest) :
    for x in dir(src) :
        y = getattr(src, x)
        if not callable(y) and not x.startswith('__') :
            setattr(dest, x, y)

def runGraphite(font, text, debugfile, feats = {}, rtl = 0, lang = 0, size = 16) :
    debugfile.truncate(0)
    grface = gr2.gr_make_file_face(font, 0)
    grfeats = gr2.gr_face_featureval_for_lang(grface, lang)
    for f, v in feats.items() :
        id = gr2.gr_str_to_tag(f)
        fref = gr2.gr_face_find_fref(grface, id)
        gr2.gr_fref_set_feature_value(fref, v, grfeats)
    grfont = gr2.gr_make_font(size, grface)
    gr2.graphite_start_logging(libc.fdopen(debugfile.fileno(), "w"), 0xFF)
    seg = gr2.gr_make_seg(grfont, grface, 0, grfeats, 1, text.encode('utf_8'), len(text), rtl)
    gr2.graphite_stop_logging()

def buildGraphite(config, font, fontfile) :
    if not config.has_option('build', 'gdlfile') :
        return 1
    gdlfile = config.get('build', 'gdlfile')
    if configval(config, 'build', 'usemakegdl') :
        font.createClasses()
        font.pointClasses()
        font.ligClasses()
        f = file(gdlfile, "w")
        font.outGDL(f)
        if config.has_option('build', 'includefile') :
            f.write('#include "%s"\n' % (config.get('build', 'includefile')))
        f.close()
    tempname = mktemp()
    if config.has_option('build', 'usettftable') :
        subprocess.call(("ttftable", "-delete", "graphite", fontfile , tempname))
        print "run ttftable"
    else :
        copyfile(font.fname, tempname)
    res = subprocess.call(("grcompiler", "-w3521", "-w510", "-d", gdlfile, tempname, fontfile))
    os.remove(tempname)
    return res


#    Copyright 2012, SIL International
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

from PySide import QtGui
from graide.graphite import gr2
from ctypes import *
from ctypes.util import find_library
import os, sys, subprocess, re
from tempfile import mktemp
from shutil import copyfile

libc = cdll.LoadLibrary(find_library("msvcrt" if sys.platform == "win32" else "c"))
c = libc.fdopen
c.restype = c_void_p
c.argtypes = [c_int, c_char_p]

mainapp = None
pendingErrors = []

class Layout(object) :
    buttonSpacing = 1
    buttonMargins = (0, 0, 0, 0)
    runEditHeight = 60
    errorColour = QtGui.QColor(255, 160, 160)
    warnColour = QtGui.QColor(255, 255, 160)
    activePassColour = QtGui.QColor(255, 255, 208)

class DataObj(object) :
    
    def attribModel(self) :
        return None

class ModelSuper(object) :
    pass

def configval(config, section, option) :
    if config.has_option(section, option) :
        return config.get(section, option)
    else :
        return None

def configintval(config, section, option) :
    if config.has_option(section, option) :
        txt = config.get(section, option)
        if not txt : return 0
        if txt.isdigit() :
            return int(txt)
        elif txt.lower() == 'true' :
            return 1
        else :
            return 0
    else :
        return 0

def copyobj(src, dest) :
    for x in dir(src) :
        y = getattr(src, x)
        if not callable(y) and not x.startswith('__') :
            setattr(dest, x, y)

def runGraphite(font, text, debugfile, feats = {}, rtl = 0, lang = 0, size = 16) :
    grface = gr2.gr_make_file_face(font, 0)
    grfeats = gr2.gr_face_featureval_for_lang(grface, lang)
    for f, v in feats.items() :
        id = gr2.gr_str_to_tag(f)
        fref = gr2.gr_face_find_fref(grface, id)
        gr2.gr_fref_set_feature_value(fref, v, grfeats)
    grfont = gr2.gr_make_font(size, grface)
    fd = libc.fdopen(debugfile.fileno(), "w")
    gr2.graphite_start_logging(fd, 0xFF)
    seg = gr2.gr_make_seg(grfont, grface, 0, grfeats, 1, text.encode('utf_8'), len(text), rtl)
    gr2.graphite_stop_logging()

def buildGraphite(config, app, font, fontfile) :
    if configintval(config, 'build', 'usemakegdl') :
        gdlfile = configval(config, 'build', 'makegdlfile')
        if config.has_option('main', 'ap') :
            font.saveAP(config.get('main', 'ap'), gdlfile)
        cmd = configval(config, 'build', 'makegdlcmd')
        if cmd and cmd.strip() :
            if config.has_option('main', 'ap') :
                font.saveAP(config.get('main', 'ap'), gdlfile)
            makecmd = expandMakeCmd(config, cmd)
            subprocess.call(makecmd, shell = True)
        else :
            font.createClasses()
            font.pointClasses()
            font.ligClasses()
            v = int(config.get('build', 'pospass'))
            if v > 0 : font.outPosRules(v)
            f = file(gdlfile, "w")
            font.outGDL(f)
            if configval(config, 'build', 'gdlfile') :
                f.write('#include "%s"\n' % (os.path.abspath(config.get('build', 'gdlfile'))))
            f.close()
            app.updateFileEdit(gdlfile)
    else :
        gdlfile = configval(config, 'build', 'gdlfile')
    if not gdlfile or not os.path.exists(gdlfile) :
        f = file('gdlerr.txt' ,'w')
        if not gdlfile :
            f.write("No GDL File specified. Build failed")
        else :
            f.write("No such GDL file: \"%s\". Build failed" % gdlfile)
        f.close()
        return True
    tempname = mktemp()
    if config.has_option('build', 'usettftable') :
        subprocess.call(("ttftable", "-delete", "graphite", fontfile , tempname))
    else :
        copyfile(fontfile, tempname)
    res = subprocess.call(("grcompiler", "-w3521", "-w510", "-d", "-q", gdlfile, tempname, fontfile))
    if res :
        copyfile(tempname, fontfile)
    os.remove(tempname)
    return res

replacements = {
    'a' : ['main', 'ap'],
    'f' : ['main', 'font'],
    'g' : ['build', 'makegdlfile'],
    'i' : ['build', 'gdlfile'],
    'p' : ['build', 'pospass']
}

def expandMakeCmd(config, txt) :
    return re.sub(r'%([afgip])', lambda m: os.path.abspath(configval(config, *replacements[m.group(1)])), txt)

def reportError(text) :
    global mainapp, pendingErrors
    if not mainapp :
        pendingErrors += [text]
    else :
        mainapp.tab_errors.addItem(text)

def registerErrorLog(app) :
    global mainapp, pendingErrors
    mainapp = app
    for e in pendingErrors :
        mainapp.tab_errors.addItem(e)
    pendingErrors = []


def canonET(et, curr = 0, indent = 2) :
    n = len(et)
    if n :
        et.text = "\n" + (' ' * (curr + indent))
        for i in range(n) :
            canonET(et[i], curr + indent, indent)
            et[i].tail = "\n" + (' ' * (curr + indent if i < n - 1 else curr))
    return et

def relpath(p, base) :
    d = os.path.dirname(base) or '.'
    return os.path.relpath(p, d)

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

import os, subprocess, re, sys
from tempfile import mktemp
from shutil import copyfile
from xml.etree import cElementTree as XmlTree

mainapp = None
pendingErrors = []

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

grcompiler = None
def findgrcompiler() :
    global grcompiler
    if sys.platform == 'win32' :
        if getattr(sys, 'frozen', None) :
            grcompiler = os.path.join(sys._MEIPASS, 'grcompiler.exe')
            return grcompiler
        try :
            from _winreg import OpenKey, QueryValue, HKEY_LOCAL_MACHINE
            node = "Microsoft\\Windows\\CurrentVersion\\Uninstall\\Graphite Compiler_is1"
            if sys.maxsize > 1 << 32 :
                r = OpenKey(HKEY_LOCAL_MACHINE, "SOFTWARE\\Wow6432Node\\" + node)
            else:
                r = OpenKey(HKEY_LOCAL_MACHINE, "SOFTWARE\\" + node)
            p = QueryValue(r, "InstallLocation")
            grcompiler = os.path.join(p, "GrCompiler.exe")
        except WindowsError :
            for p in os.environ['PATH'].split(';') :
                a = os.path.join(p, 'grcompiler.exe')
                if os.path.exists(a) :
                    grcompiler = a
                    break
    elif sys.platform == 'darwin' and getattr(sys, 'frozen', None) :
        grcompiler = os.path.join(sys._MEIPASS, 'grcompiler')
        return grcompiler
    else :
        for p in os.environ['PATH'].split(':') :
            a = os.path.join(p, "grcompiler")
            if os.path.exists(a) :
                grcompiler = a
                break
    return grcompiler

# Return 0 if successful.
def buildGraphite(config, app, font, fontfile, errfile = None) :
    global grcompiler
    if configintval(config, 'build', 'usemakegdl') :
        gdlfile = configval(config, 'build', 'makegdlfile')
        
        if config.has_option('main', 'ap') :    # AP XML file
            # Generate the AP GDL file.
            apFilename = config.get('main', 'ap')
            font.saveAP(apFilename, gdlfile)
            if app : app.updateFileEdit(apFilename)
                
        cmd = configval(config, 'build', 'makegdlcmd')
        if cmd and cmd.strip() :
            # Call the make command to perform makegdl.
            makecmd = expandMakeCmd(config, cmd)
            print makecmd
            subprocess.call(makecmd, shell = True)
        else :
            # Use the default makegdl process.
            font.createClasses()
            font.pointClasses()
            font.ligClasses()
            v = int(config.get('build', 'attpass'))
            f = file(gdlfile, "w")
            font.outGDL(f)
            if v > 0 : font.outPosRules(f, v)
            if configval(config, 'build', 'gdlfile') :
                f.write('#include "%s"\n' % (os.path.abspath(config.get('build', 'gdlfile'))))
            f.close()
            if app : app.updateFileEdit(gdlfile)
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
        
    tweakWarning = generateTweakerGDL(config, app)
    if tweakWarning != "" :
        app.tab_errors.addWarning(tweakWarning)
        app.tab_errors.setBringToFront(True)
        
    tempname = mktemp()
    if config.has_option('build', 'usettftable') :
        subprocess.call(("ttftable", "-delete", "graphite", fontfile , tempname))
    else :
        copyfile(fontfile, tempname)
    parms = {}
    if errfile :
        parms['stderr'] = subprocess.STDOUT
        parms['stdout'] = errfile
    if getattr(sys, 'frozen', None) : parms['env'] = os.environ
    res = 1
    if grcompiler is not None :
        res = subprocess.call((grcompiler, "-w3521", "-w510", "-d", "-q", gdlfile, tempname, fontfile), **parms)
    if res :
        copyfile(tempname, fontfile)
    os.remove(tempname)
    
    return res

replacements = {
    'a' : ['main', 'ap'],
    'f' : ['main', 'font'],
    'g' : ['build', 'makegdlfile'],
    'i' : ['build', 'gdlfile'],
    'p' : ['build', 'attpass']
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


def ETcanon(et, curr = 0, indent = 2) :
    n = len(et)
    if n :
        et.text = "\n" + (' ' * (curr + indent))
        for i in range(n) :
            ETcanon(et[i], curr + indent, indent)
            et[i].tail = "\n" + (' ' * (curr + indent if i < n - 1 else curr))
    return et

def ETinsert(elem, child) :
    for (i, e) in enumerate(elem) :
        if e.tag > child.tag :
            elem.insert(i, child)
            return
    elem.append(child)

def relpath(p, base) :
    d = os.path.dirname(base) or '.'
    return os.path.relpath(p, d)

def as_entities(txt) :
    if txt :
        return re.sub(ur'([^\u0000-\u007f])', lambda x: "\\u%04X" % ord(x.group(1)), txt)
    else :
        return ""

def generateTweakerGDL(config, app) :
    if not config.has_option('build', 'tweakxmlfile') :
        return ""
        
    tweakxmlfile = config.get('build', 'tweakxmlfile')
    if not config.has_option('build', 'tweakgdlfile') or config.get('build', 'tweakgdlfile') == "":
        return "Warning: no GDL tweak file specified; tweaks ignored."

    tweakgdlfile = config.get('build', 'tweakgdlfile')
    gdlfile = config.get('build', 'gdlfile')
    fontname = config.get('main', 'font')
    
    tweakData = app.tab_tweak.parseFile(tweakxmlfile)
    
    passindex = configval(config, 'build', 'tweakpass')
    f = file(tweakgdlfile, 'w')
    f.write("/*\n    Tweaker GDL file for font " + fontname + " to include in " + gdlfile + "\n*/\n\n")

    if passindex :
        f.write("pass(" + passindex + ")\n\n")
    
    for (groupLabel, tweaks) in tweakData.items() :
        f.write("\n//---  " + groupLabel + "  ---\n\n")
        
        for tweak in tweaks :
            f.write("// " + tweak.name + "\n")
            i = 0
            for twglyph in tweak.glyphs :
                if twglyph.status != "ignore" :
                    if i > 0 :
                        if len(tweak.glyphs) > 2 :
                            f.write("\n    ")
                        else :
                            f.write("  ")
                    if twglyph.gclass and twglyph.gclass != "" :
                        f.write(twglyph.gclass)
                    else:
                        f.write(twglyph.name);
                    if twglyph.status == "optional" :
                        f.write("?")
                    shiftx = twglyph.shiftx + twglyph.shiftx_pending
                    shifty = twglyph.shifty + twglyph.shifty_pending
                    if shiftx != 0 or shifty != 0 :
                        f.write(" { ")
                        if shiftx != 0 : f.write("shift.x = " + str(shiftx) + "m; ")
                        if shifty != 0 : f.write("shift.y = " + str(shifty) + "m; ")
                        f.write("}")
                i += 1
            f.write(" ;\n\n")
    
    if passindex :
        f.write("\nendpass  // " + passindex + "\n\n")

    f.close()
    
    if app : app.updateFileEdit(tweakgdlfile)
    
    print "Tweak GDL generated - accepting pending tweaks."
    
    # Accept all pending shifts, since they are now part of the Graphite rules.
    app.tab_tweak.acceptPending(tweakxmlfile)
    
    return ""  # success
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
    else :
        for p in os.environ['PATH'].split(':') :
            a = os.path.join(p, "grcompiler")
            if os.path.exists(a) :
                grcompiler = a
                break
    return grcompiler

def buildGraphite(config, app, font, fontfile, errfile = None) :
    global grcompiler
    if configintval(config, 'build', 'usemakegdl') :
        gdlfile = configval(config, 'build', 'makegdlfile')
        if config.has_option('main', 'ap') :
            font.saveAP(config.get('main', 'ap'), gdlfile)
        cmd = configval(config, 'build', 'makegdlcmd')
        if cmd and cmd.strip() :
            makecmd = expandMakeCmd(config, cmd)
            print makecmd
            subprocess.call(makecmd, shell = True)
        else :
            font.createClasses()
            font.pointClasses()
            font.ligClasses()
            v = int(config.get('build', 'pospass'))
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
    tempname = mktemp()
    if config.has_option('build', 'usettftable') :
        subprocess.call(("ttftable", "-delete", "graphite", fontfile , tempname))
    else :
        copyfile(fontfile, tempname)
    parms = {}
    if errfile :
        parms['stderr'] = subprocess.STDOUT
        parms['stdout'] = errfile
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
    return re.sub(ur'([^\u0000-\u007f])', lambda x: "\\u%04X" % ord(x.group(1)), txt)


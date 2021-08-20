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
from qtpy import QtCore, QtGui, QtWidgets
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

def configvalString(config, section, option) :
    if config.has_option(section, option) :
        return config.get(section, option)
    else :
        return ''

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
            from winreg import OpenKey, QueryValue, HKEY_LOCAL_MACHINE
            node = "Microsoft\\Windows\\CurrentVersion\\Uninstall\\Graphite Compiler_is1"
            if sys.maxsize > 1 << 32 :
                r = OpenKey(HKEY_LOCAL_MACHINE, "SOFTWARE\\Wow6432Node\\" + node)
            else:
                r = OpenKey(HKEY_LOCAL_MACHINE, "SOFTWARE\\" + node)
            p = QueryValue(r, "InstallLocation")
            grcompiler = os.path.join(p, "GrCompiler.exe")
        except WindowsError :
            exe = os.path.join(os.path.dirname(__file__), 'grcompiler', 'GrCompiler.exe')
            if os.path.exists(exe) :
                grcompiler = exe
            else :
                for p in os.environ['PATH'].split(';') :
                    a = os.path.join(p, 'grcompiler.exe')
                    if os.path.exists(a) :
                        grcompiler = a
                        break
    else :
        exe = os.path.join(os.path.dirname(__file__), 'grcompiler', 'grcompiler')
        if os.path.exists(exe) :
            grcompiler = exe
        else :
            for p in os.environ['PATH'].split(':') :
                a = os.path.join(p, "grcompiler")
                if os.path.exists(a) :
                    grcompiler = a
                    break
    if grcompiler is None:
        print("...not found")
    else:
        print("...found in " + grcompiler)

# Return 0 if successful.
def buildGraphite(config, app, font, fontFileName, lowLevelErrFile = None, gdlErrFileName = None) :
    global grcompiler

    #print("buildGraphite")

    # Prevent the error-reporting mechanism from interpreting this file as legitimate output
    # in case the entire call fails. (This assumes that the full path to the file is provided,
    # which the caller currently does.)
    try:
        os.remove(gdlErrFileName)
    except:
        pass

    if configintval(config, 'build', 'usemakegdl') :
        gdlFileName = configval(config, 'build', 'makegdlfile')  # auto-generated GDL

        if config.has_option('main', 'ap') and not configval(config, 'build', 'apronly'):    # AP XML file
            # Generate the AP GDL file.
            apFilename = config.get('main', 'ap')
            font.saveAP(apFilename, gdlFileName)
            if app : app.updateFileEdit(apFilename)

        cmd = configval(config, 'build', 'makegdlcmd')
        if cmd and cmd.strip() :
            # Call the make command to perform makegdl.
            makecmd = expandMakeCmd(config, cmd)
            print(makecmd)
            subprocess.call(makecmd, shell = True)
        else :
            # Use the default makegdl process.
            font.createClasses()
            font.calculatePointClasses()
            font.ligClasses()
            attPassNum = int(config.get('build', 'attpass'))
            f = open(gdlFileName, "w")
            font.outGDL(f)
            if attPassNum > 0 : font.outPosRules(f, attPassNum)
            if configval(config, 'build', 'gdlfile') :
                f.write('\n\n#include "%s"\n' % (os.path.abspath(config.get('build', 'gdlfile'))))
            f.close()
            if app : app.updateFileEdit(gdlFileName)
    else :
        gdlFileName = configval(config, 'build', 'gdlfile')

    if not gdlFileName or not os.path.exists(gdlFileName) :
        f = open('gdlerr.txt' ,'w')
        if not gdlFileName :
            f.write("No GDL File specified. Build failed")
        else :
            f.write("No such GDL file: \"%s\". Build failed" % gdlFileName)
        f.close()
        return True
        
    cwd = os.getcwd()
    sourcePath = os.path.dirname(os.path.abspath(gdlFileName))
    pathToCwd = pathFromTo(sourcePath, cwd)  # prepend this to existing paths

    #tweakWarning = generateTweakerGDL(config, app)
    #if tweakWarning != "" :
    #    app.tab_errors.addWarning(tweakWarning)
    #    app.tab_errors.setBringToFront(True)
        
    tempFontFileIn = mktemp()
    if config.has_option('build', 'usettftable') :  # unimplemented
        subprocess.call(("ttftable", "-delete", "graphite", fontFileName , tempFontFileIn))
    else :
        copyfile(fontFileName, tempFontFileIn)

    parms = {}
    if lowLevelErrFile :
        parms['stderr'] = subprocess.STDOUT
        parms['stdout'] = lowLevelErrFile

    if config.has_option('build', 'grcexecutable') and configval(config, 'build', 'grcexecutable') != "":
        # Call the compiler they specified:
        grcExec = configval(config, 'build', 'grcexecutable')
    else:
        grcExec = grcompiler

    if config.has_option('build', 'ignorewarnings') :
        warningList = configval(config, 'build', 'ignorewarnings')
        warningList = warningList.replace(' ', '')
        if warningList == 'none' :
            warningList = ['-wall']
        elif warningList == '' :
            warningList = ['-w510', '-w3521']  # warnings to ignore by default
        else :
            warningList = warningList.replace(',', ' -w')
            warningList = "-w" + warningList
            warningList = warningList.split(' ')
    else:
        warningList = ['-w510', '-w3521']  # warnings to ignore by default

    res = 1
    if grcExec is not None:
        try:
            # Change the current working directory to the one where the GDL file is located.
            # This is done to account for a bug in the compiler that interprets #include statements
            # as relative to the CWD rather than the main source file (happens only on Windows).
            # -- NO LONGER NEEDED; the compiler has been fixed.
            #gdlFileBase = os.path.basename(gdlFileName)
            #tempFontFileIn = os.path.abspath(tempFontFileIn)
            #fontFileName_src = pathToCwd + os.path.relpath(fontFileName)
            #os.chdir(sourcePath)

            print("Compiling...")
            argList = [grcExec]
            argList.extend(warningList)
            if gdlErrFileName is not None and gdlErrFileName != "":
                argList.extend(["-e", gdlErrFileName])
            argList.extend(["-D", "-q", gdlFileName, tempFontFileIn, fontFileName])

            res = subprocess.call(argList, **parms)
        except:
            print("error in running compiler")
    else:
        print("grcompiler is missing")

    #os.chdir(cwd)  # return to where we were - NOT NEEDED

    #print("compilation result =", res)

    if res:
        # failure in compilation - restore the previous version of the font
        copyfile(tempFontFileIn, fontFileName)

    os.remove(tempFontFileIn)

    return res


replacements = {
    'a' : ['main', 'ap'],
    'f' : ['main', 'font'],
    'g' : ['build', 'makegdlfile'],
    'i' : ['build', 'gdlfile'],
    'p' : ['build', 'attpass']
}

def expandMakeCmd(config, txt) :
    ###return re.sub(r'%([afgip])', lambda m: os.path.abspath(configval(config, *replacements[m.group(1)])), txt)
    for key, val in replacements.items() :
        cval = configval(config, val[0], val[1])
        if key == 'p' :
            # Not a filename
            txt = txt.replace('%p', cval)
        elif key == 'i' :
            # Don't convert main GDL include file to absolute path - this can create problems on Windows.
            # (It seems to confuse the gdlpp module that handles the #include statements.)
            # Just use whatever they put in the field.
            txt = txt.replace('%i', cval)
        elif cval == None :
            txt = txt.replace('%'+key, "[missing filename]")
        else :
            txt = txt.replace('%'+key, os.path.abspath(cval))
    return txt


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

# Return the file p with a path relative to the given base.
def relpath(p, base) :
    d = os.path.dirname(base) or '.'
    return os.path.relpath(p, d)

def as_entities(text) :
    if text :
        return re.sub(u'([^\u0000-\u007f])', lambda x: "\\u%04X" % ord(x.group(1)), text)
    else :
        return ""

def generateTweakerGDL(config, app) :
    if not config.has_option('build', 'tweakxmlfile') :
        return ""
        
    tweakxmlfile = config.get('build', 'tweakxmlfile')
    if not config.has_option('build', 'tweakgdlfile') or config.get('build', 'tweakgdlfile') == "":
        return "Warning: no GDL tweak file specified; tweaks ignored."

    tweakgdlfile = config.get('build', 'tweakgdlfile')
    if config.has_option('build', 'tweakconstraint') :
        tweakConstraint = config.get('build', 'tweakconstraint')
    else:
        tweakConstraint = ""
    gdlfile = config.get('build', 'gdlfile')
    fontname = config.get('main', 'font')
    
    tweakData = app.tab_tweak.parseFile(tweakxmlfile)
    
    passindex = configval(config, 'build', 'tweakpass')
    f = open(tweakgdlfile, 'w')
    f.write("/*\n    Tweaker GDL file for font " + fontname + " to include in " + gdlfile + "\n*/\n\n")

    if passindex :
        f.write("table(positioning)\n\n")
        if tweakConstraint != "" :
            # Output pass constraint
            if tweakConstraint[0:2] != "if" :
                f.write("if " + "( " + tweakConstraint + " )")
            else :
                f.write(tweakConstraint)
            f.write("\n\n")        
        f.write("pass(" + passindex + ")\n\n")
    
    for (groupLabel, tweaks) in tweakData.items() :
        f.write("\n//---  " + groupLabel + "  ---\n\n")
        
        for tweak in tweaks :
            f.write("// " + tweak.name + "\n")

            # Don't output the feature tests for now. If we reinstate this code, we need to get the
            # the GDL feature name out of the GDX file.
#            if (tweak.feats and tweak.feats != "") or (tweak.lang and tweak.lang != "") :
#                f.write("if (")
#                andText = ""
#                if (tweak.lang and tweak.lang != "") :
#                    f.write("lang"," == ", '"',tweak.lang,'"')
#                    andText = " && "
#                for (fid, value) in tweak.feats.items() :
#                    f.write(andText + fid + " == " + str(value))
#                    andText = " && "
#                f.write(")\n")

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
                        f.write(twglyph.name)
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
            if i > 0 : f.write(" ;")
            
#            if tweak.feats and tweak.feats != "" :
#                f.write("\nendif;")
            f.write("\n\n")
    
    if passindex :
        f.write("\nendpass;  // " + passindex)
        if tweakConstraint != "" : 
            f.write("\n\nendif;  // pass constraint")
        f.write("\n\nendtable;  // positioning\n\n")

    f.close()
    
    if app : app.updateFileEdit(tweakgdlfile)
    
    print("Tweak GDL generated - accepting pending tweaks.")
    
    # Accept all pending shifts, since they are now part of the Graphite rules.
    app.tab_tweak.acceptPending(tweakxmlfile)
    
    return ""  # success


def popUpError(msg) :
    dlg = QtWidgets.QMessageBox()
    dlg.setText(msg)
    dlg.setWindowTitle("Graide")
    dlg.exec_()


def pathFromTo(path1, path2):
    path1abs = splitWholePath(os.path.abspath(path1))
    path2abs = splitWholePath(os.path.abspath(path2))
    #print(path1abs)
    #print(path2abs)

    commonI = 0
    while commonI < len(path1abs) and commonI < len(path2abs) and path1abs[commonI] == path2abs[commonI]:
        commonI = commonI + 1

    result = ""

    for i2 in range(commonI, len(path1abs)):
        result += "../"

    for i2 in range(commonI, len(path2abs)):
        result += path2abs[i2] + "/"

    return result


def splitWholePath(path):
    result = []
    while True:
        (head, tail) = os.path.split(path)
        if tail is None or tail == "":
            result.append(head)
            break
        else:
            result.append(tail)
            path = head
    result.reverse()
    return result

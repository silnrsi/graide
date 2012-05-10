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

import re, psnames
from graide.makegdl.psnames import Name

class PointClass(object) :

    def __init__(self, name) :
        self.name = name
        self.glyphs = []
        self.dias = []
#        self.isBase = False

    def addBaseGlyph(self, g) :
        self.glyphs.append(g)
#        if g.isBase : self.isBase = True

    def addDiaGlyph(self, g) :
        self.dias.append(g)

    def classGlyphs(self, isDia = False) :
        if isDia :
            return self.dias
        else :
            return self.glyphs

    def isNotInClass(self, g, isDia = False) :
        if isDia :
            return g not in self.dias
        else :
            return g not in self.dias and g not in self.glyphs

class Font(object) :
    
    def __init__(self) :
        self.glyphs = []
        self.psnames = {}
        self.canons = {}
        self.gdls = {}
        self.anchors = {}
        self.ligs = {}
        self.subclasses = {}
        self.points = {}
        self.classes = {}

    def emunits(self) :
        return 0

    def addGlyph(self, g, index = None) :
        if index is None :
            self.glyphs.append(g)
        elif index >= len(self.glyphs) :
            self.glyphs.extend([None] * (len(self.glyphs) - index + 1))
        else :
            self.glyphs[index] = g
        n = g.GDLName()
        if n and n in self.gdls :
            count = 1
            index = -2
            n = n + "_1"
            while n in self.gdls :
                count = count + 1
                n = n[0:index] + "_" + str(count)
                if count == 10 : index = -3
                if count == 100 : index = -4
        self.setGDL(g, n)
        for n in g.parseNames() :
            self.psnames[n.psname] = g
            self.canons[n.canonical()] = (n, g)
        return g

    def setGDL(self, glyph, name) :
        if not glyph : return
        n = glyph.GDLName()
        if n != name and n in self.gdls : del self.gdls[n]
        self.gdls[name] = glyph
        glyph.setGDL(name)

    def createClasses(self) :
        for k, v in self.canons.items() :
            if v[0].ext :
                h = v[0].head()
                o = self.canons.get(h.canonical(), None)
                if o :
                    if v[0].ext not in self.subclasses : self.subclasses[v[0].ext] = {}
                    self.subclasses[v[0].ext][o[1].GDLName()] = v[1].GDLName()
        for g in self.glyphs :
            if not g : continue
            for c in g.classes :
                if c not in self.classes :
                    self.classes[c] = []
                self.classes[c].append(g.GDLName())

    def pointClasses(self) :
        for g in self.glyphs :
            if not g : continue
            for a in g.anchors.keys() :
                b = a
                if a.startswith("_") : b = a[1:]
                if b not in self.points :
                    self.points[b] = PointClass(b)
                if a == b :
                    self.points[b].addBaseGlyph(g)
                else :
                    self.points[b].addDiaGlyph(g)

    def ligClasses(self) :
        for g in self.glyphs :
            if not g : continue
            (h, t) = g.name.split_last()
            if t :
                o = self.canons.get(h.canonical(), None)
                if o and o[0].ext == t.ext :
                    t.ext = None
                    t.cname = None
                    if t.canonical() in self.ligs :
                        self.ligs[t.canonical()].append((g.GDLName(), o[0].GDL()))
                    else :
                        self.ligs[t.canonical()] = [(g.GDLName(), o[0].GDL())]

    def outGDL(self, fh) :
        munits = self.emunits()
        fh.write('table(glyph) {MUnits = ' + str(munits) + '};\n')
        for g in self.glyphs :
            if not g or not g.psname : continue
            if g.psname == '.notdef' :
                fh.write(g.GDLName() + ' = glyphid(0)')
            else :
               fh.write(g.GDLName() + ' = postscript("' + g.psname + '")')
            outs = []
            if len(g.anchors) :
                for a in g.anchors.keys() :
                    v = g.anchors[a]
                    if a.startswith("_") :
                        name = a[1:] + "M"
                    else :
                        name = a + "S"
                    outs.append(name + "=point(" + str(int(v[0])) + "m, " + str(int(v[1])) + "m)")
            for (p, v) in g.gdl_properties.items() :
                outs.append("%s=%s" % (p, v))
            if len(outs) : fh.write(" {" + "; ".join(outs) + "}")
            fh.write(";\n")
        fh.write("\n")
        fh.write("\n/* Point Classes */\n")
        for p in self.points.values() :
            n = p.name + "Dia"
            self.outclass(fh, "c" + n, p.classGlyphs(True))
            self.outclass(fh, "cTakes" + n, p.classGlyphs(False))
            self.outclass(fh, 'cn' + n, filter(lambda x : p.isNotInClass(x, True), self.glyphs))
            self.outclass(fh, 'cnTakes' + n, filter(lambda x : p.isNotInClass(x, False), self.glyphs))
        fh.write("\n/* Classes */\n")
        for (c, l) in self.classes.items() :
            if c not in self.subclasses and not isMakeGDLSpecialClass(c) :
                self.outclass(fh, c, l)
        for p in self.subclasses.keys() :
            ins = []
            outs = []
            for k, v in self.subclasses[p].items() :
                ins.append(k)
                outs.append(v)
            n = p.replace('.', '_')
            self.outclass(fh, 'cno_' + n, ins)
            self.outclass(fh, 'c' + n, outs)
        fh.write("/* Ligature Classes */\n")
        for k in self.ligs.keys() :
            self.outclass(fh, "clig" + k, map(lambda x: x[0], self.ligs[k]))
            self.outclass(fh, "cligno_" + k, map(lambda x: x[1], self.ligs[k]))
        fh.write("\nendtable;\n")
        fh.write("#define MAXGLYPH %d\n" % (len(self.glyphs) - 1))

    def outclass(self, fh, name, glyphs) :
        fh.write(name + " = (")
        count = 1
        sep = ""
        for g in glyphs :
            if not g : continue
            if isinstance(g, basestring) :
                fh.write(sep + g)
            else :
                fh.write(sep + g.GDLName())
            if count % 8 == 0 :
                sep = ',\n         '
            else :
                sep = ', '
            count += 1
        fh.write(');\n\n')

class Glyph(object) :

    def __init__(self, name) :
        self.psname = name
        # self.isBase = False
        self.name = next(self.parseNames())
        self.anchors = {}
        self.classes = set()
        self.gdl_properties = {}

    def addAnchor(self, name, x, y, t = None) :
        self.anchors[name] = (x, y)
        # if not name.startswith("_") and t != 'basemark' :
        #     self.isBase = True

    def parseNames(self) :
        for name in self.psname.split("/") :
            res = psnames.Name(name)
            yield res

    def GDLName(self) :
        if self.name :
            return self.name.GDL()
        else :
            return None

    def setGDL(self, name) :
        if not self.name :
            self.name = Name()
        self.name.GDLName = name

def isMakeGDLSpecialClass(name) :
    if re.match(r'^cn?(Takes)?.*?Dia$', name) : return True
    if name.startswith('clig') : return True
    if name.startswith('cno_') : return True
    if re.match(r'^\*GC\d+\*$', name) : return True
    return False
    

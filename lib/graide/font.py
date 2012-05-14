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

from xml.etree.cElementTree import parse, ElementTree, Element
from graide import freetype
from graide.glyph import Glyph, GlyphItem
from PySide import QtCore
import graide.makegdl.makegdl as gdl
from graide.makegdl.psnames import Name
import re

class Font(gdl.Font) :

    def __init__(self) :
        super(Font, self).__init__()
        self.glyphItems = []
        self.gnames = {}
        self.classes = {}
        self.pixrect = QtCore.QRect()
        self.isread = False

    def __len__(self) :
        return len(self.glyphs)

    def __getitem__(self, y) :
        try :
            return self.glyphs[y]
        except IndexError :
            return None

    def isRead(self) : return self.isread

    def loadFont(self, fontfile, size = 40) :
        self.glyphItems = []
        self.gnames = {}
        self.pixrect = QtCore.QRect()
        self.top = 0
        self.size = size
        self.fname = fontfile
        face = freetype.Face(fontfile)
        self.upem = face.units_per_EM
        self.numGlyphs = face.num_glyphs
        for i in range(self.numGlyphs) :
            g = GlyphItem(face, i, size)
            self.gnames[g.name] = i
            self.glyphItems.append(g)
            if g.pixmap :
                grect = g.pixmap.rect()
                grect.moveBottom(grect.height() - g.top)
                self.pixrect = self.pixrect | grect
            if g.top > self.top : self.top = g.top
        for (i, g) in enumerate(self.glyphs) :
            if i < len(self.glyphItems) :
                g.item = self.glyphItems[i]
        self.isread = True

    def initGlyphs(self) :
        self.glyphs = [None] * self.numGlyphs

    def loadAP(self, apfile) :
        self.initGlyphs()
        etree = parse(apfile)
        i = 0
        for e in etree.getroot().iterfind("glyph") :
            i = self.addglyph(i, e.get('PSName'))
            g = self.glyphs[i]
            g.readAP(e, self)
            i += 1

    def saveAP(self, fname) :
        root = Element('font')
        root.set('upem', str(self.upem))
        root.text = "\n\n"
        for g in self.glyphs :
            if g : g.createAP(root)
        ElementTree(root).write(fname, encoding="utf-8", xml_declaration=True)

    def loadEmptyGlyphs(self) :
        self.initGlyphs()
        for i in range(self.numGlyphs) :
            self.addglyph(i)

    def addGDXGlyph(self, e) :
        gid = int(e.get('glyphid'))
        g = self[gid]
        cname = e.get('className')
        if cname and re.match('^\*GC\d+\*$', cname) :
            cname = None
        if not g :
            if gid > len(self.glyphItems) :
                g = self[self.addglyph(gid, name = Name.createFromGDL(cname).canonical() if cname else None)]
            else :
                g = self[self.addglyph(gid)]
        else :
            g.clear()
        if cname : self.setGDL(g, cname)
        storemirror = False
        u = e.get('usv')
        if u and u.startswith('U+') : u = u[2:]
        if u : g.uid = u
        for a in e.iterfind('glyphAttrValue') :
            n = a.get('name')
            if n == 'mirror.isEncoded' :
                storemirror = True
            elif n == 'mirror.glyph' :
                mirrorglyph = a.get('value')
            elif n in ('*actualForPseudo*', 'breakweight', 'directionality') :
                pass
            elif n.find('.') != -1 :
                if n.endswith('x') : g.setpointint(n[:-2], int(a.get('value')), None)
                elif n.endswith('y') : g.setpointint(n[:-2], None, int(a.get('value')))
            else :
                g.setgdlproperty(n, a.get('value'))
        if storemirror and mirrorglyph :
            g.setgdlproperty('mirror.glyph', mirrorglyph)
            g.setgdlproperty('mirror.isEncoded', '1')

    def addglyph(self, index, name = None, gdlname = None) :
        if name and name in self.gnames :
            index = self.gnames[name]
        else :
            name = None
        if not name and index < len(self.glyphItems) :
            name = self.glyphItems[index].name
        g = Glyph(self, name, index, item = self.glyphItems[index] if index < len(self.glyphItems) else None)
        super(Font, self).addGlyph(g, index, gdlname)
        return index

    def addClass(self, name, elements) :
        self.classes[name] = elements
        for e in elements :
            g = self[e]
            if g : g.addClass(name)

    def addGlyphClass(self, name, gid) :
        if name not in self.classes :
            self.classes[name] = []
        if gid not in self.classes[name] :
            self.classes[name].append(gid)

    def classUpdated(self, name, value) :
        c = []
        if name in self.classes :
            for gid in self.classes[name] :
                g = self[gid]
                if g : g.removeClass(name)
        for n in value.split() :
            g = self.gdls.get(n, None)
            if g :
                c.append(g.gid)
                g.addClass(name)
        self.classes[name] = c
        
    def emunits(self) : return self.upem

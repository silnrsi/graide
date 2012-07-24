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

from graide import freetype
from graide.glyph import Glyph, GlyphItem
from PySide import QtCore
from graide.makegdl.font import Font as gdlFont
import re

class Font(gdlFont) :

    def __init__(self) :
        super(Font, self).__init__()
        self.glyphItems = []
        self.classes = {}
        self.pixrect = QtCore.QRect()
        self.isread = False
        self.highlighted = None

    def isRead(self) : return self.isread

    def loadFont(self, fontfile, size = 40) :
        self.glyphItems = []
        self.pixrect = QtCore.QRect()
        self.gnames = {}
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
            if i < len(self.glyphItems) and g :
                g.item = self.glyphItems[i]
        self.isread = True

    def loadEmptyGlyphs(self) :
        self.initGlyphs()
        for i in range(self.numGlyphs) :
            self.addGlyph(i)
        face = freetype.Face(self.fname)
        (uni, gid) = face.get_first_char()
        while gid :
            self[gid].uid = "%04X" % uni
            (uni, gid) = face.get_next_char(uni, gid)

    def addGlyph(self, index, name = None, gdlname = None) :
        if (not name or name not in self.gnames) and index < len(self.glyphItems) :
            name = self.glyphItems[index].name
        elif name in self.gnames :
            index = self.gnames[name]
        g = super(Font, self).addGlyph(index, name, gdlname, Glyph)
        if g.gid < len(self.glyphItems) :
            g.item = self.glyphItems[g.gid]
        return g

    def classSelected(self, name) :
        if name :
            try :
                nClass = set(self.classes[name].elements)
            except :
                nClass = None
        else :
            nClass = None
        if self.highlighted :
            dif = self.highlighted.difference(nClass) if nClass else self.highlighted
            for i in dif :
                if self.glyphs[i] : self.glyphs[i].highlight(False)
        if nClass :
            dif = nClass.difference(self.highlighted) if self.highlighted else nClass
            for i in dif :
                if self.glyphs[i] : self.glyphs[i].highlight(True)
        self.highlighted = nClass

    def emunits(self) : return self.upem

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

from xml.etree.ElementTree import parse
from graide import freetype
import ctypes
from graide.glyph import Glyph
from PySide import QtCore
import graide.makegdl.makegdl as gdl

class Font (gdl.Font) :

    def __init__(self) :
        super(Font, self).__init__()

    def __len__(self) :
        return len(self.glyphs)

    def __getitem__(self, y) :
        try :
            return self.glyphs[y]
        except IndexError :
            return None

    def loadFont(self, fontfile, apfile = None) :
        self.fname = fontfile
        self.face = freetype.Face(fontfile)
        self.glyphs = [None] * self.face.num_glyphs
        self.upem = self.face.units_per_EM
        if apfile :
            etree = parse(apfile)
            i = 0
            for e in etree.getroot().iterfind("glyph") :
                i = self.addglyph(i, e)
                i += 1
        else :
            for i in range(self.face.num_glyphs) :
                self.addglyph(i)

    def addglyph(self, index, elem = None) :
        if elem is not None :
            name = elem.get('PSName')
            if name :
                i = freetype.FT_Get_Name_Index(self.face._FT_Face, name)
                if i == None :
                    name = None
                else :
                    index = i
        else :
            name = None
        if not name :
            n = ctypes.create_string_buffer(64)
            freetype.FT_Get_Glyph_Name(self.face._FT_Face, index, n, ctypes.sizeof(n))
            name = n.value
        g = Glyph(self, name, index)
        super(Font, self).addGlyph(g, index)
        if elem is not None : g.readAP(elem)
        return index

    def makebitmaps(self, size) :
        self.pixrect = QtCore.QRect()
        self.top = 0
        self.size = size
        for i, g in enumerate(self.glyphs) :
            if g :
                g.setpixmap(self.face, i, size)
                if g.pixmap :
                    grect = g.pixmap.rect()
                    self.pixrect = self.pixrect | grect
                if g.top > self.top : self.top = g.top

    def emunits(self) : return self.upem

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
from graide import freetype
import array, re, ctypes
from xml.etree.cElementTree import SubElement
from graide.attribview import Attribute, AttribModel
from graide.utils import DataObj
import graide.makegdl.makegdl as gdl

class GlyphItem(object) :

    def __init__(self, face, gid, height = 40) :
        face.set_char_size(height = int(height * 64))
        res = freetype.FT_Load_Glyph(face._FT_Face, gid, freetype.FT_LOAD_RENDER)
        b = face.glyph.bitmap
        self.top = face.glyph.bitmap_top
        self.left = face.glyph.bitmap_left
        if b.rows :
            data = array.array('B', b.buffer)
            mask = QtGui.QImage(data, b.width, b.rows, b.pitch, QtGui.QImage.Format_Indexed8)
            image = QtGui.QImage(b.width, b.rows, QtGui.QImage.Format_Mono)
            image.fill(0)
            image.setAlphaChannel(mask)
            self.pixmap = QtGui.QPixmap(image)
        else :
            self.pixmap = None
        n = ctypes.create_string_buffer(64)
        freetype.FT_Get_Glyph_Name(face._FT_Face, gid, n, ctypes.sizeof(n))
        self.name = n.value

class Glyph(gdl.Glyph, DataObj) :

    def __init__(self, font, name, gid = 0, item = None) :
        super(Glyph, self).__init__(name)
        self.gid = gid
        self.uid = ""     # this is a string!
        self.item = item
        self.comment = ""
        self.isHigh = False

    def clear(self) :
        super(Glyph, self).clear()
        self.properties = {}

    def __str__(self) :
        return self.psname

    def readAP(self, elem, font) :
        self.uid = elem.get('UID', None)
        for p in elem.iterfind('property') :
            n = p.get('name')
            if n.startswith('GDL_') :
                self.gdl_properties[n[4:]] = p.get('value')
            else :
                self.properties[n] = p.get('value')
        for p in elem.iterfind('point') :
            l = p.find('location')
            self.anchors[p.get('type')] = (int(l.get('x', 0)), int(l.get('y', 0)))
        p = elem.find('note')
        if p is not None and p.text :
            self.comment = p.text
        if 'classes' in self.properties :
            for c in self.properties['classes'].split() :
                if c not in self.classes :
                    self.classes.add(c)
                    font.addGlyphClass(c, self.gid)

    def createAP(self, elem) :
        e = SubElement(elem, 'glyph')
        e.set('PSName', self.psname)
        if self.uid : e.set('UID', self.uid)
        e.set('GID', str(self.gid))
        ce = None
        for (k, v) in self.anchors.items() :
            p = SubElement(e, 'point')
            p.set('type', k)
            p.text = "\n        "
            l = SubElement(p, 'location')
            l.set('x', str(v[0]))
            l.set('y', str(v[1]))
            l.tail = "\n    "
            if ce is not None : ce.tail = "\n    "
            ce = p
        for (k, v) in self.gdl_properties.items() :
            p = SubElement(e, 'property')
            p.set('name', 'GDL_' + k)
            p.set('value', v)
            if ce is not None : ce.tail = "\n    "
            ce = p
        for (k, v) in self.properties.items() :
            p = SubElement(e, 'property')
            p.set('name', k)
            p.set('value', v)
            if ce is not None : ce.tail = "\n    "
            ce = p
        if self.comment :
            p = SubElement(e, 'note')
            p.text = self.comment
            if ce is not None : ce.tail = "\n    "
            ce = p
        if ce is not None :
            ce.tail = "\n"
            e.text = "\n    "
        e.tail = "\n"
        return e
      
    def attribModel(self) :
        res = []
        for a in ['psname', 'gid'] :
            res.append(Attribute(a, self.__getattribute__, None, False, a)) # read-only
        res.append(Attribute('GDLName', self.GDLName, None))
        for a in ['uid', 'comment'] :
            res.append(Attribute(a, self.__getattribute__, self.__setattr__, False, a))
        for a in sorted(self.properties.keys()) :
            res.append(Attribute(a, self.getproperty, self.setproperty, False, a))
        for a in sorted(self.gdl_properties.keys()) :
            res.append(Attribute(a, self.getgdlproperty, self.setgdlproperty, False, a))
        pres = []
        for k in self.anchors.keys() :
            pres.append(Attribute(k, self.getpoint, self.setpoint, False, k))
        resAttrib = AttribModel(res)
        pAttrib = AttribModel(pres, resAttrib)
        resAttrib.add(Attribute('points', None, None, True, pAttrib))
        return resAttrib

    def getproperty(self, key) :
        return self.properties[key]

    def setproperty(self, key, value) :
        if value == None :
            del self.properties[key]
        else :
            self.properties[key] = value

    def getgdlproperty(self, key) :
        return self.gdl_properties[key]

    def setgdlproperty(self, key, value) :
        if value == None :
            del self.gdl_properties[key]
        else :
            self.gdl_properties[key] = value

    def getpoint(self, key) :
        return str(self.anchors[key])

    def setpoint(self, key, value) :
        if value == None :
            del self.anchors[key]
        elif value == "" :
            self.anchors[key] = (0, 0)
        else :
            self.anchors[key] = map(int, re.split(r",\s*", value[1:-1]))

    def setpointint(self, key, x, y) :
        if key in self.anchors :
            if x is None : x = self.anchors[key][0]
            if y is None : y = self.anchors[key][1]
        self.anchors[key] = (x, y)

    def addClass(self, name) :
        if name not in self.classes :
            self.classes.add(name)
            self.properties['classes'] = "  ".join(sorted(self.classes))

    def removeClass(self, name) :
        if name in self.classes :
            self.classes.discard(name)
            self.properties['classes'] = "  ".join(sorted(self.classes))

    def highlight(self, value) :
        self.isHigh = value

    def isHighlighted(self) :
        return self.isHigh

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


from qtpy import QtGui
import freetype
import array

def ftGlyph(face, gid, fill = 0) :
    res = freetype.FT_Load_Glyph(face._FT_Face, gid, freetype.FT_LOAD_RENDER)
    b = face.glyph.bitmap
    top = face.glyph.bitmap_top
    left = face.glyph.bitmap_left
    if b.rows :
        data = array.array('B', b.buffer)
        mask = QtGui.QImage(data, b.width, b.rows, b.pitch, QtGui.QImage.Format_Indexed8)
        image = QtGui.QImage(b.width, b.rows, QtGui.QImage.Format_ARGB32)
        image.fill(0xFF000000 + fill)
        image.setAlphaChannel(mask)
        pixmap = QtGui.QPixmap(image)
    else :
        pixmap = None
    return (pixmap, left, top)

class GlyphItem(object) :

    def __init__(self, face, gid, height = 40) :
        face.set_char_size(height = int(height * 64))
        (self.pixmap, self.left, self.top) = ftGlyph(face, gid)
        self.name = face.get_glyph_name(gid)
        self.pixmaps = {height : (self.pixmap, self.left, self.top)}
        self.face = face
        self.gid = gid
        self.uid = None

    def pixmapAt(self, height) :
        if height not in self.pixmaps :
            self.face.set_char_size(height * 64)
            self.pixmaps[height] = ftGlyph(self.face, self.gid)
        return self.pixmaps[height]


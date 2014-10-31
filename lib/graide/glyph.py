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


from PySide import QtCore, QtGui
from graide import freetype
import array, ctypes, re, traceback
from graide.attribview import Attribute, AttribModel
from graide.utils import DataObj
from graide.makegdl.glyph import Glyph as gdlGlyph


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
        n = ctypes.create_string_buffer(64)
        freetype.FT_Get_Glyph_Name(face._FT_Face, gid, n, ctypes.sizeof(n))
        self.name = re.sub(ur'[^A-Za-z0-9._]', '', n.value)
        self.pixmaps = {height : (self.pixmap, self.left, self.top)}
        self.face = face
        self.gid = gid

    def pixmapAt(self, height) :
        if height not in self.pixmaps :
            self.face.set_char_size(height * 64)
            self.pixmaps[height] = ftGlyph(self.face, self.gid)
        return self.pixmaps[height]


class GraideGlyph(gdlGlyph, DataObj, QtCore.QObject) :

    anchorChanged = QtCore.Signal(str, int, int)

    def __init__(self, name, gid = 0, item = None) :
        super(GraideGlyph, self).__init__(name, gid)
        QtCore.QObject.__init__(self)
        self.item = item
        self.isHigh = False
        self.justifies = []
        self.fileLocs = {}   # file locations where attributes are set

    def __str__(self) :
        return self.psname

    def attribModel(self) :
        attrList = []
        
        defaultFloc = self._fileLoc("gid")
        attrList.append(Attribute('glyph number', self.__getattribute__, None, False, defaultFloc, 'gid')) # read-only
        attrList.append(Attribute('GDL name', self.GDLName, None, fileLoc=defaultFloc))  ## self.setGDL
        attrList.append(Attribute('Postscript', self.__getattribute__, None, False, defaultFloc, 'psname')) #read-only
        #attrList.append(Attribute('USV', self.__getattribute__, self.__setattr__, False, 'uid'))
        attrList.append(Attribute('USV', self.__getattribute__, None, False, defaultFloc, 'uid'))
        attrList.append(Attribute('comment', self.__getattribute__, None, False, None, 'comment')) ## self.__setattr__, False, 'comment'))

        for a in sorted(self.properties.keys()) :
            # classes
            attrList.append(Attribute(a, self.getProperty, None, False, self._fileLoc(a), a))  ## self.setPropertyX
            
        for a in sorted(self.gdl_properties.keys()) :
            # breakweight, dir, mirror, etc.
            if a == "*actualForPseudo*" :
                actual = self.getGdlProperty("*actualForPseudo*")
                if actual != 0 :
                    attrList.append(Attribute(a, self.getGdlProperty, None, False, self._fileLoc(a), a)) ## self.setGdlProperty
            else :
                attrList.append(Attribute(a, self.getGdlProperty, None, False, self._fileLoc(a), a))  ## self.setGdlProperty
                
        topModel = AttribModel(attrList) # top-level structure
        
        # points
        ptAttrList = []
        ptModel = AttribModel(ptAttrList, topModel) # sub-tree for points
        for k in sorted(self.anchors.keys()) :
            ptAttrList.append(Attribute(k, self.getPoint, None, False, self._fileLoc(k), k))  ## self.setPoint
        topModel.add(Attribute('points', None, None, True, None, ptModel))
        
        # justification - TODO clean up line-and-file stuff for multiple levels
        if len(self.justifies) :
            jModel = AttribModel([], topModel)  # sub-tree for justify attrs
            for (iLevel, j) in enumerate(self.justifies) :
                jlAttrs = [] # list of justify attrs at this level
                lModel = AttribModel(jlAttrs, jModel)  # sub-tree for this level
                for k in j.keys() :
                    fullName = "justify." + string(iLevel) + "." + k
                    jlAttrs.append(Attribute(k, self.getJustify, None, False,
                            self._fileLoc(fullName), iLevel, k))
                jModel.add(Attribute(str(iLevel), None, None, True, None, lModel))
            topModel.add(Attribute('justify', None, None, True, None, jModel))
        
        #collision
        colAttrList = []
        if (len(self.collisionProps)) :
            colModel = AttribModel(colAttrList, topModel) # sub-tree for collision
            for k in sorted(self.collisionProps.keys()) :
                colAttrList.append(Attribute(k, self.getCollision, None, False, self._fileLoc("collision."+k), k))
            topModel.add(Attribute('collision', None, None, True, None, colModel))
        
        return topModel
    
    # Return line-and-file info corresponding to this row and column.  
    def lineAndFile(self, row, col) :
        if row == 0 or row == 1 or row == 2 : # glyph ID, GDL name, or PS name
            if self.fileLoc[0] :
                return self.fileLoc[0][:2]
            else :
                return None
        else :
            return None
    
    # Store a line-and-file associated with a glyph attribute.
    def addLineAndFile(self, attrName, inFile, atLine) :
        self.fileLocs[attrName] = (inFile, atLine);
        
    def _fileLoc(self, attrName) :
        if attrName in self.fileLocs :
            x = self.fileLocs[attrName]
        else :
            x = self.fileLocs["gid"]
        ###print attrName, x
        return x

    def getProperty(self, key) :
        return self.properties[key]

    def setAnchor(self, name, x, y, t = None) :
        send = super(GraideGlyph, self).setAnchor(name, x, y, t)
        if send :
            self.anchorChanged.emit(name, x, y)
        return send

    def setPropertyX(self, key, value) :    # don't inherit
        if value == None :
            del self.properties[key]
        else :
            self.properties[key] = value

    def getGdlProperty(self, key) :
        return self.gdl_properties[key]

    def setGdlProperty(self, key, value) :
        if value == None :
            del self.gdl_properties[key]
        else :
            self.gdl_properties[key] = value

    def getPoint(self, key) :
        return str(self.anchors[key])

    def setPoint(self, key, value) :
        if value == None :
            (x, y) = (None, None)
        elif value == "" :
            (x, y) = (0, 0)
        else :
            try :
                (x, y) = map(int, re.split(r",\s*", value[1:-1]))
            except :
                msg = "Please use the format (x, y)."
                errorDialog = QtGui.QMessageBox()
                errorDialog.setText(msg)
                errorDialog.exec_()
        self.setAnchor(key, x, y)
    
    def getCollision(self, key) :
        return self.collisionProps[key]
        
    def getJustify(self, level, name) :
        if level >= len(self.justifies) or name not in self.justifies[level] : return None
        return self.justifies[level][name]

    def setJustify(self, level, name, val) :
        if level >= len(self.justifies) :
            self.justifies.extend(({},) * (level - len(self.justifies) + 1))
        self.justifies[level][name] = val

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

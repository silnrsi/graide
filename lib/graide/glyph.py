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

from __future__ import print_function

from qtpy import QtCore, QtGui
from graide import freetype
import array, ctypes, re, traceback
from graide.attribview import Attribute, AttribModel
from graide.utils import DataObj, popUpError
from graide.makegdl.glyph import Glyph as gdlGlyph
from graide.slot import Slot


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


# GlyphItems are stored in the GraideFont, in the glyphItems instance variable.
class GlyphItem(object) :

    def __init__(self, face, gid, height = 40) :
        face.set_char_size(height = int(height * 64))
        (self.pixmap, self.left, self.top) = ftGlyph(face, gid)
        n = ctypes.create_string_buffer(64)
        freetype.FT_Get_Glyph_Name(face._FT_Face, gid, n, ctypes.sizeof(n))
        self.name = re.sub(u'[^A-Za-z0-9._]', '', n.value) # Postscript name
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
        
    def setItem(self, item) :
        self.item = item

    def __str__(self) :
        return self.psname

    def attribModel(self) :
        
        attrList = []
        
        defaultFloc = self._fileLoc("gid")
        attrList.append(Attribute('glyph number', self.__getattribute__, None, False, defaultFloc, False, 'gid')) # read-only
        attrList.append(Attribute('GDL name', self.GDLName, None, fileLoc=defaultFloc))  ## self.setGDL
        attrList.append(Attribute('Postscript', self.__getattribute__, None, False, defaultFloc, False, 'psname')) #read-only
        #attrList.append(Attribute('USV', self.__getattribute__, self.__setattr__, False, False, 'uid'))
        attrList.append(Attribute('USV', self.__getattribute__, None, False, defaultFloc, False, 'uid'))
        attrList.append(Attribute('comment', self.__getattribute__, None, False, None, False, 'comment')) ## self.__setattr__, False, 'comment'))

        for a in sorted(self.properties.keys()) :
            # classes
            attrList.append(Attribute(a, self.getProperty, None, False, self._fileLoc(a), True, a))  ## self.setPropertyX
            
        for a in sorted(self.gdlProperties.keys()) :
            # breakweight, dir, mirror, etc.
            if a == "*actualForPseudo*" :
                actual = self.getGdlProperty("*actualForPseudo*")
                if actual != 0 :
                    attrList.append(Attribute(a, self.getGdlProperty, None, False, self._fileLoc(a), False, a)) ## self.setGdlProperty
            elif a == "*skipPasses*" :
                attrList.append(Attribute(a, self.getGdlPropertyWithBinary, None, False, None, False, a))
            else :
                attrList.append(Attribute(a, self.getGdlProperty, None, False, self._fileLoc(a), False, a))  ## self.setGdlProperty
                
        topModel = AttribModel(attrList) # top-level structure
        
        # points
        ptAttrList = []
        ptModel = AttribModel(ptAttrList, topModel) # sub-tree for points
        for k in sorted(self.anchors.keys()) :
            ptAttrList.append(Attribute(k, self.getPoint, None, False, self._fileLoc(k), False, k))  ## self.setPoint
        topModel.add(Attribute('points', None, None, True, None, False, ptModel))
        
        # user-defined
        #try : self.userProperties
        #except : self.userProperties = {}
        if len(self.userProperties) :
            userAttrList = []
            userModel = AttribModel(userAttrList, topModel) # sub-tree for user-defined attrs
            for k in sorted(self.userProperties.keys()) :
                userAttrList.append(Attribute(k, self.getUserProperty, None, False, self._fileLoc(k), False, k))
            topModel.add(Attribute('user-defined', None, None, True, None, False, userModel))
        
        # justification - TODO clean up line-and-file stuff for multiple levels
        if len(self.justifies) :
            jModel = AttribModel([], topModel)  # sub-tree for justify attrs
            for (iLevel, j) in enumerate(self.justifies) :
                jlAttrs = [] # list of justify attrs at this level
                lModel = AttribModel(jlAttrs, jModel)  # sub-tree for this level
                for k in j.keys() :
                    fullName = "justify." + str(iLevel) + "." + k
                    jlAttrs.append(Attribute(k, self.getJustify, None, False,
                            self._fileLoc(fullName), iLevel, k))
                jModel.add(Attribute(str(iLevel), None, None, True, None, False, lModel))
            topModel.add(Attribute('justify', None, None, True, None, False, jModel))
        
        # collision
        colAttrList = []
        if (len(self.collisionProps)) :
            colModel = AttribModel(colAttrList, topModel) # sub-tree for collision
            for k in self.sortedCollKeys(self.collisionProps.keys()) :
                colAttrList.append(Attribute(k, self.getCollisionAnnot, None, False, self._fileLoc("collision."+k), False, k))
            topModel.add(Attribute('collision', None, None, True, None, False, colModel))
            
        #sequence
        seqAttrList = []
        if (len(self.sequenceProps)) :
            seqModel = AttribModel(seqAttrList, topModel) #sub-tree for sequence
            for k in self.sortedSeqKeys(self.sequenceProps.keys()) :
                seqAttrList.append(Attribute(k, self.getSequence, None, False, self._fileLoc("sequence."+k), False, k))
            topModel.add(Attribute('sequence', None, None, True, None, False, seqModel)) 
            
        # octaboxes
        octaAttrList = []
        if (len(self.octaboxProps)) :
            octaModel = AttribModel(octaAttrList, topModel) # sub-tree for octaboxes
            for k in sorted(self.octaboxProps.keys()) :
                octaAttrList.append(Attribute(k, self.getOctabox, None, False, None, False, k))
            topModel.add(Attribute('octabox', None, None, True, None, False, octaModel))
        
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
        
    def sortedCollKeys(self, keys) :
        goodOrder = ["flags", "min.x", "max.x", "min.y", "max.y", "margin", "marginweight", \
            "exclude.glyph", "exclude.offset.x", "exclude.offset.y", "complexFit"]
        result = list()
        for k in goodOrder :  # add items above in that order
            if k in keys :
                result.append(k)
        for k in keys :       # add anything else
            if not k in result :
                result.append(k)
        return result
        
    def sortedSeqKeys(self, keys) :
        goodOrder = ["class", "proxClass", "order", "above.xoffset", "above.weight", "below.xlimit", "below.weight", \
            "valign.height", "valign.weight"]
        result = list()
        for k in goodOrder :  # add items above in that order
            if k in keys :
                result.append(k)
        for k in keys :       # add anything else
            if not k in result :
                result.append(k)
        return result

        
    def _fileLoc(self, attrName) :
        if attrName in self.fileLocs :
            x = self.fileLocs[attrName]
        elif attrName + '.x' in self.fileLocs :
            x = self.fileLocs[attrName + '.x']
        elif "gid" in self.fileLocs :
            x = self.fileLocs["gid"]
        else :
            x = None
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
        return self.gdlProperties[key]
        
    def getGdlPropertyWithBinary(self, key) :
        value = int(self.gdlProperties[key])
        binary = bin(value)[2:]
        return "%d = %s" % (value, binary)

    def setGdlProperty(self, key, value) :
        if value == None :
            del self.gdlProperties[key]
        else :
            self.gdlProperties[key] = value
    
    def getUserProperty(self, key) :
        return self.userProperties[key]
        
    def setUserProperty(self, key, value) :
        #try :
        #    self.userProperties
        #except :
        #    self.userProperties = {}
        if value == None :
            del self.userProperties[key]
        else :
            self.userProperties[key] = value

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
                popUpError("Please use the format (x, y).")

        self.setAnchor(key, x, y)
    
    def getCollision(self, key) :
        return self.collisionProps[key]
        
    def getCollisionAnnot(self, key) :
        value = self.collisionProps[key]
        if key == "flags" :
            value = Slot.colFlagsAnnot(value)
        return value
        
    def getSequence(self, key) :
        value = self.sequenceProps[key]
        return value
        
    def getOctabox(self, key) :
        return self.octaboxProps[key]
        
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

    @staticmethod
    def builtInGlyphAttr(attrName) :
        if attrName == "*skipPasses*" :
            return True
        elif attrName == "*actualForPseudo*" :
            return True
        elif attrName == "breakweight" :
            return True
        elif attrName == "directionality" :
            return True
        elif attrName.startswith('mirror') :
            return True
        else :
            return False
            
    # debugger        
    def printGdlProperties(self) :
        print("printGdlProperties:")
        print(">>>",self.gid)
        print(self.gdlProperties)


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


from graide.attribview import Attribute, AttribModel
from graide.utils import copyobj, DataObj
import traceback

class Slot(DataObj) :

    def __init__(self, info = {}) :
        self.highlighted = False
        self.highlightType = ""
        self.px = None          # set in self.pixmap()
        for k, v in info.items() :
            setattr(self, k, v)
        
        # Note that these two are different from the collision attribute displayed below.
        # They are used for values that are NOT incorporated into the slot's origin, ie,
        # for the runs in the Collision tab. These should remain None for runs in other contexts.
        self.colPending = None
        self.colKernPending = None # from neighboring glyphs


    def copy(self) :
        res = Slot()
        copyobj(self, res)
        if hasattr(self, 'collision') :
            res.collision = self.collision.copy() # otherwise slot copies will shared this dict!
        self.px = None
        #self.highlighted = False
        #self.highlightType = ""
        return res
        
    def clearHighlight(self) :
        self.highlighted = False
        self.highlightType = ""

    def attribModel(self) :
        res = []
        for pair in (('index', 'index'), ('glyph number','gid'), ('slot ID', 'id'), 
                ('breakweight', 'break'), ('insert', 'insert'), ('justification', 'justification')) :
            label,attr = pair
            if hasattr(self, attr) :
                res.append(Attribute(label, self.__getattribute__, None, False, None, attr))
        for k in ('origin', 'advance', 'shift') :
            if hasattr(self, k) :
                res.append(Attribute(k, self.getPos, None, False, None, k))
        for k in ('before', 'after') :
            res.append(Attribute(k, self.getCharInfo, None, False, None, k))
            
        if hasattr(self, 'collision') :
            cres = []
            cres.append(Attribute('flags', self.getColFlagsAnnot, None, False))
            cres.append(Attribute('margin', self.getColMargin, None, False))
            cres.append(Attribute('min', self.getColLimitMin, None, False))
            cres.append(Attribute('max', self.getColLimitMax, None, False))
            cres.append(Attribute('offset', self.getColOffset, None, False))
            flagOverlap = 256
            if self.getColFlags() & flagOverlap :
                cres.append(Attribute('maxoverlap', self.getColMaxOverlap, None, False))
            else :
                cres.append(Attribute('maxoverlap', self.getColMaxOverlapInvalid, None, False))
            if self.colPending :
                cres.append(Attribute('pending', self.getColPending, None, False))
            #if self.colKernPending :
            #    cres.append(Attribute('', self.getColKernPending, None, False))
            
        if hasattr(self, 'parent') :
            res.append(Attribute('parent slot', self.getParent, None, False, None, 'parent'))
            res.append(Attribute('parent offset', self.getOffset, None, False))
            
        resAttrib = AttribModel(res)

        ures = []
        for i in range(len(self.user)) :
            ures.append(Attribute(str(i+1), self.getUser, None, False, None, i))
            
        if hasattr(self, 'collision') :
            cAttrib = AttribModel(cres, resAttrib)
            resAttrib.add(Attribute('collision', None, None, True, None, cAttrib))

        uAttrib = AttribModel(ures, resAttrib)
        resAttrib.add(Attribute('user attributes', None, None, True, None, uAttrib))
        return resAttrib

    def getPos(self, name) :
        res = self.__getattribute__(name)
        return "(%d, %d)" % (res[0], res[1])

    def getCharInfo(self, name) :
        return self.charinfo[name]

    def getUser(self, index) :
        return self.user[index]

    def getParent(self, name) :
        try :
            return self.parent['id']
        except :
            return None

    def getOffset(self) :
        try :
            res = self.parent['offset']
            return "(%d, %d)" % (res[0], res[1])
        except :
            return None
            
    def getColFlags(self) :
        try :
            return self.collision['flags']
        except :
            return None
            
    def getColFlagsAnnot(self) :
        try :
            flags = self.collision['flags']
            result = self.colFlagsAnnot(flags)
            return result
        except :
            return None
            
    def getColMargin(self) :
        try :
            return self.collision['margin']
        except :
            return None
            
    def getColLimitMin(self) :
        try :
            res = self.collision['limit']
            return "(%d, %d)" % (res[0], res[1])
        except :
            return None
 
    def getColLimitMax(self) :
        try :
            res = self.collision['limit']
            return "(%d, %d)" % (res[2], res[3])
        except :
            return None
       
    def getColOffset(self) :
        try :
            res = self.collision['offset']
            return "(%d, %d)" % (res[0], res[1])
        except :
            return None
            
    def getColValues(self, subAttrName):
        return self.collision[subAttrName]
            
    def setColOffset(self, value) :
        self.collision['offset'] = value
        
    def getColKern(self) :
        return self.colKern
        
    def setColKern(self, f) :
        self.colKern = f
       
    def getColMaxOverlap(self) :
        try :
            return self.collision['maxoverlap']
        except :
            return None
            
    def getColMaxOverlapInvalid(self) :
        return "---"
    
    def getColPending(self) :
        try :
            res = self.colPending
            return "(%d, %d)" % (res[0], res[1])
        except :
            return None
            
    def getColKernPending(self) :
        try : 
            res = self.colKernPending
            return "%d" % (res)
        except :
            return None
            
    def setColPending(self, value) :
        self.colPending = value
        
    def setColKernPending(self, value) :
        self.colKernPending = value
       
    def highlight(self, type = "default") :
        self.highlighted = True
        self.highlightType = type
        if (self.px) :
            self.px.highlight(type)

    def setPixmap(self, px) :
        self.px = px
        if self.highlighted :
            px.highlight(self.highlightType)

    # Return line-and-file info corresponding to this row and column.
    def lineAndFile(self, row, col) :
        #print "Slot::doubleClick",event
        return None

    def drawPosX(self) :
        res = self.origin[0]
        #print self.__getattribute__('gid'),self.colPending[0] if self.colPending else "None",self.colKernPending if self.colKernPending else "None"
        if self.colPending :
            res += self.colPending[0]
        if self.colKernPending :
            res += self.colKernPending
        return res
        
    def drawPosY(self) :
        res = self.origin[1]
        if self.colPending :
            res += self.colPending[1]
        return res

    @staticmethod
    def colFlagsAnnot(flags) :
        result = str(flags)
        flagDict = { 1: "FIX", 2: "IGNORE", 4: "START", 8: "END", 16: "KERN", 32: "ISCOL", 64: "KNOWN", 128: "JUMPABLE", 256: "OVERLAP" }
        sep = "="
        for k in flagDict.keys() :
            if flags & k == k :
                result += sep + flagDict[k]
                sep = "+"
            maxKey = k
        if flags >= maxKey * 2 :
            result += "+???"
        return result
            

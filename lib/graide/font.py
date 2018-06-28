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
from graide.glyph import GraideGlyph, GlyphItem
from qtpy import QtCore
from graide.makegdl.font import Font
import re

class GraideFont(Font) :

    def __init__(self) :
        super(GraideFont, self).__init__()
        self.glyphItems = []
        self.classes = {}
        self.pixrect = QtCore.QRect()
        self.isread = False
        self.highlighted = None
        self.attGlyphSize = 200
        
        self.gnames = {} # full list of Postscript names
        self.top = 0
        self.size = 0
        self.fname = None # font filename, eg, "Hello.ttf"
        self.upem = None
        self.numGlyphs = 0

    def isRead(self) : return self.isread


    def initGlyphs(self, nGlyphs = None) :
        #print "GraideFont::initGlyphs",nGlyphs
        if nGlyphs :
            self.numGlyphs = nGlyphs
        super(GraideFont, self).initGlyphs(self.numGlyphs)


    def loadFont(self, fontfile, size = 40) :
        #print "GraideFont::loadFont",fontfile
        
        self.glyphItems = []
        self.pixrect = QtCore.QRect()
        self.gnames = {}
        self.top = 0
        self.size = size
        self.fname = fontfile
        face = freetype.Face(fontfile)
        self.upem = face.units_per_EM
        self.numGlyphs = face.num_glyphs
        
        # Generate GlyphItems for all the glyphs in the font.
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
                g.setItem(self.glyphItems[i])
        self.isread = True

    def loadEmptyGlyphs(self) :
        #print("GraideFont::loadEmptyGlyphs")
        
        self.initGlyphs(self.numGlyphs)
        for i in range(self.numGlyphs) :
            self.addGlyph(i)
        face = freetype.Face(self.fname)
        (uni, gid) = face.get_first_char()
        while gid :
            self[gid].uid = "%04X" % uni
            (uni, gid) = face.get_next_char(uni, gid)

    def addGlyph(self, index, psName = None, gdlName = None) :
        #print "GraideFont::addGlyph",index,psName,gdlName
        
        if index < len(self.glyphItems) :
            if (not psName or psName not in self.gnames) :
                psName = self.glyphItems[index].name
            elif psName != self.glyphItems[index].name and psName in self.gnames :
                index = self.gnames[psName]
        elif psName and psName in self.gnames :
            index = self.gnames[psName]
        g = super(GraideFont, self).addGlyph(index, psName, gdlName, GraideGlyph)
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
        
    def glyphWithGDLName(self, gdlName) :
        for i in range(self.numGlyphs) :
            if self[i].GDLName() == gdlName :
                return i
        return -1
        
    def glyphOrPseudoWithGDLName(self, gdlName) :
        gidResult = self.glyphWithGDLName(gdlName)
        if gidResult == -1 :
            # Look for a pseudo-glyph.
            for i in range(self.numGlyphs, len(self.glyphs)) :
                # use gdl attribute instead of GDLName() to handle pseudos
                if self[i].gdl == gdlName :
                    gidResult = i
                    break
        if gidResult == -1 :
            # Look for a single-glyph class.
            fontClass = self.classes[gdlName] if gdlName in self.classes else None
            if not fontClass == None :
                if len(fontClass.elements) == 1 :
                    gidResult = fontClass.elements[0]
        return gidResult
            

    # Return a likely pair of glyphs to initialize the Positions tab tree control.
#    def stationaryMobilePair(self) :
#        for (i, sglyph) in enumerate(self.glyphs) :
#            sAnchors = sglyph.anchors.keys()
#            sname = sglyph.GDLName()
#            if len(sAnchors) > 0 :
#                # Find a second glyph with a matching anchor.
#                for (i, mglyph) in enumerate(self.glyphs) :
#                    mAnchors = mglyph.anchors.keys()
#                    mname = mglyph.GDLName()
#                    for sAP in sAnchors :
#                        for mAP in mAnchors:
#                            if self.apNamesMatch(sAP, mAP) :
#                                return (sname, mname, sAP, mAP)
#        return False
    
    # Return true if the two anchor names are a likely stationary/mobile pair.
#    def apNamesMatch(self, sName, mName) :
#        if (mName == sName + "_") : # eg, upper and upper_
#            return True
#        if (sName[-1] == "S" and mName[-1] == "M" and sName[0:-1] == mName[0:-1]) : # eg, upperS and upperM
#            return True
#        return False
    
    # Return the real existing attachment point name, given the generic one.
    def actualAPName(self, genericName, mobile = False) :
        for g in self.glyphs :
            if not g : continue
            for apName in g.anchors.keys() :
                if mobile == True and apName == genericName + "M" :
                    return genericName + "M"
                elif not mobile and apName == genericName + "S" :
                    return genericName + "S"
            # Try again, looking for xxx and xxx_ pairs
            for apName in g.anchors.keys() :
                if mobile == True and apName == genericName + "_" :
                    return genericName + "_"
                elif not mobile and apName == genericName :
                    return genericName
        return ""                
                    

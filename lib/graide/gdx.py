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

from xml.etree.cElementTree import iterparse
from graide.makegdl.glyph import isMakeGDLSpecialClass
import os, traceback

class Gdx(object) :

    def __init__(self) :
        self.passes = []
        self.passTypes = []
        self.collisionFix=[]
        self.flipDirs = []
        self.keepelements = False

    def readfile(self, fname, font, autoGdlFile = None, apFileName = None, ronly = False) :
        relbase = os.path.relpath(os.path.dirname(fname) or ".") or ""
        
        self.file = open(fname)
        if not apFileName :  # autoGdlFile??
            font.initGlyphs()
        for (event, e) in iterparse(self.file, events=('start', 'end')) :
            if event == 'start' :
                if e.tag == 'pass' :
                    #print "table=",e.get('table'),"index=",e.get('index'),"flipDir=",e.get('flipDir'),"collisionFix",e.get('collisionFix'),"autoKern",e.get('autoKern')
                    self.passes.append([])
                    self.passTypes.append(e.get('table'))
                    self.collisionFix.append(int(e.get('collisionFix')) if e.get('collisionFix') else 0)
                    # ignore autoKern for now
                    self.flipDirs.append(int(e.get('flipDir')) if e.get('flipDir') else 0)
                    
                elif e.tag in ('rule', 'glyph', 'class') :
                    self.keepelements = True
            else :
                if e.tag == "rule" :
                    self.keepelements = False
                    self.passes[-1].append(Rule(e, relbase))
                if e.tag == 'glyph' :
                    self.keepelements = False
                    font.addGdxGlyph(e, apFileName)
                elif e.tag == 'class' :
                    self.keepelements = False
                    n = e.get('name')
                    c = e.findall('member')
                    if len(c) :
                        g = font[int(c[0].get('glyphid'))]
                        fn = c[0].get('inFile')
                        f = os.path.join(relbase, fn) if fn else None
                        l = int(c[0].get('atLine')) if f else 0
                        if len(c) == 1 and g and g.GDLName() == n :
                            pass
                        elif not isMakeGDLSpecialClass(n) :
                            # Note: subtract 1 from the line number because the GDX file 1-based,
                            # the file editor is 0-based.
                            if not autoGdlFile :
                                font.addClass(n, map(lambda x: int(x.get('glyphid')), c), f, l - 1)
                            elif n not in font.classes or ronly :
                                font.addClass(n, map(lambda x: int(x.get('glyphid')), c), f, l - 1, generated = True)
                if not self.keepelements :
                    e.clear()

class Rule(object) :

    def __init__(self, e, relbase) :   	
        self.srcfile = os.path.join(relbase, e.get('inFile'))
        self.srcline = int(e.get('atLine')) - 1
        self.pretty = e.get('prettyPrint')
        slots = map(lambda x: int(x.get('slotIndex')), e.findall('rhsSlot'))
        if len(slots) :
            d = slots[0]
            self.slots = map(lambda x : x - d, slots)
        else :
            self.slots = []

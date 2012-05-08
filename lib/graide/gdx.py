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

from xml.etree.ElementTree import iterparse
from makegdl.makegdl import isMakeGDLSpecialClass

class Gdx(object) :

    def __init__(self) :
        self.passes = []
        self.passtypes = []
        self.keepelements = False

    def readfile(self, fname, font = None) :
        self.file = file(fname)
        for (event, e) in iterparse(self.file, events=('start', 'end')) :
            if event == 'start' :
                if e.tag == 'pass' :
                    self.passes.append([])
                    self.passtypes.append(e.get('table'))
                elif e.tag in ('rule', 'glyph', 'class') :
                    self.keepelements = True
            else :
                if e.tag == "rule" :
                    self.keepelements = False
                    self.passes[-1].append(Rule(e))
                if font :
                    if e.tag == 'glyph' :
                        self.keepelements = False
                        gid = int(e.get('glyphid'))
                        g = font[gid]
                        if g :
                            cname = e.get('className')
                            if cname : font.setGDL(g, cname)
                            storemirror = False
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
                    elif e.tag == 'class' :
                        self.keepelements = False
                        n = e.get('name')
                        c = e.findall('member')
                        if len(c) :
                            g = font[int(c[0].get('glyphid'))]
                            if len(c) == 1 and g and g.GDLName() == n :
                                pass
                            elif not isMakeGDLSpecialClass(n) :
                                font.addClass(n, map(lambda x: int(x.get('glyphid')), c))
                if not self.keepelements :
                    e.clear()

class Rule(object) :

    def __init__(self, e) :
        self.srcfile = e.get('inFile')
        self.srcline = int(e.get('atLine')) - 1
        self.pretty = e.get('prettyPrint')
        slots = map(lambda x: int(x.get('slotIndex')), e.findall('rhsSlot'))
        if len(slots) :
            d = slots[0]
            self.slots = map(lambda x : x - d, slots)
        else :
            self.slots = []

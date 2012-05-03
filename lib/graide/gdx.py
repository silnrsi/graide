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

class Gdx(object) :

    def __init__(self) :
        self.passes = []
        self.passtypes = []
        self.keepelements = False

    def readfile(self, fname) :
        self.file = file(fname)
        for (event, e) in iterparse(self.file, events=('start', 'end')) :
            if event == 'start' :
                if e.tag == 'pass' :
                    self.passes.append([])
                    self.passtypes.append(e.get('table'))
                elif e.tag == 'rule' :
                    self.keepelements = True
            else :
                if e.tag == "rule" :
                    self.keepelements = False
                    self.passes[-1].append(Rule(e))
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

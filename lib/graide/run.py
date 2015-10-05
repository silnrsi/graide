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


from graide.slot import Slot

# A Run is a list of Slots

class Run(list) :

    def __init__(self, rtl = False) :
        self.rtl = rtl
        self.kernEdges = None

    def addslots(self, runinfo) :
        for slotinfo in runinfo :
            slot = Slot(slotinfo)
            self.append(slot)
            slot.index = len(self) - 1

    def copy(self) :
        res = Run(self.rtl)
        for slot in self :
            res.append(slot.copy())
        return res

    def indexOfId(self, ident) :
        for (i, slot) in enumerate(self) :
            if slot.id == ident : return i
        return -1

    def replaceSlots(self, runinfo, start, end = None) :
        """ Replaces the subrange between a slot with id of start up to but
            not including a slot with id of end (if specified, else the end
            of the run), with the given runinfo.
            Returns the two indices for (start, end) on the input run before
            editing."""
        fin = len(self)
        ini = 0
        for (i, s) in enumerate(self) :
            if s.id == start :
                ini = i
            elif s.id == end :
                fin = i
        res = []
        for slotinfo in runinfo :
            slot = Slot(slotinfo)
            res.append(slot)
        self[ini:fin] = res
        for (i, slot) in enumerate(self) :
            slot.index = i
        return (ini, fin)


    def modifySlotWithId(self, id, attrName, value) :
        for (i, s) in enumerate(self) :
            if s.id == id :
                if attrName == 'colOffset' :
                    s.setColOffset(value)
                elif attrName == 'colPending' :
                    s.setColPending(value)
                #elif attrName == 'colKernPending' :
                #    s.setColKernPending(value)
                return (i, s)
                
        return (-1, None)

    def clearHighlight(self) :
        for (i, s) in enumerate(self) :
            s.clearHighlight()
            
    def kernAfter(self, iKern, value) :
        for (i, s) in enumerate(self) :
            if s.colKernPending == None : s.colKernPending = 0
            if self.rtl and i < iKern :
                s.colKernPending = s.colKernPending + value
            elif not self.rtl and i > iKern :                
                s.colKernPending = s.colKernPending + value * -1
                
    def addKernEdge(self, edges, others, minx, width) :
        self.kernEdges = (edges, others, minx, width)

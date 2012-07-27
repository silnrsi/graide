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

class Run(list) :

    def __init__(self) :
        pass

    def addslots(self, runinfo) :
        for s in runinfo :
            r = Slot(s)
            self.append(r)
            r.index = len(self) - 1

    def copy(self) :
        res = Run()
        for s in self :
            res.append(s.copy())
        return res

    def idindex(self, ident) :
        for (i, s) in enumerate(self) :
            if s.id == ident : return i
        return -1

    def replace(self, runinfo, start, end = None) :
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
        for r in runinfo :
            s = Slot(r)
            res.append(s)
        self[ini:fin] = res
        for (i, s) in enumerate(self) :
            s.index = i
        return (ini, fin)


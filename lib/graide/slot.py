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

class Slot(DataObj) :

    def __init__(self, info = {}) :
        self.highlighted = False
        self.highlightType = ""
        self.px = None          # set in self.pixmap()
        for k, v in info.items() :
            setattr(self, k, v)

    def copy(self) :
        res = Slot()
        copyobj(self, res)
        self.px = None
        #self.highlighted = False
        #self.highlightType = ""
        return res
        
    def clearHighlight(self) :
        self.highlighted = False
        self.highlightType = ""

    def attribModel(self) :
        res = []
        for k in ('index', 'id', 'gid', 'break', 'insert', 'justification') :
            if hasattr(self, k) :
                res.append(Attribute(k, self.__getattribute__, None, False, k))
        for k in ('origin', 'advance') :
            res.append(Attribute(k, self.getpos, None, False, k))
        for k in ('before', 'after') :
            res.append(Attribute(k, self.getcharinfo, None, False, k))
        res.append(Attribute('parent', self.getparent, None, False, 'parent'))
        ures = []
        for i in range(len(self.user)) :
            ures.append(Attribute(str(i), self.getuser, None, False, i))
        resAttrib = AttribModel(res)
        uAttrib = AttribModel(ures, resAttrib)
        resAttrib.add(Attribute('user attributes', None, None, True, uAttrib))
        return resAttrib

    def getpos(self, name) :
        res = self.__getattribute__(name)
        return "(%d, %d)" % (res[0], res[1])

    def getcharinfo(self, name) :
        return self.charinfo[name]

    def getuser(self, index) :
        return self.user[index]

    def getparent(self, name) :
        try :
            return self.parent['id']
        except :
            return None

    def highlight(self, type = "default") :
        self.highlighted = True
        self.highlightType = type
        if (self.px) :
            self.px.highlight(type)

    def pixmap(self, px) :
        self.px = px
        if self.highlighted :
            px.highlight(self.highlightType)

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
from ttfrename.glyph import GlyphItem
from PySide import QtCore, QtGui
from fontTools import ttLib
import re

pgetTableModule = ttLib.getTableModule
def getTableModule(tag) :
    #if tag in ("post", "cmap", "maxp", 'glyf', 'loca', 'head', 'hmtx', 'hhea') :
    if tag in ("post", "cmap", 'maxp') :
        return pgetTableModule(tag)
    return None
ttLib.getTableModule = getTableModule

class Namedit(QtGui.QDialog) :

    def __init__(self, name, uid, parent = None) :
        super(Namedit, self).__init__(parent)
        self.layout = QtGui.QGridLayout(self)
        self.name = QtGui.QLineEdit(self)
        self.name.setText(name)
        self.name.setSelection(0, len(name))
        self.layout.addWidget(QtGui.QLabel('Name'), 0, 0)
        self.layout.addWidget(self.name, 0, 1)
        self.uid = QtGui.QLineEdit(self)
        if uid :
            self.uid.setText("%04X" % uid)
        self.layout.addWidget(QtGui.QLabel('Unicode'), 1, 0)
        self.layout.addWidget(self.uid, 1, 1)
        o = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        o.accepted.connect(self.accept)
        o.rejected.connect(self.reject)
        self.layout.addWidget(o, 2, 0, 1, 2)

    def getValues(self) :
        t = self.uid.text()
        if re.match(ur'^[0-9a-fA-F]+$', t) :
            uid = int(t, 16)
        else :
            uid = 0
        return (str(self.name.text()), uid)


def dictkeymv(d, kin, kout) :
    x = d[kin]
    del d[kin]
    d[kout] = x

def isUnicodeCmap(t) :
    p = t.platformID
    e = t.platEncID
    if p == 3 and e == 1 : return True
    if p == 0 : return True
    return False


class Ttx(ttLib.TTFont) :

    def _writeTables(self, tag, writer, done) :
        if tag in ("post", 'glyf', 'loca', 'hmtx', 'maxp') :
            gorder = self.getGlyphOrder()
            self.setGlyphOrder(self.psGlyphs)
            ttLib.TTFont._writeTable(self,tag, writer, done)
            self.setGlyphOrder(gorder)
        else :
            ttLib.TTFont._writeTable(self,tag, writer, done)


class Font(object) :

    def __init__(self) :
        super(Font, self).__init__()
        self.glyphItems = []
        self.pixrect = QtCore.QRect()
        self.ttx = None

    def loadFont(self, fontfile, size = 40) :
        self.glyphItems = []
        self.pixrect = QtCore.QRect()
        self.gnames = {}
        self.top = 0
        self.size = size
        self.fname = fontfile
        face = freetype.Face(fontfile)
        self.upem = face.units_per_EM
        self.numGlyphs = face.num_glyphs
        for i in range(self.numGlyphs) :
            g = GlyphItem(face, i, size)
            self.gnames[g.name] = i
            self.glyphItems.append(g)
            if g.pixmap :
                grect = g.pixmap.rect()
                grect.moveBottom(grect.height() - g.top)
                self.pixrect = self.pixrect | grect
            if g.top > self.top : self.top = g.top
        self.ttx = Ttx(fontfile)
        self.cmaps = []
        self.bytemaps = []
        for c in self.ttx['cmap'].tables :
            if isUnicodeCmap(c) :
                self.cmaps.append(c.cmap)
            else :
                self.bytemaps.append(c.cmap)
        cmap = self.ttx['cmap'].getcmap(3, 1)
        if not cmap : cmap = self.ttx['cmap'].getcmap(3, 0)
        if cmap : cmap = cmap.cmap
        for k, v in cmap.items() :
            if v in self.gnames :
                self.glyphItems[self.gnames[v]].uid = k
        for k in self.ttx.keys() :
            dummy = self.ttx[k]     # trigger a read of each table
        self.ttx.close()

    def save(self, filename = None) :
        if filename : self.fname = filename
        self.ttx.psGlyphs = order = map(lambda g: g.name, self.glyphItems)
        self.ttx.setGlyphOrder(order)
        #self.ttx['glyf'].glyphOrder = order
        self.ttx['post'].extraNames = []
        self.ttx.recalcBBoxes = None
        self.ttx.save(self.fname)

    def __len__(self) :
        return len(self.glyphItems)

    def __getitem__(self, y) :
        try :
            return self.glyphItems[y]
        except IndexError :
            return None

    def emunits(self) : return self.upem

    def editGlyph(self, g) :
        d = Namedit(g.name, g.uid)
        if d.exec_() :
            (name, uid) = d.getValues()
        else :
            return
        if g.name != name or g.uid != uid :
            for c in self.cmaps :
                if g.uid != uid and g.uid in c : del c[g.uid]
                c[uid] = name
            if g.uid != uid and g.uid and g.uid < 256 :
                for c in self.bytemaps :
                    c[g.uid] = '.notdef'
            if uid and uid < 256 :
                for c in self.bytemaps :
                    c[uid] = name
            if g.name != name :
                gid = self.gnames[g.name]
                del self.gnames[g.name]
                self.gnames[name] = gid
                #dictkeymv(self.ttx['glyf'].glyphs, g.name, name)
                #dictkeymv(self.ttx['hmtx'].metrics, g.name, name)
            g.uid = uid
            g.name = name

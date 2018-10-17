#!/usr/bin/python

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

from qtpy import QtCore, QtGui, QtWidgets
from graide.glyph import ftGlyph
import sys, freetype

class WaterfallDialog(QtWidgets.QDialog) :

    def __init__(self, font, run, sizes = None, margin = 2, parent = None) :
        super(WaterfallDialog, self).__init__(parent)
        if sizes is None :
            sizes = [8, 9, 10, 11, 12, 13, 14, 16, 20, 28, 40]
        else:
            sizes = list(sizes)  # convert map to list

        self.vbox = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vbox)
        self.setWindowTitle("Waterfall")
        self.gview = QtWidgets.QGraphicsView(self)
        self.gview.setAlignment(QtCore.Qt.AlignLeft)
        self.scene = QtWidgets.QGraphicsScene(self.gview)
        self.pixmaps = []
        self.pixitems = []
        face = freetype.Face(font.fname)
        currtop = 0
        master = QtCore.QRect()
        for i in range(len(sizes)) :
            size = sizes[i] * self.logicalDpiY() / 72.
            res = QtCore.QRect()
            pixmaps = []
            pixitems = []
            self.pixmaps.append(pixmaps)
            self.pixitems.append(pixitems)
            factor = size / font.upem
            face.set_char_size(int(size) * 64)
            for s in run :
                (px, left, top) = ftGlyph(face, s.gid)
                if px :
                    if sys.version_info[0] < 3:
                        item = QtWidgets.QGraphicsPixmapItem(px, None, self.scene)
                    else:
                        item = QtWidgets.QGraphicsPixmapItem(px, None)
                        if self.scene: self.scene.addItem(item)
                    ppos = (s.drawPosX() * factor + left, -s.drawPosY() * factor - top)
                    item.setOffset(ppos[0], ppos[1])
                    pixmaps.append(px)
                    pixitems.append(item)
                    sz = px.size()
                    r = QtCore.QRect(ppos[0], ppos[1], sz.width(), sz.height())
                    res = res.united(r)
            currtop += res.height() + margin
            for i in pixitems :
                xoffset = i.offset().x()
                yoffset = i.offset().y()
                i.setOffset(xoffset, yoffset + currtop)
                #i.translate(0, currtop)  # Python 2
            master = master.united(res.translated(0, currtop))
        master.adjust(-margin, -margin, margin, margin)
        self.scene.setSceneRect(master)
        self.gview.setScene(self.scene)
        self.vbox.addWidget(self.gview)
#        self.gview.setFixedSize(master.left() + master.width() + 2, master.height() - master.top() + 2)
#        self.gview.resize(master.left() + master.width() + 2, master.height() - master.top() + 2)
#        self.gview.updateScene([])



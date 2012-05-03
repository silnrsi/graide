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

from PySide import QtCore, QtGui
from graide.dataobj import DataObj
from graide.utils import ModelSuper

class GlyphPixmapItem(QtGui.QGraphicsPixmapItem) :

    def __init__(self, index, px, parent = None, scene = None) :
        super(GlyphPixmapItem, self).__init__(px, parent, scene)
        self.selected = False
        self.index = index
        self.highlighted = False

    def mousePressEvent(self, mouseEvent) :
        self.scene().glyph_clicked(self, self.index)

    def select(self, state) :
        self.selected = state
        self.update()

    def highlight(self) :
        self.highlighted = True

    def paint(self, painter, option, widget) :
        r = QtCore.QRect(QtCore.QPoint(self.offset().x(), self.offset().y()), self.pixmap().size())
        if self.selected :
            painter.fillRect(r, option.palette.highlight())
        elif self.highlighted :
            painter.fillRect(r, QtGui.QColor(0, 0, 0, 32))
        super(GlyphPixmapItem, self).paint(painter, option, widget)


class RunModel(QtGui.QGraphicsScene, ModelSuper) :

    slotSelected = QtCore.Signal(DataObj, ModelSuper)
    glyphSelected = QtCore.Signal(DataObj, ModelSuper)

    def __init__(self, run = None, font = None, parent = None) :
        super(RunModel, self).__init__(parent)
        if run and font :
            self.loadrun(run, font)

    def loadrun(self, run, font) :
        self.run = run
        self._font = font
        self.currselection = None
        self.clear()
        self.pixmaps = []
        factor = font.size * 1. / font.upem
        res = QtCore.QRect()
        for i, s in enumerate(run) :
            g = font[s.gid]
            if g and g.pixmap :
                px = GlyphPixmapItem(i, g.pixmap, scene = self)
                ppos = (s.origin[0] * factor + g.left, -s.origin[1] * factor - g.top)
                # print s.gid, g.psname, ppos, g.pixmap.size()
                px.setOffset(*ppos)
                self.pixmaps.append(px)
                if s : s.pixmap(px)
                sz = g.pixmap.size()
                r = QtCore.QRect(ppos[0], ppos[1], sz.width(), sz.height())
                res = res.united(r)
            else :
                self.pixmaps.append(None)
        self.boundingRect = res
        self.setSceneRect(res)

    def glyph_clicked(self, gitem, index) :
        if self.currselection >= 0 and self.pixmaps[self.currselection] :
            self.pixmaps[self.currselection].select(False)
        if self.currselection != index :
            self.currselection = index
            gitem.select(True)
            self.slotSelected.emit(self.run[self.currselection], self)
            self.glyphSelected.emit(self._font[self.run[self.currselection].gid], self)
        else :
            self.currselection = -1

    def keyPressEvent(self, event) :
        if self.currselection < 0 : return
        if self.pixmaps[self.currselection] :
            self.pixmaps[self.currselection].select(False)
        if event.key() == QtCore.Qt.Key_Right :
            self.currselection += 1
            if self.currselection >= len(self.pixmaps) :
                self.currselection = len(self.pixmaps) - 1
        elif event.key() == QtCore.Qt.Key_Left :
            self.currselection -= 1
            if self.currselection < 0 :
                self.currselection = 0
        if self.pixmaps[self.currselection] :
            self.pixmaps[self.currselection].select(True)
        self.slotSelected.emit(self.run[self.currselection], self)
        self.glyphSelected.emit(self._font[self.run[self.currselection].gid], self)

    def clear_selected(self) :
        if self.currselection >= 0 :
            self.pixmaps[self.currselection].select(False)
        self.currselection = -1
        

class RunView(QtGui.QGraphicsView) :

    def __init__(self, run = None, font = None, parent = None) :
        super(RunView, self).__init__(parent)
        self.model = None
        if run :
            self.set_run(run, font)

    def set_run(self, run, font) :
        if not self.model :
            self.model = RunModel(run, font)
            self.setScene(self.model)
        else:
            self.model.loadrun(run, font)
            self.updateScene([])
        b = self.model.boundingRect
        self.setFixedSize(b.left() + b.width() + 2, b.height() - b.top() + 2)
        self.resize(b.left() + b.width() + 2, b.height() - b.top() + 2)


if __name__ == "__main__" :
    import json, sys, os
    from font import Font
    from run import Run

    app = QtGui.QApplication(sys.argv)
    # print app.desktop().logicalDpiY()
    tpath = os.path.join(os.path.dirname(sys.argv[0]), '../../tests')
    jf = file(os.path.join(tpath, "padauk3.json"))
    jinfo = json.load(jf)
    font = Font()
    font.loadFont(os.path.join(tpath, "fonts/Padauk/Padauk.ttf"))
    font.makebitmaps(40)
    rinfo = jinfo['passes'][0]['slots']
    run = Run()
    run.addslots(rinfo)
    view = RunView(run, font)
    view.show()
    sys.exit(app.exec_())

    

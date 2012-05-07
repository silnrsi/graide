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

    def __init__(self, index, px, model = None, parent = None, scene = None) :
        super(GlyphPixmapItem, self).__init__(px, parent, scene)
        self.selected = False
        self.index = index
        self.highlighted = False
        self.model = model

    def mousePressEvent(self, mouseEvent) :
        if self.model :
            self.model.glyph_clicked(self, self.index)

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

class RunTextView(QtGui.QPlainTextEdit) :

    def __init__(self, creator, parent = None) :
        super(RunTextView, self).__init__(parent=parent)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.creator = creator

    def viewportEvent(self, event) :
        if event.type() == QtCore.QEvent.MouseButtonPress :
            return self.creator.tMousePress(event)
        return False

class RunView(QtCore.QObject, ModelSuper) :

    slotSelected = QtCore.Signal(DataObj, ModelSuper)
    glyphSelected = QtCore.Signal(DataObj, ModelSuper)

    def __init__(self, run = None, font = None, parent = None) :
        super(RunView, self).__init__()
        self.gview = QtGui.QGraphicsView(parent)
        self._scene = QtGui.QGraphicsScene(self.gview)
        self._scene.keyPressEvent = self.keyPressEvent
        self.tview = QtGui.QPlainTextEdit(parent)
        self.tview.setReadOnly(True)
        self.tview.mousePressEvent = self.tEvent
        self._fSelect = QtGui.QTextCharFormat()
        self._fSelect.setBackground(QtGui.QApplication.palette().highlight())
        self._fHighlight = QtGui.QTextCharFormat()
        self._fHighlight.setBackground(QtGui.QColor(0, 0, 0, 32))
        if run and font :
            self.loadrun(run, font)
        self.gview.setScene(self._scene)

    def loadrun(self, run, font) :
        self.run = run
        self._font = font
        self.currselection = None
        self._scene.clear()
        self._pixmaps = []
        self._gindices = [0]
        factor = font.size * 1. / font.upem
        res = QtCore.QRect()
        sels = []
        self.tview.setExtraSelections([])
        self.tview.setPlainText("")
        for i, s in enumerate(run) :
            g = font[s.gid]
            if g and g.pixmap :
                px = GlyphPixmapItem(i, g.pixmap, model = self, scene = self._scene)
                ppos = (s.origin[0] * factor + g.left, -s.origin[1] * factor - g.top)
                px.setOffset(*ppos)
                self._pixmaps.append(px)
                if s : s.pixmap(px)
                sz = g.pixmap.size()
                r = QtCore.QRect(ppos[0], ppos[1], sz.width(), sz.height())
                res = res.united(r)
            else :
                self._pixmaps.append(None)
            if g :
                t = g.GDLName() or g.psname
                self.tview.moveCursor(QtGui.QTextCursor.End)
                self.tview.insertPlainText(t + " ")
                self._gindices.append(self._gindices[-1] + len(t) + 1)
                if s.highlighted :
                    hselect = QtGui.QTextEdit.ExtraSelection()
                    hselect.format = self._fHighlight
                    hselect.cursor = QtGui.QTextCursor(self.tview.document())
                    hselect.cursor.movePosition(QtGui.QTextCursor.NextCharacter, n=self._gindices[-2])
                    hselect.cursor.movePosition(QtGui.QTextCursor.NextCharacter, 
                            QtGui.QTextCursor.KeepAnchor, self._gindices[-1] - 1 - self._gindices[-2])
                    sels.append(hselect)
        if len(sels) :
            self.tview.setExtraSelections(sels)
        self.boundingRect = res
        self._scene.setSceneRect(res)
        self.gview.setFixedSize(res.left() + res.width() + 2, res.height() - res.top() + 2)
        self.gview.resize(res.left() + res.width() + 2, res.height() - res.top() + 2)
        self.gview.updateScene([])

    def glyph_clicked(self, gitem, index) :
        s = self.tview.extraSelections()
        if self.currselection >= 0 and self._pixmaps[self.currselection] :
            self._pixmaps[self.currselection].select(False)
            s.pop()
        if self.currselection != index :
            self.currselection = index
            self._pixmaps[index].select(True)
            tselect = QtGui.QTextEdit.ExtraSelection()
            tselect.format = self._fSelect
            tselect.cursor = QtGui.QTextCursor(self.tview.document())
            tselect.cursor.movePosition(QtGui.QTextCursor.NextCharacter, n=self._gindices[index])
            tselect.cursor.movePosition(QtGui.QTextCursor.NextCharacter,
                    QtGui.QTextCursor.KeepAnchor, self._gindices[index + 1] - 1 - self._gindices[index])
            s.append(tselect)
            self.slotSelected.emit(self.run[self.currselection], self)
            self.glyphSelected.emit(self._font[self.run[self.currselection].gid], self)
        else :
            self.currselection = -1
        self.tview.setExtraSelections(s)

    def keyPressEvent(self, scene, event) :
        if self.currselection < 0 : return
        s = self.tview.extraSelections()
        if self._pixmaps[self.currselection] :
            self._pixmaps[self.currselection].select(False)
            s.pop()
        if event.key() == QtCore.Qt.Key_Right :
            self.currselection += 1
            if self.currselection >= len(self._pixmaps) :
                self.currselection = len(self._pixmaps) - 1
        elif event.key() == QtCore.Qt.Key_Left :
            self.currselection -= 1
            if self.currselection < 0 :
                self.currselection = 0
        if self._pixmaps[self.currselection] :
            self._pixmaps[self.currselection].select(True)
        tselect = QtGui.QTextEdit.ExtraSelection()
        tselect.format = self._fSelect
        tselect.cursor = QtGui.QTextCursor(self.tview.document())
        tselect.cursor.movePosition(QtGui.QTextCursor.NextCharacter, n=self._gindices[self.currselection])
        tselect.cursor.movePosition(QtGui.QTextCursor.NextCharacter, QtGui.QTextCursor.KeepAnchor,
                self._gindices[self.currselection + 1] - 1 - self._gindices[index])
        s.append(tselect)
        self.slotSelected.emit(self.run[self.currselection], self)
        self.glyphSelected.emit(self._font[self.run[self.currselection].gid], self)

    def clear_selected(self) :
        if self.currselection >= 0 :
            self._pixmaps[self.currselection].select(False)
            s = self.tview.extraSelections()
            s.pop()
            self.tview.setExtraSelections(s)
        self.currselection = -1
    
    def tEvent(self, event) :
        c = self.tview.cursorForPosition(event.pos()).position()
        for (i, g) in enumerate(self._gindices) :
            if c < g :
                self.glyph_clicked(None, i - 1)
                return True
        return False
            

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
    view = RunView(run, font).gview
    view.show()
    sys.exit(app.exec_())

    

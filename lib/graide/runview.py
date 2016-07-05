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

# A RunView consists of two sub-views: a display of the current glyphs (QGraphicsView)
# and a list of corresponding glyph names (QPlainTextEdit).

from PySide import QtCore, QtGui
from graide.utils import ModelSuper, DataObj
from graide.layout import Layout
import os, time, traceback

class GlyphPixmapItem(QtGui.QGraphicsPixmapItem) :

    def __init__(self, index, px, model = None, parent = None, scene = None) :
        super(GlyphPixmapItem, self).__init__(px, parent, scene)
        self.selected = False
        self.index = index
        self.highlighted = False
        self.highlightType = ""
        self.model = model
        self.highlightColours = Layout.slotColours

    def mousePressEvent(self, mouseEvent) :
        if self.model :
            self.model.glyphClicked(self, self.index, False)
            
    def mouseDoubleClickEvent(self, mouseEvent) :
        if self.scene :
            self.scene.mouseDoubleClickEvent(mouseEvent)

    def select(self, state) :
        self.selected = state
        self.update()

    def highlight(self, type = 'default') :
        self.highlighted = True
        self.highlightType = type

    def paint(self, painter, option, widget) :
        r = QtCore.QRect(QtCore.QPoint(self.offset().x(), self.offset().y()), self.pixmap().size())
        if self.selected :
            painter.fillRect(r, option.palette.highlight())
        elif self.highlighted and self.highlightType in self.highlightColours :
            painter.fillRect(r, self.highlightColours[self.highlightType])

        super(GlyphPixmapItem, self).paint(painter, option, widget)  # paint the foreground
      
      
# Apparently not used
class RunTextView(QtGui.QPlainTextEdit) :

    def __init__(self, creator, parent = None) :
        super(RunTextView, self).__init__(parent=parent)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.creator = creator

    def viewportEvent(self, event) :
        if event.type() == QtCore.QEvent.MouseButtonPress :
            return self.creator.tMousePress(event)
        return False

# Used for both the output pane in the bottom left corner of the window
# and for the Passes and Rules tabs.
class RunView(QtCore.QObject, ModelSuper) :
    
    MinHt = 70

    slotSelected = QtCore.Signal(DataObj, ModelSuper, bool)
    glyphSelected = QtCore.Signal(DataObj, ModelSuper, bool)

    def __init__(self, font = None, run = None, parent = None, collision = False) : # parent = PassesView, Matcher, or none
        super(RunView, self).__init__()
        self.parent = parent
        self.gview = QtGui.QGraphicsView(parent)	# graphics view - glyphs
        self.gview.setAlignment(QtCore.Qt.AlignLeft)
        self.gview.mouseDoubleClickEvent = self.sEvent
        if font : 
            self.gview.resize(self.gview.size().width(), max(font.pixrect.height(), RunView.MinHt))
        else :
            self.gview.resize(200, RunView.MinHt)
        self._scene = QtGui.QGraphicsScene(self.gview) # the scene contains the pixmaps
        self._scene.keyPressEvent = self.keyPressEvent
        self._scene.mouseDoubleClickEvent = self.sEvent
        self.tview = QtGui.QPlainTextEdit(parent)	# text view - glyph names
        self.tview.setReadOnly(True)
        self.tview.mousePressEvent = self.tEvent
        self.tview.mouseDoubleClickEvent = self.tEvent
        self._fSelect = QtGui.QTextCharFormat()
        self._fSelect.setBackground(QtGui.QApplication.palette().highlight())
        self._fHighlights = {}
        for c in Layout.slotColours.keys() :
            self._fHighlights[c] = QtGui.QTextCharFormat()
            self._fHighlights[c].setBackground(Layout.slotColours[c])
        self.collision = collision
        if run and font :
            self.loadRun(run, font)
        self.gview.setScene(self._scene)
        

    def loadRun(self, run, font, resize = True) :
        self.run = run
        self._font = font
        self.currselection = -1
        self._scene.clear()
        self._pixmaps = []
        # There might not be a 1-to-1 correspondence between slots and pixmaps -
        # slots with exclude glyphs create an extra pixmap:
        self._slotToPixmap = {}
        self._gindices = [0]
        scale = font.size * 1. / font.upem
        res = QtCore.QRect()
        sels = []
        self.tview.setExtraSelections([])
        self.tview.setPlainText("")
        
        self.updateData(run)
        
        for i, s in enumerate(run) :
            g = font[s.gid]
            
            # Is this a pseudo-glyph?
            try :
                gidActual = int(g.getGdlProperty("*actualForPseudo*"))
                #print s.gid," actual=",gidActual
            except :
                gidActual = 0
            gActual = font[gidActual] if gidActual != 0  else g

            self._slotToPixmap[i] = len(self._pixmaps)
            if gActual and gActual.item and gActual.item.pixmap :
                res = self.createPixmap(s, gActual, i, res, scale, model = self, scene = self._scene)
            else :
                #print "no GraideGlyph for",s.gid
                self._pixmaps.append(None)
            if g :
                glyphName = g.GDLName() or g.psname
                self.tview.moveCursor(QtGui.QTextCursor.End)
                self.tview.insertPlainText(glyphName + "  ") # 2 spaces between glyph names
                self._gindices.append(self._gindices[-1] + len(glyphName) + 2)
                if s.highlighted :
                    hselect = QtGui.QTextEdit.ExtraSelection()
                    if s.highlightType in self._fHighlights :
                        hselect.format = self._fHighlights[s.highlightType]
                    else :
                        hselect.format = self._fHighlights['default']
                    hselect.cursor = QtGui.QTextCursor(self.tview.document())
                    hselect.cursor.movePosition(QtGui.QTextCursor.NextCharacter, n=self._gindices[-2])
                    hselect.cursor.movePosition(QtGui.QTextCursor.NextCharacter, 
                            QtGui.QTextCursor.KeepAnchor, self._gindices[-1] - 2 - self._gindices[-2])
                    sels.append(hselect)
                    
            if self.collision and s.getColExclGlyph() :
                gExclude = s.getColExclGlyph()
                gExclude = font[gExclude]
                exclOff = s.getColExclOffsetSize()
                resExcl = self.createPixmap(s, gExclude, i, res, scale, model = self, scene = self._scene, exclOff = exclOff)
        
        if run.kernEdges is not None :
            def doEdge(lastx, curry, e, scale, pen) :  # local function
                if e > 1e+37 or e < -1e+37 : return None
                if lastx is not None :
                    t = QtGui.QGraphicsLineItem(lastx * scale, -curry * scale, e * scale, -curry * scale, scene = self._scene)
                    t.setPen(pen)
                    self.kernLines.append(t)
                t = QtGui.QGraphicsLineItem(e * scale, -curry * scale, e * scale, -(curry + run.kernEdges[3]) * scale, scene = self._scene)
                t.setPen(pen)
                self.kernLines.append(t)
                return e

            self.kernLines = []
            pene = QtGui.QPen('darkGreen')
            peno = QtGui.QPen('darkBlue')
#            pen.setWidth(2) # pixels
            curry = run.kernEdges[2]
            lastx = None
            for e in run.kernEdges[0] :
                lastx = doEdge(lastx, curry, e, scale, pene)
                curry += run.kernEdges[3]
            curry = run.kernEdges[2]
            lastx = None
            for e in run.kernEdges[1] :
                lastx = doEdge(lastx, curry, e, scale, peno)
                curry += run.kernEdges[3]
                
        self.tview.moveCursor(QtGui.QTextCursor.Start) # scroll to top
        
        if len(sels) :
            self.tview.setExtraSelections(sels)
        self.boundingRect = res
        self._scene.setSceneRect(res)
        
        if resize :
            ht = max(res.height() - res.top() + 2, RunView.MinHt)
            self.gview.setFixedSize(res.left() + res.width() + 2, ht)
            self.gview.resize(res.left() + res.width() + 2, ht)
            self.gview.updateScene([])

            
    # Overridden for TweakableRunView.
    def createPixmap(self, slot, glyph, index, res, scale, model = None, parent = None, scene = None, exclOff = None) :
        exclude = (exclOff != None) # is this a collision.exclude.glyph?
        if not exclOff :
            exclOff = QtCore.QSize(0, 0)
            
        px = GlyphPixmapItem(index, glyph.item.pixmap, model, parent, scene)
        ppos = (((slot.drawPosX()  + exclOff.width()) * scale) + glyph.item.left, 
                ((-slot.drawPosY() - exclOff.height()) * scale) - glyph.item.top)
        px.setOffset(*ppos)
        self._pixmaps.append(px)
        if slot : 
            if exclude :
                slot.setExclPixmap(px)
            else :
                slot.setPixmap(px)
        sz = glyph.item.pixmap.size()
        r = QtCore.QRect(ppos[0], ppos[1], sz.width(), sz.height())
        res = res.united(r)
        return res
        
    def updateData(self, run) :
        pass # overridden by TweakableRunView


    def glyphClicked(self, gitem, index, doubleClick) :
        if index != self.currselection :
            self.changeSelection(index, doubleClick)
        elif doubleClick :
            # Force the Glyph tab to be current:
            self.glyphSelected.emit(self._font[self.run[self.currselection].gid], self, doubleClick)

    def keyPressEvent(self, event) :
        if self.currselection < 0 : return  # no selection to move

        newSel = -1
        
        if event.key() == QtCore.Qt.Key_Left or event.key() == QtCore.Qt.Key_Right :
            # Figure out the new selection.
            if self.run.rtl :
                forward = True if event.key() == QtCore.Qt.Key_Left else False
            else :
                forward = True if event.key() == QtCore.Qt.Key_Right else False
            
            if forward :
                newSel = self.currselection + 1
                if newSel >= len(self._pixmaps) :
                    newSel = len(self._pixmaps) - 1
            else :
                newSel = self.currselection - 1
                if newSel < 0 :
                    newSel = 0
        
            if newSel >= 0 and newSel != self.currselection :
                self.changeSelection(newSel)
                
        
    def changeSelection(self, newSel, doubleClick) :
        s = self.tview.extraSelections()
        
        if self.currselection >= 0 :
            self.selectPixmapForSlot(self.currselection, False)
            s.pop()
            
        if newSel >= 0 and self.currselection != newSel :
            self.currselection = newSel
            self.selectPixmapForSlot(newSel, True)
                
            # Highlight the name of the selected glyph in the text view.
            tselect = QtGui.QTextEdit.ExtraSelection()
            tselect.format = self._fSelect
            tselect.cursor = QtGui.QTextCursor(self.tview.document())
            tselect.cursor.movePosition(QtGui.QTextCursor.NextCharacter, n=self._gindices[newSel])
            tselect.cursor.movePosition(QtGui.QTextCursor.NextCharacter,
                    QtGui.QTextCursor.KeepAnchor, self._gindices[newSel + 1] - self._gindices[newSel] - 2 )
            s.append(tselect)
            selectedSlot = self.run[self.currselection]
            self.slotSelected.emit(selectedSlot, self, doubleClick)
            self.glyphSelected.emit(self._font[selectedSlot.gid], self, doubleClick)
        else :
            self.currselection = -1
            
        self.tview.setExtraSelections(s)
        
    def clearSelected(self) :
        if self.currselection >= 0 :
            self.selectPixmapForSlot(self.currselection, False)

            s = self.tview.extraSelections()
            s.pop()
            self.tview.setExtraSelections(s)
        self.currselection = -1
    
    # There is not necessarily a one-to-one correspondence between slots and pixmaps 
    # (due to exclude glyphs), so this method maps from one to the other.
    def selectPixmapForSlot(self, i, selectValue) :
        if i >= 0 :
            try :
                try :
                    pixmap = self._pixmaps[self._slotToPixmap[i]]
                except :
                    pixmap = self._pixmaps[i]
            except :
                pixmap = None
            if pixmap :
                pixmap.select(selectValue)
            
    def tEvent(self, event) :
        doubleClick = (event.type() == QtCore.QEvent.MouseButtonDblClick)
        c = self.tview.cursorForPosition(event.pos()).position()
        for (i, g) in enumerate(self._gindices) :
            if c < g :
                self.glyphClicked(None, i - 1, doubleClick)
                return True
        return False
        
    def sEvent(self, event) :
        if event.type() == QtCore.QEvent.MouseButtonDblClick :
            image = QtGui.QImage(self._scene.width(), self._scene.height(), QtGui.QImage.Format_ARGB32)
            image.fill(0xFFFFFFFF)
            painter = QtGui.QPainter()
            painter.begin(image)
            self._scene.render(painter)
            #time.sleep(3)
            painter.end()
            count = 1
            fname = ''
            while True :
                fname = 'graide_image_{}.png'.format(str(count))
                if not os.path.exists(fname) :
                    break
                count += 1
            image.save(fname)
            #time.sleep(3)
            print "Saved image to " + fname

    def clear(self) :
        self._scene.clear()
        self.tview.setPlainText("")
        self.gview.update()

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
    run = Run(font, False)
    run.addSlots(rinfo)
    view = RunView(run, font).gview
    print "Padauk RunView?" ###
    view.show()
    sys.exit(app.exec_())

    

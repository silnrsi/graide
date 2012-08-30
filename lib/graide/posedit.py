#!/usr/bin/python

#    Copyright 2012, SIL International
#    All rights selferved.
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
from graide.layout import Layout

POSGLYPHID = 1
WHEELSCALEINCREMENT = 1.05

class PosGlyph(QtGui.QTreeWidgetItem, QtCore.QObject) :

    posGlyphChanged = QtCore.Signal()

    def __init__(self, font, parent, data) :
        QtCore.QObject.__init__(self)       # Qt not happy if this isn't first
        super(PosGlyph, self).__init__(parent, data, type = QtGui.QTreeWidgetItem.UserType + POSGLYPHID)
        self.px = None
        self.font = font
        self.position = (0, 0)
        self.glyph = None
        self.dialog = None
        self.scale = font.posglyphSize * 1. / font.upem

    def setDialog(self, d) :
        self.dialog = d

    def getAnchor(self, apname) :
        if self.glyph and apname in self.glyph.anchors:
            return self.glyph.anchors[apname]
        return None

    def setText(self, col, txt) :
        if txt == self.text(col) : return
        super(PosGlyph, self).setText(col, txt)
        if col == 0 :       # set glyph
            self.setGlyph(txt)

    def setGlyph(self, name) :
        glyph = self.font.gdls.get(name, None)
        if glyph == self.glyph : return
        self.glyph = glyph
        self.setPixmap()
        self.posGlyphChanged.emit()

    def setPixmap(self, scene = None) :
        if (scene is None and not self.px) : return
        if self.glyph :
            if not self.glyph.item : return
            (px, left, top) = self.glyph.item.pixmapAt(self.font.posglyphSize)
            if self.px is not None :
                self.px.setPixmap(px)
            else :
                self.px = PosPixmapItem(px, self, scene = scene)
            self.px.left = left
            self.px.top = top
            self.px.setOffset(left, -top)
        elif self.px is not None :
            self.clearpx()

    def setAnchor(self, name, x, y) :
        if self.glyph and self.glyph.setAnchor(name, x, y) :
            self.posGlyphChanged.emit()
        # print "setAnchor: ", name, (x, y)

    def setPos(self, x, y) :
        """Sets glyph position in design units"""
        x *= self.scale
        y *= -self.scale        # scene units have 0 at top
        self.position = (x, y)
        if self.px :
            # self.px.setOffset(self.px.left, -self.px.top)
            self.px.setPos(x, y)
            # print "pos, left, top ", (x, y), self.px.left, self.px.top

    def pos(self) :
        """Returns glyph position in scene units"""
        return self.position

    def clearpx(self) :
        if self.px is None : return
        scene = self.px.scene()
        scene.removeItem(self.px)
        self.px = None
        scene.update()

    def getActiveAPs(self) :
        """Return (anchor_scene_pos, [moveable_anchor_pos, stationary_anchor_pos])
            Both moveable and stationary anchor positions are in scene units relative to their glyphs"""
        res1 = self.getAnchor(self.text(1))
        res2 = self.parent().getAnchor(self.text(2))
        # print (self.position[0]/self.scale + res1[0], self.position[1]/self.scale + res1[1])
        return ((self.position[0] + self.scale * res1[0], self.position[1] - self.scale * res1[1]),
                self.position,
                [(res1[0] * self.scale, -res1[1] * self.scale), (res2[0] * self.scale, -res2[1] * self.scale)])

    def setMoveableAnchor(self, sx, sy) :
        """Adjust anchor point based on scene offsets"""
        x = int(sx / self.scale)
        y = -int(sy / self.scale)
        if self.dialog :
            self.dialog.setAPPos(x, y)
        else :
            self.glyph.setAnchor(self.text(1), x, y)

    def setBaseAnchor(self, sx, sy) :
        """Adjust base anchor position for this diacritic"""
        x = int(sx / self.scale)
        y = -int(sy / self.scale)
        if self.parent().dialog :
            self.parent().dialog.setAPPos(x, y)
        else :
            self.parent().glyph.setAnchor(self.text(2), x, y)


class PosPixmapItem(QtGui.QGraphicsPixmapItem) :

    def __init__(self, px, item, parent = None, scene = None) :
        super(PosPixmapItem, self).__init__(px, parent, scene)
        if parent is not None : raise TypeError
        self.item = item
        self.shiftState = False
        self.moveState = False
        self.apItem = None
        self.movepx = None
        self.shiftpx = None
        if item.parent() : self.setFlags(QtGui.QGraphicsItem.ItemIsMovable | QtGui.QGraphicsItem.ItemIsFocusable)

    def keyPressEvent(self, event) :
        if event.modifiers() & QtCore.Qt.ShiftModifier :
            # print "Shift pressed for " + str(self.item.glyph.name)
            self.shiftState = True
            if self.moveState :
                if self.apItem :
                    self.apItem.setPos(self.sceneAP[0], self.sceneAP[1])
                    self.apItem.setBrush(Layout.posdotShiftColour)
                self.item.setMoveableAnchor(self.diff[0] + self.origAPs[0][0], self.diff[1] + self.origAPs[0][1])
                self.item.setBaseAnchor(self.origAPs[1][0], self.origAPs[1][1])
        try : event.ignore()
        except TypeError : pass

    def keyReleaseEvent(self, event) :
        if not event.modifiers() & QtCore.Qt.ShiftModifier :
            # print "Shift released for " + str(self.item.glyph.name)
            self.shiftState = False
            if self.moveState :
                if self.apItem :
                    self.apItem.setPos(self.diff[0] + self.sceneAP[0], self.diff[1] + self.sceneAP[1])
                    self.apItem.setBrush(Layout.posdotColour)
                self.item.setMoveableAnchor(self.origAPs[0][0], self.origAPs[0][1])
                self.item.setBaseAnchor(self.diff[0] + self.origAPs[1][0], self.diff[1] + self.origAPs[1][1])
        try : event.ignore()
        except TypeError : pass

    def mousePressEvent(self, event) :
        (self.sceneAP, self.origPos, self.origAPs) = self.item.getActiveAPs()
        self.diff = (0, 0)
        self.shiftState = False
        self.keyPressEvent(event)
        try : event.accept()
        except TypeError : pass
        self.moveState = True
        self.scene().view.updateable(False)
        radius = self.item.font.posglyphSize / 20
        self.apItem = self.scene().addEllipse(-radius / 2, -radius / 2, radius, radius,
                brush = Layout.posdotShiftColour if self.shiftState else Layout.posdotColour)
        self.apItem.setPos(self.sceneAP[0], self.sceneAP[1])
        # print self.sceneAP, self.apItem.scenePos()
        super(PosPixmapItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event) :
        self.moveState = False
        self.scene().view.updateable(True)
        self.scene().view.posGlyphChanged()
        if self.apItem :
            self.scene().removeItem(self.apItem)
            self.apItem = None
        super(PosPixmapItem, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event) :
        spos = event.scenePos()
        bpos = event.buttonDownScenePos(QtCore.Qt.LeftButton)
        self.diff = (spos - bpos).toTuple()
        if self.shiftState :
            self.item.setMoveableAnchor(self.origAPs[0][0] - self.diff[0], self.origAPs[0][1] - self.diff[1])
        else :
            self.item.setBaseAnchor(self.diff[0] + self.origAPs[1][0], self.diff[1] + self.origAPs[1][1])
            #print self.diff, self.sceneAP
            if self.apItem :
                appos = (self.sceneAP[0] + self.diff[0], self.sceneAP[1] + self.diff[1])
                self.apItem.setPos(*appos)
                # print "    ", (self.apItem.scenePos().x() / self.item.scale, self.apItem.scenePos().y() / self.item.scale)
        self.item.position = (self.origPos[0] + self.diff[0], self.origPos[1] + self.diff[1])
        super(PosPixmapItem, self).mouseMoveEvent(event)


class PosGlyphInfoWidget(QtGui.QFrame) :

    def __init__(self, title, isBase = False, parent = None) :
        super(PosGlyphInfoWidget, self).__init__(parent)
        self.isBase = isBase
        self.item = None
        self.setFrameStyle(QtGui.QFrame.Box | QtGui.QFrame.Sunken)
        self.setLineWidth(1)
        self.layout = QtGui.QGridLayout(self)
        self.layout.addWidget(QtGui.QLabel(title), 0, 0, 1, 2)
        self.reset = QtGui.QPushButton("Revert")
        self.reset.setEnabled(False)
        self.reset.clicked.connect(self.doReset)
        self.layout.addWidget(self.reset, 0, 3)
        self.glyph = QtGui.QComboBox(self)
        self.layout.addWidget(QtGui.QLabel("Glyph"), 1, 0, 1, 2)
        self.layout.addWidget(self.glyph, 1, 3, 1, 2)
        self.glyph.currentIndexChanged[unicode].connect(self.posChanged)
        self.glyph.editTextChanged.connect(self.posChanged)
        self.aps = QtGui.QComboBox(self)
        self.layout.addWidget(QtGui.QLabel("Attachment"), 2, 0, 1, 2)
        self.layout.addWidget(self.aps, 2, 3, 1, 2)
        self.aps.currentIndexChanged[unicode].connect(self.posChanged)
        self.aps.editTextChanged.connect(self.posChanged)
        self.x = QtGui.QSpinBox(self)
        self.x.setRange(-32768, 32767)
        self.x.valueChanged[int].connect(self.changePos)
        self.layout.addWidget(QtGui.QLabel("X"), 3, 0)
        self.layout.addWidget(self.x, 3, 1)
        self.y = QtGui.QSpinBox(self)
        self.y.setRange(-32768, 32767)
        self.y.valueChanged[int].connect(self.changePos)
        self.layout.addWidget(QtGui.QLabel("Y"), 3, 2)
        self.layout.addWidget(self.y, 3, 3)

    def posChanged(self, text) :
        gname = self.glyph.currentText()
        self.item.setText(0, gname)
        if self.item.glyph is not None :
            ap = self.aps.currentText()
            pos = self.item.glyph.anchors.get(ap, None)
            if pos is not None :
                self.x.setValue(pos[0])
                self.y.setValue(pos[1])
                self.orig = pos
                self.reset.setEnabled(False)
                if self.isBase :
                    self.apitem.setText(2, ap)
                else :
                    self.item.setText(1, ap)

    def changePos(self, val) :
        self.item.setAnchor(self.aps.currentText(), self.x.value(), self.y.value())
        self.reset.setEnabled(True)

    def setGlyph(self, font, gname, apname, item, apitem) :
        self.font = font
        self.item = item
        self.item.setDialog(self)
        self.apitem = apitem
        if gname in font.gdls :
            glist = sorted(filter(lambda x : apname in font.gdls[x].anchors, font.gdls.keys()))
            aplist = sorted(font.gdls[gname].anchors.keys())
            self.glyph.clear()
            self.glyph.addItems(['(None)'] + glist)
            self.glyph.setCurrentIndex(1 + glist.index(gname))
            self.aps.clear()
            self.aps.addItems(['(None)'] + aplist)
            self.aps.setCurrentIndex(1 + aplist.index(apname))

    def doReset(self) :
        self.x.setValue(self.orig[0])
        self.y.setValue(self.orig[1])
        self.reset.setEnabled(False)

    def setAPPos(self, x, y) :
        self.x.setValue(x)
        self.y.setValue(y)

class PosGlyphAPDialog(QtGui.QDialog) :

    def __init__(self, font, base = None) :
        super(PosGlyphAPDialog, self).__init__()
        self.font = font
        self.base = base
        self.layout = QtGui.QGridLayout(self)
        self.names = QtGui.QComboBox(self)
        self.names.addItems(['(None)'] + sorted(font.gdls.keys()))
        self.names.currentIndexChanged[unicode].connect(self.glyphChanged)
        self.names.editTextChanged.connect(self.glyphChanged)
        self.layout.addWidget(QtGui.QLabel("Glyph Name"), 0, 0)
        self.layout.addWidget(self.names, 0, 1)
        if base is not None :
            self.withaps = QtGui.QComboBox(self)
            self.layout.addWidget(QtGui.QLabel("With AP"), 1, 0)
            self.layout.addWidget(self.withaps, 1, 1)
            self.ataps = QtGui.QComboBox(self)
            self.layout.addWidget(QtGui.QLabel("At AP"), 2, 0)
            self.layout.addWidget(self.ataps, 2, 1)
            if base in self.font.gdls :
                self.ataps.clear()
                self.ataps.addItems(sorted(self.font.gdls[base].anchors.keys()))
        o = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        o.accepted.connect(self.accept)
        o.rejected.connect(self.reject)
        self.layout.addWidget(o, (1 if base is None else 3), 0, 1, 2)

    def glyphChanged(self, txt) :
        if self.base and txt in self.font.gdls :
            g = self.font.gdls[txt]
            self.withaps.clear()
            self.withaps.addItems(sorted(g.anchors.keys()))


class PosEditTree(QtGui.QTreeWidget) :

    def __init__(self, font, parent = None) :
        super(PosEditTree, self).__init__(parent)
        self.font = font
        self.setColumnCount(3)
        self.setHeaderLabels(('Glyph', 'With', 'At'))
        self.view = None

    def contextMenuEvent(self, event) :
        item = self.itemAt(event.pos())
        menu = QtGui.QMenu()
        insertAction = menu.addAction("Insert Child")
        action = menu.exec_(event.globalPos())
        if action == insertAction :
            if self.topLevelItemCount() == 0 :
                base = None
            elif item is None :
                base = self.selectedItems()[0].text(0)
            else :
                base = item.text(0)
            d = PosGlyphAPDialog(self.font, base)
            if d.exec_() :
                gname = d.names.currentText()
                if base is None :
                    res = PosGlyph(self.font, None, (gname,))
                    self.addTopLevelItem(res)
                else :
                    withap = d.withaps.currentText()
                    atap = d.ataps.currentText()
                    res = PosGlyph(self.font, item, (gname, withap, atap))
                    item.setExpanded(True)
                if self.view is not None : res.posGlyphChanged.connect(self.view.posGlyphChanged)


class PosEdit(QtGui.QWidget) :

    def __init__(self, font, parent = None) :
        super(PosEdit, self).__init__(parent)
        self.font = font
        self.view = None
        self.layout = QtGui.QVBoxLayout(self)
        self.treeView = PosEditTree(font, self)
        self.treeView.itemClicked.connect(self.itemClicked)
        self.layout.addWidget(self.treeView)
        self.baseInfo = PosGlyphInfoWidget("Base", True, self)
        self.layout.addWidget(self.baseInfo)
        self.diaInfo = PosGlyphInfoWidget("Diacritic", False, self)
        self.layout.addWidget(self.diaInfo)

    def setView(self, view) :
        self.view = view
        self.treeView.view = view

    def itemClicked(self, item, col) :
        parent = item.parent()
        if parent is not None :
            self.baseInfo.setGlyph(self.font, parent.text(0), item.text(2), parent, item)
            self.diaInfo.setGlyph(self.font, item.text(0), item.text(1), item, item)
        while parent is not None :
            item = parent
            parent = item.parent()
        self.view.setRoot(item)
        self.view.promote()
        self.view.posGlyphChanged()

class PosView(QtGui.QGraphicsView) :

    def __init__(self, app = None, parent = None) :
        super(PosView, self).__init__(parent)
        self._scene = QtGui.QGraphicsScene()
        self._scene.view = self
        self.setScene(self._scene)
        self.centerOn(0, 0)
        self.app = app
        self.root = None
        self._updateable = True
        # self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)

    def promote(self) :
        self.app.posSelected()

    def setRoot(self, item) :
        self.root = item

    def updateable(self, state) :
        self._updateable = state

    def posGlyphChanged(self) :
        if self.root is not None and self._updateable :
            self.addTree(self.root, base = (0, 0))
#            self.org = QtGui.QGraphicsEllipseItem(0, 0, 2, 2, scene = self.scene())

    def addTree(self, item, base = (0, 0)) :
        """Adds the glyph and its children at the given position in design units"""
        pos = list(base)
        parent = item.parent()
        if parent :
            ppos = parent.getAnchor(item.text(2))
            if ppos is None : ppos = (0, 0)
            dpos = item.getAnchor(item.text(1))
            if dpos is None : dpos = (0, 0)
            pos[0] += ppos[0] - dpos[0]
            pos[1] += ppos[1] - dpos[1]
        if not item.px : item.setPixmap(scene = self.scene())
        item.setPos(pos[0], pos[1])
        for i in range(item.childCount()) :
            self.addTree(item.child(i), pos)

    def wheelEvent(self, event) :
        scale = pow(WHEELSCALEINCREMENT, event.delta() / 120.)
        self.scale(scale, scale)


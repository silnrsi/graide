
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
from graide.utils import Layout

class Classes(QtGui.QWidget) :

    classUpdated = QtCore.Signal(str, str)
    classSelected = QtCore.Signal(str)

    def __init__(self, font, parent = None) :
        super(Classes, self).__init__(parent)
        self.vb = QtGui.QVBoxLayout(self)
        self.vb.setContentsMargins(*Layout.buttonMargins)
        self.vb.setSpacing(Layout.buttonSpacing)
        self.tab = QtGui.QTableWidget(self)
        self.vb.addWidget(self.tab)
        self.tab.setColumnCount(2)
        self.tab.cellDoubleClicked.connect(self.doubleClicked)
        self.tab.cellClicked.connect(self.clicked)
        self.tab.horizontalHeader().hide()
        self.tab.verticalHeader().hide()
        self.bbox = QtGui.QWidget(self)
        self.hb = QtGui.QHBoxLayout(self.bbox)
        self.hb.setContentsMargins(*Layout.buttonMargins)
        self.hb.setSpacing(Layout.buttonSpacing)
        self.hb.addStretch()
        self.vb.addWidget(self.bbox)
        self.cButton = QtGui.QToolButton()
        self.cButton.setText(u'\u2690')
        self.cButton.clicked.connect(self.clearHighlights)
        self.hb.addWidget(self.cButton)
        self.font = font
        if font :
            self.loadFont(font)

    def resizeEvent(self, event) :
        self.tab.setColumnWidth(1, self.size().width() - self.tab.columnWidth(0) - 2)

    def loadFont(self, font) :
        self.font = font
        keys = sorted(font.classes.keys())
        num = len(keys)
        oldnum = self.tab.rowCount()
        if num != oldnum :
            self.tab.setRowCount(num)
        for i in range(num) :
            l = QtGui.QTableWidgetItem(keys[i])
            l.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            v = map(lambda x: font[x].GDLName() if font[x] else "", font.classes[keys[i]])
            m = QtGui.QTableWidgetItem("  ".join(v))
            m.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
            self.tab.setItem(i, 0, l)
            self.tab.setItem(i, 1, m)

    def doubleClicked(self, row, col) :
        d = QtGui.QDialog(self)
        d.setWindowTitle(self.tab.item(row, 0).text())
        l = QtGui.QVBoxLayout(d)
        edit = QtGui.QPlainTextEdit(self.tab.item(row, 1).text(), d)
        l.addWidget(edit)
        o = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        o.accepted.connect(d.accept)
        o.rejected.connect(d.reject)
        l.addWidget(o)
        if d.exec_() :
            t = edit.toPlainText()
            self.tab.item(row, 1).setText(t)
            self.tab.classUpdated.emit(label.text(), t)

    def clicked(self, row, cell) :
        self.classSelected.emit(self.tab.item(row, 0).text())

    def clearHighlights(self) :
        self.classSelected.emit(None)


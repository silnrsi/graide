
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

class Classes(QtGui.QTableWidget) :

    classUpdated = QtCore.Signal(str, str)

    def __init__(self, font, parent = None) :
        super(Classes, self).__init__(parent)
        self.setColumnCount(2)
        self.cellDoubleClicked.connect(self.doubleClicked)
        if font :
            self.loadFont(font)

    def loadFont(self, font) :
        keys = sorted(font.classes.keys())
        num = len(keys)
        oldnum = self.rowCount()
        if num != oldnum :
            self.setRowCount(num)
        for i in range(num) :
            l = QtGui.QTableWidgetItem(keys[i])
            l.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            v = map(lambda x: font[x].GDLName() if font[x] else "", font.classes[keys[i]])
            m = QtGui.QTableWidgetItem(" ".join(v))
            m.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
            self.setItem(i, 0, l)
            self.setItem(i, 1, m)

    def doubleClicked(self, row, col) :
        d = QtGui.QDialog(self)
        l = QtGui.QVBoxLayout(d)
        label = QtGui.QLabel(self.item(row, 0).text(), d)
        l.addWidget(label)
        edit = QtGui.QPlainTextEdit(self.item(row, 1).text(), d)
        l.addWidget(edit)
        o = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        o.accepted.connect(d.accept)
        o.rejected.connect(d.reject)
        l.addWidget(o)
        if d.exec_() :
            t = edit.toPlainText()
            self.item(row, 1).setText(t)
            self.classUpdated.emit(label.text(), t)

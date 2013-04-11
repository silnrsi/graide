
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
from graide.utils import configintval
from graide.layout import Layout

class Classes(QtGui.QWidget) :

    classUpdated = QtCore.Signal(str, str)
    classSelected = QtCore.Signal(str)

    def __init__(self, font, app, apgdlfile, parent = None) :
        super(Classes, self).__init__(parent)
        self.app = app
        self.ronly = configintval(app.config, 'build', 'apronly')
        self.apgdlfile = apgdlfile
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
        self.cButton = QtGui.QToolButton()	# clear highlights
        self.cButton.setIcon(QtGui.QIcon.fromTheme('edit-clear', QtGui.QIcon(":/images/edit-clear.png")))
        self.cButton.clicked.connect(self.clearHighlights)
        self.cButton.setToolTip('Clear glyph highlights')
        self.hb.addWidget(self.cButton)
        if not self.ronly :
            self.aButton = QtGui.QToolButton()
            self.aButton.setIcon(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")))
            self.aButton.clicked.connect(self.addClass)
            self.aButton.setToolTip('Add new class')
            self.hb.addWidget(self.aButton)
            self.rButton = QtGui.QToolButton()
            self.rButton.setIcon(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")))
            self.rButton.clicked.connect(self.delCurrent)
            self.rButton.setToolTip('Remove currently selected class')
            self.hb.addWidget(self.rButton)
        self.fButton = QtGui.QToolButton()	# find class
        self.fButton.setIcon(QtGui.QIcon.fromTheme('edit-find', QtGui.QIcon(":/images/find-normal.png")))
        self.fButton.clicked.connect(self.findSelectedClass)
        self.fButton.setToolTip('Find class selected in source code')
        self.hb.addWidget(self.fButton)
        self.classCount = 0
        self.font = font
        if font :
            self.loadFont(font)
            
        self.selClassName = ''

    def resizeEvent(self, event) :
        self.tab.setColumnWidth(1, self.size().width() - self.tab.columnWidth(0) - 2)

    # Populate the Classes tab with the defined classes.
    def loadFont(self, font) :
        self.font = font
        keys = sorted(font.classes.keys())
        num = len(keys)
        self.classCount = num
        oldnum = self.tab.rowCount()
        if num != oldnum :
            self.tab.setRowCount(num)
        for i in range(num) :
            l = QtGui.QTableWidgetItem(keys[i])
            l.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            c = font.classes[keys[i]]
            v = map(lambda x: font[x].GDLName() if font[x] else "", c.elements)
            if len(v) :
                m = QtGui.QTableWidgetItem("  ".join(filter(None, v)))
            else :
                m = QtGui.QTableWidgetItem("")
            t = ""
            if self.ronly : c.editable = False
            if c.generated : t += "Generated "
            if c.editable : t += "Editable "
            if c.fname : t += c.fname
            l.setToolTip(t)
            if (c.generated or not c.editable) and c.fname :
                m.setFlags(QtCore.Qt.NoItemFlags)
            else :
                m.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
            m.loc = (c.fname, c.lineno, c.editable)
            self.tab.setItem(i, 0, l)
            self.tab.setItem(i, 1, m)

    def doubleClicked(self, row, col) :
        self.findSourceForClass(row)

    def clicked(self, row, cell) :
        self.classSelected.emit(self.tab.item(row, 0).text())
        
    # Highlight the source code where the given class is defined in the code pane.
    def findSourceForClass(self, row) :
        c = self.tab.item(row, 1)
        if not c.loc[0] or c.loc[2] :
            d = QtGui.QDialog(self)
            name = self.tab.item(row, 0).text()
            d.setWindowTitle(name)
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
                self.classUpdated.emit(name, t)
        elif c.loc[0] :
            self.app.selectLine(*c.loc[:2])
            return True    	

    def clearHighlights(self) :
        self.classSelected.emit(None)

    def addClass(self) :
        (name, ok) = QtGui.QInputDialog.getText(self, 'Add Class', 'Class Name:')
        if name and ok :
            self.classUpdated.emit(name, "")
            l = QtGui.QTableWidgetItem(name)
            l.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            v = QtGui.QTableWidgetItem("")
            v.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
            r = self.tab.rowCount()
            self.tab.setRowCount(r + 1)
            self.tab.setItem(r, 0, l)
            self.tab.setItem(r, 1, v)

    def delCurrent(self) :
        r = self.tab.currentRow()
        name = self.tab.item(r, 0).text()
        self.classUpdated.emit(name, None)
        self.tab.removeRow(r)
    
    # Scroll to the selected class and highlight it.
    def findSelectedClass(self) :
    	className = self.app.tab_edit.selectedText
    	d = QtGui.QDialog(self)
    	rowMatched = -1
    	for row in range(0, self.classCount) :
    	    edit = QtGui.QPlainTextEdit(self.tab.item(row, 0).text(), d)
    	    cname = edit.toPlainText()
    	    if cname == className :
    	    	rowMatched = row
    	    	break
    	
    	if rowMatched > -1 :
    	    item = self.tab.item(rowMatched, 0)
    	    self.tab.scrollToItem(item)
    	    item.setBackground(Layout.activePassColour)
    	    
    	    if self.selClassName == className :  # second time clicked
    	        self.findSourceForClass(rowMatched)
    	#else :
    	#    QtGui.QSound.play()
    	        
    	self.selClassName = className


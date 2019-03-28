
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
from graide.utils import configintval
from graide.layout import Layout
import traceback

class ClassMemberDialog(QtWidgets.QDialog) :
    
    def __init__(self, parent, className, memberList) :
        super(ClassMemberDialog,self).__init__(parent)
        
        # Hide the help icon, all it does it take up space.
        #icon = self.windowIcon() -- just in case icon gets lost
        flags = self.windowFlags()
        helpFlag = QtCore.Qt.WindowContextHelpButtonHint
        flags = flags & (~helpFlag)
        self.setWindowFlags(flags)
        #self.setWindowIcon(icon)

        self.setWindowTitle(className)
        listWidget = QtWidgets.QListWidget(self)
        #listWidget.clicked.connect(self.doReturn)
        itemHeight = 18
        cnt = 0
        for member in memberList:
            if member == "" or member == " " :
                continue
                
            item = QtWidgets.QListWidgetItem(member)
            item.setSizeHint(QtCore.QSize(200, itemHeight))
            listWidget.addItem(item)
            cnt = cnt + 1
            
        listWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        if cnt <= 25 :
            displayCnt = 4 if cnt < 5 else cnt
            listWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            # It's okay if the list and dialog widths don't match, since there's no scroll bar.
            # Make the list widget wide enough that they can expand the dialog and see wide names.
            listWidget.setFixedWidth(300)
            self.setMinimumWidth(200)
        else :
            displayCnt = 25
            listWidget.setFixedWidth(300)  # make it wide enough to handle long names
            self.setMinimumWidth(300)
            #listWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        
        listWidget.setFixedHeight(displayCnt * itemHeight + 10)
        self.setMinimumHeight(displayCnt * itemHeight + 10)
        
    # end of __init_
        
                    
    def doReturn(self) :
        self.done(0)  # close
    
# end of class ClassMemberDialog


# Classes tab widget
class Classes(QtWidgets.QWidget) :

    classUpdated = QtCore.Signal(str, str)
    classSelected = QtCore.Signal(str)

    def __init__(self, font, app, apgdlfile, parent = None) :
        super(Classes, self).__init__(parent)
        self.app = app
        self.ronly = configintval(app.config, 'build', 'apronly')
        self.apgdlfile = apgdlfile
        self.vb = QtWidgets.QVBoxLayout(self)
        self.vb.setContentsMargins(*Layout.buttonMargins)
        self.vb.setSpacing(Layout.buttonSpacing)
        self.tab = QtWidgets.QTableWidget(self)
        self.vb.addWidget(self.tab)
        self.tab.setColumnCount(2)
        self.tab.cellDoubleClicked.connect(self.doubleClicked)
        self.tab.cellClicked.connect(self.clicked)
        self.tab.horizontalHeader().hide()
        self.tab.verticalHeader().hide()
        self.bbox = QtWidgets.QWidget(self)
        self.hb = QtWidgets.QHBoxLayout(self.bbox)
        self.hb.setContentsMargins(*Layout.buttonMargins)
        self.hb.setSpacing(Layout.buttonSpacing)
        self.hb.addStretch()
        self.vb.addWidget(self.bbox)
        self.cButton = QtWidgets.QToolButton()	# clear highlights
        self.cButton.setIcon(QtGui.QIcon.fromTheme('edit-clear', QtGui.QIcon(":/images/edit-clear.png")))
        self.cButton.clicked.connect(self.clearHighlights)
        self.cButton.setToolTip('Clear glyph highlights')
        self.hb.addWidget(self.cButton)
        if not self.ronly :
            self.aButton = QtWidgets.QToolButton()
            self.aButton.setIcon(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")))
            self.aButton.clicked.connect(self.addClass)
            self.aButton.setToolTip('Add new class')
            self.hb.addWidget(self.aButton)
            self.rButton = QtWidgets.QToolButton()
            self.rButton.setIcon(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")))
            self.rButton.clicked.connect(self.delCurrent)
            self.rButton.setToolTip('Remove currently selected class')
            self.hb.addWidget(self.rButton)
        self.fButton = QtWidgets.QToolButton()	# find class
        self.fButton.setIcon(QtGui.QIcon.fromTheme('edit-find', QtGui.QIcon(":/images/find-normal.png")))
        self.fButton.clicked.connect(self.findSelectedClass)
        self.fButton.setToolTip('Find class selected in source code')
        self.hb.addWidget(self.fButton)
        self.classCount = 0
        self.font = font
        if font :
            self.loadFont(font)
            
        self.selClassName = ''
        
    # end of __init__
    

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
            l = QtWidgets.QTableWidgetItem(keys[i])
            l.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            c = font.classes[keys[i]]
            v = map(lambda x: font[x].GDLName() if font[x] else "", c.elements)
            vList = list(v)
            if len(vList) :
                m = QtWidgets.QTableWidgetItem("  ".join(filter(None, vList)))
            else :
                m = QtWidgets.QTableWidgetItem("")
            t = ""
            if self.ronly : c.editable = False
            if c.generated : t += "Generated "
            if c.editable : t += "Editable "
            if c.fname : t += c.fname
            l.setToolTip(t)
            if (c.generated or not c.editable) and c.fname :
                m.setFlags(QtCore.Qt.NoItemFlags | QtCore.Qt.ItemIsEnabled)
            else :
                m.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
            m.fileLoc = (c.fname, c.lineno, c.editable)
            self.tab.setItem(i, 0, l)
            self.tab.setItem(i, 1, m)

    # end of loadFont
    
    
    def doubleClicked(self, row, col) :
        if col == 0 :
            self.findSourceForClass(row)
        elif col == 1 :
            self.popupClassMembers(row)

    
    def clicked(self, row, cell) :
        # FontView::classSelected - highlight glyphs in Font tab
        self.classSelected.emit(self.tab.item(row, 0).text())
        
    
    def popupClassMembers(self, row) :
        className = self.tab.item(row, 0).text()
        memberText = self.tab.item(row, 1).text()
        memberList = memberText.split(" ")
        dialog = ClassMemberDialog(self, className, memberList)
        dialog.show()   # modeless
        
    
    # Highlight the source code where the given class is defined in the code pane.
    def findSourceForClass(self, row) :
        #print("findSourceForClass")
        c = self.tab.item(row, 1)
        if not c.fileLoc[0] or c.fileLoc[2] :
            #print(c.fileLoc[0], c.fileLoc[2])
            d = QtWidgets.QDialog(self)
            name = self.tab.item(row, 0).text()
            d.setWindowTitle(name)
            l = QtWidgets.QVBoxLayout(d)
            edit = QtWidgets.QPlainTextEdit(self.tab.item(row, 1).text(), d)
            l.addWidget(edit)
            o = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
            o.accepted.connect(d.accept)
            o.rejected.connect(d.reject)
            l.addWidget(o)
            if d.exec_() :
                t = edit.toPlainText()
                self.tab.item(row, 1).setText(t)
                self.classUpdated.emit(name, t)
        elif c.fileLoc[0] :
            #print("send array", c.fileLoc[0], c.fileLoc[1])
            self.app.selectLine(*c.fileLoc[:2])
            return True

    #end of findSourceForClass
    
    
    def clearHighlights(self) :
        self.classSelected.emit(None)

    
    def addClass(self) :
        (name, ok) = QtWidgets.QInputDialog.getText(self, 'Add Class', 'Class Name:')
        if name and ok :
            self.classUpdated.emit(name, "")
            l = QtWidgets.QTableWidgetItem(name)
            l.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            v = QtWidgets.QTableWidgetItem("")
            v.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
            r = self.tab.rowCount()
            self.tab.setRowCount(r + 1)
            self.tab.setItem(r, 0, l)
            self.tab.setItem(r, 1, v)

    
    def delCurrent(self) :
        r = self.tab.currentRow()
        if r < 0 :
            return
        name = self.tab.item(r, 0).text()
        self.classUpdated.emit(name, None)
        self.tab.removeRow(r)
    
    
    # Scroll to the selected class and highlight it in the class pane.
    def findSelectedClass(self) :
        #print("findSelectedClass")
        className = self.app.tab_edit.selectedText
        d = QtWidgets.QDialog(self)
        rowMatched = -1
        for row in range(0, self.classCount) :
            edit = QtWidgets.QPlainTextEdit(self.tab.item(row, 0).text(), d)
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

    # end of findSelectedClass
    
# end of class Classes (tab widget)

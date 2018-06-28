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
from graide.utils import ModelSuper, DataObj
import traceback

#for line in traceback.format_stack(): print(line.strip())

#   Here is a summaryhow the Python Slots and Signals interact to update the Glyph tab when a glyph is clicked:
#
#   Set up connections:
#       runView.glyphSelect.connect(passesView.changeGlyph)
#       mainWindow.tab_passes.glyphSelected.connect(mainWindow.glyphSelected)
#       mainWindow.tab_passes.glyphSelected.connect(mainwindow.glyphAttrib.changeData)
#
#   Then when a glyph is clicked on:
#       RunView::changeSelection
#           calls self.glyphSelected.emit (defined as Signal)
#       PassesView::changeGlyph
#           calls self.glyphSelected.emit (defined as Signal)
#       MainWindow::glyphSelected
#       ...
#       AttribView::changeData

class LinePlainTextEdit(QtWidgets.QPlainTextEdit) :

    editFinished = QtCore.Signal()

    def keyPressEvent(self, key) :
        if key.matches(QtGui.QKeySequence.InsertParagraphSeparator) :
                    # or key.matches(QtGui.QKeySequence.InsertLineSeparator) :
           self.editFinished.emit()
        else :
            return super(LinePlainTextEdit, self).keyPressEvent(key)
            

class AttrValueListDialog(QtWidgets.QDialog) :
    
    def __init__(self, parent, glyphName, gClassList) :
        super(AttrValueListDialog,self).__init__(parent)
        
        # Hide the help icon, all it does it take up space.
        #icon = self.windowIcon(); -- just in case icon gets lost
        flags = self.windowFlags();
        helpFlag = QtCore.Qt.WindowContextHelpButtonHint;
        flags = flags & (~helpFlag);
        self.setWindowFlags(flags);
        #self.setWindowIcon(icon);

        self.setWindowTitle(glyphName)
        listWidget = QtWidgets.QListWidget(self)
        #listWidget.clicked.connect(self.doReturn)
        itemHeight = 18
        cnt = 0
        for gClass in gClassList:
            if gClass == "" or gClass == " " :
                continue
                
            item = QtWidgets.QListWidgetItem(gClass)
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
    
# end of class AttrValueListDialog


class AttributeDelegate(QtWidgets.QStyledItemDelegate) :

    def __init__(self, parent) :
        super(AttributeDelegate, self).__init__(parent)
        self.parent = parent

    def createEditor(self, parent, option, index) :
        dat = index.data()
        if index.column() == 0 :
            pass
        elif index.column() == 1 and dat and len(dat) > 20 :
            editor = LinePlainTextEdit(parent)
            editor.editFinished.connect(self.commitAndCloseEditor)
            editor.setMinimumHeight(100)
            return editor
        else :
            return super(AttributeDelegate, self).createEditor(parent, option, index)

    def setEditorData(self, editor, index) :
        if index.column() == 1 and len(index.data()) > 20 :
            editor.setPlainText(index.data())
        else :
            super(AttributeDelegate, self).setEditorData(editor, index)

    def setModelData(self, editor, model, index) :
        if index.column() == 1 and index.data and len(index.data()) > 20 :
            model.setData(index, editor.toPlainText(), QtCore.Qt.EditRole)
        else :
            super(AttributeDelegate, self).setModelData(editor, model, index)

    def commitAndCloseEditor(self) :
        editor = self.sender()
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)
        
#end of class AttributeDelegate


class Attribute(object) :

    def __init__(self, name, getter, setter, isTree = False, fileLoc = None, listPopup = False, *params) :
        self.name = name
        self.setter = setter
        self.getter = getter
        self.params = params
        self.isTree = isTree # debugging
        self.tree = params[0] if isTree else None  # an AttribModel, if this has an embedded tree
        self.fileLoc = fileLoc
        self.doesListPopup = listPopup
            
    def child(self, row) :
        if self.tree :
            return self.tree.child(row)
        return None

    def childNumber(self, row) :
        if self.tree :
            return self.tree.rowCount(None)
        return 0

    def getData(self, column) :
        if column == 0 :
            return self.name
        elif column == 1 and self.getter :
            return self.getter(*self.params)
        return None

    def setData(self, column, value) :
        if column == 0 and value:
            self.name = value
            return True
        elif column == 1 and self.setter:
            params = list(self.params[:]) + [value]
            self.setter(*params)
            return True
        return False

    def isEditable(self, column) :
        if self.setter : return True
        return False
        
    def getFileLoc(self, treePath) :
        if self.fileLoc :
            return self.fileLoc
        elif self.tree :
            return self.tree.fileLocAt(treePath)   # tree is an AttribModel
        else :
            return None
            
    def listForPopup(self) :
        if self.doesListPopup :
            classListStr = self.getData(1)
            # turn into list
            res = classListStr.split('  ')  # two spaces
            res.sort()
            return res
        else :
            return None
            
    def showPopupList(self, listToShow, widget) :
        dialog = AttrValueListDialog(widget, self.name, listToShow)
        dialog.show()   # modeless

        
    def debugPrintData(self) :
        print(self.name)
        if self.isTree : 
            print(">>>")
            self.tree.debugPrintData()
            print("<<<")

# end of class Attribute


# An AttribModel consists of a list of Attributes, corresponding to a row in the AttribView control.
# An Attribute can be a sub-tree which in turn contains an AttribModel with the list of sub-items.

class AttribModel(QtCore.QAbstractItemModel) :

    def __init__(self, data, parent = None, root = None) : # data is a list of Attributes
        super(AttribModel, self).__init__(parent)
        self.__data = data
        self.__root = root if root else self
        self.__parent = parent
            
    def add(self, data) :
        self.__data.append(data)

    def rowCount(self, parent) :
        if not parent or not parent.isValid() :
            return len(self.__data)
        else :
            pitem = self.getItem(parent)
            return pitem.__data[parent.row()].childNumber(parent.row())

    def columnCount(self, parent) :
        return 2

    def data(self, index, role) :
        if not index.isValid() or (role != QtCore.Qt.DisplayRole and role != QtCore.Qt.EditRole) :
            return None

        item = self.getItem(index)
        dat = item.__data[index.row()]
        return dat.getData(index.column())

    def flags(self, index) :
        res = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if index and index.isValid() :
            item = self.getItem(index)
            dat = item.__data[index.row()]
            if dat.isEditable(index.column()) :
                res |= QtCore.Qt.ItemIsEditable
        return res

    def child(self, num) :
        return self.__data[num]

    def getChildRow(self, model) :
        for i, d in enumerate(self.__data) :
            if len(d.params) and d.params[0] == model :
                return i
        return -1
        
    def parent(self, index) :
        if index and index.isValid() :
            child = self.getItem(index)
            parent = child.__parent
            if parent :
                row = parent.getChildRow(child)
                if row >= 0 :
                    return parent.createIndex(row, 0, parent)
        return QtCore.QModelIndex()

    def getItem(self, index) :
        if index and index.isValid() :
            item = index.internalPointer()
            if item : return item
        return self

    def index(self, row, column, parent = None) :
        if not parent or not parent.isValid() :
            return self.createIndex(row, column, self.__root)
        else :
            parentModel = self.getItem(parent)
            parentItem = parentModel.__data[parent.row()]
            if parentItem.tree :
                return self.createIndex(row, column, parentItem.tree)
        return QtCore.QModelIndex()

    def setData(self, index, value, role) :
        if role != QtCore.Qt.EditRole:
            return False
        item = self.getItem(index)
        attrib = item.__data[index.row()]
        res = attrib.setData(index.column(), value)
        if res :
            self.__root.dataChanged.emit(index, index)
        return res
        
    def fileLocAt(self, treePath) :
        i = treePath[0]
        attrData = self.__data[i]
        return attrData.getFileLoc(treePath[1:])
            
    def listForPopup(self, treePath) :
        i = treePath[0]
        attrData = self.__data[i]
        return attrData.listForPopup()
        
    def showPopupList(self, treePath, listToShow, widget) :
        i = treePath[0]
        attrData = self.__data[i]
        return attrData.showPopupList(listToShow, widget)       

    def debugPrintData(self) :
        print(self.__data)
        for d in self.__data :
            d.debugPrintData()

# end of class AttribModel
            

class AttribView(QtWidgets.QTreeView) :

    def __init__(self, app, parent = None) :
        super(AttribView, self).__init__(parent)
        self.app = app
        self.header().setStretchLastSection(True)
        self.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.header().hide()
        self.attribDelegate = AttributeDelegate(self)
        #self.setItemDelegateForColumn(1, self.attribDelegate)

    @QtCore.Slot(DataObj, ModelSuper)
    def changeData(self, data, modelBogus) :  # data is a Slot, GraideGlyph, etc.; modelBogus is eg RunView
        self.data = data
        self.model = data.attribModel() if data else None
        self.setModel(self.model)
        self.expandAll()
        
    def dataObject(self) :
        try :
            return self.data
        except :
            return None

    def removeCurrent(self) :
        index = self.currentIndex()
        self.model.setData(index, None, QtCore.Qt.EditRole)
        
    def mouseDoubleClickEvent(self, event) :
        #print("mouseDoubleClickEvent")
        super(AttribView, self).mouseDoubleClickEvent(event)
        
        # Generate a path to where the click was in the tree control.
        row = self.currentIndex().row()
        parentIndex = self.currentIndex().parent()
        treePath = [row]
        while parentIndex.row() > -1 :
            treePath.insert(0, parentIndex.row()) # prepend
            parentIndex = parentIndex.parent()
            
        pList = self.model.listForPopup(treePath)
        if pList :
            self.model.showPopupList(treePath, pList, self)
        else :
            fileLoc = self.model.fileLocAt(treePath)
            if fileLoc : 
                self.app.selectLine(*fileLoc)

    def findMainFileLoc(self) :
        treePath = [0]   # for Glyph tab, assumes glyph number is the first
        fileLoc = self.model.fileLocAt(treePath)
        if fileLoc :
            self.app.selectLine(*fileLoc)
            
# end of class AttribView


if __name__ == '__main__' :

    from graide.font import GraideFont
    import sys, os
 
    app = QtWidgets.QApplication(sys.argv)
    font = GraideFont()
    tpath = os.path.join(os.path.dirname(sys.argv[0]), '../../tests/fonts/Padauk')
    font.loadFont(os.path.join(tpath, 'Padauk.ttf'), os.path.join(tpath, 'padauk.xml'))
    glyph = font.psnames['u1000']
    model = glyph.attribModel()
    view = AttribView(model)
    view.show()
    sys.exit(app.exec_())


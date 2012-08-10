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
from graide.utils import ModelSuper, DataObj

class LinePlainTextEdit(QtGui.QPlainTextEdit) :

    editFinished = QtCore.Signal()

    def keyPressEvent(self, key) :
        if key.matches(QtGui.QKeySequence.InsertParagraphSeparator) :
                    # or key.matches(QtGui.QKeySequence.InsertLineSeparator) :
           self.editFinished.emit()
        else :
            return super(LinePlainTextEdit, self).keyPressEvent(key)

class AttributeDelegate(QtGui.QStyledItemDelegate) :

    def __init__(self, parent) :
        super(AttributeDelegate, self).__init__(parent)
        self.parent = parent

    def createEditor(self, parent, option, index) :
        dat = index.data()
        if index.column() == 1 and dat and len(dat) > 20 :
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

class Attribute(object) :

    def __init__(self, name, getter, setter, istree = False, *parms) :
        self.name = name
        self.setter = setter
        self.getter = getter
        self.params = parms
        self.tree = parms[0] if istree else None

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
            parms = list(self.params[:]) + [value]
            self.setter(*parms)
            return True
        return False

    def isEditable(self, column) :
        if self.setter : return True
        return False

class AttribModel(QtCore.QAbstractItemModel) :

    def __init__(self, data, parent = None, root = None) :
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

class AttribView(QtGui.QTreeView) :

    def __init__(self, parent = None) :
        super(AttribView, self).__init__(parent)
        self.header().setStretchLastSection(True)
        self.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.header().hide()
        self.attribDelegate = AttributeDelegate(self)
        self.setItemDelegateForColumn(1, self.attribDelegate)

    @QtCore.Slot(DataObj, ModelSuper)
    def changeData(self, data, model) :
        self.data = data
        self.model = data.attribModel() if data else None
        self.setModel(self.model)
        self.expandAll()

    def removeCurrent(self) :
        index = self.currentIndex()
        self.model.setData(index, None, QtCore.Qt.EditRole)

if __name__ == '__main__' :

    from graide.font import Font
    import sys, os
 
    app = QtGui.QApplication(sys.argv)
    font = Font()
    tpath = os.path.join(os.path.dirname(sys.argv[0]), '../../tests/fonts/Padauk')
    font.loadFont(os.path.join(tpath, 'Padauk.ttf'), os.path.join(tpath, 'padauk.xml'))
    glyph = font.psnames['u1000']
    model = glyph.attribModel()
    view = AttribView(model)
    view.show()
    sys.exit(app.exec_())


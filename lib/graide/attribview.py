#!/usr/bin/python

from PySide import QtCore, QtGui
from graide.dataobj import DataObj
from graide.utils import ModelSuper

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
            parms = [self.params[:]] + [value]
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
        if not index.isValid() or role != QtCore.Qt.DisplayRole:
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
            if d.params[0] == model :
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
        self.header().hide()

    @QtCore.Slot(DataObj, ModelSuper)
    def changeData(self, data, model) :
        self.model = data.attribModel() if data else None
        self.setModel(self.model)

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


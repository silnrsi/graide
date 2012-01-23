
from PySide import QtGui, QtCore
from graide.run import Run
from graide.runview import RunView
from graide.utils import ModelSuper
from graide.dataobj import DataObj

class PassesItem(QtGui.QTableWidgetItem) :

    def __init__(self, data) :
        super(PassesItem, self).__init__()
        self.data = data

class PassesView(QtGui.QTableWidget) :

    slotSelected = QtCore.Signal(DataObj, ModelSuper)
    glyphSelected = QtCore.Signal(DataObj, ModelSuper)

    @QtCore.Slot(DataObj, ModelSuper)
    def changeSlot(self, data, model) :
        self.slotSelected.emit(data, model)

    @QtCore.Slot(DataObj, ModelSuper)
    def changeGlyph(self, data, model) :
        self.glyphSelected.emit(data, model)
        if self.currsel and self.currsel != model :
            self.currsel.clear_selected()
        self.currsel = model

    def __init__(self, parent = None) :
        super(PassesView, self).__init__(parent)
        self.setColumnCount(2)
        self.horizontalHeader().hide()
        self.currsel = None

    def loadResults(self, font, json) :
        self.setRowCount(len(json))
        self.runs = []
        w = 0
        for j in range(len(json)) :
            run = Run()
            run.addslots(json[j]['slots'])
            v = RunView(run, font, self)
            self.runs.append(v)
            v.model.slotSelected.connect(self.changeSlot)
            v.model.glyphSelected.connect(self.changeGlyph)
            w = max(w, v.width())
            l = QtGui.QTableWidgetItem(str(font.describePass(json[j]['id'])))
            self.setItem(j, 0, l)
            self.setCellWidget(j, 1, v)
            self.verticalHeader().setDefaultSectionSize(v.size().height())
        w += 10
        self.setColumnWidth(1, w)
        self.columnResized(1, 0, w)

    def columnResized(self, col, old, new) :
        if col == 1 :
            for j in range(self.rowCount()) :
                w = self.cellWidget(j, 1)
                w.setFixedWidth(new)
                w.update()


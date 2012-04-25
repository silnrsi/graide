
from PySide import QtGui, QtCore
from graide.run import Run
from graide.runview import RunView, RunModel
from graide.utils import ModelSuper
from graide.dataobj import DataObj

class PassesItem(QtGui.QTableWidgetItem) :

    def __init__(self, data) :
        super(PassesItem, self).__init__()
        self.data = data

class PassesView(QtGui.QTableWidget) :

    slotSelected = QtCore.Signal(DataObj, ModelSuper)
    glyphSelected = QtCore.Signal(DataObj, ModelSuper)
    rowActivated = QtCore.Signal(int, RunModel)

    @QtCore.Slot(DataObj, ModelSuper)
    def changeSlot(self, data, model) :
        self.slotSelected.emit(data, model)

    @QtCore.Slot(DataObj, ModelSuper)
    def changeGlyph(self, data, model) :
        self.glyphSelected.emit(data, model)
        if self.currsel and self.currsel != model :
            self.currsel.clear_selected()
        self.currsel = model

    @QtCore.Slot(int)
    def activateRow(self, row) :
        self.rowActivated(row, self.views[row].model)

    def __init__(self, parent = None, index = 0) :
        super(PassesView, self).__init__(parent)
        self.setColumnCount(2)
        self.horizontalHeader().hide()
        self.currsel = None
        self.index = index

    def addrun(self, font, run, label, num) :
        v = RunView(run, font, self)
        self.views.append(v)
        v.model.slotSelected.connect(self.changeSlot)
        v.model.glyphSelected.connect(self.changeGlyph)
        l = QtGui.QTableWidgetItem(label)
        l.setFlags(QtCore.Qt.ItemIsEnabled)
        self.setItem(num, 0, l)
        self.setCellWidget(num, 1, v)
        self.verticalHeader().setDefaultSectionSize(v.size().height())
        return v.width()

    def loadResults(self, font, json, gdx = None) :
        self.setRowCount(len(json))
        self.views = []
        w = 0
        for j in range(len(json)) :
            run = Run()
            run.addslots(json[j]['slots'])
            pname = "Pass: %d" % (j)
            if gdx :
                pname += " - " + gdx.passtypes[j]
            neww = self.addrun(font, run, pname, j)
            w = max(w, neww)
        w += 10
        self.setColumnWidth(1, w)
        self.columnResized(1, 0, w)
        self.cellDoubleClicked.connect(self.doCellDoubleClicked)

    def loadRules(self, font, json, inirun) :
        self.views = []
        self.runs = [inirun.copy()]
        self.runs[-1].label="Init"
        for r in json :
            for c in r['considered'] :
                run = self.runs[-1].copy()
                if c['failed'] :
                    ind = self.runs[-1].idindex(c['input']['start'])
                    lext = " (failed)"
                    for s in self.runs[-1][ind:ind + c['input']['length']] :
                        s.highlight()
                else :
                    (beg, end) = run.replace(r['output']['slots'], r['output']['range']['start'], r['output']['range']['end'])
                    lext = ""
                    for s in self.runs[-1][beg:end] :
                        s.highlight()
                self.runs.append(run)
                run.label="Rule: %d%s" % (c['id'], lext)
                run.passindex = self.index
                run.ruleindex = int(c['id'])

        w = 0
        self.setRowCount(len(self.runs))
        for j in range(len(self.runs)) :
            neww = self.addrun(font, self.runs[j], self.runs[j].label, j)
            w = max(w, neww)
        w += 10
        self.setColumnWidth(1, w)
        self.columnResized(1, 0, w)
        self.cellDoubleClicked.connect(self.doCellDoubleClicked)

    def columnResized(self, col, old, new) :
        if col == 1 :
            for j in range(self.rowCount()) :
                w = self.cellWidget(j, 1)
                w.setFixedWidth(new)
                w.update()

    def doCellDoubleClicked(self, row, col) :
        if col == 0 :
            model = self.views[row].model
            self.rowActivated.emit(row, model)
 


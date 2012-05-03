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
        self.connected = False
        self.views = []

    def addrun(self, font, run, label, num, tooltip = "") :
        if num >= len(self.views) :
            v = RunView(run, font, self)
            self.views.append(v)
            v.model.slotSelected.connect(self.changeSlot)
            v.model.glyphSelected.connect(self.changeGlyph)
            self.setCellWidget(num, 1, v)
            l = QtGui.QTableWidgetItem(label)
            l.setFlags(QtCore.Qt.ItemIsEnabled)
            self.setItem(num, 0, l)
        else :
            v = self.views[num]
            v.set_run(run, font)
            l = self.item(num, 0)
        if tooltip : l.setToolTip(tooltip)
        self.verticalHeader().setDefaultSectionSize(v.size().height())
        return v.width()

    def loadResults(self, font, json, gdx = None) :
        num = len(json)
        if num != self.rowCount() :
            self.setRowCount(len(json))
        w = 0
        for j in range(num) :
            run = Run()
            run.addslots(json[j]['slots'])
            pname = "Pass: %d" % (j + 1)
            if gdx :
                pname += " - " + gdx.passtypes[j]
            neww = self.addrun(font, run, pname, j)
            w = max(w, neww)
        w += 10
        self.setColumnWidth(1, w)
        self.columnResized(1, 0, w)
        if not self.connected :
            self.cellDoubleClicked.connect(self.doCellDoubleClicked)
            self.connected = True

    def loadRules(self, font, json, inirun, gdx) :
        self.views = []
        self.runs = [inirun.copy()]
        self.runs[-1].label="Init"
        self.runs[-1].ruleindex = -1
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
            neww = self.addrun(font, self.runs[j], self.runs[j].label, j,
                    tooltip = gdx.passes[self.index][self.runs[j].ruleindex].pretty
                                    if gdx and self.runs[j].ruleindex >= 0 else "")
            w = max(w, neww)
        w += 10
        self.setColumnWidth(1, w)
        self.columnResized(1, 0, w)
        if not self.connected :
            self.cellDoubleClicked.connect(self.doCellDoubleClicked)
            self.connected = True

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
 


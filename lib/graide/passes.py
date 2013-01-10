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
from graide.runview import RunView
from graide.utils import ModelSuper, DataObj
from graide.layout import Layout

class PassesItem(QtGui.QTableWidgetItem) :

    def __init__(self, data) :
        super(PassesItem, self).__init__()
        self.data = data
        
# The PassesView class is also used for the Rules tab.

class PassesView(QtGui.QTableWidget) : pass

class PassesView(QtGui.QTableWidget) :

    slotSelected = QtCore.Signal(DataObj, ModelSuper)
    glyphSelected = QtCore.Signal(DataObj, ModelSuper)
    rowActivated = QtCore.Signal(int, RunView, PassesView)


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
        self.rowActivated(row, self.views[row])

    def __init__(self, parent = None, index = 0) :
        super(PassesView, self).__init__(parent)
        self.setColumnCount(3)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.currsel = None
        self.index = index
        self.connected = False
        self.views = []
        self.selectedRow = -1
        self.rules = []

    def addrun(self, font, run, label, num, tooltip = "", highlight = False) :
        if num >= len(self.views) :
            v = RunView(run, font, self)
            self.views.append(v)
            self.setCellWidget(num, 1, v.gview)
            self.setCellWidget(num, 2, v.tview)
            l = QtGui.QTableWidgetItem(label)
            l.setFlags(QtCore.Qt.ItemIsEnabled)
            self.setItem(num, 0, l)
            try :
                v.slotSelected.connect(self.changeSlot)
                v.glyphSelected.connect(self.changeGlyph)
            except :
                print "Passes connection failed"
        else :
            v = self.views[num]
            v.loadrun(run, font)
            l = self.item(num, 0)
        if tooltip : l.setToolTip(tooltip)
        l.setBackground(Layout.activePassColour if highlight else QtGui.QColor(255, 255, 255))
        l.highlight = highlight
        self.verticalHeader().setDefaultSectionSize(v.gview.size().height())
        return (v.gview.width(), v.tview.width())

    def finishLoad(self, w, wt) :
        w += 10
        wt += 10
        self.setColumnWidth(1, w)
        self.columnResized(1, 0, w)
        self.setColumnWidth(2, wt)
        self.columnResized(2, 0, wt)
        if not self.connected :
            self.cellDoubleClicked.connect(self.doCellDoubleClicked)
            self.connected = True

    def loadResults(self, font, jsonall, gdx = None) :
        self.rules = []
        self.selectRow(-1)
        self.currsel = None
        json = jsonall[0]
        num = len(json['passes']) + 1  # 0 = Init
        count = num
        
        # JSON format:
        #   'passes': [
        #      0:
        #        'id' : 1
        #        'slots' : <initial data>
        #        'rules' : <rules run by pass 1>
        #      1:
        #        'id' : 2
        #        'slots' : <output of pass 1>
        #        'rules' : <rules run by pass 2>
        #      ...
        #      N-1:
        #        'id' : N
        #        'slots' : <output of pass N-1>
        #        'rules' : <rules run by pass N>
        #   ]
        #   'output': <output of pass N>
        
        # Also note that pass IDs in JSON do not match pass indices in GDX when there is
        # a bidi pass. In JSON, the pass ID of a bidi pass in json is -1, with the
        # first positioning pass index = last subs pass + 1. (More accurately, -1 indicates
        # the INPUT to the bidi pass.) In GDX, pass indices include the bidi pass, so first
        # positioning pass index = last subs pass + 2.
        #
        # Best thing to do is to more or less ignore the JSON IDs, since they are not reliable.
            
        if len(jsonall) > 1 :
            if 'passes' in jsonall[1] :
                count += len(jsonall[1]['passes']) + 1
            else :
                count += 1
        if count != self.rowCount() :
            if count < self.rowCount() : self.views = self.views[:count]
            self.setRowCount(count)
        w = 0
        wt = 0
        for j in range(num) :
            # Process the output of pass J which = input to pass J+1, rules run by pass J+1.
            # Note that rules[J] are the rules run by pass J+1!
            run = Run()
            highlight = False
            if j < num - 1 :
                run.addslots(json['passes'][j]['slots'])  # output of pass J
                passid = int(json['passes'][j]['id']) - 1
            else :
                run.addslots(json['output'])   # final output
                passid = j
                
            if j == 0 :
                pname = "Init"
                self.rules.append(None)
                
            else :
                pname = "Pass: %d" % j
                if gdx :
                    pname += " - " + gdx.passtypes[j-1]  # j-1 because Init is not in the passtypes array
                if len(json['passes'][j-1]['rules']) :
                    highlight = True
                    self.rules.append(json['passes'][j-1]['rules'])  # rules are stored with previous pass :-(
                else :
                    self.rules.append(None)
                    
                # if passid == -1, NEXT pass is bidi pass
                    
            (neww, newt) = self.addrun(font, run, pname, j, highlight = highlight)
            w = max(w, neww)
            wt = max(wt, newt)
            
        # import pdb; pdb.set_trace()
        if len(jsonall) > 1 :
            json = jsonall[1]
            base = num
            num = 0
            if 'passes' in json :
                num = len(json['passes']) - 1
            else :
                json['passes'] = []
            num += 1
            for j in range(num) :
                run = Run()
                highlight = False
                if j < len(json['passes']) :
                    passid = int(json['passes'][j]['id']) - 1
                    if len(json['passes'][j]['rules']) :
                        highlight = True
                        self.rules.append(json['passes'][j]['rules'])
                    else :
                        self.rules.append(None)
                    pname = "Pass: %d" % passid
                    if gdx :
                        pname += " - " + gdx.passtypes[passid - 1]
                else :
                    pname = "Justification"
                    self.rules.append(None)
                if j < len(json['passes']) - 1 :
                    run.addslots(json['passes'][j+1]['slots'])
                else :
                    run.addslots(json['output'])
                (neww, newt) = self.addrun(font, run, pname, base + j, highlight = highlight)
                w = max(w, neww)
                wt = max(wt, newt)
        self.finishLoad(w, wt)

    def loadRules(self, font, json, inirun, gdx) :
        self.selectRow(-1)
        self.currsel = None
        self.views = []
        # runs correspond to rules matched (fired or failed)
        self.runs = [inirun.copy()]	 # initialize with the Init run
        self.runs[0].label="Init"
        self.runs[0].ruleindex = -1
        begprev = -1
        endprev = -1
        beg = -1
        end = -1
        for runinfo in json :		# graphite output for this run
            for cRule in runinfo['considered'] :	# rules that matched for this pass
                nextRun = self.runs[-1].copy()
                
                if begprev != -1 :	# in the previous run, highlight the modified output glyphs, if any
                    for slot in self.runs[-1][begprev:endprev] :
                	    slot.highlight('output')
                	    
                if cRule['failed'] :
                    ind = self.runs[-1].idindex(cRule['input']['start'])
                    lext = " (failed)"
                    for slot in self.runs[-1][ind:ind + cRule['input']['length']] :
                        slot.highlight('default')
                    begprev = -1
                else :
                    (beg, end) = nextRun.replace(runinfo['output']['slots'],
                    		runinfo['output']['range']['start'], runinfo['output']['range']['end'])
                    lext = ""
                    for slot in self.runs[-1][beg:end] :	# in the previous run, highlight the matched input glyphs
                        slot.highlight('input')
                    if 'postshift' in runinfo['output'] :
                        for slot in self.runs[-1][end:] :
                            slot.origin = (slot.origin[0] + runinfo['output']['postshift'][0], slot.origin[1] 
                                                          + runinfo['output']['postshift'][1])
                    begprev = beg  # remember where to highlight the output glyphs in the next iteration
                    endprev = end
                    
                self.runs.append(nextRun)
                nextRun.label="Rule: %d%s" % (cRule['id'], lext)
                nextRun.passindex = self.index
                nextRun.ruleindex = int(cRule['id'])
                # why can't we highlight the output glyphs here?
        
        # highlight the output of the last run
        if begprev != -1 :
            for slot in self.runs[-1][begprev:endprev] :
                slot.highlight('output')

        w = 0
        wt = 0
        self.setRowCount(len(self.runs))
        for j in range(len(self.runs)) :
            (neww, newt) = self.addrun(font, self.runs[j], self.runs[j].label, j,
                    tooltip = gdx.passes[self.index][self.runs[j].ruleindex].pretty
                                    if gdx and self.runs[j].ruleindex >= 0 else "")
            w = max(w, neww)
            wt = max(wt, newt)
            
        self.finishLoad(w, wt)

    def setTopToolTip(self, txt) :
        self.item(0, 0).setToolTip(txt)

    def columnResized(self, col, old, new) :
        if col >= 1 :
            for j in range(self.rowCount()) :
                w = self.cellWidget(j, col)
                w.setFixedWidth(new)
                w.update()

    def doCellDoubleClicked(self, row, col) :
        if col == 0 :
            self.rowActivated.emit(row, self.views[row], self)
 
    def selectRow(self, row) :
        if self.selectedRow >= 0 :
            it = self.item(self.selectedRow, 0)
            if it.highlight :
                it.setBackground(Layout.activePassColour)
            else : 
                it.setBackground(QtGui.QColor(255, 255, 255))
            w = self.cellWidget(self.selectedRow, 1)
            w.setBackgroundBrush(QtGui.QColor(255, 255, 255))
        self.selectedRow = row
        if self.selectedRow >= 0 :
            it = self.item(self.selectedRow, 0)
            if it : it.setBackground(self.palette().highlight())
            w = self.cellWidget(self.selectedRow, 1)
            w.setBackgroundBrush(self.palette().highlight())

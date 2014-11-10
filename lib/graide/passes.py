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
import traceback

class PassesItem(QtGui.QTableWidgetItem) :

    def __init__(self, data) :
        super(PassesItem, self).__init__()
        self.data = data
        
# The PassesView class is also used for the Rules tab.

class PassesView(QtGui.QTableWidget) : pass

class PassesView(QtGui.QTableWidget) :

    # Communication with the Glyph, Slot and Rules tabs:
    slotSelected = QtCore.Signal(DataObj, ModelSuper, bool)
    glyphSelected = QtCore.Signal(DataObj, ModelSuper, bool)
    rowActivated = QtCore.Signal(int, RunView, PassesView)


    @QtCore.Slot(DataObj, ModelSuper, bool)
    def changeSlot(self, data, model, doubleClick) : # data = Slot, model = RunView
        self.slotSelected.emit(data, model, doubleClick)

    @QtCore.Slot(DataObj, ModelSuper, bool)
    def changeGlyph(self, data, model, doubleClick) : # data = glyph ID, model = RunView
        self.glyphSelected.emit(data, model, doubleClick)
        if self.currsel and self.currsel != model :
            self.currsel.clearSelected()
        self.currsel = model

    @QtCore.Slot(int)
    def activateRow(self, row) :
        self.rowActivated(row, self.runViews[row])

    def __init__(self, parent = None, index = 0) :
        super(PassesView, self).__init__(parent)
        self.setColumnCount(3)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.currsel = None
        self.passindex = index  # used for Rules tab
        self.connected = False
        self.runViews = []
        self.selectedRow = -1
        self.rules = []
        
    def setPassIndex(self, index) :
        self.passindex = index

    def addRun(self, font, run, label, num, tooltip = "", highlight = False) :
        if num >= len(self.runViews) :
            v = RunView(font, run, self)
            self.runViews.append(v)
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
            v = self.runViews[num]
            v.loadRun(run, font)
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

    def loadResults(self, font, jsonall, gdx = None, rtl = False) :
        self.rules = []
        self.selectRow(-1)
        self.currsel = None
        if jsonall :
            json = jsonall[-1]
            ###json = jsonall[0]
        else :
            json = {'passes' : [], 'output' : [] }  # empty output
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
            
        if count != self.rowCount() :
            if count < self.rowCount() : self.runViews = self.runViews[:count]
            self.setRowCount(count)
        w = 0
        wt = 0
        for j in range(num) :
            # Process the output of pass J which = input to pass J+1, rules run by pass J+1.
            # Note that rules[J] are the rules run by pass J+1!
            run = Run(rtl)
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
                if json['passes'][j-1].has_key('rules') and len(json['passes'][j-1]['rules']) :
                    highlight = True
                    self.rules.append(json['passes'][j-1]['rules'])  # rules are stored with previous pass :-(
                else :
                    self.rules.append(None)
                    
                # if passid == -1, NEXT pass is bidi pass
                    
            (neww, newt) = self.addRun(font, run, pname, j, highlight = highlight)
            w = max(w, neww)
            wt = max(wt, newt)
            
        self.finishLoad(w, wt)
        
    # end of loadResults
    

    def loadRules(self, font, json, inirun, gdx) :
        self.selectRow(-1)
        self.currsel = None
        self.runViews = []
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
                    islot = beg
                    for slot in self.runs[-1][beg:end] :	# in the previous run, highlight the matched input glyphs
                        if begprev <= islot and islot < endprev :
                            slot.highlight('inAndOut')     # both input and output
                        else :
                            slot.highlight('input')
                        islot = islot + 1
                    if 'postshift' in runinfo['output'] :
                        for slot in self.runs[-1][end:] :
                            slot.origin = (slot.origin[0] + runinfo['output']['postshift'][0], slot.origin[1] 
                                                          + runinfo['output']['postshift'][1])
                    begprev = beg  # remember where to highlight the output glyphs in the next iteration
                    endprev = begprev + len(runinfo['output']['slots'])
                    
                self.runs.append(nextRun)
                nextRun.label="Rule: %d%s" % (cRule['id'], lext)
                nextRun.passindex = self.passindex
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
            (neww, newt) = self.addRun(font, self.runs[j], self.runs[j].label, j,
                    tooltip = gdx.passes[self.passindex][self.runs[j].ruleindex].pretty
                                    if gdx and self.runs[j].ruleindex >= 0 else "")
            w = max(w, neww)
            wt = max(wt, newt)
            
        self.finishLoad(w, wt)
        
    # end of loadRules
    

    def setTopToolTip(self, txt) :
        self.item(0, 0).setToolTip(txt)

    def columnResized(self, col, old, new) :
        if col >= 1 :
            for j in range(self.rowCount()) :
                w = self.cellWidget(j, col)
                if w :
                    w.setFixedWidth(new)
                    w.update()

    def doCellDoubleClicked(self, row, col) :
        if col == 0 :
            self.rowActivated.emit(row, self.runViews[row], self)
 
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


    def updateScroll(self, scrollWhere) :
        if scrollWhere == '' :
            pass
        elif scrollWhere == 'to-end' :
            self.scrollToItem(self.item(0,0))  # scroll to the top to help get it unconfused
            self.updateScroll(self.rowCount() - 1)
        else :
            # scrollWhere is an integer
            #print "scrolling to row",scrollWhere
            item = self.item(scrollWhere, 0)
            self.scrollToItem(item)
            
    def rule(self, num) :
        return self.rules[num]
        
    def runView(self, num) :
        return self.runViews[num]

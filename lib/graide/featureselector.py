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
import graide.graphite as gr
from graide.rungraphite import strtolong

class FeatureRefs(object) :

    def __init__(self, grface = None, lang = None) :
        self.feats = {}
        self.featids = {}
        self.fval = {}
        self.order = []
        self.forders = {}
        if grface and grface.face :
            langid = 0x0409 # English
            length = 0
            grval = grface.get_featureval(strtolong(lang))
            for f in grface.featureRefs :
                name = f.name(langid)
                if not name : continue
                name = name[:]
                self.order.append(name)
                n = f.num()
                finfo = {}
                forder = []
                for i in range(n) :
                    v = f.val(i)
                    k = f.label(i, langid)[:]
                    finfo[k] = v
                    forder.append(k)
                self.feats[name] = finfo
                self.featids[name] = f.tag()
                self.fval[f.tag()] = grval.get(f)
                self.forders[name] = forder

    def copy(self) :
        res = FeatureRefs()
        res.feats = dict(self.feats)
        res.featids = dict(self.featids)
        res.fval = dict(self.fval)
        res.order = list(self.order)
        for k, v in self.forders.items() :
            res.forders[k] = list(v)
        return res

    def apply(self, fvals) :
        for (k, v) in fvals.items() :
            self.fval[k] = v

def make_FeaturesMap(font) :
    grface = gr.Face(font)
    result = {}
    result[None] = FeatureRefs(grface)
    if not grface.face : return result
    for l in grface.featureLangs :
        lang = gr.tag_to_str(l)
        result[lang] = FeatureRefs(grface, lang)
    return result


class FeatureDialog(QtGui.QDialog) :

    def __init__(self, parent = None) : # parent = main window
        super(FeatureDialog, self).__init__(parent)
        self.setWindowTitle("Set Features")
        vLayout = QtGui.QVBoxLayout(self)
        self.currsize = None
        self.position = None
        self.isHidden = False
        self.setSizeGripEnabled(True)
        self.setWindowFlags(QtCore.Qt.Tool)
        
        self.table = QtGui.QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        # table is resized later, after feature rows are added
        vLayout.addWidget(self.table)
        
        extraWidget = QtGui.QWidget(self)
        gridLayout = QtGui.QGridLayout(extraWidget)
        vLayout.addWidget(extraWidget)
        gridLayout.addWidget(QtGui.QLabel('Language', extraWidget), 0, 0)
        self.lang = QtGui.QLineEdit(extraWidget)
#        self.lang.setInputMask("<AAan")
        #self.lang.setMaximumWidth(100)
        gridLayout.addWidget(self.lang, 0, 1)
        
        self.runWidth = QtGui.QSpinBox(extraWidget)
        self.runWidth.setRange(0, 1000)
        self.runWidth.setValue(100)
        self.runWidth.setSuffix("%")
        self.runWidth.setMaximumWidth(100)
        gridLayout.addWidget(QtGui.QLabel('Justify', extraWidget), 1, 0)
        gridLayout.addWidget(self.runWidth, 1, 1)
        
        okCancel = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        okCancel.accepted.connect(self.accept)
        okCancel.rejected.connect(self.reject)
        vLayout.addWidget(okCancel)


    def set_feats(self, feats, vals = None, lang = None, width = 100) :
        if not vals : vals = feats.fval
        while self.table.rowCount() :
            self.table.removeRow(0)
        self.combos = []
        num = len(feats.order)
        self.table.setRowCount(num)
        count = 0
        for f in feats.order :
            c = QtGui.QComboBox()
            c.userTag = feats.featids[f]
            for k in feats.forders[f] :
                c.addItem(k, feats.feats[f][k])
                if c.userTag in vals and feats.feats[f][k] == vals[c.userTag] :
                    c.setCurrentIndex(c.count() - 1)
            self.combos.append(c)
            self.table.setCellWidget(count, 1, c)
            
            label = QtGui.QTableWidgetItem(f)
            self.table.setItem(count, 0, label)
            count += 1
        if lang : self.lang.setText(lang)
        self.runWidth.setValue(width)
        self.resize(400, 400)
        #self.table.resizeColumnsToContents()


    def get_feats(self, base = None) :
        print "get_feats"
        res = {}
        for c in self.combos :
            v = c.itemData(c.currentIndex())
            if base is None or base.fval[c.userTag] != v :
                print c.userTag, v
                res[c.userTag] = v
        return res


    def get_lang(self) :
        return self.lang.text()


    def get_width(self) :
        return self.runWidth.value()


    def resizeEvent(self, event) :
        self.currsize = self.size()
        if self.table :
            tableSize = self.currsize - QtCore.QSize(20, 120)   # leave room at the bottom for the other controls
            self.table.resize(tableSize)
            tableWidth = tableSize.width()
            tableHeight = tableSize.height()
            # I don't understand why we have to do this. Is it for the scroll bar?
            if tableHeight < 30 * len(self.combos) + 3 :
                tableWidth = tableWidth - 21   # leave room for the scroll bar
            else : 
                tableWidth = tableWidth - 4    # fudge a bit just to make sure
            #if tableWidth > 600 :
            #    self.table.setColumnWidth(0, tableWidth - 300)
            #    self.table.setColumnWidth(1, 300)
            #else :
            halfTableWidth = tableWidth / 2
            self.table.setColumnWidth(0, halfTableWidth)
            self.table.setColumnWidth(1, tableWidth - halfTableWidth) # avoid rounding errors


    def closeEvent(self, event) :
        if not self.isHidden :
            self.position = self.pos()
            self.currsize = self.size()
            self.hide()
            self.isHidden = True

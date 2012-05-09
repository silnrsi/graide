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

class FeatureRefs(object) :

    def __init__(self, font = None) :
        self.feats = {}
        self.featids = {}
        self.fval = {}
        if font :
            langid = 0x0409
            length = 0
            grface = gr.Face(font)
            grval = grface.get_featureval(0)
            for f in grface.featureRefs :
                name = f.name(langid)
                if not name : continue
                name = name[:]
                n = f.num()
                finfo = {}
                for i in range(n) :
                    v = f.val(i)
                    k = f.label(i, langid)[:]
                    finfo[k] = v
                self.feats[name] = finfo
                self.featids[name] = f.tag()
                self.fval[f.tag()] = grval.get(f)

    def copy(self) :
        res = FeatureRefs()
        res.feats = dict(self.feats)
        res.featids = dict(self.featids)
        res.fval = dict(self.fval)
        return res

    def apply(self, fvals) :
        for (k, v) in fvals.items() :
            self.fval[k] = v


class FeatureDialog(QtGui.QDialog) :

    def __init__(self, parent = None) :
        super(FeatureDialog, self).__init__(parent)
        self.vbox = QtGui.QVBoxLayout(self)
        self.currsize = None
        self.position = None
        self.isHidden = False
        self.setSizeGripEnabled(True)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.table = QtGui.QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        self.vbox.addWidget(self.table)
        o = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        o.accepted.connect(self.accept)
        o.rejected.connect(self.reject)
        self.vbox.addWidget(o)

    def set_feats(self, feats, vals = None) :
        if not vals : vals = feats.fval
        while self.table.rowCount() :
            self.table.removeRow(0)
        self.combos = []
        num = len(feats.feats.keys())
        self.table.setRowCount(num)
        count = 0
        for f in sorted(feats.feats.keys()) :
            c = QtGui.QComboBox()
            c.userTag = feats.featids[f]
            for k in sorted(feats.feats[f].keys()) :
                c.addItem(k, feats.feats[f][k])
                if feats.feats[f][k] == vals[c.userTag] :
                    c.setCurrentIndex(c.count() - 1)
            self.combos.append(c)
            self.table.setCellWidget(count, 1, c)
            l = QtGui.QTableWidgetItem(f)
            self.table.setItem(count, 0, l)
            count += 1
        self.resize(600, 400)

    def get_feats(self) :
        res = {}
        for c in self.combos :
            res[c.userTag] = c.itemData(c.currentIndex())
        return res

    def resizeEvent(self, event) :
        self.currsize = self.size()
        if self.table :
            self.table.resize(self.currsize)
            if self.currsize.width() > 600 :
                self.table.setColumnWidth(0, self.currsize.width() - 300)
                self.table.setColumnWidth(1, 300)
            else :
                for i in range(2) :
                    self.table.setColumnWidth(i, self.currsize.width() / 2)

    def closeEvent(self, event) :
        if not self.isHidden :
            self.position = self.pos()
            self.currsize = self.size()
            self.hide()
            self.isHidden = True

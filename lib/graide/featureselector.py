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
from graide.layout import Layout

class FeatureRefs(object) :

    def __init__(self, grface = None, lang = None) :
        self.feats = {}     # Feature labels => { setting labels => setting values }
        self.featids = {}   # Feature labels => IDs
        self.fval = {}      # Feature IDs => current value
        self.order = []     # List of feature labels, in display order
        self.forders = {}   # Feature labels => { list of feature values, in order }
        if grface and grface.face :
            langid = 0x0409 # English
            length = 0
            grval = grface.get_featureval(strtolong(lang))
            for f in grface.featureRefs :
                name = f.name(langid)
                if not name : continue
                name = name[:]
                n = f.num()
                if n == 0 : 
                    #print n, name, f.tag()
                    continue  # probably the lang feature; ignore
                finfo = {}
                forder = []
                for i in range(n) :
                    v = f.val(i)
                    k = f.label(i, langid)[:]
                    finfo[k] = v
                    forder.append(k)
                self.order.append(name)
                self.feats[name] = finfo
                self.featids[name] = f.tag()
                self.fval[f.tag()] = grval.get(f)
                self.forders[name] = forder
                #print n, name, f.tag(), finfo, forder


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
        self.table.setColumnCount(3)  # column 0 is empty for now
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
        self.runWidth.setMaximumWidth(70)
        gridLayout.addWidget(QtGui.QLabel('Justify', extraWidget), 1, 0)
        gridLayout.addWidget(self.runWidth, 1, 1)
        
        okCancel = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        okCancel.accepted.connect(self.accept)
        okCancel.rejected.connect(self.reject)
        vLayout.addWidget(okCancel)


    def set_feats(self, feats, featsBaseForLang, vals = None, lang = None, width = 100) :
        
        self.featsBaseForLang = featsBaseForLang
        
        if not vals : vals = feats.fval
        
        self.initMode = True
        
        while self.table.rowCount() :
            self.table.removeRow(0)
        self.combos = []
        self.labels = []
        num = len(feats.order)
        self.table.setRowCount(num)
        count = 0
        for f in feats.order :
            fid = feats.featids[f] if f in feats.featids else ""
            if fid != "" :
                c = QtGui.QComboBox()
                c.connect(QtCore.SIGNAL('currentIndexChanged(int)'), self.changeSetting)
                c.userTag = feats.featids[f]
                for k in feats.forders[f] :
                    c.addItem(k, feats.feats[f][k])
                    if c.userTag in vals and feats.feats[f][k] == vals[c.userTag] :
                        c.setCurrentIndex(c.count() - 1)
                self.combos.append(c)
                self.table.setCellWidget(count, 2, c)
                
                #modText = " * " if vals[fid] and vals[fid] != featsBaseForLang.fval[fid] else ""
                #self.table.setItem(count, 0, QtGui.QTableWidgetItem(modText))
                # Column 0 currently not used
                
                labelWidget = QtGui.QTableWidgetItem(f)
                if fid in vals and vals[fid] != featsBaseForLang.fval[fid] :
                    labelWidget.setBackground(Layout.activePassColour) # modified from expected
                self.table.setItem(count, 1, labelWidget)
                self.labels.append(labelWidget)
            
            count += 1
            
        if lang : self.lang.setText(lang)
        self.runWidth.setValue(width)
        self.resize(400, 400)
        #self.table.resizeColumnsToContents()
        
        self.initMode = False
        
    def changeSetting(self, which) :
        # A feature setting was changed. Update the colors of the labels that indicate whether the setting
        # varies from the default for the language.
        
        if self.initMode : # initializing the controls - don't bother updating yet
            return
        
        i = 0
        for f in self.featsBaseForLang.order :
            fid = self.featsBaseForLang.featids[f]
            c = self.combos[i]
            v = c.itemData(c.currentIndex())
            d = self.featsBaseForLang.fval[fid]
            
            labelWidget = self.labels[i]
            backColor = Layout.activePassColour if v != d else QtGui.QColor(255, 255, 255)
            labelWidget.setBackground(backColor) # modified from expected
            
            i = i + 1
        


    def get_feats(self, base = None) :
        result = {}
        for c in self.combos :
            v = c.itemData(c.currentIndex())
            if base is None or base.fval[c.userTag] != v :
                result[c.userTag] = v
        return result


    def get_lang(self) :
        return self.lang.text()


    def get_width(self) :
        return self.runWidth.value()


    def resizeEvent(self, event) :
        self.currsize = self.size()
        if self.table :
            column0Width = 0
            self.table.setColumnWidth(0, column0Width)
            
            tableSize = self.currsize - QtCore.QSize(20, 120)   # leave room at the bottom for the other controls
            self.table.resize(tableSize)
            tableWidth = tableSize.width() - column0Width
            tableHeight = tableSize.height()
            if tableHeight < 30 * len(self.combos) + 3 :
                tableWidth = tableWidth - 21   # leave room for the scroll bar
            else : 
                tableWidth = tableWidth - 4    # fudge a few pixels' worth just to make sure
            #if tableWidth > 600 :
            #    self.table.setColumnWidth(0, tableWidth - 300)
            #    self.table.setColumnWidth(1, 300)
            #else :
            threeEightsTableWidth = (tableWidth * 3) / 8;
            self.table.setColumnWidth(1, tableWidth - threeEightsTableWidth)
            self.table.setColumnWidth(2, threeEightsTableWidth)


    def closeEvent(self, event) :
        if not self.isHidden :
            self.position = self.pos()
            self.currsize = self.size()
            self.hide()
            self.isHidden = True

    # Somehow the lang features gets in the list; remove it
    def removeLangFeature(self, featRefs) :
        print "kludgeRemoveBogusFeature"
        c = len(featRefs.order)
        featLabelLast = featRefs.order[c-1]
        featIdLast = featRefs.featids[featLabelLast]
        if featIdLast == "" :
            print "removing..."
            del featRefs.feats[featLabelLast]
            del featRefs.featids[featLabelLast]
            del featRefs.forders[featLabelLast]
            del featRefs.fval['']
            del featRefs.order[c-1]
        return featRefs
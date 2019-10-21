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


from qtpy import QtCore, QtGui, QtWidgets
import graphite2 as gr
from graide.rungraphite import strtolong, bytestostr
from graide.layout import Layout
import sys

class FeatureRefs(object) :

    # Data structure to represent feature values for a single language, or no language.

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
            print("grval = ", grval)
            for f in grface.featureRefs :
                tag = f.tag()
                if sys.version_info.major > 2:
                    tag = tag.decode("utf-8")  # convert to string
                if tag == '' : continue  # is this the lang feature? not sure...
                name = f.name(langid)
                if not name : continue
                name = name[:]
                n = f.num()
                #print(n, name, f.tag())
                if n == 0 :
                    continue  # probably the lang feature; ignore
                finfo = {}
                forder = []
                for i in range(n) :  # loop over settings
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

    def printFeatures(self):
        for (k,v) in self.fval.items():
            print(k,v)


def make_FeaturesMap(font) :
    #print("make_FeaturesMap")
    grface = gr.Face(font)
    result = {}
    result[None] = FeatureRefs(grface)
    if not grface.face : return result
    for langID in grface.featureLangs :
        langStr = gr.tag_to_str(langID)
        langStr = bytestostr(langStr)
        result[langStr] = FeatureRefs(grface, langStr)
    return result


def printFeaturesMap(fmap) :  # debugging
    for (l, f) in fmap.items():
        print("===============")
        print("lang tag", l)
        f.printFeatures()


class FeatureDialog(QtWidgets.QDialog) :

    def __init__(self, parent = None) : # parent = main window
        super(FeatureDialog, self).__init__(parent)
        self.mainWindow = parent
        self.setWindowTitle("Set Features")
        vLayout = QtWidgets.QVBoxLayout(self)
        self.currsize = None
        self.position = None
        self.isHidden = False
        self.setSizeGripEnabled(True)
        self.setWindowFlags(QtCore.Qt.Tool)
        
        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(3)  # column 0 is empty for now
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        # table is resized later, after feature rows are added
        vLayout.addWidget(self.table)
        
        extraWidget = QtWidgets.QWidget(self)
        gridLayout = QtWidgets.QGridLayout(extraWidget)
        vLayout.addWidget(extraWidget)
        gridLayout.addWidget(QtWidgets.QLabel('Language', extraWidget), 0, 0)
        self.langCtrl = QtWidgets.QLineEdit(extraWidget)
        self.langCtrl.connect(QtCore.SIGNAL('editingFinished()'), self.langChanged)
        #self.langCtrl.setInputMask("<AAan")
        #self.langCtrl.setMaximumWidth(100)
        gridLayout.addWidget(self.langCtrl, 0, 1)
        
        self.runWidth = QtWidgets.QSpinBox(extraWidget)
        self.runWidth.setRange(0, 1000)
        self.runWidth.setValue(100)
        self.runWidth.setSuffix("%")
        self.runWidth.setMaximumWidth(70)
        gridLayout.addWidget(QtWidgets.QLabel('Justify', extraWidget), 1, 0)
        gridLayout.addWidget(self.runWidth, 1, 1)
        
        okCancel = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        okCancel.accepted.connect(self.accept)
        okCancel.rejected.connect(self.reject)
        vLayout.addWidget(okCancel)

        self.featsMod = False  # whether any features have been modified from the language defaults; current not used


    def set_feats(self, feats, featsBaseForLang, vals = None, lang = None, width = 100) :

        #print("feats=", feats)
        #print("featsBaseForLang=", featsBaseForLang)
        #print("vals=", vals)
        #print("lang=", lang)
        
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
                c = QtWidgets.QComboBox()
                c.connect(QtCore.SIGNAL('currentIndexChanged(int)'), self.changeSetting)
                c.userTag = feats.featids[f]
                for k in feats.forders[f] :
                    c.addItem(k, feats.feats[f][k])
                    if c.userTag in vals and feats.feats[f][k] == vals[c.userTag] :
                        c.setCurrentIndex(c.count() - 1)
                self.combos.append(c)
                self.table.setCellWidget(count, 2, c)
                
                #modText = " * " if vals[fid] and vals[fid] != featsBaseForLang.fval[fid] else ""
                #self.table.setItem(count, 0, QtWidgets.QTableWidgetItem(modText))
                # Column 0 currently not used
                
                labelWidget = QtWidgets.QTableWidgetItem(f)
                if fid in vals and vals[fid] != featsBaseForLang.fval[fid] :
                    labelWidget.setBackground(Layout.activePassColour) # modified from expected
                    self.featsMod = True
                self.table.setItem(count, 1, labelWidget)
                self.labels.append(labelWidget)
            
            count += 1
            
        if lang : self.langCtrl.setText(lang)

        self.runWidth.setValue(width)
        self.resize(400, 400)
        #self.table.resizeColumnsToContents()
        
        self.initMode = False
        
    def changeSetting(self, which) :
        # A feature setting was changed. Update the colors of the labels that indicate whether the setting
        # varies from the default for the language.
        
        if self.initMode : # initializing the controls - don't bother updating yet
            return
        
        featI = 0
        for f in self.featsBaseForLang.order :
            fid = self.featsBaseForLang.featids[f]
            combo = self.combos[featI]
            v = combo.itemData(combo.currentIndex())
            d = self.featsBaseForLang.fval[fid]
            
            labelWidget = self.labels[i]
            if v != d:
                backColor = Layout.activePassColour
                self.featsMod = True
            else:
                backColor = QtGui.QColor(255, 255, 255)  # white
            labelWidget.setBackground(backColor)

            featI = featI + 1
        

    def langChanged(self):
        print("langCtrl changed", self.langCtrl.text())

        # Update the features to match the language.

        newLang = self.langCtrl.text()
        if newLang == '': newLang = None
        newFBase = self.mainWindow.feats[newLang]

        self.featsBaseForLang = newFBase
        vals = newFBase.fval

        featI = 0
        for f in newFBase.order :
            fid = newFBase.featids[f] if f in newFBase.featids else ""
            if fid != "":
                combo = self.combos[featI]
                settingI = 0
                for k in newFBase.forders[f] :
                    if combo.userTag in vals and newFBase.feats[f][k] == vals[combo.userTag] :
                        combo.setCurrentIndex(settingI)
                        break
                    settingI = settingI + 1
                featI = featI + 1

        # Clear all the label widget backgrounds to white (default for language).
        for labelWidget in self.labels:
            labelWidget.setBackgroundColor(QtGui.QColor(255, 255, 255))   # white


    def get_feats(self, base = None) :
        result = {}
        for c in self.combos :
            v = c.itemData(c.currentIndex())
            if base is None or base.fval[c.userTag] != v :
                result[c.userTag] = v
        return result


    def get_lang(self) :
        return self.langCtrl.text()


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
            threeEightsTableWidth = (tableWidth * 3) / 8
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
        print("kludgeRemoveBogusFeature")
        c = len(featRefs.order)
        featLabelLast = featRefs.order[c-1]
        featIdLast = featRefs.featids[featLabelLast]
        if featIdLast == "" :
            print("removing...")
            del featRefs.feats[featLabelLast]
            del featRefs.featids[featLabelLast]
            del featRefs.forders[featLabelLast]
            del featRefs.fval['']
            del featRefs.order[c-1]
        return featRefs

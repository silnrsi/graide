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
import sys, struct

# A GraideFace knows how to find the complete list of features out of the Feat table, including the hidden ones.
class GraideFace(gr.Face):
    def __init__(self, data, options=0, fn=None):
        super(GraideFace, self).__init__(data, options, fn)
        self.allFeatsInTable = None

    def setFeatsInTable(self, featsInTable):
        #print("GraideFace::setFeatsInTable", featsInTable)
        self.allFeatsInTable = featsInTable

    @property
    def featureRefs(self):
        if self.allFeatsInTable is not None:
            #print("getting feats from full list")
            i = -1
            for featid in self.allFeatsInTable:
                i = i + 1
                #print(featid)
                if isinstance(featid, int):
                    #print("featid is an integer", featid)
                    pass
                else:
                    featidInt = maybeInteger(featid)
                    if featidInt != 0:
                        # string that is really an integer, eg, '1' or '1234'
                        #print("integer-like string")
                        if featidInt != 1:  # 1 is lang
                            print("WARNING: integer feature ID " + featid + " is not handled by Graide")
                            # eventually populating the feature dialog will fail
                        featid = featidInt
                    else:
                        #print("regular string")
                        # normal case: string, not integer
                        if isinstance(featid, bytes):
                            featid = bytestostr(featid)
                        #featid = featid.encode('utf-8')   # convert to bytes - no, leave as str
                        featid = strtolong(featid)

                #print(featid)

                fref = super(GraideFace, self).get_featureref(featid)   #fref = gr_face_find_fref(self.face, featid)
                #print("created fref", i, fref)
                #yield FeatureRef(fref, index=i)
                yield fref

        else:
            #print("getting feats from gr_face_fref API")
            super(GraideFace, self).featureRefs


class FeatureRefs(object) :

    # Data structure to represent feature values for a single language, or no language.

    def __init__(self, grface = None, lang = None, featsInTable = None) :
        self.feats = {}       # Feature ID => { setting labels => setting values }
        #self.featids = {}    # Feature labels => IDs
        self.fCurVal = {}        # Feature IDs => current value
        self.orderID = []     # List of feature IDs, in display order
        self.orderLabel = []  # List of feature labels, in display order
        self.fvalOrder = {}   # Feature tag => { list of feature values, in order }
        self.featsInTable = featsInTable  # ID => hidden boolean; complete list of all the features in the table, including hidden ones
        #print("FeatureRefs.featsInTable=", self.featsInTable)

        if grface and grface.face :
            uiLangid = 0x0409 # English
            length = 0
            grval = grface.get_featureval(strtolong(lang))
            grface.setFeatsInTable(featsInTable)

            grface_featureRefs = grface.featureRefs   # returns an iterator
            #print("returned from featureRefs")
            featRefs = []
            for f in grface_featureRefs:
                #print(f.tag(), f)
                featRefs.append(f)
            #print(len(featRefs), "features")

            for oneFeatRef in featRefs:
                tag = oneFeatRef.tag()
                if sys.version_info.major > 2:
                    tag = tag.decode("utf-8")  # convert to string
                if tag == '' : continue  # is this the lang feature? not sure...
                label = oneFeatRef.name(uiLangid)
                if not label : continue
                label = label[:]
                sCnt = oneFeatRef.num()  # number of settings
                if sCnt == 0 :
                    continue  # probably the lang feature; ignore
                fSettings = {}
                fvalOrder = []
                for i in range(sCnt) :  # loop over settings
                    v = oneFeatRef.val(i)
                    k = oneFeatRef.label(i, uiLangid)[:]  # ugly to use the label as the key of the dict, but oh well
                    #("  --", k, v)
                    fSettings[k] = v
                    fvalOrder.append(k)
                self.orderID.append(tag)
                self.orderLabel.append(label)
                self.feats[tag] = fSettings
                #self.featids[name] = f.tag()
                self.fCurVal[tag] = grval.get(oneFeatRef)
                self.fvalOrder[tag] = fvalOrder
                #print(tag, sCnt, fSettings, self.fCurVal[tag])


    def copy(self) :
        res = FeatureRefs()
        res.feats = dict(self.feats)
        #res.featids = dict(self.featids)
        res.fCurVal = dict(self.fCurVal)
        res.orderID = list(self.orderID)
        res.orderLabel = list(self.orderLabel)
        for k, v in self.fvalOrder.items() :
            res.fvalOrder[k] = list(v)
        res.featsInTable = self.featsInTable
        return res

    def apply(self, fvals) :
        for (k, v) in fvals.items() :
            self.fCurVal[k] = v

    def printFeatures(self):  # debugging
        for (k,v) in self.fCurVal.items():
            print(k,"value=",v)

    def isHidden(self, feattag):
        if self.featsInTable is None:
            return False
        else:
            if isinstance(feattag, bytes):
                feattag = bytestostr(feattag)
            return self.featsInTable[feattag]

    def currentValue(self):
        return self.fCurVal


class FeatureDialog(QtWidgets.QDialog) :

    def __init__(self, parent = None) : # parent = main window
        #print("FeatureDialog::__init__")
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

        #print("FeatureDialog::set_feats=", feats)
        #print("featsBaseForLang=", featsBaseForLang)
        #print("vals=", vals)
        #print("lang=", lang)

        #feats.printFeatures()
        
        self.featsBaseForLang = featsBaseForLang
        
        if not vals : vals = feats.fCurVal
        
        self.initMode = True
        
        while self.table.rowCount() :
            self.table.removeRow(0)
        self.combos = []
        self.labels = []
        num = len(feats.orderID)
        self.table.setRowCount(num)
        count = 0
#       for f in feats.order :
#           fid = feats.featids[f] if f in feats.featids else ""
        i = 0
        for fid in feats.orderID:
            fLabel = feats.orderLabel[i]
            i = i + 1
            if fid != "" :
                c = QtWidgets.QComboBox()
                c.connect(QtCore.SIGNAL('currentIndexChanged(int)'), self.changeSetting)
                #c.userTag = feats.featids[f]
                c.userTag = fid
                for k in feats.fvalOrder[fid] :
                    c.addItem(k, feats.feats[fid][k])
                    if c.userTag in vals and feats.feats[fid][k] == vals[c.userTag] :
                        c.setCurrentIndex(c.count() - 1)
                self.combos.append(c)
                self.table.setCellWidget(count, 2, c)
                
                #modText = " * " if vals[fid] and vals[fid] != featsBaseForLang.fCurVal[fid] else ""
                #self.table.setItem(count, 0, QtWidgets.QTableWidgetItem(modText))
                # Column 0 currently not used

                fShowLabel = fLabel
                if feats.isHidden(fid):
                    fShowLabel = fLabel + " [" + fid + "]"
                labelWidget = QtWidgets.QTableWidgetItem(fShowLabel)
                if fid in vals and vals[fid] != featsBaseForLang.fCurVal[fid] :
                    labelWidget.setBackground(Layout.activePassColour) # modified from expected
                    self.featsMod = True
                if feats.isHidden(fid):
                    labelWidget.setTextColor(QtGui.QColor(130, 130, 130))  # hidden
                    #print("---", fid, " is hidden")
                #else:
                #    print(fid, "not hidden")
                self.table.setItem(count, 1, labelWidget)
                self.labels.append(labelWidget)
            
            count += 1  # number actually added
            
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
        for fid in self.featsBaseForLang.orderID :
            flabel = self.featsBaseForLang.orderLabel[featI]
            #fid = self.featsBaseForLang.featids[f]
            combo = self.combos[featI]
            v = combo.itemData(combo.currentIndex())
            d = self.featsBaseForLang.fCurVal[fid]
            
            labelWidget = self.labels[featI]
            if v != d:
                backColor = Layout.activePassColour
                self.featsMod = True
            else:
                backColor = QtGui.QColor(255, 255, 255)  # white
            labelWidget.setBackground(backColor)

            featI = featI + 1
        

    def langChanged(self):
        #print("langCtrl changed", self.langCtrl.text())

        # Update the feature controls to match the language.

        newLang = self.langCtrl.text()
        if newLang == '': newLang = None

        if newLang in self.mainWindow.feats:
            newFBase = self.mainWindow.feats[newLang]

            self.featsBaseForLang = newFBase
            vals = newFBase.fCurVal

            featI = 0
            for fid in newFBase.orderID :
                flabel = newFBase.orderLabel[featI]
                #fid = newFBase.featids[f] if f in newFBase.featids else ""
                if fid != "":
                    combo = self.combos[featI]
                    settingI = 0
                    for k in newFBase.fvalOrder[fid] :
                        if combo.userTag in vals and newFBase.feats[fid][k] == vals[combo.userTag] :
                            combo.setCurrentIndex(settingI)
                            break
                        settingI = settingI + 1
                    featI = featI + 1

            # Clear all the label widget backgrounds to white (default for language).
            for labelWidget in self.labels:
                labelWidget.setBackgroundColor(QtGui.QColor(255, 255, 255))   # white

        else:
            print("No features found for language " + newLang)


    def get_feats(self, base = None) :
        result = {}
        for c in self.combos :
            v = c.itemData(c.currentIndex())
            if base is None or base.fCurVal[c.userTag] != v :
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
        c = len(featRefs.orderID)
        featIdLast = featRefs.orderID[c-1]
        featLabelLast = featRefs.orderLabel[c-1]
        #featIdLast = featRefs.featids[featLabelLast]
        if featIdLast == "" :
            print("removing...")
            del featRefs.feats[featLabelLast]
            #del featRefs.featids[featLabelLast]
            del featRefs.fvalOrder[featLabelLast]
            del featRefs.fCurVal['']
            del featRefs.orderID[c-1]
            del featRefs.orderLabel[c-1]
        return featRefs

# end of class FeatureDialog


# Functions

# Map languages to features
def make_FeaturesMap(fontname):
    #print("make_FeaturesMap", fontname)

    # Get a complete list of features, even the hidden ones
    res = readFeaturesFromTable(fontname)
    #print(res)
    featList = res[0]
    featHidden = res[1]
    featSettings = res[2]

    grface = GraideFace(fontname)
    result = {}

    result[None] = FeatureRefs(grface, featsInTable=featHidden)
    if not grface.face: return result
    for langID in grface.featureLangs:
        langStr = gr.tag_to_str(langID)
        langStr = bytestostr(langStr)
        result[langStr] = FeatureRefs(grface, langStr, featsInTable=featHidden)
    return result

def printFeaturesMap(fmap):  # debugging
    for (l, f) in fmap.items():
        print("===============")
        print("lang tag", l)
        f.printFeatures()

# Read the Feat table from the font directly, since the Graphite engine API calls omit the hidden features.

def readFeaturesFromTable(fontfilename):
    #print("readFeatTable",fontfilename)
    tableDict = {}
    with open(fontfilename, "rb") as inf:
        dat = inf.read(12)
        (_, numtables) = struct.unpack(">4sH", dat[:6])
        #print("numtables=",numtables)
        dat = inf.read(numtables * 16)
        for i in range(numtables):
            (tag, csum, offset, length) = struct.unpack(">4sLLL", dat[i * 16: (i+1) * 16])
            tName = tag.decode("utf-8")
            #print(tName)
            tableDict[tName] = [offset, length]
        nameTbl = readNameTable(inf, tableDict)
        return readFeatTable(inf, tableDict, nameTbl)


def readFeatTable(inf, tableDict, nameTbl):
    resFeats = {}
    resHidden = {}
    resSettings = {}
    if 'Feat' not in tableDict:
        print("no Feat table")
        return [None, None]
    inf.seek(tableDict['Feat'][0])
    dat = inf.read(tableDict['Feat'][1])
    (version, subversion) = struct.unpack(">HH", dat[:4])
    #print(version, subversion)
    numFeats, = struct.unpack(">H", dat[4:6])
    #print("num feats", numFeats)

    for i in range(numFeats):
        #print("feature #",i)
        if version >= 2:
            (fid, numSettings, _, offset, flags, lid) = struct.unpack(">LHHLHH", dat[12+16*i:28+16*i])
        else:
            (fid, numSettings, offset, flags, lid) = struct.unpack(">HHLHH", dat[12+12*i:24+12*i])
        #print(fid)
        tag = num2tag(fid)

        resFeats[tag] = nameTbl.get(lid, "")
        resHidden[tag] = ((flags & 0x0800) != 0)
        #print(tag, resHidden[tag])
        settingsDict = {}
        resSettings[tag] = settingsDict
        #print("num settings", numSettings)
        for j in range(numSettings):
            val, lid = struct.unpack(">HH", dat[offset + 4*j:offset + 4*(j+1)])
            settingsDict[val] = nameTbl.get(lid, "")
        #print(settingsDict)

    #print("resHidden=", resHidden)
    return (resFeats, resHidden, resSettings)


def num2tag(n):  # convert a feature tag integer to a string
    if n < 0x00200000:
        return str(n)
    else:
        return struct.unpack('4s', struct.pack('>L', n))[0].replace(b'\000', b'').decode()

def readNameTable(inf, tableDict):
    resNameTable = {}
    if 'name' not in tableDict:
        return None
    inf.seek(tableDict['name'][0])
    data = inf.read(tableDict['name'][1])
    fmt, n, stringOffset = struct.unpack(b">HHH", data[:6])
    stringData = data[stringOffset:]
    data = data[6:]
    for i in range(n):
        if len(data) < 12:
            break
        (pid, eid, lid, nid, length, offset) = struct.unpack(b">HHHHHH", data[12*i:12*(i+1)])
        # only get unicode strings (US English)
        if (pid == 0 and lid == 0) or (pid == 3 and (eid < 2 or eid == 10) and lid == 1033):
            resNameTable[nid] = stringData[offset:offset+length].decode("utf_16_be")

    #print(resNameTable)
    return resNameTable

def maybeInteger(str):
    """Return the corresponding integer, or zero"""
    try: resInt = int(str)
    except: resInt = 0
    return resInt

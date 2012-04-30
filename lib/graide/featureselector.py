
from PySide import QtCore, QtGui
import graide.graphite as gr

class FeatureRefs(object) :

    def __init__(self, font) :
        self.feats = {}
        self.featids = {}
        self.fval = {}
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


class FeatureDialog(QtGui.QDialog) :

    def __init__(self, parent = None) :
        super(FeatureDialog, self).__init__(parent)
        self.currsize = None
        self.position = None
        self.isHidden = False
        self.setSizeGripEnabled(True)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.table = QtGui.QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()

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

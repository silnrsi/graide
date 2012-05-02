
from PySide import QtGui
from graide.featureselector import FeatureDialog
from xml.etree import ElementTree as et

class Test(object) :
    def __init__(self, text, feats, rtl = False, name = None) :
        self.text = text
        self.feats = dict(feats)
        self.name = name or text
        self.rtl = rtl

    def editDialog(self, parent) :
        self.parent = parent
        self.featdialog = None
        d = QtGui.QDialog()
        v = QtGui.QGridLayout()
        v.addWidget(QtGui.QLabel('Name:', d), 0, 0)
        eName = QtGui.QLineEdit(self.name, d)
        v.addWidget(eName, 0, 1)
        v.addWidget(QtGui.QLabel('Text:', d), 1, 0)
        eText = QtGui.QLineEdit(self.text, d)
        v.addWidget(eText, 1, 1)
        eRTL = QtGui.QCheckBox('RTL', d)
        v.addWidget(eRTL, 2, 1)
        b = QtGui.QPushButton('Features', d)
        v.addWidget(b, 3, 1)
        hw = QtGui.QWidget(d)
        h = QtGui.QHBoxLayout()
        hw.setLayout(h)
        v.addWidget(hw, 4, 1)
        bok = QtGui.QPushButton('OK', hw)
        h.addWidget(bok)
        bcancel = QtGui.QPushButton('Cancel', hw)
        h.addWidget(bcancel)
        d.setLayout(v)
        b.clicked.connect(self.featClicked)
        bok.clicked.connect(d.accept)
        bcancel.clicked.connect(d.reject)
        if d.exec_() :
            self.name = eName.text()
            self.text = eText.text()
            self.rtl = eRTL.isChecked()
            if self.featdialog : 
                self.feats = self.featdialog.get_feats()
            else :
                self.feats = dict(self.parent.feats.fval)
        del self.featdialog
        del self.parent

    def featClicked(self) :
        d = FeatureDialog(self.parent)
        f = self.parent.feats.copy()
        f.apply(self.feats)
        d.set_feats(f)
        self.featdialog = d
        d.exec_()

    def addTree(self, parent) :
        e = et.SubElement(parent, 'test')
        e.text = self.text
        e.tail = "\n"
        e.set('name', self.name)
        if self.rtl : e.set('rtl', 'True')
        feats = []
        for (k, v) in self.feats.items() :
            feats.append("%s=%d" % (k, v))
        e.set('feats', " ".join(feats))
        return e

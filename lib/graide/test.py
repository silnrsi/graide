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


from PySide import QtGui
from graide.featureselector import FeatureDialog
from xml.etree import cElementTree as et
from graide.utils import Layout
import re

def asBool(txt) :
    if not txt : return False
    if txt.lower() == 'true' : return True
    if txt.isdigit() : return int(txt) != 0
    return False

class Test(object) :
    def __init__(self, text, feats, lang = None, rtl = False, name = None, comment = "") :
        self.text = text
        self.feats = dict(feats)
        self.name = name or text
        self.rtl = rtl
        self.lang = lang
        self.comment = comment
        self.foreground = QtGui.QColor('black')
        self.background = QtGui.QColor('white')

    def editDialog(self, parent) :
        self.parent = parent
        self.featdialog = None
        d = QtGui.QDialog()
        v = QtGui.QGridLayout()
        v.addWidget(QtGui.QLabel('Name:', d), 0, 0)
        eName = QtGui.QLineEdit(self.name, d)
        v.addWidget(eName, 0, 1)
        v.addWidget(QtGui.QLabel('Text:', d), 1, 0)
        eText = QtGui.QPlainTextEdit(self.text, d)
        eText.setMaximumHeight(Layout.runEditHeight)
        v.addWidget(eText, 1, 1)
        v.addWidget(QtGui.QLabel('Comment:', d), 2, 0)
        eComment = QtGui.QPlainTextEdit()
        eComment.setPlainText(self.comment)
        eComment.setMaximumHeight(Layout.runEditHeight)
        v.addWidget(eComment, 2, 1)
        eRTL = QtGui.QCheckBox('RTL', d)
        eRTL.setChecked(asBool(self.rtl))
        v.addWidget(eRTL, 3, 1)
        bw = QtGui.QWidget(d)
        bl = QtGui.QHBoxLayout()
        bw.setLayout(bl)
        c = QtGui.QToolButton(bw)
        c.setIcon(QtGui.QIcon.fromTheme('background'))
        c.setToolTip('Set background colour')
        c.clicked.connect(self.doColour)
        bl.addWidget(c)
        b = QtGui.QPushButton('Features', bw)
        bl.addWidget(b)
        v.addWidget(bw, 4, 1)
        hw = QtGui.QWidget(d)
        h = QtGui.QHBoxLayout()
        hw.setLayout(h)
        v.addWidget(hw, 5, 1)
        bok = QtGui.QPushButton('OK', hw)
        h.addWidget(bok)
        bcancel = QtGui.QPushButton('Cancel', hw)
        h.addWidget(bcancel)
        d.setLayout(v)
        b.clicked.connect(self.featClicked)
        bok.clicked.connect(d.accept)
        bcancel.clicked.connect(d.reject)
        res = d.exec_()
        if res :
            self.name = eName.text()
            self.text = eText.toPlainText()
            self.rtl = eRTL.isChecked()
            self.comment = eComment.toPlainText()
            if self.featdialog : 
                self.lang = self.featdialog.get_lang()
                if self.lang not in self.parent.feats :
                    self.lang = None
                self.feats = self.featdialog.get_feats(self.parent.feats[self.lang])
        del self.featdialog
        del self.parent
        return res

    def featClicked(self) :
        d = FeatureDialog(self.parent)
        f = self.parent.feats[self.lang].copy()
        f.apply(self.feats)
        d.set_feats(f, lang = self.lang)
        self.featdialog = d
        if not d.exec_() :
            self.featdialog = None

    def doColour(self) :
        self.background = QtGui.QColorDialog.getColor(self.background)

    def addTree(self, parent) :
        e = et.SubElement(parent, 'test')
        if self.comment :
            c = et.SubElement(e, 'comment')
            c.text = self.comment
        t = et.SubElement(e, 'string')
        t.text = re.sub(r'\\u([0-9A-Fa-f]{4})|\\U([0-9A-Fa-f]{5,8})', \
                lambda m:unichr(int(m.group(1) or m.group(2), 16)), self.text)
        e.set('label', self.name)
        if self.background != QtGui.QColor('white') : e.set('background', self.background.name())
        if self.rtl : e.set('rtl', 'True')
        return e

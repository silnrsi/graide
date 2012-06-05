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
from xml.etree import cElementTree as et
from graide.test import Test
from graide.utils import configval, Layout, reportError
import os

class TestList(QtGui.QWidget) :

    def __init__(self, app, fname = None, parent = None) :
        super(TestList, self).__init__(parent)
        self.noclick = False
        self.app = app
        self.tests = []

        self.vbox = QtGui.QVBoxLayout()
        self.vbox.setContentsMargins(*Layout.buttonMargins)
        self.list = QtGui.QListWidget(self)
        self.list.itemDoubleClicked.connect(self.runTest)
        self.list.itemClicked.connect(self.loadTest)
        self.vbox.addWidget(self.list)
        self.bbox = QtGui.QWidget(self)
        self.hbbox = QtGui.QHBoxLayout()
        self.bbox.setLayout(self.hbbox)
        self.hbbox.setContentsMargins(*Layout.buttonMargins)
        self.hbbox.setSpacing(Layout.buttonSpacing)
        self.hbbox.insertStretch(0)
        self.vbox.addWidget(self.bbox)
        self.bEdit = QtGui.QToolButton(self.bbox)
        self.bEdit.setIcon(QtGui.QIcon.fromTheme('document-properties'))
        self.bEdit.setToolTip('edit test')
        self.bEdit.clicked.connect(self.editClicked)
        self.hbbox.addWidget(self.bEdit)
        self.bUpp = QtGui.QToolButton(self.bbox)
        self.bUpp.setArrowType(QtCore.Qt.UpArrow)
        self.bUpp.setToolTip("Move test up")
        self.bUpp.clicked.connect(self.upClicked)
        self.hbbox.addWidget(self.bUpp)
        self.bDown = QtGui.QToolButton(self.bbox)
        self.bDown.setArrowType(QtCore.Qt.DownArrow)
        self.bDown.setToolTip("Move test down")
        self.bDown.clicked.connect(self.downClicked)
        self.hbbox.addWidget(self.bDown)
        self.bSave = QtGui.QToolButton(self.bbox)
        self.bSave.setIcon(QtGui.QIcon.fromTheme('document-save'))
        self.bSave.setToolTip('save test list')
        self.bSave.clicked.connect(self.saveClicked)
        self.hbbox.addWidget(self.bSave)
        self.bAdd = QtGui.QToolButton(self.bbox)
        self.bAdd.setIcon(QtGui.QIcon.fromTheme('add'))
        self.bAdd.setToolTip('add new test')
        self.bAdd.clicked.connect(self.addClicked)
        self.hbbox.addWidget(self.bAdd)
        self.bDel = QtGui.QToolButton(self.bbox)
        self.bDel.setIcon(QtGui.QIcon.fromTheme('remove'))
        self.bDel.setToolTip('delete test')
        self.bDel.clicked.connect(self.delClicked)
        self.hbbox.addWidget(self.bDel)
        self.setLayout(self.vbox)

        self.loadTests(fname)

    def loadTests(self, fname):
        self.list.clear()
        self.tests = []
        if fname and os.path.exists(fname) :
            try :
                e = et.parse(fname)
            except Exception as err:
                reportError("TestsFile %s: %s" % (fname, str(err)))
            else :
                for t in e.iterfind('test') :
                    feats = {}
                    f = t.get('feats')
                    if f :
                        for ft in f.split(" ") :
                            (k, v) = ft.split('=')
                            feats[k] = int(v)
                    txt = t.text
                    if not txt :
                        y = t.find('text')
                        txt = y.text
                    y = t.find('comment')
                    if y is not None :
                        c = y.text
                    else :
                        c = ""
                    te = Test(txt, feats, t.get('rtl'), t.get('name'), comment = c)
                    self.appendTest(te)

    def appendTest(self, t) :
        self.tests.append(t)
        w = QtGui.QListWidgetItem(t.name, self.list)
        if t.comment :
            w.setToolTip(t.comment)

    def editTest(self, index) :
        t = self.tests[index]
        if t.editDialog(self.app) :
            self.list.item(index).setText(t.name)
            self.list.item(index).setToolTip(t.comment)
            return True
        else :
            return False

    def writeXML(self, fname) :
        e = et.Element('tests')
        e.text = "\n"
        for t in self.tests :
            t.addTree(e)
        et.ElementTree(e).write(fname, encoding="utf-8", xml_declaration=True)

    def editClicked(self) :
        self.editTest(self.list.currentRow())

    def addClicked(self, t = None) :
        if not t : t = Test('', self.app.feats.fval)
        self.appendTest(t)
        res = self.editTest(len(self.tests) - 1)
        if not t.name or not res :
            self.tests.pop()
            self.list.takeItem(len(self.tests))

    def saveClicked(self) :
        tname = configval(self.app.config, 'main', 'testsfile')
        if tname : self.writeXML(tname)

    def delClicked(self) :
        i = self.list.currentRow()
        self.tests.pop(i)
        self.list.takeItem(i)

    def upClicked(self) :
        i = self.list.currentRow()
        if i > 0 :
            self.tests.insert(i - 1, self.tests.pop(i))
            self.list.insertItem(i - 1, self.list.takeItem(i))
            self.list.setCurrentRow(i - 1)

    def downClicked(self) :
        i = self.list.currentRow()
        if i < self.list.count() - 1 :
            self.tests.insert(i + 1, self.tests.pop(i))
            self.list.insertItem(i + 1, self.list.takeItem(i))
            self.list.setCurrentRow(i + 1)

    def loadTest(self, item) :
        if not self.noclick :
            i = self.list.currentRow()
            self.app.setRun(self.tests[i])
        else :
            self.noclick = False

    def runTest(self, item) :
        # event sends clicked first so no need to select
        self.app.runClicked()
        self.noclick = True

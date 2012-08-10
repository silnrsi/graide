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
from graide.utils import configval, configintval, reportError, relpath, ETcanon, ETinsert
from graide.layout import Layout
import os, re
from cStringIO import StringIO

def asBool(txt) :
    if not txt : return False
    if txt.lower() == 'true' : return True
    if txt.isdigit() : return int(txt) != 0
    return False

class TestList(QtGui.QWidget) :

    def __init__(self, app, fname = None, parent = None) :
        super(TestList, self).__init__(parent)
        self.noclick = False
        self.app = app
        self.tests = []
        self.fsets = {"\n" : None}
        self.comments = []
        self.fcount = 0
        self.header = None

        self.setActions(app)
        self.vbox = QtGui.QVBoxLayout()
        self.vbox.setContentsMargins(*Layout.buttonMargins)
        self.cbox = QtGui.QWidget(self)
        self.chbox = QtGui.QHBoxLayout()
        self.chbox.setContentsMargins(*Layout.buttonMargins)
        self.chbox.setSpacing(Layout.buttonSpacing)
        self.cbox.setLayout(self.chbox)
        self.combo = QtGui.QComboBox(self.cbox)
        self.chbox.addWidget(self.combo)
        self.chbox.addSpacing(10)
        self.cabutton = QtGui.QToolButton(self.cbox)
        self.cabutton.setIcon(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")))
        self.cabutton.setToolTip('Add test group below this group')
        self.cabutton.clicked.connect(self.addGroupClicked)
        self.chbox.addWidget(self.cabutton)
        self.crbutton = QtGui.QToolButton(self.cbox)
        self.crbutton.setIcon(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")))
        self.crbutton.setToolTip('Remove test group')
        self.crbutton.clicked.connect(self.delGroupClicked)
        self.chbox.addWidget(self.crbutton)
        self.vbox.addWidget(self.cbox)
        self.list = QtGui.QStackedWidget(self)
        self.vbox.addWidget(self.list)
        self.combo.connect(QtCore.SIGNAL('currentIndexChanged(int)'), self.changeGroup)
        self.addGroup('main')
        self.bbox = QtGui.QWidget(self)
        self.hbbox = QtGui.QHBoxLayout()
        self.bbox.setLayout(self.hbbox)
        self.hbbox.setContentsMargins(*Layout.buttonMargins)
        self.hbbox.setSpacing(Layout.buttonSpacing)
        self.hbbox.insertStretch(0)
        self.vbox.addWidget(self.bbox)
        self.bEdit = QtGui.QToolButton(self.bbox)
        self.bEdit.setDefaultAction(self.aEdit)
        self.hbbox.addWidget(self.bEdit)
        self.bUpp = QtGui.QToolButton(self.bbox)
        self.bUpp.setDefaultAction(self.aUpp)
        self.hbbox.addWidget(self.bUpp)
        self.bDown = QtGui.QToolButton(self.bbox)
        self.bDown.setDefaultAction(self.aDown)
        self.hbbox.addWidget(self.bDown)
        self.bSave = QtGui.QToolButton(self.bbox)
        self.bSave.setDefaultAction(self.aSave)
        self.hbbox.addWidget(self.bSave)
        self.bAdd = QtGui.QToolButton(self.bbox)
        self.bAdd.setDefaultAction(self.aAdd)
        self.hbbox.addWidget(self.bAdd)
        self.bDel = QtGui.QToolButton(self.bbox)
        self.bDel.setDefaultAction(self.aDel)
        self.hbbox.addWidget(self.bDel)
        self.setLayout(self.vbox)

        self.loadTests(fname)

    def setActions(self, app) :
        self.aGAdd = QtGui.QAction(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")), "Add &Group ...", app)
        self.aGAdd.setToolTip('Add test group below this group')
        self.aGAdd.triggered.connect(self.addGroupClicked)
        self.aGDel = QtGui.QAction(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")), "&Remove Group", app)
        self.aGDel.setToolTip('Remove test group')
        self.aGDel.triggered.connect(self.delGroupClicked)
        self.aEdit = QtGui.QAction(QtGui.QIcon.fromTheme('document-properties', QtGui.QIcon(":/images/document-properties.png")), "&Add Test ...", app)
        self.aEdit.setToolTip('edit test')
        self.aEdit.triggered.connect(self.editClicked)
        self.aUpp = QtGui.QAction(QtGui.QIcon.fromTheme('go-up', QtGui.QIcon(":/images/go-up.png")), "Test &Up", app)
        self.aUpp.setToolTip("Move test up")
        self.aUpp.triggered.connect(self.upClicked)
        self.aDown = QtGui.QAction(QtGui.QIcon.fromTheme('go-down', QtGui.QIcon(":/images/go-down.png")), "Test &Down", app)
        self.aDown.setToolTip("Move test down")
        self.aDown.triggered.connect(self.downClicked)
        self.aSave = QtGui.QAction(QtGui.QIcon.fromTheme('document-save', QtGui.QIcon(":/images/document-save.png")), "&Save Tests", app)
        self.aSave.setToolTip('save test list')
        self.aSave.triggered.connect(self.saveClicked)
        self.aAdd = QtGui.QAction(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")), "&Add Test ...", app)
        self.aAdd.setToolTip('add new test')
        self.aAdd.triggered.connect(self.addClicked)
        self.aDel = QtGui.QAction(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")), "&Delete Test", app)
        self.aDel.setToolTip('delete test')
        self.aDel.triggered.connect(self.delClicked)

    def initTests(self) :
        self.addGroup('main')

    def loadTests(self, fname):
        self.tests = []
        self.combo.clear()
        for i in range(self.list.count() - 1, -1, -1) :
            self.list.removeWidget(self.list.widget(i))
        if not fname or not os.path.exists(fname) : 
            self.initTests()
            return
        try :
            e = et.parse(fname)
        except Exception as err:
            reportError("TestsFile %s: %s" % (fname, str(err)))
            return
        if e.getroot().tag == 'tests' :
            self.loadOldTests(e)
            return
        classes = {}
        langs = {}
        self.header = e.find('.//head') 
        if self.header is None : self.header = e.find('.//header')
        for s in e.iterfind('.//style') :
            k = s.get('name')
            v = s.get('feats') or ""
            l = s.get('lang') or ""
            fset = v + "\n" + l
            if fset not in self.fsets : self.fsets[fset] = k
            classes[k] = {}
            if l : langs[k] = l
            for ft in v.split(" ") :
                if '=' in ft :
                    (k1, v1) = ft.split('=')
                    classes[k][k1] = int(v1)
            m = re.match(r'fset([0-9]+)', k)
            if m :
                i = int(m.group(1))
                if i > self.fcount : self.fcount = i
        for g in e.iterfind('testgroup') :
            l = self.addGroup(g.get('label'))
            y = g.find('comment')
            self.comments.append(y.text if y else '')
            for t in g.iterfind('test') :
                y = t.find('string')
                if y is None : y = t.find('text')
                txt = y.text if y is not None else ""
                y = t.find('comment')
                c = y.text if y is not None else ""
                y = t.get('class')
                if y and y in classes :
                    feats = classes[y]
                    lng = langs.get(y)
                else :
                    feats = {}
                    lng = None
                te = Test(txt, feats, lang = lng, rtl = asBool(t.get('rtl')), name = t.get('label'), comment = c)
                b = t.get('background')
                if b :
                    res = QtGui.QColor(b)
                    if res.isValid() : te.background = res
                w = t.get('expand')
                if w :
                    te.setWidth(int(w))
                self.appendTest(te, l)

    def loadOldTests(self, e) :
        l = self.addGroup('main')
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
            te = Test(txt, feats, rtl = t.get('rtl'), name = t.get('name'), comment = c)
            b = t.get('background')
            if b :
                res = QtGui.QColor(b)
                if res.isValid() : te.background = res
            self.appendTest(te, l)

    def addGroup(self, name, index = None, comment = "") :
        l = QtGui.QListWidget()
        l.itemDoubleClicked.connect(self.runTest)
        l.itemClicked.connect(self.loadTest)
        res = []
        if index is None :
            self.list.addWidget(l)
            self.combo.addItem(name)
            self.tests.append(res)
            self.comments.append(comment)
        else :
            self.list.insertWidget(index, l)
            self.combo.insertItem(index, name)
            self.tests.insert(index, res)
            self.comments.insert(index, comment)
        return l

    def appendTest(self, t, l = None) :
        if not l : l = self.list.currentWidget()
        self.tests[self.list.indexOf(l)].append(t)
        w = QtGui.QListWidgetItem(t.name or "", l)
        if t.comment :
            w.setToolTip(t.comment)
            w.setBackground(QtGui.QBrush(t.background))

    def editTest(self, index) :
        i = self.list.currentIndex()
        t = self.tests[i][index]
        if t.editDialog(self.app) :
            l = self.list.widget(i)
            l.item(index).setText(t.name)
            l.item(index).setToolTip(t.comment)
            l.item(index).setBackground(QtGui.QBrush(t.background))
            return True
        else :
            return False

    def writeXML(self, fname) :
        e = et.Element('ftml', {'version' : '1.0'})
        if self.header is not None :
            h = self.header
            if h.tag == 'header' : h.tag = 'head'
            e.append(h)
        else :
            h = et.SubElement(e, 'head')
        fs = h.find('fontsrc')
        if fs is None:
            fs = h.makeelement('fontsrc', {})
            ETinsert(h, fs)
        fs.text = 'url(' + relpath(self.app.fontfile, fname) + ')'
        used = set()
        for i in range(len(self.tests)) :
            g = et.SubElement(e, 'testgroup')
            g.set('label', self.combo.itemText(i))
            for t in self.tests[i] :
                te = t.addTree(g)
                c = self.findClass(t)
                if c :
                    te.set('class', c)
                    used.add(c)
        s = h.find('styles')
        invfsets = {}
        for k, v in self.fsets.items() :
            if v is not None and v not in used :
                del self.fsets[k]
            else :
                invfsets[v] = k
        if len(self.fsets) > 1 :
            if s is not None :
                for i in range(len(s) - 1, -1, -1) :
                    s.remove(s[i])
            else :
                s = h.makeelement('styles', {})
                ETinsert(h, s)
            for v in sorted(invfsets.keys()) :
                k = invfsets[v]
                if not v : continue
                st = et.SubElement(s, 'style')
                st.set('name', v)
                (k, sep, l) = k.rpartition("\n")
                if k : st.set('feats', k)
                if l and l != 'None' : st.set('lang', l)
        elif s :
            h.remove(s)
        f = open(fname, "wb")
        sio = StringIO()
        sio.write('<?xml version="1.0" encoding="utf-8"?>\n')
        sio.write('<?xml-stylesheet type="text/xsl" href="Testing.xsl"?>\n')
        et.ElementTree(ETcanon(e)).write(sio, encoding="utf-8")
        f.write(sio.getvalue().replace(' />', '/>'))
        sio.close()
        f.close()

    @QtCore.Slot(int)
    def changeGroup(self, index) :
        self.list.setCurrentIndex(index)
        if index < len(self.comments) :
            self.combo.setToolTip(self.comments[index])

    def addGroupClicked(self) :
        (name, ok) = QtGui.QInputDialog.getText(self, 'Test Group', 'Test Group Name')
        if ok :
            index = self.combo.currentIndex() + 1
            self.addGroup(name, index)
            self.combo.setCurrentIndex(self.combo.currentIndex() + 1)

    def delGroupClicked(self) :
        index = self.combo.currentIndex()
        self.list.removeWidget(self.list.widget(index))
        self.combo.removeItem(index)
        self.tests.pop(index)

    def editClicked(self) :
        self.editTest(self.list.currentWidget().currentRow())

    def addClicked(self, t = None) :
        i = self.list.currentIndex()
        if not t : t = Test('', self.app.feats[None].fval, rtl = configintval(self.app.config, 'main', 'defaultrtl'))
        self.appendTest(t)
        res = self.editTest(len(self.tests[i]) - 1)
        if not t.name or not res :
            self.tests[i].pop()
            self.list.widget(i).takeItem(len(self.tests))

    def saveClicked(self) :
        tname = configval(self.app.config, 'main', 'testsfile')
        if tname : self.writeXML(tname)

    def delClicked(self) :
        j = self.list.currentIndex()
        i = self.list.widget(j).currentRow()
        self.tests[j].pop(i)
        self.list.widget(j).takeItem(i)

    def upClicked(self) :
        l = self.list.currentWidget()
        j = self.list.currentIndex()
        i = l.currentRow()
        if i > 0 :
            self.tests[j].insert(i - 1, self.tests[j].pop(i))
            l.insertItem(i - 1, l.takeItem(i))
            l.setCurrentRow(i - 1)

    def downClicked(self) :
        l = self.list.currentWidget()
        j = self.list.currentIndex()
        i = l.currentRow()
        if i < l.count() - 1 :
            self.tests[j].insert(i + 1, self.tests[j].pop(i))
            l.insertItem(i + 1, l.takeItem(i))
            l.setCurrentRow(i + 1)

    def loadTest(self, item) :
        if not self.noclick :
            j = self.list.currentIndex()
            i = self.list.currentWidget().currentRow()
            self.app.setRun(self.tests[j][i])
        else :
            self.noclick = False

    def runTest(self, item) :
        # event sends clicked first so no need to select
        self.app.runClicked()
        self.noclick = True

    def findClass(self, t) :
        k = " ".join(map(lambda x: x + "=" + str(t.feats[x]), sorted(t.feats.keys())))
        k += "\n" + (t.lang or "")
        if k not in self.fsets :
            self.fcount += 1
            self.fsets[k] = "fset%d" % self.fcount
        return self.fsets[k]


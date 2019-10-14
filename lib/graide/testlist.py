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
from xml.etree import ElementTree as et
from graide.test import Test
from graide.utils import configval, configintval, reportError, relpath, ETcanon, ETinsert
from graide.layout import Layout
import os, re
import codecs, traceback # debugging


def asBool(txt) :
    if not txt : return False
    if txt.lower() == 'true' : return True
    if txt.isdigit() : return int(txt) != 0
    return False


class TestListWidget(QtWidgets.QListWidget) :
    
    def __init__(self, testList) :
        super(TestListWidget, self).__init__()
        self.testList = testList
        
    def keyPressEvent(self, event) :
        res = super(TestListWidget, self).keyPressEvent(event)
        
        if event.key() == QtCore.Qt.Key_Up :
            self.testList.upArrowKey()
        elif event.key() == QtCore.Qt.Key_Down :
            self.testList.downArrowKey()

        return res

# end of clas TestListWidget

    
class TestList(QtWidgets.QWidget) :

    def __init__(self, app, fName = None, parent = None) :
        super(TestList, self).__init__(parent)
        self.noclick = False
        self.quickProofMode = True
        self.app = app
        self.testFiles = []     # list of filenames, include paths
        self.currentFile = ""
        self.testGroups = []    # data structure of groups and tests
        self.fsets = {"\n" : None}
        self.comments = []
        self.fcount = 0
        self.header = None

        # Get the current test stuff from the configuration before setting up the files, which could change it.
        curTest = self.app.config.get('data','currenttest') if self.app.config.has_option('data','currenttest') else ""
        fListString = self.app.config.get('data', 'testfiles') if self.app.config.has_option('data','testfiles') else ""

        self.setActions(app)
        vLayout = QtWidgets.QVBoxLayout()
        vLayout.setContentsMargins(*Layout.buttonMargins)
        
        # test file control
        self.cbox1 = QtWidgets.QWidget(self)
        fhLayout = QtWidgets.QHBoxLayout()
        fhLayout.setContentsMargins(*Layout.buttonMargins)
        fhLayout.setSpacing(Layout.buttonSpacing)    
        self.cbox1.setLayout(fhLayout)
        self.fcombo = QtWidgets.QComboBox(self.cbox1)  # file combo box
        self.fcombo.setToolTip('Choose test file')
        fhLayout.addWidget(self.fcombo)
        fhLayout.addSpacing(10)
        self.fabutton = QtWidgets.QToolButton(self.cbox1)
        self.fabutton.setIcon(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")))
        self.fabutton.setToolTip('Add test file')
        self.fabutton.clicked.connect(self.addFileClicked)
        fhLayout.addWidget(self.fabutton)
        self.frbutton = QtWidgets.QToolButton(self.cbox1)
        self.frbutton.setIcon(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")))
        self.frbutton.setToolTip('Remove test file from list')
        self.frbutton.clicked.connect(self.delFileClicked)
        fhLayout.addWidget(self.frbutton)
        vLayout.addWidget(self.cbox1)
        
        # test group controls
        self.cbox2 = QtWidgets.QWidget(self)
        ghLayout = QtWidgets.QHBoxLayout()
        ghLayout.setContentsMargins(*Layout.buttonMargins)
        ghLayout.setSpacing(Layout.buttonSpacing)
        self.cbox2.setLayout(ghLayout)
        self.gcombo = QtWidgets.QComboBox(self.cbox2)  # group combo box
        self.gcombo.setToolTip('Choose test group')
        ghLayout.addWidget(self.gcombo)
        ghLayout.addSpacing(10)
        self.gabutton = QtWidgets.QToolButton(self.cbox2)
        self.gabutton.setIcon(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")))
        self.gabutton.setToolTip('Add test group below this group')
        self.gabutton.clicked.connect(self.addGroupClicked)
        ghLayout.addWidget(self.gabutton)
        self.grbutton = QtWidgets.QToolButton(self.cbox2)
        self.grbutton.setIcon(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")))
        self.grbutton.setToolTip('Remove test group')
        self.grbutton.clicked.connect(self.delGroupClicked)
        ghLayout.addWidget(self.grbutton)
        vLayout.addWidget(self.cbox2)
        
        self.liststack = QtWidgets.QStackedWidget(self)  # stack of lists of test items
        vLayout.addWidget(self.liststack) 

        self.fcombo.connect(QtCore.SIGNAL('currentIndexChanged(int)'), self.changeFileCombo)
        
        self.gcombo.connect(QtCore.SIGNAL('currentIndexChanged(int)'), self.changeGroupCombo)
        self.addGroup('main', record = False)

        # list control
        self.bbox = QtWidgets.QWidget(self)
        hbLayout = QtWidgets.QHBoxLayout()
        self.bbox.setLayout(hbLayout)
        hbLayout.setContentsMargins(*Layout.buttonMargins)
        hbLayout.setSpacing(Layout.buttonSpacing)
        hbLayout.insertStretch(0)
        vLayout.addWidget(self.bbox)
        self.bEdit = QtWidgets.QToolButton(self.bbox)
        self.bEdit.setDefaultAction(self.aEdit)
        hbLayout.addWidget(self.bEdit)
        self.bUpp = QtWidgets.QToolButton(self.bbox)
        self.bUpp.setDefaultAction(self.aUpp)
        hbLayout.addWidget(self.bUpp)
        self.bDown = QtWidgets.QToolButton(self.bbox)
        self.bDown.setDefaultAction(self.aDown)
        hbLayout.addWidget(self.bDown)
        self.bSave = QtWidgets.QToolButton(self.bbox)
        self.bSave.setDefaultAction(self.aSave)
        hbLayout.addWidget(self.bSave)
        self.bAdd = QtWidgets.QToolButton(self.bbox)
        self.bAdd.setDefaultAction(self.aAdd)
        hbLayout.addWidget(self.bAdd)
        self.bDel = QtWidgets.QToolButton(self.bbox)
        self.bDel.setDefaultAction(self.aDel)
        hbLayout.addWidget(self.bDel)
        
        self.setLayout(vLayout)

        if fName :
            self.addFile(fName, None, False)
        if fListString :
            fList = fListString.split(';')
            for f in fList :
                if f != "" and f != fName:
                    self.addFile(f, None, False)
        
        self.selectCurrentTest(curTest)
        
    # end of __init__

    def setActions(self, app) :
        self.aGAdd = QtWidgets.QAction(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")), "Add &Group ...", app)
        self.aGAdd.setToolTip('Add test group below this group')
        self.aGAdd.triggered.connect(self.addGroupClicked)
        self.aGDel = QtWidgets.QAction(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")), "&Remove Group", app)
        self.aGDel.setToolTip('Remove test group')
        self.aGDel.triggered.connect(self.delGroupClicked)
        self.aEdit = QtWidgets.QAction(QtGui.QIcon.fromTheme('document-properties', QtGui.QIcon(":/images/document-properties.png")), "&Edit Test ...", app)
        self.aEdit.setToolTip('Edit test')
        self.aEdit.triggered.connect(self.editClicked)
        self.aUpp = QtWidgets.QAction(QtGui.QIcon.fromTheme('go-up', QtGui.QIcon(":/images/go-up.png")), "Test &Up", app)
        self.aUpp.setToolTip("Move test up")
        self.aUpp.triggered.connect(self.upClicked)
        self.aDown = QtWidgets.QAction(QtGui.QIcon.fromTheme('go-down', QtGui.QIcon(":/images/go-down.png")), "Test &Down", app)
        self.aDown.setToolTip("Move test down")
        self.aDown.triggered.connect(self.downClicked)
        self.aSave = QtWidgets.QAction(QtGui.QIcon.fromTheme('document-save', QtGui.QIcon(":/images/document-save.png")), "&Save Tests", app)
        self.aSave.setToolTip('Save test list')
        self.aSave.triggered.connect(self.saveTestsClicked)
        self.aAdd = QtWidgets.QAction(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")), "&Add Test ...", app)
        self.aAdd.setToolTip('Add new test')
        self.aAdd.triggered.connect(self.addTestClicked)
        self.aDel = QtWidgets.QAction(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")), "&Delete Test", app)
        self.aDel.setToolTip('Delete test')
        self.aDel.triggered.connect(self.delTestClicked)
        
    # end of setActions
    
    def selectCurrentTest(self, curTestString) :
        if curTestString == "" :
            return
        (fileIndex, groupIndex, testIndex) = curTestString.split('.')
        fileIndex = int(fileIndex)
        groupIndex = int(groupIndex)
        testIndex = int(testIndex)
        if fileIndex == -1 :
            fileIndex = 0
            groupIndex = -1
            testIndex = -1
        if groupIndex == -1 :
            groupIndex = 0
            testIndex = -1
        # First set up the data structures for the right file and group. Ideally this
        # would happen as a result of calling setCurrentIndex, but the signal processing
        # doesn't allow things to happen in the right order.
        self.changeFile(fileIndex)
        self.changeGroup(groupIndex)
        # These calls make the combo boxes match the data.
        self.fcombo.setCurrentIndex(fileIndex)
        self.gcombo.setCurrentIndex(groupIndex)
        l = self.liststack.currentWidget()
        if l:
            l.setCurrentItem(l.item(testIndex))
            self.recordCurrentTest()


    def initTests(self, fname) :
        self.addGroup('main', record = False)

    def loadTests(self, fname):
        #print("TestList::loadTests(" + fname + ")")
        
        # Assumes the file has been added to the UI.
        self.testGroups = []
        self.gcombo.clear()
        for i in range(self.liststack.count()-1, -1, -1) :
            self.liststack.removeWidget(self.liststack.widget(i))
        if not fname or not os.path.exists(fname) :
            # Create a new set of tests - these will be stored in a new file.
            self.initTests(fname)
            return
            
        try :
            e = et.parse(fname)
        except Exception as err:
            reportError("TestsFile %s: %s" % (fname, str(err)))
            return
        if e.getroot().tag == 'tests' :
            print("Can't find tests file " + fname)
            self.loadOldTests(e)
            return
            
        styles = {}
        langs = {}
        self.header = e.find('.//head') 
        if self.header is None : self.header = e.find('.//header')
        for s in e.iterfind('.//style') :
            styleName = s.get('name')
            featDescrip = s.get('feats') or ""
            langCode = s.get('lang') or ""
            fset = featDescrip + "\n" + langCode
            if fset not in self.fsets : self.fsets[fset] = styleName
            styles[styleName] = {}
            if langCode : langs[styleName] = langCode
            for ft in featDescrip.split(" ") :
                if '=' in ft :
                    (fname, value) = ft.split('=')
                    if value and value != "None" :  # under buggy circumstances value can be 'None'; test for it just in case
                        styles[styleName][fname] = int(value)
            m = re.match(r'fset([0-9]+)', styleName)
            if m :
                i = int(m.group(1)) ## number of the fset, eg 'fset2' -> 2
                if i > self.fcount : self.fcount = i
                    
        for g in e.iterfind('testgroup') :
            listwidget = self.addGroup(g.get('label'))
            y = g.find('comment')
            self.comments.append(y.text if y else '')
            for t in g.iterfind('test') :
                y = t.find('string')
                if y is None : y = t.find('text')
                txt = y.text if y is not None else ""
                y = t.find('comment')
                c = y.text if y is not None else ""
                y = t.get('class')
                if y and y in styles :
                    feats = styles[y]
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
                self.appendTest(te, listwidget)
        
    # end of loadTests

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
            
    # end of loadOldTests
            
    def addFile(self, fname, index = None, savePrevious = True) :
        #print("TestList::addFile(" + fname + "," + index + "," + str(savePrevious) + ")")
        if fname == '' : return

        if len(self.testFiles) == 0 and fname is not None:
            # Make this the main test file.
            self.app.config.set('main', 'testsfile', fname)
            
        basename = os.path.basename(fname)
        if index == None :
            index = len(self.testFiles)
            self.testFiles.append(fname)
            self.fcombo.addItem(basename)
        else :
            self.testFiles.insert(index, fname)
            self.fcombo.insertItem(index, basename)

        self.changeFile(index)
        self.recordTestFiles()
        self.recordCurrentTest()

        
    def changeFile(self, index) :
        #print("TestList::changeFile(" + str(index) + ")")
        
        # Save current set of tests.
        if self.currentFile != "" :
            self.writeXML(self.currentFile)
        # Delete all the existing UI for the current test file.
        for i in range(self.liststack.count()-1, -1, -1) :
            self.liststack.removeWidget(self.liststack.widget(i))
        self.gcombo.clear()
        # Load the new test file.
        if len(self.testFiles) > index:
            self.loadTests(self.testFiles[index])
            self.currentFile = self.testFiles[index]
            self.recordCurrentTest()
        
    def addGroup(self, name, index = None, comment = "", record = True) :
        listWidget = TestListWidget(self) # create a test list widget for this group
        listWidget.itemClicked.connect(self.singleClick)
        listWidget.itemDoubleClicked.connect(self.doubleClick)
        groupList = []  # initially empty
        if index is None :
            self.liststack.addWidget(listWidget)
            self.gcombo.addItem(name)
            self.testGroups.append(groupList)
            self.comments.append(comment)
        else :
            self.liststack.insertWidget(index, listWidget)
            self.gcombo.insertItem(index, name)
            self.testGroups.insert(index, groupList)
            self.comments.insert(index, comment)
        if record :
            self.recordCurrentTest()
        return listWidget
        
    def appendTest(self, t, l = None) :
        #print("TestList::appendTest(" + t.name + ")")
        if not l : l = self.liststack.currentWidget()
        self.testGroups[self.liststack.indexOf(l)].append(t)
        w = QtWidgets.QListWidgetItem(t.name or "", l)
        if t.comment :
            w.setToolTip(t.comment)
        w.setBackground(QtGui.QBrush(t.background))

    def editTest(self, testindex) :
        groupindex = self.liststack.currentIndex()
        t = self.testGroups[groupindex][testindex]
        bgndSave = t.background
        if t.editDialog(self.app) :
            l = self.liststack.widget(groupindex)
            l.item(testindex).setText(t.name)
            l.item(testindex).setToolTip(t.comment)
            l.item(testindex).setBackground(QtGui.QBrush(t.background))
            return True
        else :
            # Undo any change to background.
            t.background = bgndSave

    def writeXML(self, fname) :
        #print("TestList::writeXML(" + fname + ")")
        
        e = et.Element('ftml', {'version' : '1.0'})
        if self.header is not None :
            h = self.header
            if h.tag == 'header' : h.tag = 'head'
            e.append(h)
        else :
            h = et.SubElement(e, 'head')
        cols = h.find('columns')
        if cols is None :
            cols = h.makeelement('columns', {'label' : "15%", 'string' : '50%', 'comment' : '30%', 'style' : '5%'})
            ETinsert(h, cols)
        fs = h.find('fontsrc')
        if fs is None:
            fs = h.makeelement('fontsrc', {})
            ETinsert(h, fs)
        if self.app.fontFileName :
            fs.text = 'url(' + relpath(self.app.fontFileName, fname) + ')'
        else :
            fs.text = 'url(unknown font)'
        used = set()
        for i in range(len(self.testGroups)) :
            g = et.SubElement(e, 'testgroup')
            g.set('label', self.gcombo.itemText(i))
            for t in self.testGroups[i] :
                te = t.addXML(g)
                c = self.findStyleClass(t)
                if c :
                    te.set('class', c)
                    used.add(c)
        s = h.find('styles')

        invfsets = {}
        kNotUsed = []
        for k, v in self.fsets.items() :
            if v is not None :
                if v not in used :
                    kNotUsed.append(k)  # don't actually delete while iterating over the dictionary
                else :
                    invfsets[v] = k
        for k in kNotUsed:
            self.fsets.pop(k, None)

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
        f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
        f.write(b'<?xml-stylesheet type="text/xsl" href="Testing.xsl"?>\n')
        et.ElementTree(ETcanon(e)).write(f, encoding="utf-8")
        f.close()
        
    # end of writeXML
        
    @QtCore.Slot(int)
    def changeFileCombo(self, index) :
        #print("changeFileCombo(" + str(index) + ")")
        self.changeFile(index)

    def addFileClicked(self) :
        # This dialog allows specifying a file that does not exist.
        qdialog = QtWidgets.QFileDialog()
        qdialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        qdialog.setViewMode(QtWidgets.QFileDialog.Detail)
        qdialog.setNameFilter('XML files (*.xml)')
        if qdialog.exec_() :
            selected = qdialog.selectedFiles()
            fname = selected[0]
            if fname[-4:] != ".xml" :
                fname += ".xml"
            index = self.fcombo.currentIndex() + 1
            self.addFile(fname, index)
            #self.fcombo.setCurrentIndex(self.fcombo.currentIndex() + 1)
            self.fcombo.setCurrentIndex(index)
        
    def delFileClicked(self) :
        if len(self.testFiles) <= 1 :
            return  # don't delete the last one
        index = self.fcombo.currentIndex()
            
        # Save current set of tests.
        if self.currentFile != "" :
            self.writeXML(self.currentFile)
        self.currentFile = ""
            
        self.testFiles.pop(index)
        self.fcombo.removeItem(index)
        
        index = min(index, len(self.testFiles) - 1)
        self.changeFile(index)
        self.record
        
    @QtCore.Slot(int)
    def changeGroupCombo(self, index) :
        #print("changeGroupCombo(" + str(index) + ")")
        self.changeGroup(index)
        
    def changeGroup(self, index) :
        self.liststack.setCurrentIndex(index)
        if index < len(self.comments) :
            self.gcombo.setToolTip(self.comments[index])
        self.recordCurrentTest()

    def addGroupClicked(self) :
        (name, ok) = QtWidgets.QInputDialog.getText(self, 'Test Group', 'Test Group Name')
        if ok :
            index = self.gcombo.currentIndex() + 1
            self.addGroup(name, index)
            self.gcombo.setCurrentIndex(self.gcombo.currentIndex() + 1)
            self.recordCurrentTest()

    def delGroupClicked(self) :
        index = self.gcombo.currentIndex()
        if index < 0 :
            return
        self.liststack.removeWidget(self.liststack.widget(index))
        self.gcombo.removeItem(index)
        self.testGroups.pop(index)
        self.recordCurrentTest()

    def editClicked(self) :
        if self.liststack.currentWidget() is None :
            return
        index = self.liststack.currentWidget().currentRow()
        if index >= 0 :
            self.editTest(index)

    def addTestClicked(self, t = None) :
        if not hasattr(self.app, 'feats') :
            return
        groupIndex = self.liststack.currentIndex()
        if not t : t = Test('', self.app.feats[None].fval, rtl = configintval(self.app.config, 'main', 'defaultrtl'))
        self.appendTest(t)
        res = self.editTest(len(self.testGroups[groupIndex]) - 1)
        if not t.name or not res :
            self.testGroups[groupIndex].pop()
            self.liststack.widget(groupIndex).takeItem(len(self.testGroups))
        self.recordTestFiles()

    def delTestClicked(self) :
        groupindex = self.liststack.currentIndex()
        if groupindex < 0 :
            return
        testindex = self.liststack.widget(groupindex).currentRow()
        if testindex < 0 :
            return
        self.testGroups[groupindex].pop(testindex)
        self.liststack.widget(groupindex).takeItem(testindex)
        self.recordTestFiles()

    def saveTestsClicked(self) :
        self.saveTests()
        
    def saveTests(self) :
        #tname = configval(self.app.config, 'main', 'testsfile')
        #if tname : self.writeXML(tname)
        if self.currentFile :
            self.writeXML(self.currentFile)

    def upClicked(self) :
        l = self.liststack.currentWidget()
        groupindex = self.liststack.currentIndex()
        if groupindex < 0 :
            return
        testindex = l.currentRow()
        if testindex > 0 :
            self.testGroups[groupindex].insert(testindex - 1, self.testGroups[groupindex].pop(testindex))
            l.insertItem(testindex - 1, l.takeItem(testindex))
            l.setCurrentRow(testindex - 1)
        self.recordCurrentTest()

    def downClicked(self) :
        l = self.liststack.currentWidget()
        groupindex = self.liststack.currentIndex()
        if groupindex < 0 :
            return
        testindex = l.currentRow()
        if testindex < l.count() - 1 :
            self.testGroups[groupindex].insert(testindex + 1, self.testGroups[groupindex].pop(testindex))
            l.insertItem(testindex + 1, l.takeItem(testindex))
            l.setCurrentRow(testindex + 1)
        self.recordCurrentTest()
            
    def singleClick(self, item) :
        if self.quickProofMode :
            self.loadTest(item)
            self.runTest(item)
        else :
            if not self.noclick :
                self.loadTest(item)
            else :
                self.noclick = False
            
    def doubleClick(self, item) :
        if self.quickProofMode :
            # the single click routine already did everything
            pass
        else :
            # event sends itemClicked first so no need to select
            self.runTest(item)
            self.noclick = True  # because itemClicked event will happen again--ignore it

    def loadTest(self, item) :
        groupIndex = self.liststack.currentIndex()
        testIndex = self.liststack.currentWidget().currentRow()
        self.selectTest(groupIndex, testIndex)

    def runTest(self, item) :
        self.app.runClicked()

    def upArrowKey(self) :
        l = self.liststack.currentWidget()
        groupIndex = self.liststack.currentIndex()
        testIndex = l.currentRow()
        self.selectTest(groupIndex, testIndex)
        if self.quickProofMode :
            self.runTest("bogus")

    def downArrowKey(self) :
        l = self.liststack.currentWidget()
        groupIndex = self.liststack.currentIndex()
        testIndex = l.currentRow()
        self.selectTest(groupIndex, testIndex)
        if self.quickProofMode :
            self.runTest("bogus")
    
    def selectTest(self, groupIndex, testIndex) :
        self.recordCurrentTest()
        self.app.setRun(self.testGroups[groupIndex][testIndex])
        
    def recordCurrentTest(self) :
        fileIndex = self.fcombo.currentIndex()
        l = self.liststack.currentWidget()
        groupIndex = self.liststack.currentIndex()
        testIndex = l.currentRow() if l else -1
        value = str(fileIndex) + '.' + str(groupIndex) + '.' + str(testIndex)
        if not self.app.config.has_section('data') :
            self.app.config.add_section('data')
        self.app.config.set('data', 'currenttest', value)
        
    def recordTestFiles(self) :
        fileString = ''
        for f in self.testFiles :
            fileString = fileString + f + ';'
        if not self.app.config.has_section('data') :
            self.app.config.add_section('data')
        self.app.config.set('data', 'testfiles', fileString)
        
    def findStyleClass(self, t) :
        k = ""
        for label,val in t.feats.items():
            lstr = label.decode() if isinstance(label, bytes) else label
            k += " " + lstr + "=" + str(val)
        k = k[1:] # take off initial superfluous space
        ####k = " ".join(map(lambda x: x + "=" + str(t.feats[x]), sorted(str(t.feats.keys()))))
        k += "\n" + (t.lang or "")
        if k not in self.fsets :
            self.fcount += 1
            self.fsets[k] = "fset%d" % self.fcount
        return self.fsets[k]

# end of class TestList

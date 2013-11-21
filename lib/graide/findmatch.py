#    Copyright 2013, SIL International
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

import os, re
from xml.etree import cElementTree as et
from graide.utils import reportError
from rungraphite import makeFontAndFace


from PySide import QtCore, QtGui
from graide.test import Test
from graide.utils import configval, configintval, reportError, relpath, ETcanon, ETinsert
from graide.run import Run
from graide.runview import RunView
from graide.layout import Layout
from cStringIO import StringIO


class GlyphPatternMatcher() :
    
    def __init__(self, app, matcher) :
        self.app = app
        self.matcher = matcher
        self.pattern = ""
    
    # Create a reg-exp from the list of glyphs in the pattern JSON.
    # TEMPORARY FOR DEBUGGING
    def tempCreateRegExp(self, font, json, startI = 0, endI = 3) :
        jsonOutput = json[0]["output"]
        pattern = ""
        tempCnt = 0
        for g in jsonOutput :
            if tempCnt < startI :
                continue
            if g["gid"] == 848 :
                classData = font.classes['cDiacritics']
                pattern += "("
                sep = ""
                for classGlyph in classData.elements :
                   pattern += sep + "_" + str(classGlyph)
                   sep = "|"
                pattern += ")"
            elif tempCnt == 1 :
                pattern += self._singleGlyphPattern() # ANY
            else :    
                pattern += "_" + str(g["gid"])
                
            tempCnt = tempCnt + 1
            if tempCnt >= endI :
                break;
               
        self.pattern = pattern

    # end of tempCreateRegExp
    
    def setUpPattern(self, glyphPattern, font) :
        regexpPattern = ""
        glyphItems = glyphPattern.split(' ')
        
        for item in glyphItems :
            if item[0:2] == "g_" :
                item = item[2:]
                    
            if item == "ANY" :
                regexpPattern += self._singleGlyphPattern()
                
            elif item in font.classes :
                print item + " is class"
                classData = font.classes[item]
                regexpPattern += "("
                sep = ""
                for classGlyph in classData.elements :
                   regexpPattern += sep + "_" + str(classGlyph)
                   sep = "|"
                regexpPattern += ")"
                
            elif item in font.gnames :
                print item + " is glyph"
                regexpPattern += "_" + str(font.gnames[item])
                
            else :
                print item + " not found"
                self.pattern = ""
                
                msg = "ERROR: '" + item + "' is not a valid class or glyph name."
                #reportError(msg)
                errorDialog = QtGui.QMessageBox()
                errorDialog.setText(msg)
                errorDialog.exec_()

                return
                
        self.pattern = regexpPattern
        
    # end of setUpPattern
        
    # Search for all matches of the stored pattern in the target file, which is an XML test file.
    def search(self, fontFile, targetFile) :
        
        matchResults = []
        
        if self.pattern == "" :
            print "No valid search pattern"
            return matchResults
        
        print "Searching " + targetFile + " for '" + self.pattern + "'..."
        
        cpat = re.compile(self.pattern)  # compiled pattern
        
        # Read and parse the target file.
        try :
            e = et.parse(targetFile)
        except Exception as err :
            reportError("Could not search %s: %s" % (targetFile, str(err)))
            print "could not search " + targetFile ####
            return matchResults
            
        faceAndFont = makeFontAndFace(fontFile, 12)

        cnt = 0;
        for g in e.iterfind('testgroup') :
            groupLabel = g.get('label')
            #print "GROUP: " + groupLabel
            for t in g.iterfind('test') :
                testLabel = t.get('label')
                r = t.get('rtl')
                testRtl = True if r == 'True' else False
                d = t.find('string')
                if d is None : d = t.find('text')
                testString = d.text if d is not None else ""
                testComment = t.find('comment') or ""
                featDescrip = t.get('feats') or ""
                langCode = t.get('lang') or ""
                
                ###print testLabel
                
                jsonOutput = self.app.runGraphiteOverString(fontFile, faceAndFont, testString, 12, testRtl, {}, {}, 100)
                if jsonOutput != False :
                    glyphOutput = self._dataFromGlyphs(jsonOutput)
                    match = cpat.search(glyphOutput)
                else :
                    match = False
                    
                if match :
                    key = "[" + groupLabel + "] " + testLabel
                    matchResults.append((key, testString, testRtl, testComment, featDescrip, langCode))
                    print testLabel + " MATCHED"
                ###else :
                ###    print testLabel + " did not match"
                
                cnt = cnt + 1
                #if cnt > 25 : break;
            # end of for t loop
            
            #if cnt > 25 : break;
        # end of for g loop
        
        return matchResults

    # end of search
        
        
    def _singleGlyphPattern(self) :
        return "_[0-9]+"
            
    # Generate a data string corresponding to the glyph output
    # that can be matched against the reg-exp.
    def _dataFromGlyphs(self, json) :
        jsonOutput = json[0]["output"]
        result = ""
        for g in jsonOutput :
            result += "_" + str(g["gid"])
        return result
    
# end of GlyphPatternMatcher class


def asBool(txt) :
    if not txt : return False
    if txt.lower() == 'true' : return True
    if txt.isdigit() : return int(txt) != 0
    return False

# List of matched results
class MatchList(QtGui.QWidget) :

    def __init__(self, app, font, fname = None, parent = None) : # parent = Matcher
        super(MatchList, self).__init__(parent)
        self.noclick = False
        self.app = app
        self.font = font
        self.testFiles = []     # list of filenames, include paths
        self.currentFile = fname
        self.testGroups = [[]]    # data structure of groups and tests; for now there will be only one group
        self.fsets = {"\n" : None}
        self.comments = []
        self.fcount = 0
        self.header = None

        self.setActions(app)
        self.vbox = QtGui.QVBoxLayout()
        self.vbox.setContentsMargins(*Layout.buttonMargins)
        
        # test file control
        self.cbox1 = QtGui.QWidget(self)
        self.fhbox = QtGui.QHBoxLayout()
        self.fhbox.setContentsMargins(*Layout.buttonMargins)
        self.fhbox.setSpacing(Layout.buttonSpacing)    
        self.cbox1.setLayout(self.fhbox)
        self.fcombo = QtGui.QComboBox(self.cbox1)  # file combo box   
        self.fcombo.setToolTip('Choose test file')
        self.fhbox.addWidget(self.fcombo)
        self.fhbox.addSpacing(10)
        self.fabutton = QtGui.QToolButton(self.cbox1)
        self.fabutton.setIcon(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")))
        self.fabutton.setToolTip('Add test file')
        self.fabutton.clicked.connect(self.addFileClicked)
        self.fhbox.addWidget(self.fabutton)
        self.frbutton = QtGui.QToolButton(self.cbox1)
        self.frbutton.setIcon(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")))
        self.frbutton.setToolTip('Remove test file from list')
        self.frbutton.clicked.connect(self.delFileClicked)
        self.fhbox.addWidget(self.frbutton)
        self.vbox.addWidget(self.cbox1)
        
        self.liststack = QtGui.QStackedWidget(self)  # stack of lists of test items - for now there will be only one
        self.vbox.addWidget(self.liststack)

        self.fcombo.connect(QtCore.SIGNAL('currentIndexChanged(int)'), self.changeFileCombo)
        
        self.createOneGroup('matches')

        # list control
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

        self.addFile(fname, None, False)

    def setActions(self, app) :
        self.aEdit = QtGui.QAction(QtGui.QIcon.fromTheme('document-properties', QtGui.QIcon(":/images/document-properties.png")), "&Add Test ...", app)
        self.aEdit.setToolTip('Edit result')
        self.aEdit.triggered.connect(self.editClicked)
        self.aUpp = QtGui.QAction(QtGui.QIcon.fromTheme('go-up', QtGui.QIcon(":/images/go-up.png")), "Test &Up", app)
        self.aUpp.setToolTip("Move result up")
        self.aUpp.triggered.connect(self.upClicked)
        self.aDown = QtGui.QAction(QtGui.QIcon.fromTheme('go-down', QtGui.QIcon(":/images/go-down.png")), "Test &Down", app)
        self.aDown.setToolTip("Move result down")
        self.aDown.triggered.connect(self.downClicked)
        self.aSave = QtGui.QAction(QtGui.QIcon.fromTheme('document-save', QtGui.QIcon(":/images/document-save.png")), "&Save Tests", app)
        self.aSave.setToolTip('Save result list')
        self.aSave.triggered.connect(self.saveTestsClicked)
        self.aAdd = QtGui.QAction(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")), "&Add Test ...", app)
        self.aAdd.setToolTip('Add new result')
        self.aAdd.triggered.connect(self.addTestClicked)
        self.aDel = QtGui.QAction(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")), "&Delete Test", app)
        self.aDel.setToolTip('Delete result')
        self.aDel.triggered.connect(self.delTestClicked)

    def initResults(self, fname) :
         self.addGroup('matches')
        
    def loadTests(self, fname):
        print "loadTests - WHY ARE WE CALLING THIS METHOD?"
        
        # Assumes the file has been added to the UI.
        #for i in range(self.liststack.count()-1, -1, -1) :
        #    self.liststack.removeWidget(self.liststack.widget(i))
        ###self. - ???
        if not fname or not os.path.exists(fname) :
            # Create a new set of tests - these will be stored in a new file.
            self.initResults(fname)
            return
            
        try :
            e = et.parse(fname)
        except Exception as err:
            reportError("TestsFile %s: %s" % (fname, str(err)))
            return
        if e.getroot().tag == 'tests' :
            print "Can't find tests file " + fname
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
            
    def addFile(self, fname, index = None, savePrevious = True) :
        #print "addFile(" + fname + "," + str(savePrevious) + ")"
        basename = os.path.basename(fname)
        if index == None :
            index = len(self.testFiles)
            self.testFiles.append(fname)
            self.fcombo.addItem(basename)
        else :
            self.testFiles.insert(index, fname)
            self.fcombo.insertItem(index, basename)
        # TODO add file to configuration list
        self.changeFile(index)
        
    def changeFile(self, index) :
        #print "changeFile(" + str(index) + ")"
        
        # Save current set of tests.
        ##if self.currentFile != "" :
        ##    self.writeXML(self.currentFile)
        
        # Delete all the existing UI for the current test file.
        ###for i in range(self.liststack.count()-1, -1, -1) :
        ###    self.liststack.removeWidget(self.liststack.widget(i))
        
        # Load the new test file.
        ####self.loadTests(self.testFiles[index])
        self.currentFile = self.testFiles[index]
        
    def createOneGroup(self, name, index = None, comment = "") :
        listWidget = QtGui.QListWidget() # create a test list widget for this group
        listWidget.itemDoubleClicked.connect(self.runTest)
        listWidget.itemClicked.connect(self.loadTest)
        self.liststack.addWidget(listWidget)        
        return listWidget
        
    def clearTests(self, l = None) :
        # Delete all the existing UI for the current test file.
        if not l : l = self.liststack.currentWidget()
        groupIndex = self.liststack.indexOf(l)
        print self.testGroups[groupIndex]
        while len(self.testGroups[groupIndex]) > 0 :
            self.testGroups[groupIndex].pop(0)
            self.liststack.widget(groupIndex).takeItem(0)

    def appendTest(self, t, l = None) :
        if not l : l = self.liststack.currentWidget()
        groupIndex = self.liststack.indexOf(l) # should always be 0
        self.testGroups[groupIndex].append(t)
        w = QtGui.QListWidgetItem(t.name or "", l)
        if t.comment :
            w.setToolTip(t.comment)
        w.setBackground(QtGui.QBrush(t.background))

    def editTest(self, testindex) :
        groupindex = self.liststack.currentIndex() # for now, should be 0
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
        #print "writeXML(" + fname + ")"
        
        print "MatchList::writeXML(" + fname + ")"
        
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
    def changeFileCombo(self, index) :
        #print "changeFileCombo(" + str(index) + ")"
        self.changeFile(index)

    def addFileClicked(self) :
        # This dialog allows specifying a file that does not exist.
        qdialog = QtGui.QFileDialog()
        qdialog.setFileMode(QtGui.QFileDialog.AnyFile)
        qdialog.setViewMode(QtGui.QFileDialog.Detail)
        qdialog.setNameFilter('XML files (*.xml)')
        if qdialog.exec_() :
            selected = qdialog.selectedFiles()
            fname = selected[0]
            if fname[-4:] != ".xml" :
                fname += ".xml"
            index = self.fcombo.currentIndex() + 1
            self.addFile(fname, index)
            self.fcombo.setCurrentIndex(self.fcombo.currentIndex() + 1)
        
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
        
    @QtCore.Slot(int)
    def changeGroupCombo(self, index) :
        #print "changeGroupCombo(" + str(index) + ")"
        self.liststack.setCurrentIndex(index)
        if index < len(self.comments) :
            self.gcombo.setToolTip(self.comments[index])

    def editClicked(self) :
        self.editTest(self.liststack.currentWidget().currentRow())

    def addTestClicked(self, t = None) :
        groupIndex = self.liststack.currentIndex()
        if not t : t = Test('', self.app.feats[None].fval, rtl = configintval(self.app.config, 'main', 'defaultrtl'))
        self.appendTest(t)
        res = self.editTest(len(self.testGroups[groupIndex]) - 1)
        if not t.name or not res :
            self.testGroups[groupIndex].pop()
            self.liststack.widget(groupIndex).takeItem(len(self.testGroups))

    def delTestClicked(self) :
        groupindex = self.liststack.currentIndex()
        testindex = self.liststack.widget(groupindex).currentRow()
        self.testGroups[groupindex].pop(testindex)
        self.liststack.widget(groupindex).takeItem(testindex)

    def saveTestsClicked(self) :
        self.saveTests()
        
    def saveTests(self) :
        print "saveTests - not yet implemented"
        #tname = configval(self.app.config, 'main', 'testsfile')
        #if tname : self.writeXML(tname)
        #if self.currentFile :
        #    self.writeXML(self.currentFile)

    def upClicked(self) :
        l = self.liststack.currentWidget()
        groupindex = self.liststack.currentIndex()
        testindex = l.currentRow()
        if testindex > 0 :
            self.testGroups[groupindex].insert(testindex - 1, self.testGroups[groupindex].pop(testindex))
            l.insertItem(testindex - 1, l.takeItem(testindex))
            l.setCurrentRow(testindex - 1)

    def downClicked(self) :
        l = self.liststack.currentWidget()
        groupindex = self.liststack.currentIndex()
        testindex = l.currentRow()
        if testindex < l.count() - 1 :
            self.testGroups[groupindex].insert(testindex + 1, self.testGroups[groupindex].pop(testindex))
            l.insertItem(testindex + 1, l.takeItem(testindex))
            l.setCurrentRow(testindex + 1)

    def loadTest(self, item) :
        if not self.noclick :
            groupIndex = self.liststack.currentIndex()
            testIndex = self.liststack.currentWidget().currentRow()
            self.app.setRun(self.testGroups[groupIndex][testIndex])
        else :
            # this is the side-effect of a double-click: ignore it
            self.noclick = False

    def runTest(self, item) :
        # event sends clicked first so no need to select
        self.app.runClicked()
        self.noclick = True  # because itemClick event will happen again--ignore it

    def findStyleClass(self, t) :
        k = " ".join(map(lambda x: x + "=" + str(t.feats[x]), sorted(t.feats.keys())))
        k += "\n" + (t.lang or "")
        if k not in self.fsets :
            self.fcount += 1
            self.fsets[k] = "fset%d" % self.fcount
        return self.fsets[k]

# end of class MatchList



class Matcher(QtGui.QTabWidget) :
    
    def __init__(self, fontFile, font, parent = None, xmlFile = None) :   # parent = app
        super(Matcher, self).__init__(parent)
        self.fontFile = fontFile
        self.font = font
        self.app = parent
        self.xmlFile = xmlFile
        self.layout = QtGui.QVBoxLayout(self)
        self.setActions(self.app)
        self.initializeLayout(xmlFile)
        
    def setActions(self, app) :
        self.aSearchGo = QtGui.QAction(QtGui.QIcon.fromTheme('edit-find', QtGui.QIcon(":/images/find-normal.png")), "", self)
        self.aSearchGo.setToolTip("Search for pattern in specified test file")
        self.aSearchGo.triggered.connect(self.searchClicked)
        
    # end of setActions
        
    def initializeLayout(self, xmlFile) :
        vsplitter = QtGui.QSplitter()  # allows sizing of results view
        vsplitter.setOrientation(QtCore.Qt.Vertical)
        vsplitter.setContentsMargins(0, 0, 0, 0)
        vsplitter.setHandleWidth(4)
        self.layout.addWidget(vsplitter)
        
        self.widget = QtGui.QWidget(vsplitter)
        vbox = QtGui.QVBoxLayout(self.widget) # MatchList + input control
        vbox.setContentsMargins(*Layout.buttonMargins)
        vbox.setSpacing(Layout.buttonSpacing)
        
        self.patternEdit = QtGui.QPlainTextEdit(self.widget)
        self.patternEdit.setMaximumHeight(Layout.runEditHeight)
        vbox.addWidget(self.patternEdit)
        
        hbox = QtGui.QHBoxLayout()  # just in case we want to add more buttons here
        vbox.addLayout(hbox)
        hbox.addStretch()
        hbox.setContentsMargins(*Layout.buttonMargins)
        hbox.setSpacing(Layout.buttonSpacing)
        searchGo = QtGui.QToolButton(self.widget)
        searchGo.setDefaultAction(self.aSearchGo)
        hbox.addWidget(searchGo)
    
        self.matchList = MatchList(self.app, self.font, xmlFile, self)
        #self.matchList.itemClicked.connect(self.itemClicked)
        vbox.addWidget(self.matchList)

        # line below MatchList
        line = QtGui.QFrame(self.widget)
        line.setFrameStyle(QtGui.QFrame.HLine | QtGui.QFrame.Raised)
        line.setLineWidth(2)
        vbox.addWidget(line)
        vbox.addSpacing(2)
        
        # input control
        self.runEdit = QtGui.QPlainTextEdit(self.widget)
        self.runEdit.setMaximumHeight(Layout.runEditHeight)
        vbox.addWidget(self.runEdit)
        
        # control buttons
        hbox = QtGui.QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.setContentsMargins(*Layout.buttonMargins)
        hbox.setSpacing(Layout.buttonSpacing)
        runGo = QtGui.QToolButton(self.widget)
        #runGo.setDefaultAction(aRunGo)
        hbox.addWidget(runGo)
        hbox.addStretch()
        runRtl = QtGui.QCheckBox("RTL", self.widget)
        runRtl.setChecked(True if configintval(self.app.config, 'main', 'defaultrtl') else False)
        runRtl.setToolTip("Process text right to left")
        hbox.addWidget(runRtl)
        runFeats = QtGui.QToolButton(self.widget)
        #runFeats.setDefaultAction(aRunFeats)
        hbox.addWidget(runFeats)
        runAdd = QtGui.QToolButton(self.widget)
        #runAdd.setDefaultAction(aRunAdd)
        hbox.addWidget(runAdd)
    
        # test output
        self.run = Run(runRtl.isChecked())
        self.runView = RunView(self.font)
        self.runView.gview.resize(self.runView.gview.width(), self.font.pixrect.height() + 5)
        vsplitter.addWidget(self.runView.gview)
        
    # end of initializeLayout
    
    def searchClicked(self) :
        pattern = self.patternEdit.toPlainText()
        print "Searching for: '" + pattern + "'"
        
        if pattern != "" :
            # Populate the MatchList with the results.
            self.matchList.clearTests()
            
            patternMatcher = GlyphPatternMatcher(self.app, self)
            patternMatcher.setUpPattern(pattern, self.font)
            matchResults = patternMatcher.search(self.fontFile, self.app.config.get('main', 'testsfile'))
            
            ##print matchResults
            
            for data in matchResults :
                print data[0]
                matchKey = data[0]
                matchText = data[1]
                matchRtl = data[2]
                matchComment = data[3]
                matchFeats = data[4]
                matchLang = data[5]
                
                te = Test(text = matchText, feats = matchFeats, lang = matchLang, rtl = matchRtl, name = matchKey, comment = matchComment)
                self.matchList.appendTest(te)
        
    # end of searchClicked
       
    
# end of class Matcher
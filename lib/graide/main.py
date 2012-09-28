#!/usr/bin/python

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

from graide.font import Font
from graide.run import Run
from graide.attribview import AttribView
from graide.fontview import FontView
from graide.runview import RunView
from graide.passes import PassesView
from graide.gdx import Gdx
from graide.filetabs import FileTabs
from graide.utils import buildGraphite, configval, configintval, registerErrorLog, findgrcompiler, as_entities
from graide.layout import Layout
from graide.rungraphite import runGraphite
from graide.featureselector import make_FeaturesMap, FeatureDialog
from graide.testlist import TestList
from graide.test import Test
from graide.classes import Classes
from graide.config import ConfigDialog
from graide.debug import ContextToolButton, DebugMenu
from graide.errors import Errors
from graide.waterfall import WaterfallDialog
from graide.pyresources import qInitResources, qCleanupResources
from graide.posedit import PosEdit, PosView
from PySide import QtCore, QtGui
from tempfile import NamedTemporaryFile, TemporaryFile
from ConfigParser import RawConfigParser
import json, os, sys, re

class MainWindow(QtGui.QMainWindow) :

    def __init__(self, config, configfile, jsonfile) :
        super(MainWindow, self).__init__()
        self.rules = None
        self.runfile = None
        self.runloaded = False
        self.fDialog = None
        self.config = config
        self.configfile = configfile
        self.currFeats = None
        self.currLang = None
        self.currWidth = 100
        self.font = Font()
        self.apname = None
        
        if (self.configfile == None) :
            self.setWindowTitle("Graide")
        else :
        	self.setWindowTitle("[" + self.configfile + "] - Graide")

        #import pdb; pdb.set_trace()  # debug
        
        #if sys.platform == 'darwin' :
        #    QtGui.QIcon.setThemeSearchPaths(['/opt/local/share/icons', ':/icons'])
        #    QtGui.QIcon.setThemeName('Tango')
        app = QtCore.QCoreApplication.instance()
        appicon = QtGui.QIcon(':/images/graide_logo_256px.png')
        appicon.addFile(':/images/graide_logo_96px.png')
        appicon.addFile(':/images/graide logo.svg')
        app.setWindowIcon(appicon)

        findgrcompiler()
        for s in ('main', 'build', 'ui') :
            if not config.has_section(s) :
                config.add_section(s)

        if config.has_option('main', 'font') :
            self.loadFont(config.get('main', 'font'))

        if jsonfile :
            f = file(jsonfile)
            self.json = json.load(f)
            f.close()
        else :
            self.json = None

        if config.has_option('main', 'testsfile') :
            self.testsfile = config.get('main', 'testsfile')
        else :
            self.testsfile = None

        if config.has_option('ui', 'posglyphsize') :
            self.setposglyphsize(configintval(config, 'ui', 'posglyphsize'))

        self.setActions()
        self.setupUi()
        self.setMenus()
        registerErrorLog(self)

        mainfile = configval(config, 'build', 'gdlfile')
        if mainfile :
            self.tabEdit.selectLine(mainfile, -1)

    def loadFont(self, fontname) :
        if self.config.has_option('main', 'size') :
            fontsize = self.config.getint('main', 'size')
        else :
            fontsize = 40
        self.fontfile = str(fontname)
        self.fonttime = os.stat(fontname).st_ctime
        self.font.loadFont(self.fontfile, fontsize)
        self.feats = make_FeaturesMap(self.fontfile)
        
        # Look for the GDX file with the font; if it's not there, look in the current directory.
        self.gdxfile = os.path.splitext(self.fontfile)[0] + '.gdx'
        if not os.path.exists(self.gdxfile) :
        	basename = os.path.basename(fontname)
        	self.gdxfile = os.path.splitext(basename)[0] + '.gdx'
        
        self.loadAP(configval(self.config, 'main', 'ap'))
        if hasattr(self, 'tab_font') :
            if self.tab_font :
                self.tab_font.resizeRowsToContents()
                self.tab_font.resizeColumnsToContents()
            else :
                self.tab_classes.classUpdated.disconnect(self.font.classUpdated)
                i = self.tabResults.currentIndex()
                self.tab_font = FontView(self.font)
                self.tab_font.changeGlyph.connect(self.glyphSelected)
                self.tabResults.insertTab(0, self.tab_font, "Font")
                self.tabResults.setCurrentIndex(i)
                self.tab_classes.classSelected.connect(self.font.classSelected)
            self.tab_classes.loadFont(self.font)
        if hasattr(self, 'runView') :
            self.runView.gview.setFixedHeight(self.font.pixrect.height())

    def loadAP(self, apname) :
        self.apname = apname
        if apname and os.path.exists(apname) :
            self.font.loadAP(apname)
        else :
            self.font.loadEmptyGlyphs()
        if os.path.exists(self.gdxfile) :
            self.gdx = Gdx()
            self.gdx.readfile(self.gdxfile, self.font, configval(self.config, 'build', 'makegdlfile'),
                                ronly = configintval(self.config, 'build', 'apronly'))
        else :
            self.gdx = None
        if hasattr(self, 'tab_classes') : self.tab_classes.loadFont(self.font)

    def loadTests(self, testsname) :
        self.testsfile = testsname
        if self.tabTest :
            self.tabTest.loadTests(testsname)

    def closeEvent(self, event) :
        if self.rules :
            self.rules.close()
        event.accept()

    def setActions(self) :
        self.aRunGo = QtGui.QAction(QtGui.QIcon.fromTheme("media-playback-start", QtGui.QIcon(":/images/media-playback-start.png")), "&Run Test", self)
        self.aRunGo.setToolTip("Run text string after rebuild")
        self.aRunGo.triggered.connect(self.runClicked)
        self.aWater = QtGui.QAction(QtGui.QIcon.fromTheme("document-preview", QtGui.QIcon(":/images/document-preview.png")), "&Waterfall ...", self)
        self.aWater.setToolTip('Display run as a waterfall')
        self.aWater.triggered.connect(self.doWaterfall)
        self.aRunFeats = QtGui.QAction(QtGui.QIcon.fromTheme("view-list-details", QtGui.QIcon(":/images/view-list-details.png")), "Set &Features ...", self)
        self.aRunFeats.triggered.connect(self.featuresClicked)
        self.aRunFeats.setToolTip("Edit features of test run")
        self.aRunAdd = QtGui.QAction(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")), "Test from &Run ...", self)
        self.aRunAdd.setToolTip("Add run to tests list under a new name")
        self.aRunAdd.triggered.connect(self.runAddClicked)

        self.aSaveAP = QtGui.QAction(QtGui.QIcon.fromTheme('document-save', QtGui.QIcon(":/images/document-save.png")), "Save &APs", self)
        self.aSaveAP.triggered.connect(self.saveAP)
        self.aSaveAP.setToolTip('Save AP Database')

        self.aCfg = QtGui.QAction(QtGui.QIcon.fromTheme("configure", QtGui.QIcon(":/images/configure.png")), "&Configure Project ...", self)
        self.aCfg.setToolTip("Configure project")
        self.aCfg.triggered.connect(self.configClicked)
        self.aCfgOpen = QtGui.QAction(QtGui.QIcon.fromTheme("document-open", QtGui.QIcon(":/images/document-open.png")), "&Open Project ...", self)
        self.aCfgOpen.setToolTip("Open existing project")
        self.aCfgOpen.triggered.connect(self.configOpenClicked)
        self.aCfgNew = QtGui.QAction(QtGui.QIcon.fromTheme("document-new", QtGui.QIcon(":/images/document-new.png")), "&New Project ...", self)
        self.aCfgNew.setToolTip("Create new project")
        self.aCfgNew.triggered.connect(self.configNewClicked)

        self.aHAbout = QtGui.QAction("&About", self)
        self.aHAbout.triggered.connect(self.helpAbout)

    def setupUi(self) :
        qInitResources()
        self.resize(994, 696)
        self.centralwidget = QtGui.QWidget(self)
        self.verticalLayout = QtGui.QHBoxLayout(self.centralwidget)
        self.hsplitter = QtGui.QSplitter(self.centralwidget)
        self.hsplitter.setOrientation(QtCore.Qt.Horizontal)
        self.hsplitter.setHandleWidth(4)
        self.verticalLayout.addWidget(self.hsplitter)

        self.tabInfo = QtGui.QTabWidget(self.hsplitter)
        self.widget = QtGui.QWidget(self.hsplitter)
        self.setwidgetstretch(self.widget, 55, 100)
        self.topLayout = QtGui.QVBoxLayout(self.widget)
        self.topLayout.setContentsMargins(*Layout.buttonMargins)
        self.vsplitter = QtGui.QSplitter(self.widget)
        self.vsplitter.setOrientation(QtCore.Qt.Vertical)
        self.vsplitter.setHandleWidth(2)
        self.topLayout.addWidget(self.vsplitter)

        self.ui_tests(self.tabInfo)
        self.ui_left(self.tabInfo)
        self.ui_fileEdits(self.vsplitter)

        self.tabResults = QtGui.QTabWidget(self.vsplitter)
        self.ui_bottom(self.tabResults)

        if self.config.has_section('window') :
            self.resize(configintval(self.config, 'window', 'mainwidth'), configintval(self.config, 'window', 'mainheight'))
            self.hsplitter.restoreState(QtCore.QByteArray.fromBase64(configval(self.config, 'window', 'hsplitter')))
            self.vsplitter.restoreState(QtCore.QByteArray.fromBase64(configval(self.config, 'window', 'vsplitter')))

    def ui_tests(self, parent) :
        self.setwidgetstretch(self.tabInfo, 30, 100)
        self.test_splitter = QtGui.QSplitter()
        self.test_splitter.setOrientation(QtCore.Qt.Vertical)
        self.test_splitter.setContentsMargins(0, 0, 0, 0)
        self.test_splitter.setHandleWidth(4)
        self.test_widget = QtGui.QWidget(self.test_splitter)
        self.test_vbox = QtGui.QVBoxLayout(self.test_widget)
        self.test_vbox.setContentsMargins(*Layout.buttonMargins)
        self.test_vbox.setSpacing(Layout.buttonSpacing)
        self.tabTest = TestList(self, self.testsfile, parent = self.test_widget)
        self.test_vbox.addWidget(self.tabTest)
        self.test_vbox.addSpacing(2)
        self.test_line = QtGui.QFrame(self.test_widget)
        self.test_line.setFrameStyle(QtGui.QFrame.HLine | QtGui.QFrame.Raised)
        self.test_line.setLineWidth(2)
        self.test_vbox.addWidget(self.test_line)
        self.test_vbox.addSpacing(2)
        self.runEdit = QtGui.QPlainTextEdit(self.test_widget)
        self.runEdit.setMaximumHeight(Layout.runEditHeight)
        self.test_vbox.addWidget(self.runEdit)
        self.test_hbox = QtGui.QHBoxLayout()
        self.test_vbox.addLayout(self.test_hbox)
        self.test_hbox.setContentsMargins(*Layout.buttonMargins)
        self.test_hbox.setSpacing(Layout.buttonSpacing)
        self.runGo = QtGui.QToolButton(self.test_widget)
        self.runGo.setDefaultAction(self.aRunGo)
        self.test_hbox.addWidget(self.runGo)
        self.runWater = QtGui.QToolButton(self.test_widget)
        self.runWater.setDefaultAction(self.aWater)
        self.test_hbox.addWidget(self.runWater)
        self.test_hbox.addStretch()
        self.runRtl = QtGui.QCheckBox("RTL", self.test_widget)
        self.runRtl.setChecked(True if configintval(self.config, 'main', 'defaultrtl') else False)
        self.runRtl.setToolTip("Process text right to left")
        self.test_hbox.addWidget(self.runRtl)
        self.runFeats = QtGui.QToolButton(self.test_widget)
        self.runFeats.setDefaultAction(self.aRunFeats)
        self.test_hbox.addWidget(self.runFeats)
        self.runAdd = QtGui.QToolButton(self.test_widget)
        self.runAdd.setDefaultAction(self.aRunAdd)
        self.test_hbox.addWidget(self.runAdd)
        self.run = Run()
        self.runView = RunView(self.font)
        self.runView.gview.resize(self.runView.gview.width(), self.font.pixrect.height() + 5)
        self.test_splitter.addWidget(self.runView.gview)
        parent.addTab(self.test_splitter, "Tests")

    def ui_left(self, parent) :
        # glyph, slot, classes, positions
        self.tab_glyph = QtGui.QWidget()
        self.glyph_vb = QtGui.QVBoxLayout(self.tab_glyph)
        self.glyph_vb.setContentsMargins(*Layout.buttonMargins)
        self.glyph_vb.setSpacing(Layout.buttonSpacing)
        self.glyphAttrib = AttribView()
        self.glyph_vb.addWidget(self.glyphAttrib)
        self.glyph_bbox = QtGui.QWidget(self.tab_glyph)
        self.glyph_hb = QtGui.QHBoxLayout(self.glyph_bbox)
        self.glyph_hb.setContentsMargins(*Layout.buttonMargins)
        self.glyph_hb.setSpacing(Layout.buttonSpacing)
        self.glyph_hb.insertStretch(0)
        if self.apname :
            self.glyph_saveAP = QtGui.QToolButton(self.glyph_bbox)
            self.glyph_saveAP.setDefaultAction(self.aSaveAP)
            self.glyph_hb.addWidget(self.glyph_saveAP)
        self.glyph_addPoint = QtGui.QToolButton(self.glyph_bbox)
        self.glyph_addPoint.setIcon(QtGui.QIcon.fromTheme('character-set', QtGui.QIcon(":/images/character-set.png")))
        self.glyph_addPoint.setText(u'\u2022')
        self.glyph_addPoint.clicked.connect(self.glyphAddPoint)
        self.glyph_addPoint.setToolTip('Add attachment point to glyph')
        self.glyph_hb.addWidget(self.glyph_addPoint)
        self.glyph_addProperty = QtGui.QToolButton(self.glyph_bbox)
        self.glyph_addProperty.setIcon(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")))
        self.glyph_addProperty.clicked.connect(self.glyphAddProperty)
        self.glyph_addProperty.setToolTip('Add property to glyph')
        self.glyph_hb.addWidget(self.glyph_addProperty)
        self.glyph_remove = QtGui.QToolButton(self.glyph_bbox)
        self.glyph_remove.setIcon(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")))
        self.glyph_remove.clicked.connect(self.glyphRemoveProperty)
        self.glyph_remove.setToolTip('Remove property from glyph')
        self.glyph_hb.addWidget(self.glyph_remove)
        self.glyph_vb.addWidget(self.glyph_bbox)
        self.tabInfo.addTab(self.tab_glyph, "Glyph")
        self.tab_slot = AttribView()
        self.tabInfo.addTab(self.tab_slot, "Slot")
        self.tab_classes = Classes(self.font, self, configval(self.config, 'build', 'makegdlfile') if configval(self.config, 'main', 'ap') else None)
        self.tab_classes.classUpdated.connect(self.font.classUpdated)
        self.tabInfo.addTab(self.tab_classes, "Classes")
        self.tab_poses = PosEdit(self.font, self)
        self.tabInfo.addTab(self.tab_poses, "Positions")

    def ui_fileEdits(self, parent) :
        # file edit view
        self.tabEdit = FileTabs(self.config, self, parent)
        self.setwidgetstretch(self.tabEdit, 100, 50)
        self.tabEdit.setTabsClosable(True)

    def ui_bottom(self, parent) :
        # bottom pane
        self.setwidgetstretch(self.tabResults, 100, 45)
        parent.setTabPosition(QtGui.QTabWidget.South)
        self.cfg_widget = QtGui.QWidget()
        self.cfg_hbox = QtGui.QHBoxLayout(self.cfg_widget)
        self.cfg_hbox.setContentsMargins(*Layout.buttonMargins)
        self.cfg_hbox.setSpacing(Layout.buttonSpacing)
        self.cfg_button = ContextToolButton(self.cfg_widget)
        self.cfg_button.setDefaultAction(self.aCfg)
        self.cfg_button.rightClick.connect(self.debugClicked)
        self.cfg_hbox.addWidget(self.cfg_button)
        self.cfg_open = QtGui.QToolButton(self.cfg_widget)
        self.cfg_open.setDefaultAction(self.aCfgOpen)
        self.cfg_hbox.addWidget(self.cfg_open)
        self.cfg_new = QtGui.QToolButton(self.cfg_widget)
        self.cfg_new.setDefaultAction(self.aCfgNew)
        self.cfg_hbox.addWidget(self.cfg_new)
        parent.setCornerWidget(self.cfg_widget)

        # font tab
        if self.font.isRead() :
            self.tab_font = FontView(self.font)
            self.tab_font.changeGlyph.connect(self.glyphSelected)
            self.tab_classes.classSelected.connect(self.tab_font.classSelected)
        else :
            self.tab_font = None
        self.tabResults.addTab(self.tab_font, "Font")

        # errors tab
        self.tab_errors = Errors()
        self.tabResults.addTab(self.tab_errors, "Errors")
        self.tab_errors.errorSelected.connect(self.tabEdit.selectLine)

        # passes tab
        self.tab_passes = PassesView()
        self.tab_passes.slotSelected.connect(self.slotSelected)
        self.tab_passes.glyphSelected.connect(self.glyphAttrib.changeData)
        self.tab_passes.rowActivated.connect(self.rulesSelected)
        self.tabResults.addTab(self.tab_passes, "Passes")
        if self.json :
            self.run.addslots(self.json['output'])
            self.runView.loadrun(self.run, self.font)
            self.runView.slotSelected.connect(self.slotSelected)
            self.runView.glyphSelected.connect(self.glyphAttrib.changeData)
            self.tab_passes.loadResults(self.font, self.json, self.gdx)
            istr = unicode(map(lambda x:unichr(x['unicode']), self.json['chars']))
            self.runEdit.setPlainText(istr.encode('raw_unicode_escape'))
            self.tab_passes.setTopToolTip(istr.encode('raw_unicode_escape'))
            self.runloaded = True
        self.setCentralWidget(self.centralwidget)

        # rules tab
        self.tab_rules = PassesView()
        self.tab_rules.slotSelected.connect(self.slotSelected)
        self.tab_rules.glyphSelected.connect(self.glyphAttrib.changeData)
        self.tab_rules.rowActivated.connect(self.ruleSelected)
        self.tabResults.addTab(self.tab_rules, "Rules")

        # positioning tab
        self.tab_pos = PosView(self)
        if hasattr(self, 'tab_poses') : self.tab_poses.setView(self.tab_pos)
        self.tabResults.addTab(self.tab_pos, "Positions")

    def setMenus(self) :
        filemenu = self.menuBar().addMenu("&File")
        filemenu.addAction(self.tabEdit.aAdd)
        filemenu.addAction(self.tabEdit.aSave)
        filemenu.addAction(self.tabEdit.aBuild)
        filemenu.addAction('&Reset Names', self.resetNames)

        projectmenu = self.menuBar().addMenu("&Project")
        projectmenu.addAction(self.aCfg)
        projectmenu.addAction(self.aCfgOpen)
        projectmenu.addAction(self.aCfgNew)
        projectmenu.addAction(self.aSaveAP)

        testmenu = self.menuBar().addMenu("&Tests")
        testmenu.addAction(self.aRunGo)
        testmenu.addAction(self.aWater)
        testmenu.addAction(self.aRunFeats)
        testmenu.addAction(self.aRunAdd)
        testmenu.addSeparator()
        testmenu.addAction(self.tabTest.aGAdd)
        testmenu.addAction(self.tabTest.aGDel)
        testmenu.addSeparator()
        testmenu.addAction(self.tabTest.aAdd)
        testmenu.addAction(self.tabTest.aEdit)
        testmenu.addAction(self.tabTest.aSave)
        testmenu.addAction(self.tabTest.aDel)
        testmenu.addAction(self.tabTest.aUpp)
        testmenu.addAction(self.tabTest.aDown)

        helpmenu = self.menuBar().addMenu("&Help")
        helpmenu.addAction(self.aHAbout)

    def helpAbout(self) :
        QtGui.QMessageBox.about(self, "Graide", """GRAphite Integrated Development Environment

An environment for the creation and debugging of Graphite fonts.

Copyright 2012 SIL International and M. Hosken""")

    def setwidgetstretch(self, widget, hori, vert) :
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        if hori != 100 : sizePolicy.setHorizontalStretch(hori)
        if vert != 100 : sizePolicy.setVerticalStretch(vert)
        sizePolicy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
        size = self.size()
        widget.resize(QtCore.QSize(size.width() * hori / 100, size.height() * vert / 100))
        widget.setSizePolicy(sizePolicy)

    def closeEvent(self, event) :
        if not self.config.has_section('window') :
            self.config.add_section('window')
        s = self.size()
        self.config.set('window', 'mainwidth', str(s.width()))
        self.config.set('window', 'mainheight', str(s.height()))
        self.config.set('window', 'vsplitter', self.vsplitter.saveState().toBase64())
        self.config.set('window', 'hsplitter', self.hsplitter.saveState().toBase64())
        if self.testsfile :
            self.tabTest.writeXML(self.testsfile)
        if self.configfile :
            try :
                f = file(self.configfile, "w")
                self.config.write(f)
                f.close()
            except :
                pass
        self.tabEdit.writeIfModified()
        self.saveAP()
        qCleanupResources()

    def glyphSelected(self, data, model) :
        self.glyphAttrib.changeData(data, model)
        self.tabInfo.setCurrentWidget(self.tab_glyph)

    def slotSelected(self, data, model) :
        self.tab_slot.changeData(data, model)
        if self.tabInfo.currentWidget() is not self.tab_glyph :
            self.tabInfo.setCurrentWidget(self.tab_slot)

    def rulesSelected(self, row, view, passview) :
        if row == 0 : return
        self.tab_rules.index = row - 1
        if passview.rules[row] is not None :
            self.tab_rules.loadRules(self.font, passview.rules[row], passview.views[row-1].run, self.gdx)
            ruleLabel = "Rules: pass %d" % row
            self.tabResults.setTabText(3, ruleLabel)
            self.tabResults.setCurrentWidget(self.tab_rules)
        passview.selectRow(row)

    def rulesclosed(self, dialog) :
        self.ruleView.slotSelected.disconnect()
        self.ruleView.glyphSelected.disconnect()
        self.ruleView = None

    def ruleSelected(self, row, view, passview) :
        if self.gdx and hasattr(view.run, 'passindex') :
            rule = self.gdx.passes[view.run.passindex][view.run.ruleindex]
            self.selectLine(rule.srcfile, rule.srcline)

    def posSelected(self) :
        self.tabResults.setCurrentWidget(self.tab_pos)

    def selectLine(self, fname = None, srcline = -1) :
        if not fname :
            fname = configval(self.config, 'build', 'gdlfile')
        self.tabEdit.selectLine(fname, srcline)

    def setRun(self, test) :
        self.runRtl.setChecked(True if test.rtl else False)
        if configintval(self.config, 'ui', 'entities') :
            t = as_entities(test.text)
        else :
            t = test.text
        self.runEdit.setPlainText(t)
        self.currFeats = dict(test.feats)
        self.currLang = test.lang
        self.currWidth = test.width
        self.runView.clear()

    def buildClicked(self) :
        self.tabEdit.writeIfModified()
        self.tab_errors.clear()
        errfile = TemporaryFile(mode="w+")
        res = buildGraphite(self.config, self, self.font, self.fontfile, errfile)
        if res :
            errfile.seek(0)
            for l in errfile.readlines() : self.tab_errors.addItem(l.strip())
        self.tab_errors.addGdlErrors('gdlerr.txt')
        if res :
            self.tabResults.setCurrentWidget(self.tab_errors)
        self.loadAP(self.apname)
        self.feats = make_FeaturesMap(self.fontfile)
        return True

    def runClicked(self) :
        if self.tabEdit.writeIfModified() and not self.buildClicked() : return
        if os.stat(self.fontfile).st_ctime > self.fonttime :
            self.loadFont(self.fontfile)
        text = re.sub(r'\\u([0-9A-Fa-f]{4})|\\U([0-9A-Fa-f]{5,8})', \
                lambda m:unichr(int(m.group(1) or m.group(2), 16)), self.runEdit.toPlainText())
        if not text : return
        if not self.currFeats and self.currLang not in self.feats :
            if None not in self.feats :    # not a graphite font, try to build
                self.buildClicked()
                if self.currLang not in self.feats :
                    if None not in self.feats :     # build failed do nothing.
                        self.tab_errors.addError("Can't run test on a non-Graphite font")
                        self.tabResults.setCurrentWidget(self.tab_errors)
                        return
                    else :
                        self.currLang = None
            else :
                self.currLang = None
        runfile = NamedTemporaryFile(mode="w+")
        runname = runfile.name
        runfile.close()
        runGraphite(self.fontfile, text, runname, size = self.font.size, rtl = self.runRtl.isChecked(),
            feats = self.currFeats or self.feats[self.currLang].fval, lang = self.currLang, expand = self.currWidth)
        runfile = open(runname)
        self.json = json.load(runfile)
        if isinstance(self.json, dict) : self.json = [self.json]
        runfile.close()
        os.unlink(runname)
        self.run = Run()
        self.run.addslots(self.json[-1]['output'])
        self.runView.loadrun(self.run, self.font, resize = False)
        if not self.runloaded :
            try :
                self.runView.slotSelected.connect(self.slotSelected)
                self.runView.glyphSelected.connect(self.glyphAttrib.changeData)
                self.runloaded = True
            except :
                print "Selection connection failed"
        self.tab_passes.loadResults(self.font, self.json, self.gdx)
        self.tab_passes.setTopToolTip(self.runEdit.toPlainText())
        self.tabResults.setCurrentWidget(self.tab_passes)

    def doWaterfall(self) :
        self.runClicked()
        if self.config.has_option('ui', 'waterfall') :
            sizes = map(int, config.get('ui', 'waterfall').split(' '))
        else :
            sizes = None
        if self.run :
            w = WaterfallDialog(self.font, self.run, sizes = sizes)
            w.exec_()

    def runAddClicked(self) :
        text = self.runEdit.toPlainText()
        if not text : return
        test = Test(text, self.currFeats or {}, self.currLang, self.runRtl.isChecked())
        self.tabTest.addClicked(test)

    def featuresClicked(self) :
        if self.font :
            fDialog = FeatureDialog(self)
            fDialog.set_feats(self.feats[self.currLang], self.currFeats, lang = self.currLang, width = self.currWidth)
            if fDialog.exec_() :
                self.currFeats = fDialog.get_feats()
                self.currLang = fDialog.get_lang()
                self.currWidth = fDialog.get_width()

    # called from utils
    def updateFileEdit(self, fname) :
        self.tabEdit.updateFileEdit(fname)

    def propDialog(self, name) :
        d = QtGui.QDialog(self)
        d.setWindowTitle(name)
        g = QtGui.QGridLayout()
        d.setLayout(g)
        n = QtGui.QLineEdit()
        g.addWidget(QtGui.QLabel(name + ' Name:'), 0, 0)
        g.addWidget(n, 0, 1)
        v = QtGui.QLineEdit()
        g.addWidget(QtGui.QLabel('Value:'), 1, 0)
        g.addWidget(v, 1, 1)
        o = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        o.accepted.connect(d.accept)
        o.rejected.connect(d.reject)
        g.addWidget(o, 2, 0, 1, 2)
        if d.exec_() :
            return (n.text(), v.text())
        else :
            return (None, None)

    def glyphAddPoint(self) :
        (n, v) = self.propDialog('Point')
        if n :
            glyph = self.glyphAttrib.data
            glyph.setpoint(n, v)
            self.glyphAttrib.changeData(glyph, None)

    def glyphAddProperty(self) :
        (n, v) = self.propDialog('Property')
        if n :
            glyph = self.glyphAttrib.data
            glyph.setgdlproperty(n, v)
            self.glyphAttrib.changeData(glyph, None)

    def glyphRemoveProperty(self) :
        self.glyphAttrib.removeCurrent()

    def saveAP(self) :
        if self.apname and not configintval(self.config, 'build', 'apronly') :
            self.font.saveAP(self.apname, configval(self.config, 'build', 'gdlfile'))

    def configClicked(self) :
        if not self.configfile :
            self.configNewClicked()
            return
        d = ConfigDialog(self.config)
        if d.exec_() :
            d.updateConfig(self, self.config)
            if self.configfile :
                f = file(self.configfile, "w")
                self.config.write(f)
                f.close()


    def configOpenClicked(self) :
        (fname, filt) = QtGui.QFileDialog.getOpenFileName(self, filter='Configuration files (*.cfg *.ini)')
        if not os.path.exists(fname) : return
        (dname, fname) = os.path.split(fname)
        if dname :
            os.chdir(dname)
        if os.path.splitext(fname)[1] == "" :
        	fname = fname + ".cfg"
        self.configfile = fname
        self.config = RawConfigParser()
        self.config.read(fname)
        if self.config.has_option('main', 'font') :
            self.loadFont(self.config.get('main', 'font'))
            if self.config.has_option('main', 'ap') :
                self.loadAP(self.config.get('main', 'ap'))
        if self.config.has_option('main', 'testsfile') :
            self.loadTests(self.config.get('main', 'testsfile'))
        if self.config.has_option('build', 'gdlfile') :
            self.selectLine(self.config.get('build', 'gdlfile'), -1)
            self.tabEdit.updateFromConfigSettings(self.config)
        
        
    def configNewClicked(self) :
        (fname, filt) = QtGui.QFileDialog.getSaveFileName(self, filter='Configuration files (*.cfg *ini)')
        if not fname : return
        (dname, fname) = os.path.split(fname)
        if dname :
            os.chdir(dname)
        if os.path.splitext(fname)[1] == "" :
        	fname = fname + ".cfg"
        self.configfile = fname
        self.config = RawConfigParser()
        for s in ('main', 'build', 'ui') : self.config.add_section(s)
        self.configClicked()

    def resetNames(self) :
        if self.font :
            self.font.loadEmptyGlyphs()
            self.tab_classes.loadFont(self.font)
            if self.tab_font : self.tab_font.update()

    def debugClicked(self, event) :
        m = DebugMenu(self)
        m.exec_(event.globalPos())

    def setposglyphsize(self, size) :
        if self.font : self.font.posglyphSize = size

if __name__ == "__main__" :
    from argparse import ArgumentParser
    import sys

    app = QtGui.QApplication(sys.argv)
    p = ArgumentParser()
    p.add_argument("font", help="Font .ttf file to process")
    p.add_argument("-a","--ap",help="AP XML database file for font")
    p.add_argument("-r","--results",help="graphite JSON debug output")
    args = p.parse_args()

    if args.font :
        mainWindow = MainWindow(args.font, args.ap, args.results, 40)
        mainWindow.show()
        sys.exit(app.exec_())


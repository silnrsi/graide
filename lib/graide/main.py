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

from graide.font import GraideFont
from graide.run import Run
from graide.attribview import AttribView
from graide.fontview import FontView
from graide.runview import RunView
from graide.passes import PassesView
from graide.gdx import Gdx
from graide.filetabs import FileTabs, FindInFilesResults
from graide.utils import buildGraphite, configval, configintval, configvalString, registerErrorLog, findgrcompiler, as_entities, popUpError
from graide.layout import Layout
from graide.rungraphite import runGraphite, makeFontAndFace, runGraphiteWithFontFace
from graide.featureselector import make_FeaturesMap, FeatureDialog
from graide.testlist import TestList
from graide.test import Test
from graide.classes import Classes
from graide.config import ConfigDialog
from graide.startdialog import StartDialog
from graide.recentprojects import RecentProjectList
from graide.debug import ContextToolButton, DebugMenu
from graide.errors import Errors
from graide.waterfall import WaterfallDialog
from graide.pyresources import qInitResources, qCleanupResources
from graide.posedit import PosEdit, PosView
from graide.tweaker import Tweaker, TweakView
from graide.findmatch import GlyphPatternMatcher, MatchList, Matcher
from qtpy import QtCore, QtGui, QtWidgets
from graide.utils import ModelSuper, DataObj

from builtins import chr
from tempfile import NamedTemporaryFile, TemporaryFile
from configparser import RawConfigParser
import json, os, sys, re
import codecs, traceback  ### debug

# Debugging:
#for line in traceback.format_stack(): print(line.strip())

class MainWindow(QtWidgets.QMainWindow) :

    def __init__(self, config, configFile, jsonFile) :

        super(MainWindow, self).__init__()

        self.rules = None
        #self.runFile = None
        self.runLoaded = False
        #self.fDialog = None
        self.config = config
        self.cfgFileName = configFile
        self.appSettings = QtCore.QSettings("SIL", "Graide")
        self.recentProjects = RecentProjectList(self.appSettings)
        self.currFeats = None
        self.currLang = None
        self.currWidth = 100
        self.font = GraideFont()
        self.fontFaces = {}
        self.fontFileName = None
        self.apname = None
        self.appTitle = "Graide v0.8.80"
        self.currConfigTab = 0
        
        self.debugCnt = 0  # debug

        windowTitle = ''
        if (self.cfgFileName != None) :
            basename = os.path.basename(self.cfgFileName)
            windowTitle = windowTitle + "[" + basename + "] - "
        windowTitle = windowTitle + self.appTitle
        self.setWindowTitle(windowTitle)

        #if sys.platform == 'darwin' :
        #    QtGui.QIcon.setThemeSearchPaths(['/opt/local/share/icons', ':/icons'])
        #    QtGui.QIcon.setThemeName('Tango')
        #app = QtCore.QCoreApplication.instance()
        appicon = QtGui.QIcon(':/images/graide_logo_256px.png')
        appicon.addFile(':/images/graide-logo_16px.png')
        appicon.addFile(':/images/graide-logo_96px.png')
        appicon.addFile(':/images/graide logo.svg')
        self.setWindowIcon(appicon)
        if Layout.noMenuIcons : QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_DontShowIconsInMenus)
            
        print("Finding compiler...") #===
        findgrcompiler()

        for s in ('main', 'build', 'ui', 'window', 'data') :
            if not config.has_section(s) :
                config.add_section(s)
                
        print("Loading font...") #===
        if config.has_option('main', 'font') :
            fontname = os.path.join(os.path.dirname(self.cfgFileName), config.get('main', 'font'))
            if fontname == None or fontname == "" :
                popUpError("WARNING: No font file specified")
            elif not os.path.exists(fontname) :
                popUpError("WARNING: Font file " + fontname + " does not exist.")
            self.loadFont(fontname)
        elif self.cfgFileName is None or self.cfgFileName == "":
            # show() function will force them to create one.
            pass
        else :
            fontFile = ""
            okCancel = self.runStartupDialog()  # forces them to define a font or Cancel
            if okCancel == False :
                self.doExit()
            fontname = os.path.join(os.path.dirname(self.cfgFileName), config.get('main', 'font'))
            self.loadFont(fontname)

        if jsonFile :
            f = open(jsonFile)
            self.json = json.load(f)
            f.close()
        else :
            self.json = None

        if config.has_option('main', 'testsfile') :
            self.testsfile = config.get('main', 'testsfile')
        else :
            self.testsfile = None
            
        if config.has_option('build', 'tweakxmlfile') :
            self.tweaksfile = config.get('build', 'tweakxmlfile')
        else :
            self.tweaksfile = None
            
        if config.has_option('ui', 'tweakglyphsize') :
            self.tweaksize = configintval(config, 'ui', 'tweakglyphsize')
        else :
            self.tweaksize = 80

        if config.has_option('ui', 'attglyphsize') :
            self.setAttGlyphSize(configintval(config, 'ui', 'attglyphsize'))

        print("Initializing program...") #===
        self.setActions()
        self.setupUi()
        self.setMenus()
        registerErrorLog(self)
        
        print("Opening files...") #===
        self._ensureMainGdlFile()            
        self._openFileList()
        
    # end of __init__
        
        
    def show(self) :
        super(MainWindow, self).show()
        
        #initializedConfig = self.runStartupDialog(True)  # make sure there is a valid project
        initializedConfig = True

        if initializedConfig :
            self._ensureMainGdlFile()
            self._openFileList()
        
        if (self.tab_font) :
            # This helps ensure the cells of the Font tab are the right size.
            # It has to be done at the very last minute.
            self.tab_font.resizeRowsToContents()
            self.tab_font.resizeColumnsToContents()
        
        
    def runStartupDialog(self, delayedInit = False) :
        result = (not self.cfgFileName is None or self.cfgFileName == "")
        initializedConfig = False
        
        # While we don't have a valid project, ask for one.
        while not result :
            initializedConfig = True
            projFile = self.getStartupProject()
            if projFile == False :
                self.doExit()
            elif projFile == "!!create-new-project!!" :
                result = self.configNewProject()
            else :
                # Open the specified config file.
                if not os.path.exists(projFile) :
                    f = codecs.open(projFile, "w", encoding="UTF-8")
                    f.write("")
                    f.close()      
                    self.cfgFileName = projFile      
                    result = self.runConfigDialog()
                else :
                    result = self._configOpenExisting(projFile)
                    
        # Then make sure there is a valid font.
        
        fontFile = self.config.get('main', 'font') if self.config.has_option('main', 'font') else ""
        while fontFile is None or fontFile == "" or not os.path.exists(fontFile) :
            if fontFile == "" or not os.path.exists(fontFile) :
                if fontFile is None or fontFile == "" :
                    popUpError("Please choose a valid .TTF file.")
                else :
                    popUpError("Font file '" + fontFile + "' does not exist.")
            # Configuration has no font - get them to set it.
            okCancel = self.runConfigDialog()
            if not okCancel : self.doExit()
            fontFile = self.config.get('main', 'font') if self.config.has_option('main', 'font') else ""
        
        if delayedInit :
            # Caller wants to know whether to set up the file list.
            return initializedConfig
        else :
            # Caller wants to know whether to exit or continue.
            return True
            
    # end of runStartupDialog


    def getStartupProject(self) :
        d = StartDialog(self.config, self.recentProjects)
        if d.exec_() :
            result = d.returnResults()
            return result
        else :
            return False
            
            
    def _ensureMainGdlFile(self) :
        gdlFile = configval(self.config, 'build', 'gdlfile')
        if gdlFile and not os.path.exists(gdlFile) :
            f = codecs.open(gdlFile, "w", encoding="UTF-8")
            f.write("// Enter your GDL code here //")
            f.close()            

    def incDebug(self) :
        self.debugCnt = self.debugCnt + 1
        return self.debugCnt
        

    def loadFont(self, fontname) :
        
        if fontname == None : return
        if fontname == "" : return
        if not os.path.exists(fontname) : return
            
        self.fontFaces = {}
        
        if self.config.has_option('main', 'size') :
            fontsize = self.config.getint('main', 'size')
        else :
            fontsize = 40
        self.fontFileName = str(fontname)
        self.fontBuildTime = os.stat(fontname).st_ctime # modify time, for knowing when to rebuild
        self.font.loadFont(self.fontFileName, fontsize)
        try:
            self.feats = make_FeaturesMap(self.fontFileName) # map languages to features  ### FEATURE BUG
        except:
            # A font without Graphite?
            print("WARNING: failure to load Graphite font features while loading font")
            self.feats = {None: {}}
        
        # basename = os.path.basename(fontname) # look in current directory. Why would you do that?
        self.gdxfile = os.path.splitext(self.fontFileName)[0] + '.gdx'
        
        self.loadAP(os.path.join(os.path.dirname(self.cfgFileName), configvalString(self.config, 'main', 'ap')))
        if hasattr(self, 'tab_font') :
            if self.tab_font :
                self.tab_font.resizeRowsToContents()
                self.tab_font.resizeColumnsToContents()
            else :
                self.tab_classes.classUpdated.disconnect(self.font.classUpdated)
                i = self.tab_results.currentIndex()
                self.tab_font = FontView(self.font)
                self.tab_font.changeGlyph.connect(self.glyphSelected)
                self.tab_results.insertTab(0, self.tab_font, "Font")
                self.tab_results.setCurrentIndex(i)
                self.tab_classes.classSelected.connect(self.font.classSelected)
            self.tab_classes.loadFont(self.font)

        if hasattr(self, 'runView') :
            self.runView.gview.setFixedHeight(self.font.pixrect.height())
            
    # end of loadFont

    def loadAP(self, apFileName) :
        #print("main - loadAP")
        self.apname = apFileName
        if apFileName and os.path.exists(apFileName) :
            self.font.loadAP(apFileName)
        else :
            self.font.loadEmptyGlyphs("loadAP")

        self.loadGdx()
        self.loadClasses()


    def loadGdx(self):
        if os.path.exists(self.gdxfile) :
            self.gdx = Gdx()
            self.gdx.readfile(self.gdxfile, self.font, configval(self.config, 'build', 'makegdlfile'),
                                configval(self.config, 'main', 'ap'),
                                ronly = configintval(self.config, 'build', 'apronly'))
        else :
            self.gdx = None

    def loadClasses(self):
        if hasattr(self, 'tab_classes') :
            self.tab_classes.loadFont(self.font)

    def loadTests(self, testsfile) :
        #print "MainWindow::loadTests(",testsfile,')'
        self.testsfile = testsfile
        fileList = []
        if self.config.has_option('data', 'testfiles') :
            fileListString = configval(self.config, 'data', 'testfiles')
            fileList = fileListString.split(';')
            #print "has file list:",fileList
        if not testsfile in fileList :
            #print "prepend main test file",testsFile
            fileList2 = fileList
            fileList = [testsfile]
            fileList.extend(fileList2)
            #print "-->",fileList
        if hasattr(self, "tab_tests") and self.tab_tests :
            for f in fileList :
                if f != '' : self.tab_tests.addFile(f, None, False)
        # otherwise MainWindow is not set up yet
            
    def loadTweaks(self, tweaksfile) :
        self.tweaksfile = tweaksfile
        if self.tab_tweak :
            self.tab_tweak.loadTweaks(tweaksfile)

    def setActions(self) :
        self.aRunGo = QtWidgets.QAction(QtGui.QIcon.fromTheme("media-playback-start", QtGui.QIcon(":/images/media-playback-start.png")), "&Run Test", self)
        self.aRunGo.setToolTip("Run text string after rebuild")
        self.aRunGo.triggered.connect(self.runClicked)
        
        self.aWater = QtWidgets.QAction(QtGui.QIcon.fromTheme("waterfall", QtGui.QIcon(":/images/waterfall.png")), "&Waterfall ...", self)
        self.aWater.setToolTip('Display run as a waterfall')
        self.aWater.triggered.connect(self.doWaterfall)
        
        self.aRunMatch = QtWidgets.QAction(QtGui.QIcon.fromTheme('edit-find', QtGui.QIcon(":/images/find-normal.png")), "", self)
        self.aRunMatch.setToolTip("Use test output as pattern to match")
        self.aRunMatch.triggered.connect(self.matchOutput)
        
        self.aRunFeats = QtWidgets.QAction(QtGui.QIcon.fromTheme("view-list-details", QtGui.QIcon(":/images/view-list-details.png")), "Set &Features ...", self)
        self.aRunFeats.triggered.connect(self.featuresClicked)
        self.aRunFeats.setToolTip("Edit features of test run")
        
        self.aRunAdd = QtWidgets.QAction(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")), "Test from &Run ...", self)
        self.aRunAdd.setToolTip("Add run to tests list under a new name")
        self.aRunAdd.triggered.connect(self.runAddClicked)

        self.aSaveAP = QtWidgets.QAction(QtGui.QIcon.fromTheme('document-save', QtGui.QIcon(":/images/document-save.png")), "Save &APs", self)
        self.aSaveAP.triggered.connect(self.saveAP)
        self.aSaveAP.setToolTip('Save AP Database')

        self.aFindInFiles = QtWidgets.QAction(QtGui.QIcon.fromTheme('edit-find', QtGui.QIcon(":/images/find-normal.png")), "Find in Files ...", self)
        self.aFindInFiles.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.SHIFT + QtCore.Qt.Key_F))
        self.aFindInFiles.triggered.connect(self.findInFiles)
        self.aFindInFiles.setToolTip('Find a text string in all open files')

        self.aCfg = QtWidgets.QAction(QtGui.QIcon.fromTheme("configure", QtGui.QIcon(":/images/configure.png")), "&Configure Project ...", self)
        self.aCfg.setToolTip("Configure project")
        self.aCfg.triggered.connect(self.runConfigDialog)
        
        self.aCfgOpen = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-open", QtGui.QIcon(":/images/document-open.png")), "&Open Project ...", self)
        self.aCfgOpen.setToolTip("Open existing project")
        self.aCfgOpen.triggered.connect(self.configOpenClicked)
        
        self.aCfgNew = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-new", QtGui.QIcon(":/images/document-new.png")), "&New Project ...", self)
        self.aCfgNew.setToolTip("Create new project")
        self.aCfgNew.triggered.connect(self.configNewClicked)

        self.aHAbout = QtWidgets.QAction("&About", self)
        self.aHAbout.triggered.connect(self.helpAbout)
        
        # Recent projects
        # TODO: use QSignalMapper instead of four openRecentProject methods:
        # http://stackoverflow.com/questions/8824311/how-to-pass-arguments-to-callback-functions-in-pyqt
        recentProjectFiles = self.recentProjects.projects()
        self.aRecProjs = []
        cnt = 0
        for (basename, fullname) in recentProjectFiles :
            if basename != '' :
                projAction = QtWidgets.QAction(basename, self)
                if   cnt == 0 : projAction.triggered.connect(self.openRecentProject1)
                elif cnt == 1 : projAction.triggered.connect(self.openRecentProject2)
                elif cnt == 2 : projAction.triggered.connect(self.openRecentProject3)
                elif cnt == 3 : projAction.triggered.connect(self.openRecentProject4)
                self.aRecProjs.append((basename, fullname, projAction))
                cnt = cnt + 1
                
    # end of setActions

    def setupUi(self) :
        qInitResources()
        self.resize(*Layout.initWinSize)
        self.centralwidget = QtWidgets.QWidget(self)
        self.verticalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.hsplitter = QtWidgets.QSplitter(self.centralwidget) #splitter between left tabbed pane and two right panes
        self.hsplitter.setOrientation(QtCore.Qt.Horizontal)
        self.hsplitter.setHandleWidth(4)
        self.verticalLayout.addWidget(self.hsplitter)

        self.tab_info = QtWidgets.QTabWidget(self.hsplitter)  # left pane
        #self.tab_info = InfoTabs(self.hsplitter)
        self.widget = QtWidgets.QWidget(self.hsplitter)
        self.setwidgetstretch(self.widget, 55, 100)
        self.topLayout = QtWidgets.QVBoxLayout(self.widget)  # right two panes
        self.topLayout.setContentsMargins(*Layout.buttonMargins)
        self.vsplitter = QtWidgets.QSplitter(self.widget) # splitter between code pane and lower pane
        self.vsplitter.setOrientation(QtCore.Qt.Vertical)
        self.vsplitter.setHandleWidth(2)
        self.topLayout.addWidget(self.vsplitter)

        self.ui_tests(self.tab_info)
        self.ui_left(self.tab_info)
        self.ui_fileEdits(self.vsplitter)

        self.tab_results = QtWidgets.QTabWidget(self.vsplitter)
        self.ui_bottom(self.tab_results)

        if self.config.has_section('window') :
            self.resize(configintval(self.config, 'window', 'mainwidth'), configintval(self.config, 'window', 'mainheight'))
            hsplit = configval(self.config, 'window', 'hsplitter')
            vsplit = configval(self.config, 'window', 'vsplitter')
            if hsplit and vsplit:
                hsplitBytes = self.splitterStringToBytes(hsplit)
                self.hsplitter.restoreState(QtCore.QByteArray.fromBase64(hsplitBytes))
                vsplitBytes = self.splitterStringToBytes(vsplit)
                self.vsplitter.restoreState(QtCore.QByteArray.fromBase64(vsplitBytes))
            else:
                self.hsplitter.setSizes((Layout.initHSplitWidth, Layout.initWinSize[0] - Layout.initHSplitWidth))
        else :
            self.hsplitter.setSizes((Layout.initHSplitWidth, Layout.initWinSize[0] - Layout.initHSplitWidth))

    # end of setupUi


    def splitterStringToBytes(self, splitterValue):
        """Convert a string that looks like b'AABBCC' to a byte array AABBCC."""
        if sys.version_info[0] < 3:
            result = splitterValue
        else:
            if splitterValue[0:2] == "b'" and splitterValue[-1:] == "'":
                splitterValue = splitterValue[2:-1]
            result = splitterValue.encode('utf-8')

        return result


    def ui_tests(self, parent) : # parent = tab_info
        self.setwidgetstretch(self.tab_info, 30, 100)
        self.test_splitter = QtWidgets.QSplitter() # left-hand vertical pane; allows sizing of results view
        self.test_splitter.setOrientation(QtCore.Qt.Vertical)
        self.test_splitter.setContentsMargins(0, 0, 0, 0)
        self.test_splitter.setHandleWidth(4)
        self.test_widget = QtWidgets.QWidget(self.test_splitter)
        self.test_vbox = QtWidgets.QVBoxLayout(self.test_widget) # TestList + input control
        self.test_vbox.setContentsMargins(*Layout.buttonMargins)
        self.test_vbox.setSpacing(Layout.buttonSpacing)
        
        # Tests control
        self.tab_tests = TestList(self, self.testsfile, parent = self.test_widget)
        self.test_vbox.addWidget(self.tab_tests)
        self.test_vbox.addSpacing(2)
        
        # line below test lists
        self.test_line = QtWidgets.QFrame(self.test_widget)
        self.test_line.setFrameStyle(QtWidgets.QFrame.HLine | QtWidgets.QFrame.Raised)
        self.test_line.setLineWidth(2)
        self.test_vbox.addWidget(self.test_line)
        self.test_vbox.addSpacing(2)
        
        # test input pane
        self.runEdit = QtWidgets.QPlainTextEdit(self.test_widget)
        self.runEdit.setMaximumHeight(Layout.runEditHeight)
        self.test_vbox.addWidget(self.runEdit)
        
        # test control buttons
        self.test_hbox = QtWidgets.QHBoxLayout()
        self.test_vbox.addLayout(self.test_hbox)
        self.test_hbox.setContentsMargins(*Layout.buttonMargins)
        self.test_hbox.setSpacing(Layout.buttonSpacing)
        self.runGo = QtWidgets.QToolButton(self.test_widget)
        self.runGo.setDefaultAction(self.aRunGo)
        self.test_hbox.addWidget(self.runGo)
        self.runWater = QtWidgets.QToolButton(self.test_widget)
        self.runWater.setDefaultAction(self.aWater)
        self.test_hbox.addWidget(self.runWater)
        self.runMatch = QtWidgets.QToolButton(self.test_widget)
        self.runMatch.setDefaultAction(self.aRunMatch)
        self.test_hbox.addWidget(self.runMatch)
        self.test_hbox.addStretch()
        self.runRtl = QtWidgets.QCheckBox("RTL", self.test_widget)
        self.runRtl.setChecked(True if configintval(self.config, 'main', 'defaultrtl') else False)
        self.runRtl.setToolTip("Process text right to left")
        self.test_hbox.addWidget(self.runRtl)
        self.runFeats = QtWidgets.QToolButton(self.test_widget)
        self.runFeats.setDefaultAction(self.aRunFeats)
        self.test_hbox.addWidget(self.runFeats)
        self.runAdd = QtWidgets.QToolButton(self.test_widget)
        self.runAdd.setDefaultAction(self.aRunAdd)
        self.test_hbox.addWidget(self.runAdd)
        
        # test output
        self.run = Run(self.font, self.runRtl.isChecked())
        self.runView = RunView(self.font)
        self.runView.gview.resize(self.runView.gview.width(), self.font.pixrect.height() + 5)
        self.test_splitter.addWidget(self.runView.gview)
        # Ignore runView.tview - text view that shows the glyph names.
        
        parent.addTab(self.test_splitter, "Tests")

    # end of ui_tests

    def ui_left(self, parent) :
        # glyph, slot, classes, positions
                
        # Glyph tab
        self.tab_glyph = QtWidgets.QWidget()
        self.glyph_vb = QtWidgets.QVBoxLayout(self.tab_glyph)
        self.glyph_vb.setContentsMargins(*Layout.buttonMargins)
        self.glyph_vb.setSpacing(Layout.buttonSpacing)
        self.glyphAttrib = AttribView(self)
        self.glyph_vb.addWidget(self.glyphAttrib)
        self.glyph_bbox = QtWidgets.QWidget(self.tab_glyph)
        self.glyph_hb = QtWidgets.QHBoxLayout(self.glyph_bbox)
        self.glyph_hb.setContentsMargins(*Layout.buttonMargins)
        self.glyph_hb.setSpacing(Layout.buttonSpacing)
        self.glyph_hb.insertStretch(0)
        if self.apname :
            self.glyph_saveAP = QtWidgets.QToolButton(self.glyph_bbox)
            self.glyph_saveAP.setDefaultAction(self.aSaveAP)
            self.glyph_hb.addWidget(self.glyph_saveAP)
        self.glyph_find = QtWidgets.QToolButton()	# find glyph
        self.glyph_find.setIcon(QtGui.QIcon.fromTheme('edit-find', QtGui.QIcon(":/images/find-normal.png")))
        self.glyph_find.clicked.connect(self.glyphFindSelected)
        self.glyph_find.setToolTip('Find glyph selected in source code')
        self.glyph_hb.addWidget(self.glyph_find)
        self.glyph_addPoint = QtWidgets.QToolButton(self.glyph_bbox)
        self.glyph_addPoint.setIcon(QtGui.QIcon.fromTheme('character-set', QtGui.QIcon(":/images/character-set.png")))
        self.glyph_addPoint.setText(u'\u2022')
        self.glyph_addPoint.clicked.connect(self.glyphAddPoint)
        self.glyph_addPoint.setToolTip('Add attachment point to glyph')
        self.glyph_hb.addWidget(self.glyph_addPoint)
        self.glyph_addProperty = QtWidgets.QToolButton(self.glyph_bbox)
        self.glyph_addProperty.setIcon(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")))
        self.glyph_addProperty.clicked.connect(self.glyphAddProperty)
        self.glyph_addProperty.setToolTip('Add property to glyph')
        self.glyph_hb.addWidget(self.glyph_addProperty)
        self.glyph_remove = QtWidgets.QToolButton(self.glyph_bbox)
        self.glyph_remove.setIcon(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")))
        self.glyph_remove.clicked.connect(self.glyphRemoveProperty)
        self.glyph_remove.setToolTip('Remove property from glyph')
        self.glyph_hb.addWidget(self.glyph_remove)
        self.glyph_vb.addWidget(self.glyph_bbox)
        self.tab_info.addTab(self.tab_glyph, "Glyph")
        
        # Slot tab
        self.tab_slot = AttribView(self)
        self.tab_info.addTab(self.tab_slot, "Slot")
        
        # Classes tab
        self.tab_classes = Classes(self.font, self, configval(self.config, 'build', 'makegdlfile') if configval(self.config, 'main', 'ap') else None)
        self.tab_classes.classUpdated.connect(self.font.classUpdated)
        self.tab_info.addTab(self.tab_classes, "Classes")
        
        # Tweak tab
        self.tab_tweak = Tweaker(self.font, self, self.tweaksfile)
        self.tab_info.addTab(self.tab_tweak, "Tweak")
        
        # Attach tab
        self.tab_posedit = PosEdit(self.font, self)
        self.tab_info.addTab(self.tab_posedit, "Attach")
        
        # Match tab
        self.tab_match = Matcher(self.fontFileName, self.font, self, self.testsfile)
        self.tab_info.addTab(self.tab_match, "Match")
        
        self.tab_info.currentChanged.connect(self.infoTabChanged)

    # end of ui_left

    def ui_fileEdits(self, parent) :
        # file edit view
        self.tab_edit = FileTabs(self.config, self, parent)
        self.setwidgetstretch(self.tab_edit, 100, 50)
        self.tab_edit.setTabsClosable(True)

    def ui_bottom(self, parent) :
        # bottom pane
        self.setwidgetstretch(self.tab_results, 100, 45)
        parent.setTabPosition(QtWidgets.QTabWidget.South)
        self.cfg_widget = QtWidgets.QWidget()
        self.cfg_hbox = QtWidgets.QHBoxLayout(self.cfg_widget)
        self.cfg_hbox.setContentsMargins(*Layout.buttonMargins)
        self.cfg_hbox.setSpacing(Layout.buttonSpacing)
        self.cfg_button = ContextToolButton(self.cfg_widget)
        self.cfg_button.setDefaultAction(self.aCfg)
        self.cfg_button.rightClick.connect(self.debugClicked)
        self.cfg_hbox.addWidget(self.cfg_button)
        self.cfg_open = QtWidgets.QToolButton(self.cfg_widget)
        self.cfg_open.setDefaultAction(self.aCfgOpen)
        self.cfg_hbox.addWidget(self.cfg_open)
        self.cfg_new = QtWidgets.QToolButton(self.cfg_widget)
        self.cfg_new.setDefaultAction(self.aCfgNew)
        self.cfg_hbox.addWidget(self.cfg_new)
        parent.setCornerWidget(self.cfg_widget)

        # Font tab
        if self.font.isRead() :
            self.tab_font = FontView(self.font)
            self.tab_font.changeGlyph.connect(self.glyphSelected)
            self.tab_classes.classSelected.connect(self.tab_font.classSelected)
        else :
            self.tab_font = None
        self.tab_results.addTab(self.tab_font, "Font")

        # Errors tab
        self.tab_errors = Errors()
        self.tab_results.addTab(self.tab_errors, "Errors")
        self.tab_errors.errorSelected.connect(self.tab_edit.selectLine)

        # Find tab
        self.tab_findInFiles = FindInFilesResults()
        self.tab_results.addTab(self.tab_findInFiles, "Find")
        self.tab_findInFiles.resultSelected.connect(self.tab_edit.selectLine)

        # Passes tab
        self.tab_passes = PassesView(self)
        self.tab_passes.slotSelected.connect(self.slotSelected)
        self.tab_passes.glyphSelected.connect(self.glyphSelected)
        self.tab_passes.glyphSelected.connect(self.glyphAttrib.changeData)
        self.tab_passes.rowActivated.connect(self.rulesSelected)
        self.tab_results.addTab(self.tab_passes, "Passes")
        if self.json :
            self.run.addSlots(self.json[-1]['output'])
            self.runView.loadRun(self.run, self.font)
            self.runView.slotSelected.connect(self.slotSelected)
            self.runView.glyphSelected.connect(self.glyphAttrib.changeData)
            self.tab_passes.loadResults(self.font, self.json, self.gdx)
            istr = u"".join(map(lambda x:chr(x['unicode']), self.json[-1]['chars']))
            self.runEdit.setPlainText(istr.encode("utf-8").decode('raw_unicode_escape'))
            self.tab_passes.setTopToolTip(istr.encode("utf-8").decode('raw_unicode_escape'))
            self.runLoaded = True
        self.setCentralWidget(self.centralwidget)

        # Rules tab
        self.tab_rules = PassesView(self)
        self.tab_rules.slotSelected.connect(self.slotSelected)
        self.tab_passes.glyphSelected.connect(self.glyphSelected)
        self.tab_rules.glyphSelected.connect(self.glyphAttrib.changeData)
        self.tab_rules.rowActivated.connect(self.ruleSelected)
        self.tab_results.addTab(self.tab_rules, "Rules")

        # Tweaks tab
        ffile = self.fontFileName if self.fontFileName else ""
        self.tab_tweakview = TweakView(ffile, self.tweaksize, app = self)
        if hasattr(self, 'tab_tweak') :
            self.tab_tweak.setView(self.tab_tweakview)
            self.tab_tweakview.setTweaker(self.tab_tweak)
        self.tab_results.addTab(self.tab_tweakview, "Tweak")

        # Attachment tab
        self.tab_posview = PosView(self)
        if hasattr(self, 'tab_posedit') : self.tab_posedit.setView(self.tab_posview)
        self.tab_results.addTab(self.tab_posview, "Attach")

    # end of ui_bottom

    def setMenus(self) :
        filemenu = self.menuBar().addMenu("&File")
        filemenu.addAction(self.tab_edit.aAdd)
        filemenu.addAction(self.tab_edit.aSave)
        filemenu.addSeparator()
        filemenu.addAction(self.tab_edit.aBuild)
        filemenu.addAction('&Reset Names', self.resetNames)
        filemenu.addAction('Exit', self.doExit)
        ################3
        filemenu.addAction('Start up...', self.runStartupDialog)

        projectmenu = self.menuBar().addMenu("&Project")
        projectmenu.addAction(self.aCfg)
        projectmenu.addAction(self.aCfgOpen)
        projectmenu.addAction(self.aCfgNew)
        projectmenu.addSeparator()
        projectmenu.addAction(self.aSaveAP)
        projectmenu.addSeparator()
        projectmenu.addAction(self.aFindInFiles)

        # Add recent projects
        if (len(self.aRecProjs) > 0) : projectmenu.addSeparator()
        for (basename, fullname, aProj) in self.aRecProjs :
            projectmenu.addAction(aProj)

        testmenu = self.menuBar().addMenu("&Tests")
        testmenu.addAction(self.aRunGo)
        testmenu.addAction(self.aWater)
        testmenu.addAction(self.aRunFeats)
        testmenu.addAction(self.aRunAdd)
        testmenu.addSeparator()
        testmenu.addAction(self.tab_tests.aGAdd)
        testmenu.addAction(self.tab_tests.aGDel)
        testmenu.addSeparator()
        testmenu.addAction(self.tab_tests.aAdd)
        testmenu.addAction(self.tab_tests.aEdit)
        testmenu.addAction(self.tab_tests.aSave)
        testmenu.addAction(self.tab_tests.aDel)
        testmenu.addAction(self.tab_tests.aUpp)
        testmenu.addAction(self.tab_tests.aDown)

        helpmenu = self.menuBar().addMenu("&Help")
        helpmenu.addAction(self.aHAbout)

    # end of setMenus

    def helpAbout(self) :
        QtWidgets.QMessageBox.about(self, "Graide", """GRAphite Integrated Development Environment

An environment for the creation and debugging of Graphite fonts.

Copyright 2012-2013 SIL International and M. Hosken""")

    def setwidgetstretch(self, widget, hori, vert) :
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        if hori != 100 : sizePolicy.setHorizontalStretch(hori)
        if vert != 100 : sizePolicy.setVerticalStretch(vert)
        sizePolicy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
        size = self.size()
        widget.resize(QtCore.QSize(size.width() * hori / 100, size.height() * vert / 100))
        widget.setSizePolicy(sizePolicy)

    def isInitialized(self) :
        # Indicate whether the app has gone a reasonable way through the initialization process.
        return hasattr(self, "tab_edit")

    def doExit(self) :
        self.closeApp()
        sys.exit()

    def closeEvent(self, event) :
        if self.rules :
            self.rules.close()
        self.closeApp()
        event.accept()

    def closeApp(self):
        #print("closeApp")
        if self.rules:
            self.rules.close()
        if self.isInitialized():
            self._saveProjectData()
        self.recentProjects.close()
        qCleanupResources()

    def infoTabChanged(self) :
        # Don't call updatePositions unnecessarily, because it causes a switch of focus.
        if self.tab_info.currentWidget() == self.tab_tweak :
            self.tab_tweak.updatePositions()
        elif self.tab_info.currentWidget() == self.tab_posedit :
            self.tab_posedit.updatePositions()

    def _saveProjectData(self) :
        #print("_saveProjectData")
        self.recentProjects.addProject(self.cfgFileName)  # remember that this was a recent project
        self.recentProjects.saveFiles()

        if not self.config.has_section('window') :
            self.config.add_section('window')
        s = self.size()
        self.config.set('window', 'mainwidth', str(s.width()))
        self.config.set('window', 'mainheight', str(s.height()))
        hsplit = self.hsplitter.saveState().toBase64()
        vsplit = self.vsplitter.saveState().toBase64()
        if sys.version_info[0] > 2:
            hsplit = str(hsplit.data(), encoding='utf-8')
            vsplit = str(vsplit.data(), encoding='utf-8')
        self.config.set('window', 'hsplitter', hsplit)
        self.config.set('window', 'vsplitter', vsplit)

        if self.testsfile :
            self.tab_tests.saveTests()
        if self.tweaksfile :
            self.tab_tweak.writeXML(self.tweaksfile)
        if self.cfgFileName :
            try :
                f = open(self.cfgFileName, "w")
                self.config.write(f)
                f.close()
            except :
                pass
        self.tab_edit.writeIfModified()
        self.saveAP()
    
    # end of _saveProjectData    

    # see comment in attribview.py for how this works
    QtCore.Slot(DataObj, ModelSuper, bool)
    def glyphSelected(self, data, model, doubleClick) :
        # data = GraideGlyph, model = RunView, FontView
        self.glyphAttrib.changeData(data, model)    # redundant with tab_passes.glyphSelected.connect(self.glyphAttrib.changeData)
                                                    # call, so it happens twice. But both might be needed in some cases.
        if doubleClick:
            self.tab_info.setCurrentWidget(self.tab_glyph)
        

    QtCore.Slot(DataObj, ModelSuper, bool)
    def slotSelected(self, data, model, doubleClick) :
        # data = Slot, model = RunView
        self.tab_slot.changeData(data, model)
        if doubleClick and self.tab_info.currentWidget() is not self.tab_glyph :
            self.tab_info.setCurrentWidget(self.tab_slot)

    def rulesSelected(self, row, view, passview) :
        if row == 0 : return
        self.tab_rules.setPassIndex(row - 1)
        
        # Here we assume that if the default direction of the configuration is RTL, the
        # font is RTL (which may not necessarily be true).
        fontIsRtl = configintval(self.config, 'main', 'defaultrtl')
        
        if passview.rules(row) is not None or passview.collisions(row) is not None:
            self.tab_rules.loadRules(self.font, passview.rules(row), passview.collisions(row), passview.runView(row-1).run, passview.flipDir(row-1), passview.flipDir(row), self.gdx)
            
            if passview.collisions(row) is not None :
                if passview.rules(row) is not None :
                    ruleLabel = "Rules + Collisions: pass %d" % row
                else :
                    ruleLabel = "Collisions: pass %d" % row
            else :
                ruleLabel = "Rules: pass %d" % row

            ###flipLabel = (" (LTR)" if fontIsRtl else " (RTL)") if passview.flipDir(row) else ""
            ruleLabel += passview.dirLabel(row)
            
            self.tab_results.setTabText(4, ruleLabel)
            self.tab_results.setCurrentWidget(self.tab_rules)
            
        passview.selectRow(row)

    def rulesClosed(self, dialog) :
        self.ruleView.slotSelected.disconnect()
        self.ruleView.glyphSelected.disconnect()
        self.ruleView = None

    def ruleSelected(self, row, view, passview) :
        if self.gdx and hasattr(view.run, 'passindex') and view.run.ruleindex >= 0:
            rule = self.gdx.passes[view.run.passindex][view.run.ruleindex]
            self.selectLine(rule.srcfile, rule.srcline)

    def posSelected(self) :
        self.tab_results.setCurrentWidget(self.tab_posview)

    def selectLine(self, fname = None, srcline = -1) :
        #print("select line in ", fname, srcline)
        if not fname :
            fname = configval(self.config, 'build', 'gdlfile')
        if self.isInitialized() :
            self.tab_edit.selectLine(fname, srcline)
        # otherwise MainWindow is not set up yet

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
        #print("buildClicked")

        self.tab_edit.writeIfModified()

        if self.tweaksfile :
            self.tab_tweak.writeXML(self.tweaksfile)

        self.tab_errors.clear()
        errfile = NamedTemporaryFile(mode="w+")  ###, delete=False)   # delete=False for debugging

        self.fontFaces = {}

        outputPath = os.path.dirname(self.fontFileName)
        gdlErrFileName = outputPath + '/gdlerr.txt' if outputPath != "" else './gdlerr.txt'

        res = buildGraphite(self.config, self, self.font, self.fontFileName, errfile, gdlErrFileName)

        if res :
            # Compilation failure
            # Process temporary file generated by buildGraphite function.
            errfile.seek(0)
            for l in errfile.readlines() :
                self.tab_errors.addItem(l.strip())
                print(l.strip())  ####
        # Process error list generated by Graphite compiler.
        self.tab_errors.addGdlErrors(gdlErrFileName)

        # Print the results of the compilation to the console.
        if os.path.exists(gdlErrFileName) :
            gdlFile = open(gdlErrFileName)
            for l in gdlFile.readlines() :
                lastLine = l
            print("..." + l)
        else :
            print('...no GDL output file')

        if res or self.tab_errors.bringToFront :
            self.tab_results.setCurrentWidget(self.tab_errors)
        if self.apname :
            self.loadAP(self.apname)
        else:
            self.loadGdx()
            self.loadClasses()

        if self.fontFileName :
            try:
                self.feats = make_FeaturesMap(self.fontFileName)
            except:
                # A font without Graphite?
                print("WARNING: failure to reinitialize Graphite font features")
                self.feats = {None: {}}

        # Get source-code files up-to-date.
        self.tab_edit.reloadModifiedFiles()

        return True

    # end of buildClicked

    # Run Graphite over a test string.
    def runClicked(self) :
        
        # Don't automatically build the font - the user might be part way through
        # making changes and not ready to build.
        #if self.tab_edit.writeIfModified() and not self.buildClicked() :
        #    # Error in saving code or building 
        #    return

        if not self.fontFileName :
            return
        if os.stat(self.fontFileName).st_ctime > self.fontBuildTime :
            self.loadFont(self.fontFileName)
        
        if not self.currFeats and self.currLang not in self.feats :
            if None not in self.feats :    # not a graphite font, try to build
                self.buildClicked()
                if self.currLang not in self.feats :
                    if None not in self.feats :     # build failed, do nothing.
                        self.tab_errors.addError("Can't run test on a non-Graphite font")
                        self.tab_results.setCurrentWidget(self.tab_errors)
                        return
                    else :
                        self.currLang = None
            else :
                self.currLang = None

        ### FEATURE BUG
        if self.currFeats:
            tFeats = self.currFeats
        elif self.currLang and self.feats[self.currLang]:
            tFeats = self.feats[self.currLang].fval
        else:
            tFeats = {}  # probably an error in loading the font

        jsonResult = self.runGraphiteOverString(self.fontFileName, None, self.runEdit.toPlainText(),
            self.font.size, self.runRtl.isChecked(), tFeats,
            self.currLang,
            self.currWidth)
        if jsonResult != False :
            self.json = jsonResult
        else :
            print("No Graphite result")
            self.json = [ {'passes' : [], 'output' : [] } ]
                
        ### Temp
        #patternMatcher = GlyphPatternMatcher(self)
        #patternMatcher.tempCreateRegExp(self.font, self.json, 0, 3)
        #patternMatcher.search(self.fontFileName, self.config.get('main', 'testsfile'))
        #####################
        
        self.run = self.loadRunViewAndPasses(self, self.json)
        
    # end of runClicked

    def loadRunViewAndPasses(self, widget, json, scroll = '') :
        # widget might be self (the main window) or it might be the Matcher
        rtl = widget.runRtl.isChecked()
        # Here we assume that if the default direction of the configuration is RTL, the
        # font is RTL (which may not necessarily be true).
        fontIsRtl = configintval(self.config, 'main', 'defaultrtl')
        
        runResult = Run(rtl)
        ###if self.run :
        runResult.addSlots(json[-1]['output'])
        widget.runView.loadRun(runResult, self.font, resize = False)
        if not widget.runLoaded :
            try :
                widget.runView.slotSelected.connect(self.slotSelected)
                widget.runView.glyphSelected.connect(self.glyphAttrib.changeData)
                widget.runLoaded = True
            except :
                print("Selection connection failed")
        self.tab_passes.loadResults(self.font, json, self.gdx, rtl, fontIsRtl)
        self.tab_passes.setTopToolTip(widget.runEdit.toPlainText())
        self.tab_results.setCurrentWidget(self.tab_passes)
        self.tab_passes.updateScroll(scroll)
        
        return runResult

    # end of loadRunViewAndPasses
    
    
    def runGraphiteOverString(self, fontFileName, faceAndFont, inputString, size, rtl, feats, lang, expand) :
        
        if inputString and inputString != "" :
            text = re.sub(r'\\u([0-9A-Fa-f]{4})|\\U([0-9A-Fa-f]{5,8})', \
                    lambda m: chr(int(m.group(1) or m.group(2), 16)), inputString)
        else :
            text = None
        if not text :
            return False
            
        tempFile = NamedTemporaryFile(mode="w+")
        tempJsonFileName = tempFile.name
        tempFile.close()
        
        #print(self.fontFaces)
        
        if faceAndFont != None :
            self.fontFaces[size] = faceAndFont
            
        if not size in self.fontFaces :
            faceAndFont = makeFontAndFace(fontFileName, size)
            # Cache these so we don't have to keep recreating them
            self.fontFaces[size] = faceAndFont
        
        inputEntities = as_entities(text)
        ###print "inputEntities=", inputEntities ###
        
        #if faceAndFont == None :
        #    runGraphite(fontFileName, text, runfname, feats, rtl, lang, size, expand)
        #else :
        runGraphiteWithFontFace(self.fontFaces[size], text, tempJsonFileName,
            feats, rtl, lang, size, expand)
        
        #print(tempJsonFileName)     # uncomment to save JSON file
        
        tempJsonFile = open(tempJsonFileName)
        jsonResult = json.load(tempJsonFile)
        if isinstance(jsonResult, dict) : jsonResult = [jsonResult]
        tempJsonFile.close()

        # copy JSON to a debugger file in an accessible place
        tempJsonFile = open(tempJsonFileName, "r")
        stuff = tempJsonFile.read()
        jsonDbgFilename = "./graide_dbg_output.json"
        dbgJsonFile = open(jsonDbgFilename, "w")
        dbgJsonFile.write("# Graphite JSON output for input string:\n#\n# ")
        dbgJsonFile.write(inputEntities)
        dbgJsonFile.write("\n\n")
        dbgJsonFile.write(stuff)
        dbgJsonFile.close()
        
        tempJsonFile.close()
        os.unlink(tempJsonFileName)   # comment out to save JSON file
        
        return jsonResult
    
    # end of runGraphiteOverString
    
    def doWaterfall(self) :
        self.runClicked()
        if self.config.has_option('ui', 'waterfall') :
            sizes = map(int, self.config.get('ui', 'waterfall').split(','))
        else :
            sizes = None
        if self.run :
            w = WaterfallDialog(self.font, self.run, sizes = sizes)
            w.exec_()


    def matchOutput(self) :
        rtl = self.runRtl.isChecked()
        glyphList = self. _finalOutput(self.font, self.json, self.gdx, rtl)
        self.tab_match.pasteAsPattern(glyphList)
        self.tab_info.setCurrentWidget(self.tab_match)


    # Return the output of the final pass.
    def _finalOutput(self, font, jsonall, gdx = None, rtl = False) :
        if jsonall :
            json = jsonall[0]
        else :
            json = {'passes' : [], 'output' : [] }  # empty output
        num = len(json['passes']) + 1  # 0 = Init
            
        glyphList = []
        run = Run(self.font, rtl)
        run.addSlots(json['output'])   # final output
        for i, s in enumerate(run) :
            g = font[s.gid] # g is a GraideGlyph
            if g :
                t = g.GDLName() or g.psname
                glyphList.append(t)
        return glyphList
        
    # end of _finalOutput()
    

    def runAddClicked(self) :
        text = self.runEdit.toPlainText()
        if not text : return
        test = Test(text, self.currFeats or {}, self.currLang, self.runRtl.isChecked())
        self.tab_tests.addClicked(test)

    def featuresClicked(self) :
        if self.font :
            fDialog = FeatureDialog(self)
            fDialog.set_feats(self.feats[self.currLang], self.feats[self.currLang],
                vals = self.currFeats, lang = self.currLang, width = self.currWidth)
            if fDialog.exec_() :
                self.currFeats = fDialog.get_feats()
                self.currLang = fDialog.get_lang()
                if self.currLang == "" : self.currLang = None
                self.currWidth = fDialog.get_width()

    # called from utils
    def updateFileEdit(self, fname) :
        self.tab_edit.updateFileEdit(fname)

    def propDialog(self, name) :
        d = QtWidgets.QDialog(self)
        d.setWindowTitle(name)
        g = QtWidgets.QGridLayout()
        d.setLayout(g)
        n = QtWidgets.QLineEdit()
        g.addWidget(QtWidgets.QLabel(name + ' Name:'), 0, 0)
        g.addWidget(n, 0, 1)
        v = QtWidgets.QLineEdit()
        g.addWidget(QtWidgets.QLabel('Value:'), 1, 0)
        g.addWidget(v, 1, 1)
        o = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        o.accepted.connect(d.accept)
        o.rejected.connect(d.reject)
        g.addWidget(o, 2, 0, 1, 2)
        if d.exec_() :
            return (n.text(), v.text())
        else :
            return (None, None)
            
    # end of propDialog
    
    def glyphFindSelected(self) :
        glyphName = self.tab_edit.selectedText
        gidSelected = self.font.glyphOrPseudoWithGDLName(glyphName)
        if gidSelected > -1 :
            prevGlyph = self.glyphAttrib.dataObject()
            glyph = self.font[gidSelected]
            self.glyphAttrib.changeData(glyph, None)
            if prevGlyph == glyph :
                self.glyphAttrib.findMainFileLoc()

    def glyphAddPoint(self) :
        (n, v) = self.propDialog('Point')
        if n :
            glyph = self.glyphAttrib.data
            glyph.setPoint(n, v)
            self.glyphAttrib.changeData(glyph, None)

    def glyphAddProperty(self) :
        (n, v) = self.propDialog('Property')
        if n :
            glyph = self.glyphAttrib.data
            glyph.setGdlProperty(n, v)
            self.glyphAttrib.changeData(glyph, None)

    def glyphRemoveProperty(self) :
        self.glyphAttrib.removeCurrent()

    def saveAP(self) :
        if self.apname and not configintval(self.config, 'build', 'apronly') :
            self.font.saveAP(self.apname, configval(self.config, 'build', 'gdlfile'))

    def runConfigDialog(self) :
        if not self.cfgFileName :
            self.configNewClicked()
            return
        dialog = ConfigDialog(self.config, self.currConfigTab)
        result = dialog.exec_()
        self.setConfigTab(dialog.currentTab())
        if result :
            dialog.updateConfig(self, self.config)
            if self.cfgFileName :
                f = open(self.cfgFileName, "w")
                self.config.write(f)
                f.close()
            mainFileTemp = configval(self.config, "build", "gdlfile")
            return True  # OK
        else :
            return False  # Cancel

    def setConfigTab(self, index) :
        self.currConfigTab = index

    # Open an (existing) project.
    def configOpenClicked(self) :
        (cfgFileName, filt) = QtWidgets.QFileDialog.getOpenFileName(self, filter='Configuration files (*.cfg *.ini)')
        if not os.path.exists(cfgFileName) : return
        if os.path.splitext(cfgFileName)[1] == "" :
            cfgFileName = cfgFileName + ".cfg"
        self._configOpenExisting(cfgFileName)

    def _configOpenExisting(self, cfgFileName) :
        #print("_configOpenExisting")
        self._saveProjectData()
        
        self.tab_edit.closeAllTabs()

        (path, cfgFileName) = os.path.split(cfgFileName)
        if path :
            os.chdir(path)

        self.cfgFileName = cfgFileName
        self.setWindowTitle("[" + cfgFileName + "] - " + self.appTitle)
        
        self.config = RawConfigParser()
        try :
            self.config.read(cfgFileName)
        except :
            popUpError("ERROR: configuration file " + cfgFileName + " could not be read.")
            return False

        if self.config.has_option('main', 'font') :
            fontFileName = self.config.get('main', 'font')
            if not os.path.exists(fontFileName) :
                popUpError("ERROR: font file " + fontFileName + " does not exist.")
                return False  # fail and try to open a different project
            self.loadFont(fontFileName)
            
            if self.config.has_option('main', 'ap') :
                apFileName = self.config.get('main', 'ap')
                if not os.path.exists(apFileName) :
                    popUpError("WARNING: AP file " + apFileName + " does not exist.")
                else :
                    self.loadAP(apFileName)
            
        if self.config.has_option('main', 'testsfile') :
            testsFileName = self.config.get('main', 'testsfile')
            if not os.path.exists(testsFileName) :
                popUpError("WARNING: Tests file " + testsFileName + " does not exist.")
            else :
                self.loadTests(testsFileName)
            
        if self.config.has_option('build', 'tweakxmlfile') :
            self.loadTweaks(self.config.get('build', 'tweakxmlfile'))

        self._ensureMainGdlFile()
        self._openFileList()

        #self.selectLine(self.config.get('build', 'gdlfile'), -1)
        self.tab_edit.updateFromConfigSettings(self.config)
        self.tab_tweak.updateFromConfigSettings(self.font, self.fontFileName, self.config)
        self.tab_match.updateFromConfigSettings(self.fontFileName, self.config)
        
        return True  # success
    
    # end of _configOpenExisting        


    # When opening a project, open the list of previously open files.
    def _openFileList(self) :
        if self.config.has_option('window', 'openfiles') :
            openFileString = self.config.get('window', 'openfiles')
            openFiles = openFileString.split(';')
            for f in openFiles :
                if (f) :
                    if os.path.isfile(f) :
                        self.tab_edit.selectLine(f, -1)
        # Open the main file.
        mainfile = configval(self.config, 'build', 'gdlfile')
        if mainfile :
            self.tab_edit.selectLine(mainfile, -1)


    # Create a new project.
    def configNewClicked(self) :
        self.configNewProject()
        
    def configNewProject(self) :
        if self.cfgFileName :
            # record current config, if any, as a recent project
            self.recentProjects.addProject(self.cfgFileName)
            
        (fname, filt) = QtWidgets.QFileDialog.getSaveFileName(self, filter='Configuration files (*.cfg *ini)')
        if not fname : return
        (path, fname) = os.path.split(fname)
        if path :
            os.chdir(path)
        if os.path.splitext(fname)[1] == "" :
            fname = fname + ".cfg"
        self.cfgFileName = fname
        self.recentProjects.addProject(self.cfgFileName)
        self.config = RawConfigParser()
        for s in ('main', 'build', 'ui') : self.config.add_section(s)
            
        result = self.runConfigDialog()
        return result  # OK or Cancel
        
    # end of configNewClicked  


    def resetNames(self) :
        if self.font :
            self.font.loadEmptyGlyphs("resetNames")
            self.tab_classes.loadFont(self.font)
            if self.tab_font : self.tab_font.update()


    def debugClicked(self, event) :
        m = DebugMenu(self)
        m.exec_(event.globalPos())

    def setTweakGlyphSize(self, size) :
        self.tab_tweakview.changeFontSize(size)    


    def setAttGlyphSize(self, size) :
        if self.font : self.font.attGlyphSize = size


    # TODO: use QSignalMapper instead of four openRecentProject methods:
    def openRecentProject1(self) :
        self.openRecentProject(1)
    def openRecentProject2(self) :
        self.openRecentProject(2)
    def openRecentProject3(self) :
        self.openRecentProject(3)
    def openRecentProject4(self) :
        self.openRecentProject(4)


    def openRecentProject(self, i) :
        (basename, fullname, action) = self.aRecProjs[i-1]
        if not os.path.exists(fullname) :
            print("ERROR: project " + fullname + " does not exist")
        else :
            self._configOpenExisting(fullname)
            
    def findInFiles(self) :
        if self.tab_edit.findInOpenFiles(self.tab_findInFiles) :
            self.tab_results.setCurrentWidget(self.tab_findInFiles)
            
# end of MainWindow class


if __name__ == "__main__" :
    from argparse import ArgumentParser
    import sys

    app = QtWidgets.QApplication(sys.argv)
    p = ArgumentParser()
    p.add_argument("font", help="Font .ttf file to process")
    p.add_argument("-a","--ap",help="AP XML database file for font")
    p.add_argument("-r","--results",help="graphite JSON debug output")
    args = p.parse_args()
    
    if args.font :
        mainWindow = MainWindow(args.font, args.ap, args.results)
        mainWindow.show()
        sys.exit(app.exec_())


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
from graide.ruledialog import RuleDialog
from graide.gdx import Gdx
from graide.filetabs import FileTabs
from graide.utils import runGraphite, buildGraphite, configval
from graide.featureselector import FeatureRefs, FeatureDialog
from graide.testlist import TestList
from graide.test import Test
from graide.classes import Classes
from graide.config import ConfigDialog
from PySide import QtCore, QtGui
from tempfile import NamedTemporaryFile
import json, os

class MainWindow(QtGui.QMainWindow) :

    def __init__(self, config, jsonfile) :
        super(MainWindow, self).__init__()
        self.rules = None
        self.runfile = None
        self.runloaded = False
        self.fDialog = None
        self.config = config
        self.currFeats = None

        if config.has_option('main', 'font') :
            if config.has_option('main', 'size') :
                fontsize = config.getint('main', 'size')
            else :
                fontsize = 40
            self.fontfile = config.get('main', 'font')
            self.font = Font()
            self.font.loadFont(self.fontfile, config.get('main', 'ap') if config.has_option('main', 'ap') else None)
            self.font.makebitmaps(fontsize)
            self.feats = FeatureRefs(self.fontfile)
            self.gdxfile = os.path.splitext(self.fontfile)[0] + '.gdx'
            if os.path.exists(self.gdxfile) :
                self.gdx = Gdx()
                self.gdx.readfile(self.gdxfile, self.font if not configval(config, 'build', 'usemakegdl') else None)
            else :
                self.gdx = None
        else :
            self.font = None

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

        self.setupUi()

    def closeEvent(self, event) :
        if self.rules :
            self.rules.close()
        event.accept()

    def setupUi(self) :
        self.resize(994, 696)
        self.centralwidget = QtGui.QWidget(self)
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.vsplitter = QtGui.QSplitter(self.centralwidget)
        self.vsplitter.setOrientation(QtCore.Qt.Vertical)
        self.vsplitter.setHandleWidth(2)

        self.widget = QtGui.QWidget(self.vsplitter)
        self.setwidgetstretch(self.widget, 100, 55)
        self.horizontalLayout = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.hsplitter = QtGui.QSplitter(self.widget)
        self.hsplitter.setOrientation(QtCore.Qt.Horizontal)
        self.hsplitter.setHandleWidth(4)

        # tests list
        self.test_widget = QtGui.QWidget(self.hsplitter)
        self.test_vbox = QtGui.QVBoxLayout(self.test_widget)
        self.test_vbox.setContentsMargins(0, 0, 0, 0)
        self.tabTest = TestList(self, self.testsfile, parent = self.test_widget)
        self.test_vbox.addWidget(self.tabTest)
        self.setwidgetstretch(self.test_widget, 30, 100)
        self.test_line = QtGui.QFrame(self.test_widget)
        self.test_line.setFrameStyle(QtGui.QFrame.HLine | QtGui.QFrame.Raised)
        self.test_line.setLineWidth(2)
        self.test_vbox.addWidget(self.test_line)
        self.runEdit = QtGui.QPlainTextEdit(self.test_widget)
        self.runEdit.setMaximumHeight(60)
        self.test_vbox.addWidget(self.runEdit)
        self.test_hbox = QtGui.QHBoxLayout()
        self.test_vbox.addLayout(self.test_hbox)
        self.test_hbox.setContentsMargins(0, 0, 0, 0)
        self.runRtl = QtGui.QCheckBox("RTL", self.test_widget)
        self.runRtl.setChecked(True if configval(self.config, 'main', 'defaultrtl') else False)
        self.runRtl.setToolTip("Process text right to left")
        self.test_hbox.addWidget(self.runRtl)
        self.runFeats = QtGui.QPushButton("Features", self.test_widget)
        self.runFeats.clicked.connect(self.featuresClicked)
        self.runFeats.setToolTip("Edit run features")
        self.test_hbox.addWidget(self.runFeats)
        self.runGo = QtGui.QPushButton("Run", self.test_widget)
        self.runGo.setToolTip("Rebuild and process run")
        self.runGo.clicked.connect(self.runClicked)
        self.test_hbox.addWidget(self.runGo)
        self.runAdd = QtGui.QToolButton(self.test_widget)
        self.runAdd.setIcon(QtGui.QIcon.fromTheme('add'))
        self.runAdd.setToolTip("Add run to tests list under a new name")
        self.runAdd.clicked.connect(self.runAddClicked)
        self.test_hbox.addWidget(self.runAdd)

        # file edit view
        self.tabEdit = FileTabs(self.config, self, self.hsplitter)
        self.setwidgetstretch(self.tabEdit, 40, 100)
        self.tabEdit.tabs.setTabsClosable(True)

        # glyph, slot, classes, tabview
        self.tabInfo = QtGui.QTabWidget(self.hsplitter)
        self.setwidgetstretch(self.tabInfo, 30, 100)
        self.tab_glyph = AttribView()
        self.tabInfo.addTab(self.tab_glyph, "Glyph")
        self.tab_slot = AttribView()
        self.tabInfo.addTab(self.tab_slot, "Slot")
        self.tab_classes = Classes(self.font)
        if self.font :
            self.tab_classes.classUpdated.connect(self.font.classUpdated)
        self.tabInfo.addTab(self.tab_classes, "Classes")

        self.horizontalLayout.addWidget(self.hsplitter)

        # bottom pain
        self.tabResults = QtGui.QTabWidget(self.vsplitter)
        self.setwidgetstretch(self.tabResults, 100, 45)
        self.tabResults.setTabPosition(QtGui.QTabWidget.South)
        self.cfg_widget = QtGui.QWidget()
        self.cfg_hbox = QtGui.QHBoxLayout(self.cfg_widget)
        self.cfg_hbox.setContentsMargins(0, 0, 0, 0)
        self.cfg_hbox.setSpacing(0)
        self.cfg_button = QtGui.QToolButton(self.cfg_widget)
        self.cfg_button.setIcon(QtGui.QIcon.fromTheme("document-properties"))
        self.cfg_button.setToolTip("Configure project")
        self.cfg_button.clicked.connect(self.configClicked)
        self.cfg_hbox.addWidget(self.cfg_button)
        self.cfg_open = QtGui.QToolButton(self.cfg_widget)
        self.cfg_open.setIcon(QtGui.QIcon.fromTheme("document-open"))
        self.cfg_open.setToolTip("Open existing project")
        self.cfg_hbox.addWidget(self.cfg_open)
        self.cfg_new = QtGui.QToolButton(self.cfg_widget)
        self.cfg_new.setIcon(QtGui.QIcon.fromTheme("document-new"))
        self.cfg_new.setToolTip("Create new project")
        self.cfg_hbox.addWidget(self.cfg_new)
        self.tabResults.setCornerWidget(self.cfg_widget)

        # font tab
        self.tab_font = FontView(self.font)
        self.tabResults.addTab(self.tab_font, "Font")

        # errors tab
        self.tab_errors = QtGui.QPlainTextEdit()
        self.tab_errors.setReadOnly(True)
        self.tabResults.addTab(self.tab_errors, "Errors")

        # results tab
        self.tab_results = QtGui.QWidget()
        self.tab_vbox = QtGui.QVBoxLayout(self.tab_results)
        self.tab_vbox.setSpacing(0)
        self.run = Run()
        self.runView = RunView()
        self.tab_vbox.addWidget(self.runView.gview)
        self.tab_vbox.addStretch()
        self.tabResults.addTab(self.tab_results, "Results")

        # passes tab
        self.tab_passes = PassesView()
        self.tab_passes.slotSelected.connect(self.tab_slot.changeData)
        self.tab_passes.glyphSelected.connect(self.tab_glyph.changeData)
        self.tab_passes.rowActivated.connect(self.ruledialog)
        self.tabResults.addTab(self.tab_passes, "Passes")
        if self.json :
            self.run.addslots(self.json['output'])
            self.runView.loadrun(self.run, self.font)
            self.runView.slotSelected.connect(self.tab_slot.changeData)
            self.runView.glyphSelected.connect(self.tab_glyph.changeData)
            self.tab_passes.loadResults(self.font, self.json, self.gdx)
            istr = unicode(map(lambda x:unichr(x['unicode']), self.json['chars']))
            self.runEdit.setPlainText(istr.encode('raw_unicode_escape'))
            self.tab_passes.setTopToolTip(istr.encode('raw_unicode_escape'))
            self.runloaded = True
        self.verticalLayout.addWidget(self.vsplitter)
        self.setCentralWidget(self.centralwidget)
        self.tab_font.changeGlyph.connect(self.tab_glyph.changeData)
        self.tabResults.currentChanged.connect(self.setrunEditFocus)

    def setwidgetstretch(self, widget, hori, vert) :
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        if hori != 100 : sizePolicy.setHorizontalStretch(hori)
        if vert != 100 : sizePolicy.setVerticalStretch(vert)
        sizePolicy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
        size = self.size()
        widget.resize(QtCore.QSize(size.width() * hori / 100, size.height() * vert / 100))
        widget.setSizePolicy(sizePolicy)

    def closeEvent(self, event) :
        if self.testsfile :
            self.tabTest.writeXML(self.testsfile)

    def ruledialog(self, row, view, passview) :
        if self.rules : self.rules.close()
        else : self.rules = RuleDialog(self)
        if row == 0 : return
        self.ruleView = PassesView(parent = self.rules, index = row - 1)
        self.ruleView.loadRules(self.font, self.json['passes'][row - 1]['rules'], passview.views[row-1].run, self.gdx)
        self.ruleView.slotSelected.connect(self.tab_slot.changeData)
        self.ruleView.glyphSelected.connect(self.tab_glyph.changeData)
        self.ruleView.rowActivated.connect(self.ruleSelected)
        self.rules.setView(self.ruleView, "Pass %d" % (row))
        self.rules.show()

    def rulesclosed(self, dialog) :
        self.ruleView.slotSelected.disconnect()
        self.ruleView.glyphSelected.disconnect()
        self.ruleView = None

    def ruleSelected(self, row, view, passview) :
        if self.gdx and hasattr(view.run, 'passindex') :
            rule = self.gdx.passes[view.run.passindex][view.run.ruleindex]
            self.tabEdit.selectLine(rule.srcfile, rule.srcline)

    def setRun(self, test) :
        self.runRtl.setChecked(True if test.rtl else False)
        self.runEdit.setPlainText(test.text)
        self.currFeats = dict(test.feats)

    def buildClicked(self) :
        self.tabEdit.writeIfModified()
        if buildGraphite(self.config, self, self.font, self.fontfile) :
            f = file('gdlerr.txt')
            self.tab_errors.setPlainText("".join(f.readlines()))
            f.close()
            self.tabResults.setCurrentWidget(self.tab_errors)
            return False
        else :
            self.tab_errors.setPlainText("")
        if os.path.exists(self.gdxfile) :
            self.gdx = Gdx()
            self.gdx.readfile(self.gdxfile,
                    None if configval(self.config, 'build', 'usemakegdl') else self.font)
        self.feats = FeatureRefs(self.fontfile)
        return True

    def runClicked(self) :
        if self.tabEdit.writeIfModified() and not self.buildClicked() : return
        runfile = NamedTemporaryFile(mode="rw")
        text = self.runEdit.toPlainText().decode('unicode_escape')
        runGraphite(self.fontfile, text, runfile, size = self.font.size, rtl = self.runRtl.isChecked(),
            feats = self.currFeats or self.feats.fval)
        runfile.seek(0)
        self.json = json.load(runfile)
        runfile.close()
        self.run = Run()
        self.run.addslots(self.json['output'])
        self.runView.loadrun(self.run, self.font)
        if not self.runloaded :
            try :
                self.runView.slotSelected.connect(self.tab_slot.changeData)
                self.runView.glyphSelected.connect(self.tab_glyph.changeData)
                self.runloaded = True
            except :
                print "Selection connection failed"
        self.tab_passes.loadResults(self.font, self.json, self.gdx)
        self.tab_passes.setTopToolTip(self.runEdit.toPlainText())
        if self.tabResults.currentWidget() is not self.tab_passes :
            self.tabResults.setCurrentWidget(self.tab_results)

    def runAddClicked(self) :
        text = self.runEdit.toPlainText()
        if not text : return
        (name, ok) = QtGui.QInputDialog.getText(self, "Test Name", "Test Name")
        if not name or not ok : return
        test = Test(text, self.fDialog.currFeats or self.feats.fval, self.runRtl.isChecked(), name)
        self.tabTest.appendTest(test)

    def featuresClicked(self) :
        if self.font :
            fDialog = FeatureDialog(self)
            fDialog.set_feats(self.feats, self.currFeats)
            if fDialog.exec_() :
                self.currFeats = fDialog.get_feats()

    def setrunEditFocus(self, widget) :
        if (isinstance(widget, QtGui.QWidget) and widget == self.tab_results) \
                or (not isinstance(widget, QtGui.QWidget) and widget == 2) :
            self.runEdit.setFocus(QtCore.Qt.MouseFocusReason)

    def updateFileEdit(self, fname) :
        self.tabEdit.updateFileEdit(fname)

    def configClicked(self) :
        d = ConfigDialog(self.config)
        d.exec_()

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

#!/usr/bin/python

from graide.font import Font
from graide.run import Run
from graide.attribview import AttribView
from graide.fontview import FontView
from graide.runview import RunView, RunModel
from graide.passes import PassesView
from graide.ruledialog import RuleDialog
from graide.gdx import Gdx
from graide.filetabs import FileTabs
from PySide import QtCore, QtGui
import json

class MainWindow(QtGui.QMainWindow) :

    def __init__(self, fontfile, apfile, jsonfile, fontsize, gdxfile) :
        super(MainWindow, self).__init__()
        self.rules = None

        if fontfile :
            self.font = Font()
            self.font.loadFont(fontfile, apfile)
            self.font.makebitmaps(fontsize)
        else :
            self.font = None

        if jsonfile :
            f = file(jsonfile)
            self.json = json.load(f)
            f.close()
        else :
            self.json = None

        if gdxfile :
            self.gdx = Gdx()
            self.gdx.readfile(gdxfile)
        else :
            self.gdx = None

        self.setupUi()
        self.createActions()
        self.createToolBars()
        self.createStatusBar()

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
        self.horizontalLayout.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.hsplitter = QtGui.QSplitter(self.widget)
        self.hsplitter.setOrientation(QtCore.Qt.Horizontal)
        self.hsplitter.setHandleWidth(4)

        self.tabInfo = QtGui.QTabWidget(self.hsplitter)
        self.setwidgetstretch(self.tabInfo, 30, 100)
        self.tab_glyph = AttribView()
        self.tabInfo.addTab(self.tab_glyph, "Glyph")
        self.tab_slot = AttribView()
        self.tabInfo.addTab(self.tab_slot, "Slot")
        self.tab_classes = QtGui.QWidget()
        self.tabInfo.addTab(self.tab_classes, "Classes")

        self.tabEdit = FileTabs(self.hsplitter)
        self.setwidgetstretch(self.tabEdit, 40, 100)

        self.tabTest = QtGui.QTabWidget(self.hsplitter)
        self.setwidgetstretch(self.tabTest, 30, 100)

        self.horizontalLayout.addWidget(self.hsplitter)

        self.tabResults = QtGui.QTabWidget(self.vsplitter)
        self.setwidgetstretch(self.tabResults, 100, 45)
        self.tabResults.setTabPosition(QtGui.QTabWidget.South)

        self.tab_font = FontView(self.font)
        self.tabResults.addTab(self.tab_font, "Font")

        self.tab_errors = QtGui.QWidget()
        self.tabResults.addTab(self.tab_errors, "Errors")
        if self.json :
            self.run = Run()
            self.run.addslots(self.json['output'])
            self.tab_results = RunView(self.run, self.font)
            self.tabResults.addTab(self.tab_results, "Results")
            self.tab_results.model.slotSelected.connect(self.tab_slot.changeData)
            self.tab_results.model.glyphSelected.connect(self.tab_glyph.changeData)
            self.tab_passes = PassesView()
            self.tab_passes.loadResults(self.font, self.json['passes'], self.gdx)
            self.tabResults.addTab(self.tab_passes, "Passes")
            self.tab_passes.slotSelected.connect(self.tab_slot.changeData)
            self.tab_passes.glyphSelected.connect(self.tab_glyph.changeData)
            self.tab_passes.rowActivated.connect(self.ruledialog)
        self.verticalLayout.addWidget(self.vsplitter)
        self.setCentralWidget(self.centralwidget)
        
        self.tab_font.changeGlyph.connect(self.tab_glyph.changeData)

    def setwidgetstretch(self, widget, hori, vert) :
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        if hori != 100 : sizePolicy.setHorizontalStretch(hori)
        if vert != 100 : sizePolicy.setVerticalStretch(vert)
        sizePolicy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
        size = self.size()
        widget.resize(QtCore.QSize(size.width() * hori / 100, size.height() * vert / 100))
        widget.setSizePolicy(sizePolicy)

    def createActions(self) :
        pass

    def createToolBars(self) :
        pass

    def createStatusBar(self) :
        pass

    def ruledialog(self, row, model) :
        if self.rules : self.rules.close()
        self.rules = RuleDialog(self)
        self.ruleView = PassesView(parent = self.rules, index = row)
        self.ruleView.loadRules(self.font, self.json['passes'][row]['rules'], model.run, self.gdx)
        self.ruleView.slotSelected.connect(self.tab_slot.changeData)
        self.ruleView.glyphSelected.connect(self.tab_glyph.changeData)
        self.ruleView.rowActivated.connect(self.ruleSelected)
        self.rules.setView(self.ruleView)
        self.rules.show()

    def rulesclosed(self, dialog) :
        self.ruleView.slotSelected.disconnect()
        self.ruleView.glyphSelected.disconnect()
        self.ruleView = None
        self.rules = None

    def ruleSelected(self, row, model) :
        if self.gdx :
            rule = self.gdx.passes[model.run.passindex][model.run.ruleindex]
            self.tabEdit.selectLine(rule.srcfile, rule.srcline)

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

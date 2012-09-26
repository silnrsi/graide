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
from graide.utils import configval, configintval
import os

class FileEntry(QtGui.QWidget) :

    textChanged = QtCore.Signal(str)

    def __init__(self, parent, val, pattern) :
        super(FileEntry, self).__init__(parent)
        self.pattern = pattern
        self.hb = QtGui.QHBoxLayout(self)
        self.hb.setContentsMargins(0, 0, 0, 0)
        self.hb.setSpacing(0)
        self.le = QtGui.QLineEdit(self)
        self.le.textChanged.connect(self.txtChanged)
        if val :
            self.le.setText(val)
        self.hb.addWidget(self.le)
        self.b = QtGui.QToolButton(self)
        self.b.setIcon(QtGui.QIcon.fromTheme("document-open", QtGui.QIcon(":/images/document-open.png")))
        self.hb.addWidget(self.b)
        self.b.clicked.connect(self.bClicked)

    def bClicked(self) :
        (fname, filt) = QtGui.QFileDialog.getSaveFileName(self,
                dir=os.path.dirname(self.le.text()), filter=self.pattern,
                options=QtGui.QFileDialog.DontConfirmOverwrite)
        self.le.setText(os.path.relpath(fname) if fname else "")

    def text(self) :
        return self.le.text()

    def setText(self, txt) :
        self.le.setText(txt)

    def txtChanged(self, txt) :
        self.textChanged.emit(txt)

class PassSpin(QtGui.QSpinBox) :

    def __init__(self, parent = None) :
        super(PassSpin, self).__init__(parent)
        self.setMinimum(0)
        self.setSpecialValueText('None')
        self.setValue(-1)


class ConfigDialog(QtGui.QDialog) :

    def __init__(self, config, parent = None) :
        super(ConfigDialog, self).__init__(parent)
        self.config = config
        
        self.setWindowTitle("Configuration")

        self.vb = QtGui.QVBoxLayout(self)
        self.tb = QtGui.QToolBox(self)
        self.vb.addWidget(self.tb)
        self.ok = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.ok.accepted.connect(self.accept)
        self.ok.rejected.connect(self.reject)
        self.vb.addWidget(self.ok)

        self.main = QtGui.QWidget(self.tb)
        self.main_vb = QtGui.QGridLayout(self.main)
#        self.main_vb.setVerticalSpacing(0)
        self.main_font = FileEntry(self.main, configval(config, 'main', 'font'), 'Font Files (*.ttf)')
        self.main_vb.addWidget(QtGui.QLabel('Font File:'), 0, 0)
        self.main_vb.addWidget(self.main_font, 0, 1, 1, 2)
        self.main_gdl = FileEntry(self.main, configval(config, 'build', 'gdlfile'), 'GDL Files (*.gdl)')
        self.main_vb.addWidget(QtGui.QLabel('GDL File:'), 1, 0)
        self.main_vb.addWidget(self.main_gdl, 1, 1, 1, 2)
        self.main_tests = FileEntry(self.main, configval(config, 'main', 'testsfile'), 'Tests Lists (*.xml)')
        self.main_vb.addWidget(QtGui.QLabel('Tests File:'), 2, 0)
        self.main_vb.addWidget(self.main_tests, 2, 1, 1, 2)
        self.main_rtl = QtGui.QCheckBox()
        self.main_rtl.setChecked(configintval(config, 'main', 'defaultrtl'))
        self.main_vb.addWidget(QtGui.QLabel('Default RTL'), 3, 0)
        self.main_vb.addWidget(self.main_rtl, 3, 1)
        self.main_vb.setRowStretch(4, 1)
        self.tb.addItem(self.main, "General")

        self.build = QtGui.QWidget(self.tb)
        self.build_vb = QtGui.QGridLayout(self.build)
        self.build_ap = FileEntry(self.main, configval(config, 'main', 'ap'), 'AP Files (*.xml)')
        self.build_ap.textChanged.connect(self.apChanged)
        self.build_vb.addWidget(QtGui.QLabel('Attachment Point Database:'), 0, 0, 1, 2)
        self.build_vb.addWidget(self.build_ap, 0, 2)
        self.build_inmake = QtGui.QWidget(self.build)
        self.build_vb.addWidget(self.build_inmake, 1, 0, 1, 3)
        self.build_invb = QtGui.QGridLayout(self.build_inmake)
        self.build_apronly = QtGui.QCheckBox()
        self.build_apronly.setChecked(configintval(config, 'build', 'apronly'))
        self.build_invb.addWidget(QtGui.QLabel('AP Database is read only:'), 0, 0, 1, 2)
        self.build_invb.addWidget(self.build_apronly, 0, 2)
        self.build_cmd = QtGui.QLineEdit(self.build_inmake)
        self.build_cmd.setText(configval(config, 'build', 'makegdlcmd'))
        self.build_cmd.setToolTip('External make gdl command: %a=AP Database, %f=Font File, %g=Generated GDL File,\n    %i=included GDL file %p=positioning pass number')
        self.build_invb.addWidget(QtGui.QLabel('Make GDL Command:'), 1, 0)
        self.build_invb.addWidget(self.build_cmd, 1, 1, 1, 2)
        self.build_inc = FileEntry(self.build_inmake, configval(config, 'build', 'makegdlfile'), 'GDL Files (*.gdl)')
        self.build_invb.addWidget(QtGui.QLabel('Autogenerated GDL file:'), 2, 0)
        self.build_invb.addWidget(self.build_inc, 2, 1, 1, 2)
        self.build_pos = PassSpin(self.build_inmake)
        self.build_invb.addWidget(QtGui.QLabel('Automatic positioning pass:'), 3, 0, 1, 2)
        self.build_invb.addWidget(self.build_pos, 3, 2)
        self.build_vb.setRowStretch(3, 1)
        if not self.build_ap.text() :
            self.build_inmake.setEnabled(False)
        self.tb.addItem(self.build, 'Build')

        self.ui = QtGui.QWidget(self.tb)
        self.ui_vb = QtGui.QGridLayout(self.ui)

        self.ui_editorfont = QtGui.QLineEdit(self.ui)
        self.ui_editorfont.setText(configval(config, 'ui', 'editorfont'))
        self.ui_editorfont.setToolTip('Font to use for editor pane, or specification such as "monospace"')
        self.ui_vb.addWidget(QtGui.QLabel('Editor font spec'), 0, 0)
        self.ui_vb.addWidget(self.ui_editorfont, 0, 1)
        
        self.ui_size = QtGui.QSpinBox(self.ui)
        self.ui_size.setRange(1, 36)
        if config.has_option('ui', 'textsize') :
            self.ui_size.setValue(configintval(config, 'ui', 'textsize'))
        else :
            self.ui_size.setValue(10)
        self.ui_size.setToolTip('Text size in editing windows')
        self.ui_vb.addWidget(QtGui.QLabel('Editor text point size'), 1, 0)
        self.ui_vb.addWidget(self.ui_size, 1, 1)
        
        self.ui_tabstop = QtGui.QSpinBox(self.ui)
        self.ui_tabstop.setRange(1, 100)
        if config.has_option('ui', 'tabstop') :
            self.ui_tabstop.setValue(configintval(config, 'ui', 'tabstop'))
        else :
            self.ui_tabstop.setValue(40)
        self.ui_tabstop.setToolTip('Tab stop in pixels')
        self.ui_vb.addWidget(QtGui.QLabel('Tab stop width'), 2, 0)
        self.ui_vb.addWidget(self.ui_tabstop, 2, 1)
        
        self.ui_gsize = QtGui.QSpinBox(self.ui)
        self.ui_gsize.setRange(1, 288)
        if config.has_option('main', 'size') :
            self.ui_gsize.setValue(configintval(config, 'main', 'size'))
        else :
            self.ui_gsize.setValue(40)
        self.ui_gsize.setToolTip('Pixel size of glyphs in the font window and results, passes, rules, etc.')
        self.ui_vb.addWidget(QtGui.QLabel('Font glyph pixel size'), 3, 0)
        self.ui_vb.addWidget(self.ui_gsize, 3, 1)
        
        self.ui_psize = QtGui.QSpinBox(self.ui)
        self.ui_psize.setRange(1, 1088)
        if config.has_option('ui', 'posglyphsize') :
            self.ui_psize.setValue(configintval(config, 'ui', 'posglyphsize'))
        else :
            self.ui_psize.setValue(200)
        self.ui_psize.setToolTip('Pixel size of glyphs in the position editing window')
        self.ui_vb.addWidget(QtGui.QLabel('Positioning glyph pixel size'), 4, 0)
        self.ui_vb.addWidget(self.ui_psize, 4, 1)
        
        self.ui_sizes = QtGui.QLineEdit(self.ui)
        self.ui_sizes.setText(configval(config, 'ui', 'waterfall'))
        self.ui_sizes.setToolTip('Point sizes for waterfall display, space separated')
        self.ui_vb.addWidget(QtGui.QLabel('Waterfall sizes'), 5, 0)
        self.ui_vb.addWidget(self.ui_sizes, 5, 1)
        
        self.ui_ent = QtGui.QCheckBox()
        self.ui_ent.setChecked(configintval(config, 'ui', 'entities'))
        self.ui_ent.setToolTip('Display entry strings using \\u type entities for non-ASCII chars')
        self.ui_vb.addWidget(QtGui.QLabel('Display character entities'), 6, 0)
        self.ui_vb.addWidget(self.ui_ent, 6, 1)
        
        self.ui_vb.setRowStretch(7, 1)
        self.tb.addItem(self.ui, 'User Interface')

        self.resize(500, 500)

    def apChanged(self, txt) :
        self.build_inmake.setEnabled(True if txt else False)
        if txt and not self.build_inc.text() :
            fname = (self.main_font.text() or configval(self.config, 'main', 'font'))[0:-3] + "gdl"
            count = 0
            nname = fname
            while os.path.exists(nname) :
                nname = fname[:-4] + "_makegdl"
                if count : nname += "_" + str(count)
                nname += ".gdl"
            self.build_inc.setText(nname)

    def updateConfig(self, app, config) :
        self.updateChanged(self.main_font, config, 'main', 'font', (app.loadFont if app else None))
        self.updateChanged(self.main_gdl, config, 'build', 'gdlfile', (app.selectLine if app else None))
        self.updateChanged(self.main_tests, config, 'main', 'testsfile', (app.loadTests if app else None))
        self.cbChanged(self.main_rtl, config, 'main', 'defaultrtl')
        self.updateChanged(self.build_ap, config, 'main', 'ap', (app.loadAP if app else None))
        if self.build_ap.text() :
            config.set('build', 'usemakegdl', "1")
            self.updateChanged(self.build_inc, config, 'build', 'makegdlfile')
            config.set('build', 'pospass', str(self.build_pos.value()))
            self.cbChanged(self.build_apronly, config, 'build', 'apronly')
            txt = self.build_cmd.text()
            if txt :
                config.set('build', 'makegdlcmd', txt)
            elif config.has_option('build', 'makegdlcmd') :
                config.remove_option('build', 'makegdlcmd')
        else :
            config.set('build', 'usemakegdl', '0')
            if config.has_option('build', 'makegdlfile') :
                config.remove_option('build', 'makegdlfile')
                self.build_inc.setText("")
                
        if self.ui_size.value() != configintval(config, 'ui', 'textsize') :
		        config.set('ui', 'textsize', str(self.ui_size.value()))
		        if app : app.tabEdit.setSize(self.ui_size.value())
        self.updateChanged(self.ui_editorfont, config, 'ui', 'editorfont', \
        				(app.tabEdit.updateFont(self.ui_editorfont.text(), self.ui_size.value()) if app else None))
        if self.ui_tabstop.value() != configintval(config, 'ui', 'tabstop') :
            config.set('ui', 'tabstop', str(self.ui_tabstop.value()))
            if app : app.tabEdit.updateTabstop(self.ui_tabstop.value())
        
        if self.ui_gsize.value() != configintval(config, 'main', 'size') :
            config.set('main', 'size', str(self.ui_gsize.value()))
            if app : app.loadFont(configval(config, 'main', 'font'))
        if self.ui_psize.value() != configintval(config, 'ui', 'posglyphsize') :
            config.set('ui', 'posglyphsize', str(self.ui_psize.value()))
            if app : app.setposglyphsize(self.ui_psize.value())
        self.updateChanged(self.ui_sizes, config, 'ui', 'waterfall')
        self.cbChanged(self.ui_ent, config, 'ui', 'entities')

    def updateChanged(self, widget, config, section, option, fn = None) :
        t = widget.text()
        if t != configval(config, section, option) and (t or configval(config, section, option)) :
            if not t :
                config.remove_option(section, option)
            else :
                config.set(section, option, t)
            if fn :
                fn(t)

    def cbChanged(self, widget, config, section, option, fn = None) :
        if widget.isChecked != configval(config, section, option) :
            config.set(section, option, "1" if widget.isChecked() else "0")
            if fn : fn(widget.isChecked())



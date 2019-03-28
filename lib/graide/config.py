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
from graide.utils import configval, configintval
import os


class FileEntry(QtWidgets.QWidget) :

    textChanged = QtCore.Signal(str)

    def __init__(self, parent, val, pattern) :
        super(FileEntry, self).__init__(parent)
        self.pattern = pattern
        hboxLayout = QtWidgets.QHBoxLayout(self)
        hboxLayout.setContentsMargins(0, 0, 0, 0)
        hboxLayout.setSpacing(0)
        self.le = QtWidgets.QLineEdit(self)
        self.le.textChanged.connect(self.txtChanged)
        if val :
            self.le.setText(val)
        hboxLayout.addWidget(self.le)
        self.b = QtWidgets.QToolButton(self)
        self.b.setIcon(QtGui.QIcon.fromTheme("document-open", QtGui.QIcon(":/images/document-open.png")))
        hboxLayout.addWidget(self.b)
        self.b.clicked.connect(self.bClicked)

    def bClicked(self) :
        (fname, filt) = QtWidgets.QFileDialog.getSaveFileName(self,
                dir=os.path.dirname(self.le.text()), filter=self.pattern,
                options=QtWidgets.QFileDialog.DontConfirmOverwrite)
        if fname :
            self.le.setText(os.path.relpath(fname))
        #else Cancel was hit

    def text(self) :
        return self.le.text()

    def setText(self, txt) :
        self.le.setText(txt)

    def txtChanged(self, txt) :
        self.textChanged.emit(txt)
        
#end of class FileEntry


class PassSpin(QtWidgets.QSpinBox) :

    def __init__(self, parent = None) :
        super(PassSpin, self).__init__(parent)
        self.setMinimum(0)
        self.setSpecialValueText('None')
        self.setValue(-1)
        self.setMaximumWidth(50)

# end of class PassSpin


class ConfigDialog(QtWidgets.QDialog) :

    def __init__(self, config, currTab = None, parent = None) :
        super(ConfigDialog, self).__init__(parent)
        self.config = config
        
        self.setWindowTitle("Configure project")

        vboxLayout = QtWidgets.QVBoxLayout(self)
        self.tb = QtWidgets.QToolBox(self)
        vboxLayout.addWidget(self.tb)
        self.ok = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.ok.accepted.connect(self.accept)
        self.ok.rejected.connect(self.reject)
        vboxLayout.addWidget(self.ok)

        # General section
        self.general = QtWidgets.QWidget(self.tb)
        genGridLay = QtWidgets.QGridLayout(self.general)
#        self.general_vb.setVerticalSpacing(0)
        self.general_font = FileEntry(self.general, configval(config, 'main', 'font'), 'Font Files (*.ttf)')
        genGridLay.addWidget(QtWidgets.QLabel('Font File:'), 0, 0)
        genGridLay.addWidget(self.general_font, 0, 1, 1, 2)
        self.general_gdl = FileEntry(self.general, configval(config, 'build', 'gdlfile'), 'GDL Files (*.gdl)')
        genGridLay.addWidget(QtWidgets.QLabel('GDL File:'), 1, 0)
        genGridLay.addWidget(self.general_gdl, 1, 1, 1, 2)
        self.general_tests = FileEntry(self.general, configval(config, 'main', 'testsfile'), 'Tests Lists (*.xml)')
        genGridLay.addWidget(QtWidgets.QLabel('Tests File:'), 2, 0)
        genGridLay.addWidget(self.general_tests, 2, 1, 1, 2)
        self.general_rtl = QtWidgets.QCheckBox()
        self.general_rtl.setChecked(configintval(config, 'main', 'defaultrtl'))
        genGridLay.addWidget(QtWidgets.QLabel('Default RTL'), 3, 0)
        genGridLay.addWidget(self.general_rtl, 3, 1)
        genGridLay.setRowStretch(4, 1)
        self.tb.addItem(self.general, "General")

        # Build section
        # column 0 = main sub-section labels, column 1 - indented labels, column 2 = control for main sub-section,
        # column 3 = controls for indented stuff
        self.build = QtWidgets.QWidget(self.tb)
        buildGridLo = QtWidgets.QGridLayout(self.build)
        
        # makegdl / attachment point generation
        #self.build_apxml = FileEntry(self.general, configval(config, 'main', 'ap'), 'AP Files (*.xml)')
        #self.build_apxml.textChanged.connect(self.apChanged)
        #buildGridLo.addWidget(QtWidgets.QLabel('Attachment point database:'), 0, 0, 1, columnSpan = 2) # cols 0-1
        #buildGridLo.addWidget(self.build_apxml, 0, 2)

        self.build_gdlinc = FileEntry(self.general, configval(config, 'build', 'makegdlfile'), 'GDL Files (*.gdl *.gdh)')
        self.build_gdlinc.textChanged.connect(self.apChanged)
        buildGridLo.addWidget(QtWidgets.QLabel('Autogenerated GDL file:'), 0, 0, 1, columnSpan = 2) # cols 0-1
        buildGridLo.addWidget(self.build_gdlinc, 0, 2)
        
        # sub-controls for AP generation, enabled or disabled as a unit
        self.build_apctrls = QtWidgets.QWidget(self.build)
        buildGridLo.addWidget(self.build_apctrls, 1, 0, 1, 3)
        apGridLo = QtWidgets.QGridLayout(self.build_apctrls)
        apGridLo.setColumnMinimumWidth(0, 125) # !!! Make the columns in this control match build_twkgrid !!!
        apGridLo.setColumnMinimumWidth(1, 20)
        
        self.build_cmd = QtWidgets.QLineEdit(self.build_apctrls)
        self.build_cmd.setMinimumWidth(250)
        self.build_cmd.setText(configval(config, 'build', 'makegdlcmd'))
        self.build_cmd.setToolTip('External make gdl command: %a=AP Database, %f=Font File, %g=Generated GDL File,\n    %i=included GDL file %p=positioning pass number')
        apGridLo.addWidget(QtWidgets.QLabel('Make GDL Command:'), 0, 0)
        apGridLo.addWidget(self.build_cmd, 0, 2, 1, columnSpan = 3) # cols 1-3
        
        #self.build_gdlinc = FileEntry(self.build_apctrls, configval(config, 'build', 'makegdlfile'), 'GDL Files (*.gdl *.gdh)')
        #self.build_gdlinc.setMinimumWidth(250)
        #apGridLo.addWidget(QtWidgets.QLabel('Autogenerated GDL file:'), 2, 0, 1, columnSpan = 2) # cols 0-1
        #apGridLo.addWidget(self.build_gdlinc, 2, 2, 1, columnSpan = 2) # cols 2-3
        
        self.build_apxml = FileEntry(self.build_apctrls, configval(config, 'main', 'ap'), 'AP Files (*.xml)')
        self.build_apxml.setMinimumWidth(250)
        apGridLo.addWidget(QtWidgets.QLabel('Attachment point database:'), 1, 0, 1, columnSpan = 2) # cols 0-1
        apGridLo.addWidget(self.build_apxml, 1, 2, 1, columnSpan = 2) # cols 2-3
        
        self.build_apronly = QtWidgets.QCheckBox()
        self.build_apronly.setChecked(configintval(config, 'build', 'apronly'))
        self.build_apronly.setDisabled(True)  # mechanism to update AP file from Graide is not reliable
        apGridLo.addWidget(QtWidgets.QLabel('AP Database is read-only:'), 2, 0, 1, columnSpan = 2) # cols 0-1
        apGridLo.addWidget(self.build_apronly, 2, 2)
        
        self.build_att = PassSpin(self.build_apctrls)
        attpass = configval(config, 'build', 'attpass')
        if attpass :
            self.build_att.setValue(int(attpass))
        apGridLo.addWidget(QtWidgets.QLabel('Attachment positioning pass:'), 3, 0, 1, columnSpan = 2) # cols 0-1
        apGridLo.addWidget(self.build_att, 3, 2)
        
        #if not self.build_apxml.text() :
        if not self.build_gdlinc.text() :
            self.build_apctrls.setEnabled(False)
           
        self.build_noWarning = QtWidgets.QLineEdit(self.build_apctrls)
        self.build_noWarning.setMinimumWidth(300)
        if config.has_option('build', 'ignorewarnings') :
            self.build_noWarning.setText(configval(config, 'build', 'ignorewarnings'))
        else :
            self.build_noWarning.setText("510,3521")  # warnings to ignore by default
        self.build_noWarning.setToolTip('List warning numbers to be ignored, or \'none\'')
        buildGridLo.addWidget(QtWidgets.QLabel('Ignore warnings:'), 4, 0, 1)
        buildGridLo.addWidget(self.build_noWarning, 4, 2, 1, columnSpan = 3) # cols 1-3
             
        # Tweaking controls
        self.build_tweak = FileEntry(self.general, configval(config, 'build', 'tweakxmlfile'), 'Tweak Files (*.xml)')
        self.build_tweak.textChanged.connect(self.tweakFileChanged)
        buildGridLo.addWidget(QtWidgets.QLabel('Position tweaker file'), 5, 0, 1, columnSpan = 2) # cols 0-1
        buildGridLo.addWidget(self.build_tweak, 5, 2)
        # sub-controls for AP generation, enabled or disabled as a unit
        self.build_twkctrls = QtWidgets.QWidget(self.build)
        buildGridLo.addWidget(self.build_twkctrls, 6, 0, 1, 4)
        tweakGridLo = QtWidgets.QGridLayout(self.build_twkctrls)
        tweakGridLo.setColumnMinimumWidth(0, 125) # make this columns in this control match build_apgrid
        tweakGridLo.setColumnMinimumWidth(1, 20)
        self.build_twkgdl = FileEntry(self.build_apctrls, configval(config, 'build', 'tweakgdlfile'), 'GDL Files (*.gdl *.gdh)')
        self.build_twkgdl.setMinimumWidth(250)
        tweakGridLo.addWidget(QtWidgets.QLabel('Autogenerated GDL file:'), 0, 0, 1, columnSpan = 2) # cols 0-1
        tweakGridLo.addWidget(self.build_twkgdl, 0, 2, 1, columnSpan = 2) # cols 2-3
        self.build_twkpass = PassSpin(self.build_twkctrls)
        tweakpass = configval(config, 'build', 'tweakpass')
        if tweakpass : self.build_twkpass.setValue(int(tweakpass))
        tweakGridLo.addWidget(QtWidgets.QLabel('Tweaking positioning pass:          '), 1, 0, 1, columnSpan = 2) # cols 0-1
        tweakGridLo.addWidget(self.build_twkpass, 1, 2)
        self.build_twktest = QtWidgets.QLineEdit(self.build_twkctrls)
        self.build_twktest.setText(configval(config, 'build', 'tweakconstraint'))
        self.build_twktest.setMinimumWidth(250)
        self.build_twktest.setToolTip('GDL constraint code for tweak pass')
        tweakGridLo.addWidget(QtWidgets.QLabel('Tweak pass constraint:'), 2, 0, 1, columnSpan = 2)
        tweakGridLo.addWidget(self.build_twktest, 2, 2)
        if not self.build_tweak.text() :
            self.build_twkctrls.setEnabled(False)
       
        buildGridLo.setRowStretch(8, 1)
        self.tb.addItem(self.build, 'Build')

        # UI section
        self.ui = QtWidgets.QWidget(self.tb)
        uiGridLo = QtWidgets.QGridLayout(self.ui)

        self.ui_editorfont = QtWidgets.QLineEdit(self.ui)
        self.ui_editorfont.setText(configval(config, 'ui', 'editorfont'))
        self.ui_editorfont.setToolTip('Font to use for editor pane, or specification such as "monospace"')
        uiGridLo.addWidget(QtWidgets.QLabel('Editor font spec'), 0, 0)
        uiGridLo.addWidget(self.ui_editorfont, 0, 1)

        self.ui_size = QtWidgets.QSpinBox(self.ui)
        self.ui_size.setMaximumWidth(60)
        self.ui_size.setRange(1, 36)
        if config.has_option('ui', 'textsize') :
            self.ui_size.setValue(configintval(config, 'ui', 'textsize'))
        else :
            self.ui_size.setValue(10)
        self.ui_size.setToolTip('Text size in editing windows')
        uiGridLo.addWidget(QtWidgets.QLabel('Editor text point size'), 1, 0)
        uiGridLo.addWidget(self.ui_size, 1, 1)

        self.ui_tabstop = QtWidgets.QSpinBox(self.ui)
        self.ui_tabstop.setMaximumWidth(60)
        self.ui_tabstop.setRange(1, 100)
        if config.has_option('ui', 'tabstop') :
            self.ui_tabstop.setValue(configintval(config, 'ui', 'tabstop'))
        else :
            self.ui_tabstop.setValue(40)
        self.ui_tabstop.setToolTip('Tab stop in pixels')
        uiGridLo.addWidget(QtWidgets.QLabel('Tab stop width'), 2, 0)
        uiGridLo.addWidget(self.ui_tabstop, 2, 1)

        self.ui_gsize = QtWidgets.QSpinBox(self.ui)
        self.ui_gsize.setMaximumWidth(60)
        self.ui_gsize.setRange(1, 288)
        if config.has_option('main', 'size') :
            self.ui_gsize.setValue(configintval(config, 'main', 'size'))
        else :
            self.ui_gsize.setValue(40)
        self.ui_gsize.setToolTip('Pixel size of glyphs in the font window and results, passes, and rules panes')
        uiGridLo.addWidget(QtWidgets.QLabel('Font glyph pixel size'), 3, 0)
        uiGridLo.addWidget(self.ui_gsize, 3, 1)

        self.ui_twsize = QtWidgets.QSpinBox(self.ui)
        self.ui_twsize.setMaximumWidth(60)
        self.ui_twsize.setRange(1, 1088)
        if config.has_option('ui', 'tweakglyphsize') :
            self.ui_twsize.setValue(configintval(config, 'ui', 'tweakglyphsize'))
        else :
            self.ui_twsize.setValue(80)
        self.ui_twsize.setToolTip('Pixel size of glyphs in the Tweak editing window')
        uiGridLo.addWidget(QtWidgets.QLabel('Tweak glyph pixel size'), 4, 0)
        uiGridLo.addWidget(self.ui_twsize, 4, 1)

        self.ui_apsize = QtWidgets.QSpinBox(self.ui)
        self.ui_apsize.setMaximumWidth(60)
        self.ui_apsize.setRange(1, 1088)
        if config.has_option('ui', 'attglyphsize') :
            self.ui_apsize.setValue(configintval(config, 'ui', 'attglyphsize'))
        else :
            self.ui_apsize.setValue(200)
        self.ui_apsize.setToolTip('Pixel size of glyphs in the Attach editing window')
        uiGridLo.addWidget(QtWidgets.QLabel('Attachment glyph pixel size'), 5, 0)
        uiGridLo.addWidget(self.ui_apsize, 5, 1)

        self.ui_sizes = QtWidgets.QLineEdit(self.ui)
        self.ui_sizes.setText(configval(config, 'ui', 'waterfall'))
        self.ui_sizes.setToolTip('Point sizes for waterfall display, comma-separated; eg: 10, 12, 16, 20, 48')
        uiGridLo.addWidget(QtWidgets.QLabel('Waterfall sizes'), 6, 0)
        uiGridLo.addWidget(self.ui_sizes, 6, 1)

        self.ui_ent = QtWidgets.QCheckBox()
        self.ui_ent.setChecked(configintval(config, 'ui', 'entities'))
        self.ui_ent.setToolTip('Display entry strings using \\u type entities for non-ASCII chars')
        uiGridLo.addWidget(QtWidgets.QLabel('Display character entities'), 7, 0)
        uiGridLo.addWidget(self.ui_ent, 7, 1)

        self.ui_kernedges = QtWidgets.QCheckBox()
        self.ui_kernedges.setChecked(configintval(config, 'ui', 'kernedges'))
        self.ui_kernedges.setToolTip('Display the edges of glyphs that affect kerning in the Collisions tab')
        uiGridLo.addWidget(QtWidgets.QLabel('Display kerning edges'), 8, 0)
        uiGridLo.addWidget(self.ui_kernedges, 8, 1)

        uiGridLo.setRowStretch(9, 1)
        self.tb.addItem(self.ui, 'User Interface')

        self.resize(500, 500)
        if currTab:
            self.tb.setCurrentIndex(currTab)


    # The name of the attachment point database file changed.
    def apChanged(self, txt) :
        self.build_apctrls.setEnabled(True if txt else False) # enable/disable sub-controls
        if txt and not self.build_gdlinc.text() :
            # Fill in a default for the GDL filename.
            # This is no longer relevant because they must supply a GDL filename in order
            # for the AP controls to be activated.
            fname = (self.general_font.text() or configval(self.config, 'main', 'font'))[0:-3] + "gdl"
            count = 0
            nname = fname
            while os.path.exists(nname) :
                nname = fname[:-4] + "_autogen"
                if count : nname += "_" + str(count)
                count += 1
                nname += ".gdl"
            self.build_gdlinc.setText(nname)
        if txt and (not self.build_att.text() or self.build_att.text() == 'None') :
            # Pass number must be at least 1.
            self.build_att.setValue(1)

    def tweakFileChanged(self, txt) :
        self.build_twkctrls.setEnabled(True if txt else False) # enable/disable sub-controls
        if txt and not self.build_twkgdl.text() :
            # Fill in a default for the tweak GDL filename.
            fname = (self.general_font.text() or configval(self.config, 'main', 'font'))[0:-4] + "_tweaks.gdh"
            count = 1
            nname = fname
            while os.path.exists(nname) :
                nname = fname[:-4] + str(count) + ".gdh"
                count += 1
            self.build_twkgdl.setText(nname)
        if txt and (not self.build_twkpass.text() or self.build_twkpass.text() == 'None') :
            # Pass number must be at least 1.
            self.build_twkpass.setValue(1)

    def updateConfig(self, app, config) :
        self.updateChanged(self.general_font, config, 'main', 'font', "ttf", (app.loadFont if app else None))
        self.updateChanged(self.general_gdl, config, 'build', 'gdlfile', "gdl", (app.selectLine if app else None))
        self.updateChanged(self.general_tests, config, 'main', 'testsfile', "xml", (app.loadTests if app else None))

        self.cbChanged(self.general_rtl, config, 'main', 'defaultrtl')
        self.updateChanged(self.build_apxml, config, 'main', 'ap', "xml", (app.loadAP if app else None))
        #if self.build_apxml.text() :
        if self.build_gdlinc.text() :
            config.set('build', 'usemakegdl', "1")
            self.updateChanged(self.build_gdlinc, config, 'build', 'makegdlfile', "gdl")
            config.set('build', 'attpass', str(self.build_att.value()))
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
                self.build_gdlinc.setText("")

        if self.build_noWarning.text() :
            tempVal = self.build_noWarning.text()
            tempVal = tempVal.replace(' ','')
            config.set('build', 'ignorewarnings', tempVal)
        else :
            if config.has_option('build', 'ignorewarnings') :
                config.remove_option('build', 'ignorewarnings')

        self.updateChanged(self.build_tweak, config, 'build', 'tweakxmlfile',
                None) # TODO
        if self.build_tweak.text() :
            self.updateChanged(self.build_twkgdl, config, 'build', 'tweakgdlfile', "gdl")
            self.updateChanged(self.build_twktest, config, 'build', 'tweakconstraint', "")
            config.set('build', 'tweakpass', str(self.build_twkpass.value()))
            txt = self.build_twktest.text()
            if txt :
                config.set('build', 'tweakconstraint', txt)

        appInit = app and app.isInitialized()

        if self.ui_size.value() != configintval(config, 'ui', 'textsize') :
            config.set('ui', 'textsize', str(self.ui_size.value()))
            if appInit : app.tab_edit.setSize(self.ui_size.value())
        self.updateChanged(self.ui_editorfont, config, 'ui', 'editorfont', "", \
        				(app.tab_edit.updateFont(self.ui_editorfont.text(), self.ui_size.value()) if appInit else None))
        if self.ui_tabstop.value() != configintval(config, 'ui', 'tabstop') :
            config.set('ui', 'tabstop', str(self.ui_tabstop.value()))
            if appInit : app.tab_edit.updateTabstop(self.ui_tabstop.value())

        if self.ui_gsize.value() != configintval(config, 'main', 'size') :
            config.set('main', 'size', str(self.ui_gsize.value()))
            if appInit : app.loadFont(configval(config, 'main', 'font'))
        if self.ui_twsize.value() != configintval(config, 'ui', 'tweakglyphsize') :
            config.set('ui', 'tweakglyphsize', str(self.ui_twsize.value()))
            if appInit : app.setTweakGlyphSize(self.ui_twsize.value())
        if self.ui_apsize.value() != configintval(config, 'ui', 'attglyphsize') :
            config.set('ui', 'attglyphsize', str(self.ui_apsize.value()))
            if appInit : app.setAttGlyphSize(self.ui_apsize.value())
        self.updateChanged(self.ui_sizes, config, 'ui', 'waterfall', "")
        self.cbChanged(self.ui_ent, config, 'ui', 'entities')
        self.cbChanged(self.ui_kernedges,  config, 'ui', 'kernedges')

    # When OK is clicked on config dialog:
    def updateChanged(self, widget, config, section, option, defaultExt, fn = None) :
        t = widget.text()

        # Append the default extension.
        ext = os.path.splitext(t)[1]
        if t != "" and ext == "" and defaultExt != "" :
            t = t + "." + defaultExt

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

    def currentTab(self) :
        return self.tb.currentIndex()

# end of class ConfigDialog

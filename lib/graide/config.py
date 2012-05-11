
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
from graide.utils import configval
import os

class FileEntry(QtGui.QWidget) :

    def __init__(self, parent, val, pattern) :
        super(FileEntry, self).__init__(parent)
        self.pattern = pattern
        self.hb = QtGui.QHBoxLayout(self)
        self.hb.setContentsMargins(0, 0, 0, 0)
        self.hb.setSpacing(0)
        self.le = QtGui.QLineEdit(self)
        if val :
            self.le.setText(val)
        self.hb.addWidget(self.le)
        self.b = QtGui.QToolButton(self)
        self.b.setIcon(QtGui.QIcon.fromTheme("document-open"))
        self.hb.addWidget(self.b)
        self.b.clicked.connect(self.bClicked)

    def bClicked(self) :
        (fname, filt) = QtGui.QFileDialog.getSaveFileName(self,
                dir=os.path.dirname(self.le.text()), filter=self.pattern,
                options=QtGui.QFileDialog.DontConfirmOverwrite)
        self.le.setText(os.path.relpath(fname) if fname else "")

    def text(self) :
        return self.le.text()

class ConfigDialog(QtGui.QDialog) :

    def __init__(self, config, parent = None) :
        super(ConfigDialog, self).__init__(parent)
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
        self.main_ap = FileEntry(self.main, configval(config, 'main', 'ap'), 'AP Files (*.xml)')
        self.main_vb.addWidget(QtGui.QLabel('Attachment Point Database:'), 2, 0, 1, 2)
        self.main_vb.addWidget(self.main_ap, 2, 2)
        self.main_tests = FileEntry(self.main, configval(config, 'main', 'testsfile'), 'Tests Lists (*.xml)')
        self.main_vb.addWidget(QtGui.QLabel('Tests File:'), 3, 0)
        self.main_vb.addWidget(self.main_tests, 3, 1, 1, 2)
        self.main_vb.setRowStretch(4, 1)
        self.tb.addItem(self.main, "General")

        self.build = QtGui.QWidget(self.tb)
        self.build_vb = QtGui.QGridLayout(self.build)
        self.build_make = QtGui.QCheckBox()
        self.build_make.stateChanged.connect(self.makegdlClicked)
        self.build_vb.addWidget(QtGui.QLabel('Autogenerate font level GDL'), 0, 1, 1, 2)
        self.build_vb.addWidget(self.build_make, 0, 0)
        self.build_inc = FileEntry(self.build, configval(config, 'build', 'includefile'), 'GDL Files (*.gdl)')
        self.build_vb.addWidget(QtGui.QLabel('Included GDL file:'), 1, 1)
        self.build_vb.addWidget(self.build_inc, 1, 2)
        self.build_vb.setRowStretch(2, 1)
        if configval(config, 'build', 'usemakegdl') :
            self.build_make.setChecked(True)
        else :
            self.build_inc.setEnabled(False)
        self.tb.addItem(self.build, 'Build')

    def makegdlClicked(self) :
        self.build_inc.setEnabled(self.build_make.isChecked())

    def updateConfig(self, app, config) :
        self.updateChanged(self.main_font, config, 'main', 'font', app.loadFont)
        self.updateChanged(self.main_gdl, config, 'build', 'gdlfile')
        self.updateChanged(self.main_ap, config, 'main', 'ap', app.loadAP)
        self.updateChanged(self.main_tests, config, 'main', 'testsfile', app.loadTests)
        self.updateChanged(self.build_inc, config, 'build', 'includefile')
        if self.build_make.isChecked() != configval(config, 'build', 'usemakegdl') :
            config.set('build', 'usemakegdl', "1" if self.build_make.isChecked() else "0")

    def updateChanged(self, widget, config, section, option, fn = None) :
        t = widget.text()
        if t != configval(config, section, option) and (t or configval(config, section, option)) :
            if not t :
                config.remove_option(section, option)
            else :
                config.set(section, option, t)
            if fn :
                fn(t)



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
        (self.main_fontw, self.main_font) = self.fileEntry(self.main, configval(config, 'main', 'font'), 'Font Files (*.ttf)')
        self.main_vb.addWidget(QtGui.QLabel('Font File:'), 0, 0)
        self.main_vb.addWidget(self.main_fontw, 0, 1)
        (self.main_gdxw, self.main_gdx) = self.fileEntry(self.main, configval(config, 'main', 'gdx'), 'Debug Files (*.gdx)')
        self.main_vb.addWidget(QtGui.QLabel('Graphite Debug File:'), 1, 0)
        self.main_vb.addWidget(self.main_gdxw, 1, 1)
        (self.main_apw, self.main_ap) = self.fileEntry(self.main, configval(config, 'main', 'ap'), 'AP Files (*.xml)')
        self.main_vb.addWidget(QtGui.QLabel('Attachment Point Database:'), 2, 0)
        self.main_vb.addWidget(self.main_apw, 2, 1)
        (self.main_testsw, self.main_tests) = self.fileEntry(self.main, configval(config, 'main', 'testsfile'), 'Tests Lists (*.xml)')
        self.main_vb.addWidget(QtGui.QLabel('Tests File:'), 3, 0)
        self.main_vb.addWidget(self.main_testsw, 3, 1)
        self.tb.addItem(self.main, "General")

    def fileEntry(self, parent, val, pattern) :
        res = QtGui.QWidget(parent)
        hb = QtGui.QHBoxLayout(res)
        le = QtGui.QLineEdit(res)
        if val :
            le.setText(val)
        hb.addWidget(le)
        b = QtGui.QToolButton(res)
        b.setIcon(QtGui.QIcon.fromTheme("document-open"))
        hb.addWidget(b)

        def bClicked() :
            (fname, filt) = QtGui.QFileDialog.getSaveFileName(res, dir = os.path.dirname(le.text()), filter = pattern)
            le.setText(fname)

        b.clicked.connect(bClicked)
        return (res, le)


            

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
from graide.layout import Layout
import os, re

class Errors(QtGui.QListWidget) :

    errorSelected = QtCore.Signal(str, int)

    def __init__(self, parent = None) :
        super(Errors, self).__init__(parent)
        self.itemDoubleClicked.connect(self.selectItem)

    def addItem(self, txt, srcfile = None, line = 0) :
        w = QtGui.QListWidgetItem(txt, self)
        w.srcfile = srcfile
        w.line = line
        return w

    def addError(self, txt, srcfile = None, line = 0) :
        w = self.addItem(txt, srcfile, line)
        w.setBackground(Layout.errorColour)

    def addWarning(self, txt, srcfile = None, line = 0) :
        w = self.addItem(txt, srcfile, line)
        w.setBackground(Layout.warnColour)

    def addGdlErrors(self, fname) :
        if not os.path.exists(fname) : return
        f = file(fname)
        for l in f.readlines() :
            l = l.strip()
            m = re.match(r'^(.*?)\((\d+)\) : (error|warning)\((\d+)\): (.*)$', l)
            if m :
                if m.group(3) == 'error' :
                    self.addError(l, m.group(1), int(m.group(2)) - 1)
                elif m.group(3) == 'warning' :
                    self.addWarning(l, m.group(1), int(m.group(2)) - 1)
                continue
            m = re.match(r'(error|warning)\((\d+)\): (.*)$', l)
            if m :
                if m.group(1) == 'error' :
                    self.addError(l)
                else :
                    self.addWarning(l)
            m = re.match(r'^Compilation', l)
            if m :
                self.addItem(l.strip())
        f.close()

    def selectItem(self, item) :
        if item.srcfile and len(item.srcfile) :
            self.errorSelected.emit(item.srcfile, item.line)


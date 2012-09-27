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

# This class is no longer used. The PassesView class is used for the Rules tab.

from PySide import QtGui, QtCore

class RuleDialog(QtGui.QDialog) :

    def __init__(self, parent = None) :
        super(RuleDialog, self).__init__(parent)
        self.position = None
        self.currsize = None
        self.isHidden = False
        self.setSizeGripEnabled(True)
        self.setWindowFlags(QtCore.Qt.Tool)

    def setView(self, runview, title = None) :
        if title : self.setWindowTitle(title)
        self.runview = runview
        runview.resize(self.size())
        #self.setLayout(runview)
        if self.position :
            self.move(self.position)
        if self.currsize :
            self.resize(self.currsize)
        else :
            self.resize(550, 300)
        self.isHidden = False

    def closeEvent(self, event) :
        if not self.isHidden :
            self.position = self.pos()
            self.currsize = self.size()
            self.parent().rulesclosed(self)
            self.hide()
            self.isHidden = True

    def resizeEvent(self, event) :
        self.currsize = self.size()
        if self.runview :
            self.runview.resize(self.currsize)

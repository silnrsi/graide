#    Copyright 2013, SIL International
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
from graide.config import FileEntry
import os


class StartDialog(QtGui.QDialog) :
    
    def __init__(self, config, recentProjects, parent = None) :
        super(StartDialog, self).__init__(parent)
        
        self.recentProjects = recentProjects
        
        self.setWindowTitle("Starting Graide")
        appicon = QtGui.QIcon(':/images/graide_logo_256px.png')
        appicon.addFile(':/images/graide-logo_16px.png')
        appicon.addFile(':/images/graide-logo_96px.png')
        appicon.addFile(':/images/graide logo.svg')
        self.setWindowIcon(appicon)
        
        vLayout = QtGui.QVBoxLayout(self)
        frame = QtGui.QFrame(self)
        vLayout.addWidget(frame)
        
        gridLayout = QtGui.QGridLayout(frame)
        #frame.addItem(gridLayout)
        
        self.radioRecent = QtGui.QRadioButton("Open a recent project", frame)
        self.comboRecent = QtGui.QComboBox(frame)
        self.comboRecent.connect(QtCore.SIGNAL('currentIndexChanged(int)'), self.chooseRecentProject)
        self.radioExisting = QtGui.QRadioButton("Open an existing project", frame)
        self.fileExisting = FileEntry(frame, "", 'Configuration files (*.cfg *.ini)')
        self.fileExisting.textChanged.connect(self.fileSelected)
        self.radioCreate = QtGui.QRadioButton("Create a new project", frame)
        recentProjectFiles = self.recentProjects.projects()
        for (basename, fullname) in recentProjectFiles :
            self.comboRecent.addItem(basename)
        gridLayout.addWidget(self.radioRecent, 0, 0)
        gridLayout.addWidget(self.comboRecent, 0, 1)
        gridLayout.addWidget(self.radioExisting, 1, 0)
        gridLayout.addWidget(self.fileExisting, 1, 1)
        gridLayout.addWidget(self.radioCreate, 2, 0)
        
        gridLayout.setRowMinimumHeight(0, 30)
        gridLayout.setRowMinimumHeight(1, 30)
        gridLayout.setRowMinimumHeight(2, 30)
        
        gridLayout.setColumnMinimumWidth(0, 150)
        
        self.okExit = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        self.okExit.addButton("Exit", QtGui.QDialogButtonBox.RejectRole)
        self.okExit.accepted.connect(self.accept)
        self.okExit.rejected.connect(self.reject)
        vLayout.addSpacing(25)
        vLayout.addWidget(self.okExit)
        
        self.radioRecent.setChecked(True)

    # end of init
    

    def fileSelected(self) :
        self.radioExisting.setChecked(True)

        
    def chooseRecentProject(self) :
        self.radioRecent.setChecked(True)


    def returnResults(self) :
        if self.radioCreate.isChecked() :
            return "!!create-new-project!!"
        elif self.radioExisting.isChecked() :
            # returns a filename with a path relative to the current working directory
            return self.fileExisting.text()
        elif self.radioRecent.isChecked() :
            recentProjectFiles = self.recentProjects.projects() # (basename, fullname) pairs
            i = self.comboRecent.currentIndex()
            return recentProjectFiles[i][1]
        else :
            return False
            
    
# end of class StartDialog
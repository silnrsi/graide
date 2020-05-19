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


from qtpy import QtGui, QtWidgets
from graide.featureselector import FeatureDialog
from xml.etree import cElementTree as et
from graide.layout import Layout
from graide.utils import configintval, as_entities, popUpError
from builtins import chr
import re

class Test(object) :
    def __init__(self, text, feats, lang = None, rtl = False, name = None, comment = "", width = 100, bgnd = 'white') :
        self.text = text
        self.feats = self.fixFeatsDict(dict(feats))    # feature IDs -> values
        self.name = name or text
        self.rtl = rtl
        self.lang = lang
        self.comment = comment
        self.foreground = QtGui.QColor('black')
        bcolorRes = QtGui.QColor(bgnd)
        if bcolorRes.isValid() :
            self.background = bcolorRes
        else :
            self.background = QtGui.QColor('white')
        self.width = width

    def fixFeatsDict(self, dict):
        "Convert feature dict keys to str, not bytes."
        for k,v in dict.items():
            """if isinstance(k, str):
                kbytes = k.encode('utf-8')  # convert to bytes
                dict[kbytes] = v
                dict.pop(k, None)"""

            if isinstance(k, bytes):
                kstr = k.decode('utf-8')  #  convert to str
                dict[kstr] = v
                dict.pop(k, None)
        return dict

    def editDialog(self, parent, isTweak = False) :
        self.parent = parent
        self.featDialog = None
        
        dlg = QtWidgets.QDialog()
        topWidget = QtWidgets.QWidget(dlg)
        hboxLayout = QtWidgets.QHBoxLayout()
        topWidget.setLayout(hboxLayout)
        gridLayout = QtWidgets.QGridLayout()
        gridLayout.addWidget(topWidget, 4, 1)
        dlg.setLayout(gridLayout)
        
        gridLayout.addWidget(QtWidgets.QLabel('Name:', dlg), 0, 0)
        editName = QtWidgets.QLineEdit(self.name, dlg)
        gridLayout.addWidget(editName, 0, 1)
        gridLayout.addWidget(QtWidgets.QLabel('Text:', dlg), 1, 0)
        if configintval(parent.config, 'ui', 'entities') :
            t = as_entities(self.text)
        else :
            t = self.text
        editText = QtWidgets.QPlainTextEdit(t, dlg)
        editText.setMaximumHeight(Layout.runEditHeight)
        gridLayout.addWidget(editText, 1, 1)
        gridLayout.addWidget(QtWidgets.QLabel('Comment:', dlg), 2, 0)
        editComment = QtWidgets.QPlainTextEdit()
        editComment.setPlainText(self.comment)
        editComment.setMaximumHeight(Layout.runEditHeight)
        gridLayout.addWidget(editComment, 2, 1)
        cbRTL = QtWidgets.QCheckBox('RTL', dlg)
        cbRTL.setChecked(self.rtl)
        gridLayout.addWidget(cbRTL, 3, 1)

        colourButton = QtWidgets.QToolButton(topWidget)
        colourButton.setIcon(QtGui.QIcon.fromTheme('background', QtGui.QIcon(":/images/format-fill-color.png")))
        colourButton.setToolTip('Set background colour')
        colourButton.clicked.connect(self.doColour)
        hboxLayout.addWidget(colourButton)
        
        featButton = QtWidgets.QPushButton('Features', topWidget)
        hboxLayout.addWidget(featButton)
        
        hboxWidget = QtWidgets.QWidget(dlg)  # generic widget containing the OK/Cancel buttons
        hboxButtonLo = QtWidgets.QHBoxLayout()
        hboxWidget.setLayout(hboxButtonLo)
        gridLayout.addWidget(hboxWidget, 5, 1)
        
        buttonOk = QtWidgets.QPushButton('OK', hboxWidget)
        hboxButtonLo.addWidget(buttonOk)
        buttonCancel = QtWidgets.QPushButton('Cancel', hboxWidget)
        hboxButtonLo.addWidget(buttonCancel)
        
        if (self.name == "") :
            dlg.setWindowTitle("Add new tweak" if isTweak else "Add new test")
        else :
            dlg.setWindowTitle("Edit tweak" if isTweak else "Edit test")
            
        featButton.clicked.connect(self.featClicked)
        buttonOk.clicked.connect(dlg.accept)
        buttonCancel.clicked.connect(dlg.reject)
        
        res = dlg.exec_()
        if res :
            self.name = editName.text()
            self.text = editText.toPlainText()
            self.rtl = cbRTL.isChecked()
            self.comment = editComment.toPlainText()
            if self.featDialog :
                self.lang = self.featDialog.get_lang()
                if self.lang not in self.parent.feats : # default feats for language are owned by the MainWindow
                    self.lang = None
                self.feats = self.featDialog.get_feats(self.parent.feats[self.lang])
                self.width = self.featDialog.get_width()
        del self.featDialog
        del self.parent
        return res

    def featClicked(self) :
        newD = False
        if not self.featDialog :
            d = FeatureDialog(self.parent)  # parent = main window
            # Initialize the dialog with the features associated with the language.
            fBase = self.parent.feats[self.lang]  # default feats for language are owned by the MainWindow
            f = fBase.copy()
            f.apply(self.feats)
            d.set_feats(f, fBase, lang = self.lang)
            self.featDialog = d
            newD = True
        d = self.featDialog
        if not d.exec_() :  # Cancel
            if newD : self.featDialog = None


    def setWidth(self, w) :
        self.width = w

    # Launch the color dialog and store the result.
    def doColour(self) :
        d = QtWidgets.QColorDialog
        res = d.getColor(self.background)
        if res.isValid() :
            self.background = res
        #else they hit Cancel

    # Add this test to the XML output tree.
    def addXML(self, parent) :
        try :
            e = et.SubElement(parent, 'test')
            if self.comment :
                c = et.SubElement(e, 'comment')
                c.text = self.comment
            t = et.SubElement(e, 'string')
            if self.text :
                t.text = re.sub(r'\\u([0-9A-Fa-f]{4})|\\U([0-9A-Fa-f]{5,8})', \
                    lambda m:chr(int(m.group(1) or m.group(2), 16)), self.text)
            else :
                t.text = ""
            e.set('label', self.name)
            if self.background != QtGui.QColor('white') : 
                e.set('background', self.background.name())
            if self.rtl : e.set('rtl', 'True')
            if self.width != 100 : e.set('expand', str(self.width))
        except :
            popUpError(msg = "ERROR: test could not be saved: " + self.name)

        return e

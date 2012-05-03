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

from PySide import QtCore, QtGui
from graide.dataobj import DataObj
from graide.utils import ModelSuper

class GlyphDelegate(QtGui.QAbstractItemDelegate) :

    textheight = 12

    def __init__(self, font, parent=None) :
        super(GlyphDelegate, self).__init__(parent)
        self.brect = font.pixrect
        self.desc = font.pixrect.height() - font.top

    def paint(self, painter, option, index) :
        if option.state & QtGui.QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        g = index.data()
        if g :
            if g.pixmap :
                x = option.rect.left() + (option.rect.width() - g.pixmap.width()) / 2
                y = option.rect.bottom() - self.textheight - self.desc - g.top
                painter.drawPixmap(x, y, g.pixmap)
            font = painter.font()
            myfont = QtGui.QFont(font)
            myfont.setPointSize(myfont.pointSize() * 0.8)
            theight = myfont.pixelSize()
            painter.setFont(myfont)
            namerect = QtCore.QRect(option.rect.left(), option.rect.bottom()-self.textheight, option.rect.width(), self.textheight)
            painter.drawText(namerect, QtCore.Qt.AlignLeft | QtCore.Qt.TextSingleLine, str(g))
            painter.setPen(QtCore.Qt.red)
            namerect.translate(QtCore.QPoint(0, -option.rect.height() + self.textheight))
            painter.drawText(namerect, QtCore.Qt.AlignRight | QtCore.Qt.TextSingleLine, str(g.gid))
            painter.setPen(QtCore.Qt.black)
            painter.setFont(font)

    def sizeHint(self, option, index) :
        return self.brect.size() + QtCore.QSize(0, self.textheight)

class FontModel(QtCore.QAbstractTableModel, ModelSuper) :

    def __init__(self, font, delegate, width = 800) :
        super(FontModel, self).__init__()
        self.font = font
        self.delegate = delegate
        self.columns = 0
        self.set_width(width)

    def set_width(self, width) :
        oldcolumns = self.columns
        self.beginResetModel()
        self.columns = width / (self.delegate.sizeHint(None, None).width() + 1)
        self.rows = (len(self.font) + self.columns - 1) / self.columns
        if oldcolumns and oldcolumns > self.columns :
            self.columnsRemoved.emit(self.createIndex(0, 0), oldcolumns, self.columns)
        elif oldcolumns and oldcolumns < self.columns :
            self.columnsInserted.emit(self.createIndex(0, 0), oldcolumns, self.columns)
        self.endResetModel()

    def rowCount(self, parent) :
        return self.rows

    def columnCount(self, parent) :
        return self.columns

    def data(self, index, role) :
        if not index.isValid() or role != QtCore.Qt.DisplayRole:
            return None

        return self.font[index.row() * self.columns + index.column()]

class FontView(QtGui.QTableView) :

    changeGlyph = QtCore.Signal(DataObj, ModelSuper)

    def __init__(self, font, parent = None) :
        super(FontView, self).__init__(parent)
        
        width = self.viewport().size().width()
        self.delegate = GlyphDelegate(font)
        self.model = FontModel(font, self.delegate, width)
        self.setModel(self.model)
        self.setItemDelegate(self.delegate)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.activated.connect(self.do_activate)
#       self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)

    def resizeEvent(self, event) :
        self.model.set_width(self.viewport().size().width())
        self.resizeColumnsToContents()
        super(FontView, self).resizeEvent(event)

    def do_activate(self, index) :
        self.changeGlyph.emit(index.data(), self.model)

def clicked_glyph(index) :
    print str(index.data())

if __name__ == "__main__" :
    from graide.font import Font
    import sys

    app = QtGui.QApplication(sys.argv)
    font = Font()
    font.loadFont("/usr/share/fonts/opentype/charissil/CharisSIL-R.ttf")
    font.makebitmaps(40)
    table = FontView(font)
    table.activated.connect(clicked_glyph)
    table.show()
    sys.exit(app.exec_())

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

from qtpy import QtCore, QtGui, QtWidgets

class GlyphDelegate(QtWidgets.QAbstractItemDelegate) :

    textheight = 12

    def __init__(self, font, parent=None) :
        super(GlyphDelegate, self).__init__(parent)
        self.font = font

    def paint(self, painter, option, index) :
        g = index.data()
        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        if g :
            if g.pixmap :
                x = option.rect.left() + (option.rect.width() - g.pixmap.width()) / 2
                y = option.rect.bottom() - self.textheight - self.font.pixrect.height() + self.font.top - g.top
                painter.drawPixmap(x, y, g.pixmap)
            font = painter.font()
            myfont = QtGui.QFont(font)
            myfont.setPointSize(myfont.pointSize() * 0.75)
            theight = myfont.pixelSize()
            painter.setFont(myfont)
            namerect = QtCore.QRect(option.rect.left(), option.rect.bottom()-self.textheight, option.rect.width(), self.textheight)
            painter.drawText(namerect, QtCore.Qt.AlignLeft | QtCore.Qt.TextSingleLine, str(g.name))
            namerect.translate(QtCore.QPoint(0, -option.rect.height() + self.textheight))
            if g.uid :
                painter.drawText(namerect, QtCore.Qt.AlignLeft | QtCore.Qt.TextSingleLine, "%04X" % g.uid)
            painter.setPen(QtCore.Qt.red)
            painter.drawText(namerect, QtCore.Qt.AlignRight | QtCore.Qt.TextSingleLine, str(g.gid))
            painter.setPen(QtCore.Qt.black)
            painter.setFont(font)

    def sizeHint(self, option, index) :
        return self.font.pixrect.size() + QtCore.QSize(0, 2 * self.textheight)

class FontModel(QtCore.QAbstractTableModel) :

    def __init__(self, font, delegate, width = 800) :
        super(FontModel, self).__init__()
        self.font = font
        self.delegate = delegate
        self.columns = 0
        self.set_width(width)

    def set_width(self, width) :
        oldcolumns = self.columns
        self.beginResetModel()
        cellwidth = self.delegate.sizeHint(None, None).width() + 1
        if cellwidth < 56 : cellwidth = 56
        self.columns = width / cellwidth
        self.rows = (self.font.numGlyphs + self.columns - 1) / self.columns
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

class FontView(QtWidgets.QTableView) :

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

    def resizeEvent(self, event) :
        self.model.set_width(self.viewport().size().width())
        self.resizeColumnsToContents()
        super(FontView, self).resizeEvent(event)

    def keyPressEvent(self, event) :
        if event.matches(QtGui.QKeySequence.Copy) :
            res = []
            for i in self.selectedIndexes() :
                g = i.data()
                res.append(g.GDLName())
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText("  ".join(res))
        else :
            super(FontView, self).keyPressEvent(event)

    def classSelected(self, name) :
        self.model.font.classSelected(name)
        self.viewport().update()

def clicked_glyph(index) :
    print(str(index.data()))

if __name__ == "__main__" :
    from ttfrename.font import Font
    import sys

    def clicked(index) :
        font.editGlyph(index.data())

    app = QtWidgets.QApplication(sys.argv)
    font = Font()
    font.loadFont(sys.argv[1], 40)
    table = FontView(font)
    table.activated.connect(clicked)
    table.show()
    sys.exit(app.exec_())

from PySide import QtGui, QtCore

class EditFile(QtGui.QPlainTextEdit) :

    highlighFormat = None

    def __init__(self, fname) :
        super(EditFile, self).__init__()
        self.fname = fname
        self.selection = QtGui.QTextEdit.ExtraSelection()
        self.selection.format = QtGui.QTextCharFormat()
        self.selection.format.setBackground(QtGui.QColor(QtCore.Qt.yellow))
        self.selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
#        self.setFontFamily('Courier')
#        self.setFontPointSize(10)
        f = file(fname)
        self.setPlainText("".join(f.readlines()))
        f.close()

    def highlight(self, lineno) :
        self.selection.cursor = QtGui.QTextCursor(self.document().findBlockByLineNumber(lineno))
        self.setExtraSelections([self.selection])
        self.setTextCursor(self.selection.cursor)

    def unhighlight(self, lineno) :
        self.setExtraSelections([])

class FileTabs(QtGui.QTabWidget) :

    def __init__(self, parent = None) :
        super(FileTabs, self).__init__(parent)
        self.currselIndex = None
        self.currselline = 0

    def selectLine(self, fname, lineno) :
        for i in range(self.count()) :
            f = self.widget(i)
            if f.fname == fname :
                self.highlightLine(i, lineno)
                return
        newFile = EditFile(fname)
        self.addTab(newFile, fname)
        self.highlightLine(self.count() - 1, lineno)

    def highlightLine(self, tabindex, lineno) :
        if self.currselIndex != None and (self.currselIndex != tabindex or self.currselline != lineno) :
            self.widget(self.currselIndex).unhighlight(self.currselline)
        self.widget(tabindex).highlight(lineno)
        self.currselIndex = tabindex
        self.currselline = lineno


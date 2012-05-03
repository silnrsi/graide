from PySide import QtGui, QtCore
import os

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
        self.selection.cursor = QtGui.QTextCursor(self.document().findBlockByNumber(lineno))
        self.setExtraSelections([self.selection])
        self.setTextCursor(self.selection.cursor)

    def unhighlight(self, lineno) :
        self.setExtraSelections([])

    def writeIfModified(self) :
        if self.document().isModified() :
            f = file(self.fname, "w")
            f.write(self.document().toPlainText())
            f.close()
            return True
        else :
            return False

    def closeEvent(self, event) :
        self.writeIfModified()


class FileTabs(QtGui.QTabWidget) :

    def __init__(self, config, parent = None) :
        super(FileTabs, self).__init__(parent)
        self.currselIndex = None
        self.currselline = 0
        self.config = config
        self.tabCloseRequested.connect(self.closeRequest)

    def selectLine(self, fname, lineno) :
        for i in range(self.count()) :
            f = self.widget(i)
            if f.fname == fname :
                self.highlightLine(i, lineno)
                return
        newFile = EditFile(fname)
        self.addTab(newFile, fname)
        self.highlightLine(self.count() - 1, lineno)
        if self.config.has_option('build', 'gdlfile') and os.path.abspath(self.config.get('build', 'gdlfile')) == os.path.abspath(fname) :
            newFile.setReadOnly(True)

    def highlightLine(self, tabindex, lineno) :
        if self.currselIndex != None and (self.currselIndex != tabindex or self.currselline != lineno) :
            self.widget(self.currselIndex).unhighlight(self.currselline)
        self.widget(tabindex).highlight(lineno)
        self.currselIndex = tabindex
        self.currselline = lineno

    def writeIfModified(self) :
        res = False
        for i in range(self.count()) :
            res = res | self.widget(i).writeIfModified()
        return res

    def closeRequest(self, index) :
        self.widget(index).close()
        self.removeTab(index)

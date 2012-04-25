from PySide import QtGui, QtCore

class RuleDialog(QtGui.QDialog) :

    def __init__(self, parent = None) :
        super(RuleDialog, self).__init__(parent)
        self.position = None
        self.currsize = None
        self.setSizeGripEnabled(True)

    def setView(self, runview) :
        self.runview = runview
        runview.resize(self.size())
        #self.setLayout(runview)
        if self.position :
            self.move(self.position)
        if self.currsize :
            self.resize(self.size)
        else :
            self.resize(300, 300)

    def closeEvent(self, event) :
        self.position = self.pos()
        self.currsize = self.size()
        self.parent().rulesclosed(self)
        event.accept()

    def resizeEvent(self, event) :
        self.currsize = self.size()
        if self.runview :
            self.runview.resize(self.currsize)

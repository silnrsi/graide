from PySide import QtGui, QtCore

class RuleDialog(QtGui.QDialog) :

    def __init__(self, parent = None) :
        super(RuleDialog, self).__init__(parent)
        self.position = None
        self.currsize = None
        self.isHidden = False
        self.setSizeGripEnabled(True)
        self.setWindowFlags(QtCore.Qt.Tool)

    def setView(self, runview) :
        self.runview = runview
        runview.resize(self.size())
        #self.setLayout(runview)
        if self.position :
            self.move(self.position)
        if self.currsize :
            self.resize(self.currsize)
        else :
            self.resize(300, 300)
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

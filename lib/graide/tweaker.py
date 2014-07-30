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
from xml.etree import cElementTree as XmlTree
from graide.font import GraideFont
from graide.test import Test
from graide.utils import configval, configintval, reportError, relpath, ETcanon, ETinsert
from graide.layout import Layout
from graide.run import Run
from graide.runview import GlyphPixmapItem, RunView
from graide.posedit import PosGlyphInfoWidget ## TODO: remove
from graide.utils import ModelSuper, DataObj
import os, re
from cStringIO import StringIO

def asBool(txt) :
    if not txt : return False
    if txt.lower() == 'true' : return True
    if txt.isdigit() : return int(txt) != 0
    return False
    

# A single glyph in a tweakable string.
class TweakGlyph() :
    
    def __init__(self, gid, name, gclass = None, status = "required", shiftx = 0, shifty = 0,
            shiftx_pending = 0, shifty_pending = 0) :
        self.gid = gid
        self.name = name
        self.gclass = gclass
        self.status = status
        self.shiftx = shiftx    # already built into GDL rules
        self.shifty = shifty
        self.shiftx_pending = shiftx_pending
        self.shifty_pending = shifty_pending
        

    def update(self, gid, name) :
        self.gid = gid
        self.name = name
        # TODO: if gclass is set and gid is not in gclass, this is a very different glyph than previously,
        # so clear all the shifts and the status.
        # Or maybe if gid != new ID, clear everything.
        

    def setShiftXpending(self, x) :
        self.shiftx_pending = x
        
    def setShiftYpending(self, y ) :
        self.shifty_pending = y
        
    def setStatus(self, status) :
        self.status = status
        
    def setGlyphClass(self, classname) :
        self.gclass = classname
    

    # New GDL rules have been generated, so record pending adjustments as accepted.
    def acceptPending(self) :
        self.shiftx = self.shiftx + self.shiftx_pending
        self.shifty = self.shifty + self.shifty_pending
        self.shiftx_pending = 0
        self.shifty_pending = 0
        
# end of class TweakGlyph


# A single string containing potentially tweaked glyphs.
class Tweak(Test) :
    
    # self.glyphs => list of TweakGlyphs
    
    def __init__(self, text, feats, lang = None, rtl = False, name = None, comment = "", width = 100, bgnd = 'white', \
            glyphs = []) : 
        super(Tweak, self).__init__(text, feats, lang, rtl, name, comment, width, bgnd)
        self.glyphs = glyphs
        # self.feats is a dictionary: feature IDs -> values
        

    def setGlyphs(self, glyphs) :
        self.glyphs = glyphs  # list of TweakGlyphs
        

    def glyphs(self) :
        return self.glyphs


    # Add this tweak to the XML output tree.
    def addXML(self, parent) :
        try :
            e = XmlTree.SubElement(parent, 'tweak')
            if self.comment :
                c = XmlTree.SubElement(e, 'comment')
                c.text = self.comment
            t = XmlTree.SubElement(e, 'string')
            if self.text :
                t.text = re.sub(r'\\u([0-9A-Fa-f]{4})|\\U([0-9A-Fa-f]{5,8})', \
                    lambda m:unichr(int(m.group(1) or m.group(2), 16)), self.text)
            else :
                t.text = ""
            e.set('label', self.name)
            if self.background != QtGui.QColor('white') : 
                e.set('background', self.background.name())
            if self.rtl : e.set('rtl', 'True')
            if self.width != 100 : e.set('expand', str(self.width))
                
            gl = XmlTree.SubElement(e, 'glyphs')
            for twglyph in self.glyphs  :
                gf = XmlTree.SubElement(gl, 'glyph')
                gf.set('gid', str(twglyph.gid))
                gf.set('name', twglyph.name)
                if twglyph.gclass and twglyph.gclass != "" :
                    gf.set('class', twglyph.gclass)
                if twglyph.status and twglyph.status != "required" :
                    gf.set('status', twglyph.status)
                gf.set('shiftx', str(twglyph.shiftx))
                gf.set('shifty', str(twglyph.shifty))
                gf.set('shiftx-pending', str(twglyph.shiftx_pending))
                gf.set('shifty-pending', str(twglyph.shifty_pending))
                
        except :
            msg = "ERROR: tweak could not be saved: " + self.name
            errorDialog = QtGui.QMessageBox()
            errorDialog.setText(msg)
            errorDialog.exec_()
            
        return e
        
    # end of addXML
    
    
    def glyphShifts(self, index) :
        return (self.glyphs[index].shiftx, self.glyphs[index].shifty,
            self.glyphs[index].shiftx_pending, self.glyphs[index].shifty_pending)
        
    def glyphShiftX(self, index) :
        return self.glyphs[index].shiftx
        
    def glyphShiftY(self, index) :
        return self.glyphs[index].shifty

    def glyphShiftXPending(self, index) :
        return self.glyphs[index].shiftx_pending
        
    def glyphShiftYPending(self, index) :
        return self.glyphs[index].shifty_pending
    

    # The Tweak has been run or rerun though Graphite.
    # Update the the given glyph in the list to match the output.
    def updateGlyph(self, index, gid, gname) :
        if len(self.glyphs) <= index :
            newGlyph = TweakGlyph(gid, gname)
            self.glyphs.append(newGlyph)
        else :
            self.glyphs[index].update(gid, gname)


    def deleteExtraGlyphs(self, newLen) :
        while len(self.glyphs) > newLen :
            self.glyphs.pop()
            

    # New GDL rules have been generated, so pending adjustments are now accepted.
    def acceptPending(self) :
        for g in self.glyphs :
            g.acceptPending()

# end of class Tweak
        

# The control that handles the list of tweaked strings
class TweakList(QtGui.QWidget) :
    
    # parent => Tweaker
    # view => TweakView

    def __init__(self, app, font, xmlfilename = None, parent = None) :
        super(TweakList, self).__init__(parent) # parent = Tweaker

        self.noclick = False
        self.app = app
        self.tweakGroups = []
        self.fsets = {"\n" : None}
        self.comments = []
        self.fcount = 0
        self.header = None

        self.setActions(app)
        vLayout = QtGui.QVBoxLayout()
        vLayout.setContentsMargins(*Layout.buttonMargins)
        self.cbox = QtGui.QWidget(self)
        chLayout = QtGui.QHBoxLayout()
        chLayout.setContentsMargins(*Layout.buttonMargins)
        chLayout.setSpacing(Layout.buttonSpacing)
        self.cbox.setLayout(chLayout)
        self.combo = QtGui.QComboBox(self.cbox)
        chLayout.addWidget(self.combo)
        chLayout.addSpacing(10)
        self.cabutton = QtGui.QToolButton(self.cbox)
        self.cabutton.setIcon(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")))
        self.cabutton.setToolTip('Add tweak group below this group')
        self.cabutton.clicked.connect(self.addGroupClicked)
        chLayout.addWidget(self.cabutton)
        self.crbutton = QtGui.QToolButton(self.cbox)
        self.crbutton.setIcon(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")))
        self.crbutton.setToolTip('Remove tweak group')
        self.crbutton.clicked.connect(self.delGroupClicked)
        chLayout.addWidget(self.crbutton)
        vLayout.addWidget(self.cbox)
        
        self.liststack = QtGui.QStackedWidget(self)
        vLayout.addWidget(self.liststack)
        self.combo.connect(QtCore.SIGNAL('currentIndexChanged(int)'), self.changeGroup)
        self.addGroup('main')
        self.bbox = QtGui.QWidget(self)
        hbLayout = QtGui.QHBoxLayout()
        self.bbox.setLayout(hbLayout)
        hbLayout.setContentsMargins(*Layout.buttonMargins)
        hbLayout.setSpacing(Layout.buttonSpacing)
        hbLayout.insertStretch(0)
        vLayout.addWidget(self.bbox)
        self.bEdit = QtGui.QToolButton(self.bbox)
        self.bEdit.setDefaultAction(self.aEdit)
        hbLayout.addWidget(self.bEdit)
        self.bUpp = QtGui.QToolButton(self.bbox)
        self.bUpp.setDefaultAction(self.aUpp)
        hbLayout.addWidget(self.bUpp)
        self.bDown = QtGui.QToolButton(self.bbox)
        self.bDown.setDefaultAction(self.aDown)
        hbLayout.addWidget(self.bDown)
        self.bSave = QtGui.QToolButton(self.bbox)
        self.bSave.setDefaultAction(self.aSave)
        hbLayout.addWidget(self.bSave)
        self.bAdd = QtGui.QToolButton(self.bbox)
        self.bAdd.setDefaultAction(self.aAdd)
        hbLayout.addWidget(self.bAdd)
        self.bDel = QtGui.QToolButton(self.bbox)
        self.bDel.setDefaultAction(self.aDel)
        hbLayout.addWidget(self.bDel)
        self.setLayout(vLayout)

        self.loadTweaks(xmlfilename)

    # end of __init__
    
    
    def setActions(self, app) :
        self.aGAdd = QtGui.QAction(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")), "Add &Group ...", app)
        self.aGAdd.setToolTip('Add tweak group below this group')
        self.aGAdd.triggered.connect(self.addGroupClicked)
        self.aGDel = QtGui.QAction(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")), "&Remove Group", app)
        self.aGDel.setToolTip('Remove tweak group')
        self.aGDel.triggered.connect(self.delGroupClicked)
        self.aEdit = QtGui.QAction(QtGui.QIcon.fromTheme('document-properties', QtGui.QIcon(":/images/document-properties.png")), "&Add Tweak ...", app)
        self.aEdit.setToolTip('Edit tweak')
        self.aEdit.triggered.connect(self.editClicked)
        self.aUpp = QtGui.QAction(QtGui.QIcon.fromTheme('go-up', QtGui.QIcon(":/images/go-up.png")), "Tweak &Up", app)
        self.aUpp.setToolTip("Move tweak up")
        self.aUpp.triggered.connect(self.upClicked)
        self.aDown = QtGui.QAction(QtGui.QIcon.fromTheme('go-down', QtGui.QIcon(":/images/go-down.png")), "Tweak &Down", app)
        self.aDown.setToolTip("Move tweak down")
        self.aDown.triggered.connect(self.downClicked)
        self.aSave = QtGui.QAction(QtGui.QIcon.fromTheme('document-save', QtGui.QIcon(":/images/document-save.png")), "&Save Tweaks", app)
        self.aSave.setToolTip('Save tweak list')
        self.aSave.triggered.connect(self.saveTestsClicked)
        self.aAdd = QtGui.QAction(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")), "&Add Tweak ...", app)
        self.aAdd.setToolTip('Add new tweak')
        self.aAdd.triggered.connect(self.addTestClicked)
        self.aDel = QtGui.QAction(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")), "&Delete Tweak", app)
        self.aDel.setToolTip('Delete tweak')
        self.aDel.triggered.connect(self.delTestClicked)

    # end of setActions
    
    
    def initTweaks(self) :
        self.addGroup('main')  # initial empty group

    
    def loadTweaks(self, fname):
        self.tweakGroups = []
        self.combo.clear()
        for i in range(self.liststack.count() - 1, -1, -1) :
            self.liststack.removeWidget(self.liststack.widget(i))
        if not fname or not os.path.exists(fname) : 
            self.initTweaks()
            return
            
        tweakStuff = self.parseTweaks(fname)
        for (groupLabel, tweaks) in tweakStuff.items() :
            listwidget = self.addGroup(groupLabel)
            for tweak in tweaks :
                self.appendTweak(tweak, listwidget)


    def parseTweaks(self, fname) :
        try :
            e = XmlTree.parse(fname)
        except Exception as err:
            reportError("TweaksFile %s: %s" % (fname, str(err)))
            return

        result = {}
            
        styles = {}
        langs = {} 
        self.header = e.find('.//head') 
        if self.header is None : self.header = e.find('.//header')
        for s in e.iterfind('.//style') :
            styleName = s.get('name')
            featDescrip = s.get('feats') or ""
            langCode = s.get('lang') or ""
            fset = featDescrip + "\n" + langCode
            if fset not in self.fsets :
                self.fsets[fset] = styleName
            styles[styleName] = {}
            if langCode :
                langs[styleName] = langCode
            for ft in featDescrip.split(" ") :
                if '=' in ft :
                    (fname, value) = ft.split('=')
                    styles[styleName][fname] = int(value)
            m = re.match(r'fset([0-9]+)', styleName)
            if m :
                i = int(m.group(1)) ## number of the fset, eg 'fset2' -> 2
                if i > self.fcount : self.fcount = i
                    
        for g in e.iterfind('tweakgroup') :
            groupLabel = g.get('label')
            groupList = []

            tmp = g.find('comment')
            self.comments.append(tmp.text if tmp else '')
            for t in g.iterfind('tweak') :
                tmp = t.find('string')
                if tmp is None : tmp = t.find('text')
                txt = tmp.text if tmp is not None else ""
                
                tmp = t.find('comment')
                c = tmp.text if tmp is not None else ""
                tmp = t.get('class')  # named style, group of features
                if tmp and tmp in styles :
                    feats = styles[tmp]
                    lng = langs.get(tmp)
                else :
                    feats = {}
                    lng = None
                    
                label = t.get('label')
                tweak = Tweak(txt, feats, lang = lng, rtl = asBool(t.get('rtl')), name = t.get('label'), comment = c)
                b = t.get('background')
                if b :
                    res = QtGui.QColor(b)
                    if res.isValid() : tweak.background = res
                w = t.get('expand')  # ???
                if w :
                    tweak.setWidth(int(w))
                twglyphs = []                    
                for gl in t.iterfind('glyphs') :
                    for gf in gl.iterfind('glyph') :
                        if gf.find('gid') :
                            gid = int(gf.get('gid'))
                        else :
                            gid = 0
                        gname = gf.get('name')
                        gclass = gf.get('class')
                        req = gf.get('status')
                        shiftx = int(gf.get('shiftx'))
                        shifty = int(gf.get('shifty'))
                        shiftx_pending = int(gf.get('shiftx-pending'))
                        shifty_pending = int(gf.get('shifty-pending'))
                        twglyph = TweakGlyph(gid, gname, gclass, req, shiftx, shifty, shiftx_pending, shifty_pending)
                        twglyphs.append(twglyph)
                tweak.setGlyphs(twglyphs)
                
                groupList.append(tweak)
            result[groupLabel] = groupList
            
        return result
            
    # end of parseTweaks
    
            
    def addGroup(self, name, index = None, comment = "") :
        listwidget = QtGui.QListWidget()
        #listwidget.itemDoubleClicked.connect(self.runTest)
        listwidget.itemClicked.connect(self.loadTweak)
        res = []
        if index is None :
            self.liststack.addWidget(listwidget)
            self.combo.addItem(name)
            self.tweakGroups.append(res)
            self.comments.append(comment)
        else :
            self.liststack.insertWidget(index, listwidget)
            self.combo.insertItem(index, name)
            self.tweakGroups.insert(index, res)
            self.comments.insert(index, comment)
        return listwidget

    
    def appendTweak(self, tweak, listwidget = None) :
        if not listwidget : listwidget = self.liststack.currentWidget()
        self.tweakGroups[self.liststack.indexOf(listwidget)].append(tweak)
        w = QtGui.QListWidgetItem(tweak.name or "",listwidget)
        if tweak.comment :
            w.setToolTip(t.comment)
        w.setBackground(QtGui.QBrush(tweak.background))

    
    def editTweak(self, tIndex) :
        gIndex = self.liststack.currentIndex()
        t = self.tweakGroups[gIndex][tIndex]
        bgndSave = t.background
        if t.editDialog(self.app, True) :
            listwidget = self.liststack.widget(gIndex)
            listwidget.item(tIndex).setText(t.name)
            listwidget.item(tIndex).setToolTip(t.comment)
            listwidget.item(tIndex).setBackground(QtGui.QBrush(t.background))
            return True
        else :
            # Undo any change to background.
            t.background = bgndSave

    
    def writeXML(self, fname) :
        e = XmlTree.Element('tweak-ftml', {'version' : '1.0'})
        if self.header is not None :
            h = self.header
            if h.tag == 'header' : h.tag = 'head'
            e.append(h)
        else :
            h = XmlTree.SubElement(e, 'head')
        fs = h.find('fontsrc')
        if fs is None:
            fs = h.makeelement('fontsrc', {})
            ETinsert(h, fs)
        fs.text = 'url(' + relpath(self.app.fontFileName, fname) + ')'
        used = set()
        for i in range(len(self.tweakGroups)) :
            g = XmlTree.SubElement(e, 'tweakgroup')
            g.set('label', self.combo.itemText(i))
            for t in self.tweakGroups[i] :
                te = t.addXML(g)
                c = self.findStyleClass(t)
                if c :
                    te.set('class', c)
                    used.add(c)
        s = h.find('styles')
        invfsets = {}
        for k, v in self.fsets.items() :
            if v is not None and v not in used :
                del self.fsets[k]
            else :
                invfsets[v] = k
        if len(self.fsets) > 1 :
            if s is not None :
                for i in range(len(s) - 1, -1, -1) :
                    s.remove(s[i])
            else :
                s = h.makeelement('styles', {})
                ETinsert(h, s)
            for v in sorted(invfsets.keys()) :
                k = invfsets[v]
                if not v : continue
                st = XmlTree.SubElement(s, 'style')
                st.set('name', v)
                (k, sep, l) = k.rpartition("\n")
                if k : st.set('feats', k)
                if l and l != 'None' : st.set('lang', l)
        elif s :
            h.remove(s)
        f = open(fname, "wb")
        sio = StringIO()
        sio.write('<?xml version="1.0" encoding="utf-8"?>\n')
        sio.write('<?xml-stylesheet type="text/xsl" href="Testing.xsl"?>\n')
        XmlTree.ElementTree(ETcanon(e)).write(sio, encoding="utf-8")
        f.write(sio.getvalue().replace(' />', '/>'))
        sio.close()
        f.close()

    # end of writeXML
    
    
    @QtCore.Slot(int)
    def changeGroup(self, index) :
        self.liststack.setCurrentIndex(index)
        if index < len(self.comments) :
            self.combo.setToolTip(self.comments[index])

    
    def addGroupClicked(self) :
        (name, ok) = QtGui.QInputDialog.getText(self, 'Tweak Group', 'Tweak Group Name')
        if ok :
            index = self.combo.currentIndex() + 1
            self.addGroup(name, index)
            self.combo.setCurrentIndex(self.combo.currentIndex() + 1)

    
    def delGroupClicked(self) :
        index = self.combo.currentIndex()
        self.liststack.removeWidget(self.liststack.widget(index))
        self.combo.removeItem(index)
        self.tweakGroups.pop(index)

    
    def editClicked(self) :
        self.editTweak(self.liststack.currentWidget().currentRow())

    
    def addTestClicked(self, t = None) :
        gIndex = self.liststack.currentIndex()
        if not t : t = Tweak('', self.app.feats[None].fval, rtl = configintval(self.app.config, 'main', 'defaultrtl'))
        self.appendTweak(t)
        res = self.editTweak(len(self.tweakGroups[gIndex]) - 1)
        if not t.name or not res :
            self.tweakGroups[gIndex].pop()
            self.liststack.widget(gIndex).takeItem(len(self.tweakGroups))

    
    def delTestClicked(self) :
        gIndex = self.liststack.currentIndex()
        tIndex = self.liststack.widget(gIndex).currentRow()
        self.tweakGroups[gIndex].pop(tIndex)
        self.liststack.widget(gIndex).takeItem(tIndex)

    
    def saveTestsClicked(self) :
        tname = configval(self.app.config, 'build', 'tweakxmlfile')
        if tname : self.writeXML(tname)

    
    def upClicked(self) :
        l = self.liststack.currentWidget()
        gIndex = self.liststack.currentIndex()
        tIndex = l.currentRow()
        if tIndex > 0 :
            self.tweakGroups[gIndex].insert(tIndex - 1, self.tweakGroups[gIndex].pop(tIndex))
            l.insertItem(tIndex - 1, l.takeItem(tIndex))
            l.setCurrentRow(tIndex - 1)

    
    def downClicked(self) :
        l = self.liststack.currentWidget()
        gIndex = self.liststack.currentIndex()
        tIndex = l.currentRow()
        if tIndex < l.count() - 1 :
            self.tweakGroups[gIndex].insert(tIndex + 1, self.tweakGroups[gIndex].pop(tIndex))
            l.insertItem(tIndex + 1, l.takeItem(tIndex))
            l.setCurrentRow(tIndex + 1)

    
    def findStyleClass(self, t) :
        k = " ".join(map(lambda x: x + "=" + str(t.feats[x]), sorted(t.feats.keys())))
        k += "\n" + (t.lang or "")
        if k not in self.fsets :
            self.fcount += 1
            self.fsets[k] = "fset%d" % self.fcount
        return self.fsets[k]

    
    # A Tweak was clicked on in the list.
    def loadTweak(self, item) :
        self.app.setRun(self.currentTweak())  # do we want this?
        self.showTweak(item)
        # do this after the glyphs have been displayed:
        self.parent().tweakChanged(item)

    
    def showTweak(self, item) :
        self.view.updateDisplay(self.currentTweak(), 0)

    
    # Return the Tweak object that is currently selected.
    def currentTweak(self):
        gIndex = self.liststack.currentIndex()
        tIndex = self.liststack.currentWidget().currentRow()
        if gIndex == -1 or tIndex == -1 :
            return None
        else :
            return self.tweakGroups[gIndex][tIndex]

    
    # New GDL rules have been generated, so pending adjustments are now accepted.
    def acceptPending(self) :
        for g in self.tweakGroups :
            for t in g :
                t.acceptPending()
                
# end of class TweakList       


# The controls at the bottom of the pane that allow adjustment of the glyph tweaks
class TweakInfoWidget(QtGui.QFrame) :
    
    # self.parent => Tweaker
    # self.parent().currentTweak() => Tweak

    def __init__(self, app, parent = None) :
        super(TweakInfoWidget, self).__init__(parent) # parent = Tweaker
        self.app = app

        self.item = None
        self.setFrameStyle(QtGui.QFrame.Box | QtGui.QFrame.Sunken)
        self.setLineWidth(1)
        self.layout = QtGui.QGridLayout(self)
        
        self.layout.addWidget(QtGui.QLabel("Slot"), 0, 0)
        self.slotCtrl = QtGui.QComboBox(self)
        self.slotCtrl.currentIndexChanged[unicode].connect(self.slotCtrlChanged)
        self.slotCtrl.editTextChanged.connect(self.slotCtrlChanged)
        self.layout.addWidget(self.slotCtrl, 0, 1, 1, 3)
        self.revert = QtGui.QPushButton("Revert")
        self.revert.clicked.connect(self.doRevert)
        self.layout.addWidget(self.revert, 0, 4)
        
        self.x = QtGui.QSpinBox(self)
        self.x.setRange(-32768, 32767)
        self.x.valueChanged[int].connect(self.posCtrlChanged)
        self.layout.addWidget(QtGui.QLabel("X"), 1, 0)
        self.layout.addWidget(self.x, 1, 1)
        self.y = QtGui.QSpinBox(self)
        self.y.setRange(-32768, 32767)
        self.y.valueChanged[int].connect(self.posCtrlChanged)
        self.layout.addWidget(QtGui.QLabel("Y"), 1, 3)
        self.layout.addWidget(self.y, 1, 4)
        self.posButtonsEnabled = True
        
        frame = QtGui.QFrame()
        #frame.setFrameStyle(QtGui.QFrame.WinPanel | QtGui.QFrame.Sunken)
        frame.setFrameStyle(QtGui.QFrame.Box | QtGui.QFrame.Sunken)
        innerGrid = QtGui.QGridLayout(frame)

        ####self.buttonGroup = QtGui.QButtonGroup(self) - could need if we add any different buttons
        self.statusReq = QtGui.QRadioButton("Required")
        self.statusReq.toggled.connect(self.statusButtonsChanged)
        self.statusOpt = QtGui.QRadioButton("Optional")
        self.statusOpt.toggled.connect(self.statusButtonsChanged)
        self.statusIgnore = QtGui.QRadioButton("Ignore")
        self.statusIgnore.toggled.connect(self.statusButtonsChanged)
        innerGrid.addWidget(self.statusReq, 0, 0, 1, 2)
        innerGrid.addWidget(self.statusOpt, 1, 0, 1, 2)
        innerGrid.addWidget(self.statusIgnore, 2, 0, 1, 2)
        
        self.gclassCtrl = QtGui.QComboBox(self)
        self.gclassCtrl.setEditable(True)
        innerGrid.addWidget(QtGui.QLabel("Class"), 0, 3, 1, 2)
        innerGrid.addWidget(self.gclassCtrl, 1, 3, 1, 2)
        self.gclassCtrl.currentIndexChanged[unicode].connect(self.classCtrlChanged)
        self.gclassCtrl.editTextChanged.connect(self.classCtrlChanged)
        
        self.layout.addWidget(frame, 2, 0, 3, 5)
        
        self.orig = None   # for reverting
        self.revert.setEnabled(False)
        
        self.tweakSelected = None   # Tweak object
        self.rtl = False            # get from Tweak object later
        self.glyphSelected = None   # TweakGlyph
        self.slotSelected = -1
        
        # True means we want the TweakView to respond to the user's manipulation of the controls;
        # set to False when we want to change the controls under program control:
        self.updateMode = True
        
        # Set to False when we initialize the controls for a Tweak, because we don't
        # want to update the data with what is in them.
        self.dataMode = True
        
    # end of __init__
    
       
    def setControlsForTweakItem(self, item) :
        self.tweakSelected = self.parent().currentTweak()
        self.rtl = self.tweakSelected.rtl
        if self.tweakSelected :
            glyphs = self.tweakSelected.glyphs
        else :
            glyphs = []
        
        # Populate the slot-selector control; the labels look like '<index>:  <glyph-name>'
        self.dataMode = False
        self.slotCtrl.clear()
        self.gclassCtrl.clear()
        i = 1
        for glyph in glyphs :
            label = str(i) + ":  " + glyph.name
            self.slotCtrl.addItem(label)
            i = i + 1
        
        self.slotSelected = -1 # the slot really is changing!
        self.glyphSelected = None
        self.selectSlot(0)
        self.dataMode = True
    
    # end of setControlsForTweakItem
    
    
    # Show the given slot in the controls
    def selectSlot(self, slotIndex) :  # 0-based
        if self.slotSelected != slotIndex :
            self.slotCtrl.setCurrentIndex(slotIndex)
            self.slotSelected = slotIndex
            self.glyphSelected = self.tweakSelected.glyphs[slotIndex]
            self.revert.setEnabled(False)

            # Set the controls to show the current values for the first glyph
            self.setControlsForGlyph(slotIndex)
        
    
    def setControlsForGlyph(self, slotIndex) :
        gid = self.glyphSelected.gid
        shiftx = self.glyphSelected.shiftx
        shifty = self.glyphSelected.shifty
        shiftx_pending = self.glyphSelected.shiftx_pending
        shifty_pending = self.glyphSelected.shifty_pending
        gclass = self.glyphSelected.gclass
        status = self.glyphSelected.status

        self.updateMode = False  # don't touch the TweakView for now
        
        shiftx_total = shiftx + shiftx_pending
        shifty_total = shifty + shifty_pending
        
        self.x.setValue(shiftx_total)
        self.y.setValue(shifty_total)
        
        # Populate the class control with the classes this glyph is a member of.
        glyph = self.parent().font[gid]
        self.glyphClasses = glyph.classes
        self.gclassCtrl.clear()
        self.gclassCtrl.addItem("None")
        gclassIndex = 0 # None
        i = 1
        for gcLp in self.glyphClasses :
            self.gclassCtrl.addItem(gcLp)
            if gcLp == gclass :
                gclassIndex = i
            i += 1
        if gclassIndex == 0 and gclass and gclass != "" and gclass != "None" :
            # Not one of the expected values - add it to the end of the list.
            self.gclassCtrl.addItem(gclass)
            gclassIndex = i
            i += 1
                
        self.gclassCtrl.setCurrentIndex(gclassIndex)
                   
        if shiftx_total != 0 or shifty_total != 0 :
            self.statusReq.setChecked(True)
            self.enablePosButtons(True)
            self.enableStatusButtons(False)
        else :
            self.enableStatusButtons(True)
            if status == "ignore" :
                self.statusIgnore.setChecked(True)
                self.enablePosButtons(False)
            elif status == "optional" :
                self.statusOpt.setChecked(True)
                self.enablePosButtons(False)
            else :
                self.statusReq.setChecked(True)
        
        self.updateMode = True
        
        # Save the original values so we can revert.
        self.orig = {'x-total': shiftx + shiftx_pending, 'y-total': shifty + shifty_pending,
                'x-pending': shiftx_pending, 'y-pending': shifty_pending,
                'gclass': gclass, 'status': status}
                
    # end of setControlsForGlyph
    
    
    def tweakView(self) :
        return self.parent().view  # parent = Tweaker
    
    
    # The slot control was changed. Update the selection in the TweakView.
    def slotCtrlChanged(self) :
        if not self.dataMode :
            return
            
        # Get the index from the string that looks like "<index>:  <glyph-name>"
        slotCtrlText = self.slotCtrl.currentText()
        if slotCtrlText == "" or slotCtrlText == "None" :
            slotIndex = -1
        else :
            slotIndex = 0
            for char in slotCtrlText :
                if char == ":" or char == " " : break
                slotIndex = slotIndex * 10 + int(char)
            slotIndex -= 1  # 0-based
        tweakView = self.tweakView()
        self.tweakView().highlightSlot(slotIndex)

    
    # The X or Y control was changed.
    def posCtrlChanged(self) :
        if not self.dataMode :
            return

        if self.slotSelected >= 0 :
            newX = self.x.value()
            newY = self.y.value()
            newXpending = newX - self.glyphSelected.shiftx
            newYpending = newY - self.glyphSelected.shifty
            # Update the data.
            self.glyphSelected.setShiftXpending(newXpending)
            self.glyphSelected.setShiftYpending(newYpending)
            
            self.enableStatusButtons(newX == 0 and newY == 0)

            if self.updateMode :
                # Inform the TweakView
                self.tweakView().updateDisplay(self.tweakSelected, self.slotSelected)
                self.tweakView().highlightSlot(self.slotSelected)
                self.revert.setEnabled(True)
            # otherwise we are just getting these controls in sync
    
    # end of posCtrlChanged
            
            
    # The class control was changed.
    def classCtrlChanged(self) :
        if not self.dataMode :
            return

        if self.slotSelected >= 0 :
            newClass = self.gclassCtrl.currentText()
            if newClass == "None" :
                self.glyphSelected.setGlyphClass("")
            else :
                self.glyphSelected.setGlyphClass(newClass)
                
            #if self.updateMode :  # Inform the TweakView if necessary
            #    pass
                
    
    def statusButtonsChanged(self) :
        if not self.dataMode :
            return
            
        if self.slotSelected >= 0 :
            if self.statusOpt.isChecked() :
                self.glyphSelected.setStatus("optional")
                self.enablePosButtons(False)
            elif self.statusIgnore.isChecked() :
                self.glyphSelected.setStatus("ignore")
                self.enablePosButtons(False)
            else :
                self.glyphSelected.setStatus("required")
                self.enablePosButtons(True)
                
            #if self.updateMode :  # Inform the TweakView if necessary
            #    pass
            
    
    def enablePosButtons(self, on = True) :
        self.x.setEnabled(on)
        self.y.setEnabled(on)
        self.posButtonsEnabled = on
    
    
    def enableStatusButtons(self, on = True) :
        self.statusReq.setEnabled(on)
        self.statusOpt.setEnabled(on)
        self.statusIgnore.setEnabled(on)
        
    
    def setX(self, x) :
        self.x.setValue(x)
        
    def setY(self, y) :
        self.y.setValue(y)
            
    def incrementX(self, dx) :
        x = self.x.value() + dx
        self.x.setValue(x)
            
    def incrementY(self, dy) :
        y = self.y.value() + dy
        self.y.setValue(y)

    
    def doRevert(self) :
        self.x.setValue(self.orig['x-total'])
        self.y.setValue(self.orig['y-total'])
        self.glyphSelected.setShiftXpending(self.orig['x-pending'])
        self.glyphSelected.setShiftYpending(self.orig['y-pending'])
        # Do we also revert the status and glyph class?
        self.revert.setEnabled(False)
        

#    def clear(self) : # currently not used
#        self.glyph.clear()
#        self.glyph.addItems(['(None)'])
#        self.glyph.setCurrentIndex(0)
#        self.aps.clear()
#        self.aps.addItems(['(None)'])
#        self.aps.setCurrentIndex(0)


    # The idea here is to pass appropriate key presses on to the TweakView. I couldn't get it to work.
#    def keyReleaseEvent(self, event) :
#        print "TweakInfoWidget::keyReleaseEvent" ###
#        if event.key() == QtCore.Qt.Key_Right or event.key() == QtCore.Qt.Key_Left :
#            print "pass the key press on to the TweakView"  ###
#            self.tweakView().snagKeyPress(event)
#        elif (event.modifiers() & QtCore.Qt.ShiftModifier) and \
#                (event.key() == QtCore.Qt.Key_Right or event.key() == QtCore.Qt.Key_Left or \
#                    event.key() == QtCore.Qt.Key_Down or event.key() == QtCore.Qt.Key_Up) :
#            print "pass the shifted key press on to the TweakView"  ###
#            self.tweakView().snagKeyPress(event)
#        else :
#            super(TweakInfoWidget,self).keyReleaseEvent(event)

# end of class TweakInfoWidget


# Main class to manage tweaking
class Tweaker(QtGui.QWidget) :

    #self.view => TweakView
    
    def __init__(self, font, parent = None, xmlfile = None) :   # parent = app
        super(Tweaker, self).__init__(parent)
        self.app = parent
        self.font = font
        self.view = None
        self.layout = QtGui.QVBoxLayout(self)
        self.initializeLayout(xmlfile)

        
    def initializeLayout(self, xmlfile) :
        self.tweakList = TweakList(self.app, self.font, xmlfile, self)
        #self.tweakList.itemClicked.connect(self.itemClicked)
        self.layout.addWidget(self.tweakList)
        self.infoWidget = TweakInfoWidget(self.app, self)
        self.layout.addWidget(self.infoWidget)


    def updateFromConfigSettings(self, font, fontname, config) :
        self.font = font
        self.view.updateFromConfigSettings(fontname, config)
        

    def setView(self, view) :
        self.view = view  # TweakView - lower-right tab
        self.tweakList.view = view
        

    def tweakChanged(self, item) :
        self.infoWidget.setControlsForTweakItem(item)
        self.view.highlightSlot(0)
        

    def writeXML(self, xmlfile) :
        if self.tweakList :
            self.tweakList.writeXML(xmlfile)
            

    def currentTweak(self) :
        return self.tweakList.currentTweak()
    

    # The slot was changed in the TweakView. Update yourself.
    def slotChanged(self, index) :
        self.infoWidget.selectSlot(index)
        

    def setX(self, x) :
        self.infoWidget.setX(x)
        
    def setY(self, y) :
        self.infoWidget.setY(y)
        
    def incrementX(self, dx) :
        self.infoWidget.incrementX(dx)
        
    def incrementY(self, dy) :
        self.infoWidget.incrementY(dy)
        

    # Called from main application when we switch tabs, also when we finish dragging a glyph.
    def updatePositions(self, highlight = False) :
        tweak = self.currentTweak()
        slot = self.infoWidget.slotSelected
        if tweak :
            self.view.updateDisplay(tweak, slot, highlight)


    def parseFile(self, filename) :
        return self.tweakList.parseTweaks(filename)
    

    # New GDL rules have been generated, so pending adjustments are now accepted.
    def acceptPending(self, tweakxmlfile) :
        self.tweakList.acceptPending()
        self.writeXML(tweakxmlfile)
        

    def posButtonsEnabled(self) :
        return self.infoWidget.posButtonsEnabled
        
        
    def loadTweaks(self, tweaksfile) :
        self.tweakList.loadTweaks(tweaksfile)
      
# end of class Tweaker

#------ TweakView classes ------

# A single displayed glyph of in a TweakedRunView
class TweakableGlyphPixmapItem(GlyphPixmapItem) :
    
    # self.runView => TweakableRunView

    def __init__(self, index, px, scale, runView, model = None, parent = None, scene = None) :
        super(TweakableGlyphPixmapItem, self).__init__(index, px, model, parent, scene)
        
        self.runView = runView  # TweakableRunView (parent, sort of)
        self.scale = scale  # convert from font's design units to display units
        
        # These are in font design units (em):
        self.shiftx = 0
        self.shifty = 0
        self.shiftx_pending = 0
        self.shifty_pending = 0
        
    def setShifts(self, shiftData) :
        # See Tweak::glyphShifts()
        self.shiftx = shiftData[0]
        self.shifty = shiftData[1]
        self.shiftx_pending = shiftData[2]
        self.shifty_pending = shiftData[3]
        

#    def revert(self) :
#        self.shiftx_pending = 0
#        self.shifty_pending = 0
        # redraw
        

    def mousePressEvent(self, event) :
        self.diffPx = (0, 0)  # pixels
        # Remember the position at the mouse press--moving will be relative to this.
        self.posStartPx = self.pos().toTuple()
        self.shiftStart = (self.shiftx + self.shiftx_pending, self.shifty + self.shifty_pending)
        ###self.keyPressEvent(event)
        try : event.accept()
        except TypeError : pass
        self.moveState = True
        self.runView.setUpdateable(False)
        super(TweakableGlyphPixmapItem, self).mousePressEvent(event)
        

    def mouseMoveEvent(self, event) :
        rtl = self.runView.run.rtl
        rtlDir = -1 if rtl else 1
        posPx = event.scenePos()
        posPxStart = event.buttonDownScenePos(QtCore.Qt.LeftButton)
        self.diffPx = (posPx - posPxStart).toTuple()
        diffXPxRtl = self.diffPx[0] * rtlDir
        xNew = self.shiftStart[0] + (diffXPxRtl / self.scale)
        yNew = self.shiftStart[1] - (self.diffPx[1] / self.scale)  # subtract because y coordinate system is opposite
        self.runView.tweaker().setX(xNew)
        self.runView.tweaker().setY(yNew)
        super(TweakableGlyphPixmapItem, self).mouseMoveEvent(event)
        
        # Since we can't regenerate the display (since the pixmap we are dragging will get 
        # deleted), just change its location.
        self.setPos(self.posStartPx[0] + self.diffPx[0], self.posStartPx[1] + self.diffPx[1])


    def mouseReleaseEvent(self, event) :
        self.moveState = False
        self.runView.setUpdateable(True)
        super(TweakableGlyphPixmapItem, self).mouseReleaseEvent(event)
        
        # We have been keeping the display static - now update it.
        self.runView.tweaker().updatePositions(highlight = True)
        
# end of class TweakableGlyphPixmapItem


class TweakableRunView(RunView) :
    
    # self.parentView => TweakView
    # self.parentView.tweaker => Tweaker
    
    def __init__(self, font = None, run = None, parent = None) :
        super(TweakableRunView, self).__init__(font, run, None)
        # For some reason when I try to store the parent in the normal way, I get errors that say:
        # TypeError: 'TweakView' is not callable.
        self.parentView = parent
        self._font = font # store it in case there is no run and the superclass ignores it
        self._updateable = True
        

    def setUpdateable(self, state) :
        self._updateable = state
        self.parentView.setUpdateable(state)
        

    def createPixmap(self, slot, glyph, index, res, scale,
            model = None,   # RunView
            parent = None,
            scene = None) : # RunView's scene
        currentTweak = self.parentView.tweaker.currentTweak()
        shiftData = currentTweak.glyphShifts(index)
        
        self.scale = scale   # convert from font's design units to display units
        rtl = self.run.rtl
        rtlDir = -1 if rtl else 1
        
        px = TweakableGlyphPixmapItem(index, glyph.item.pixmap, scale, self, model, parent, scene)
        px.setShifts(shiftData)        

        # Don't include shiftx and shifty, because they are already incorporated into the GDL rules
        # and so are accounted for in the slot's origins.
        xoffset = slot.origin[0] + (px.shiftx_pending * rtlDir)
        yoffset = slot.origin[1] + px.shifty_pending
        ppos = ((xoffset * scale) + glyph.item.left, -yoffset * scale - glyph.item.top)
        px.setOffset(*ppos)
        self._pixmaps.append(px)
        if slot : slot.pixmap(px)
        sz = glyph.item.pixmap.size()
        r = QtCore.QRect(ppos[0], ppos[1], sz.width(), sz.height())
        res = res.united(r)
        return res
        
    # end of createPixmap
    
        
    
    def tweaker(self) :
        return self.parentView.tweaker
        
    
    def updateData(self, run) :
        currentTweak = self.parentView.tweaker.currentTweak()
        for i, slot in enumerate(run) :
            glyph = self.parentView.app.font[slot.gid]
            gname = glyph.GDLName() or glyph.psname
            currentTweak.updateGlyph(i, slot.gid, gname)
        currentTweak.deleteExtraGlyphs(len(run))
        
            
    def glyphClicked(self, gitem, index) :
        if index == self.currselection :
            # Reclicking the same glyph has no effect
            pass
        else :
            super(TweakableRunView, self).glyphClicked(gitem, index)
            # Also inform the Tweaker so it can update the controls
            self.tweaker().slotChanged(index)
            
    
    def keyPressEvent(self, event) :
        
        rtl = self.run.rtl
        rtlDir = -1 if rtl else 1
        shiftPressed = event.modifiers() & QtCore.Qt.ShiftModifier
        if shiftPressed:
            # Tweak glyph positions.
            if not self.tweaker().posButtonsEnabled() :
                # Ignore shifts.
                pass
            elif event.key() == QtCore.Qt.Key_Up :
                self.tweaker().incrementY(20)
            elif event.key() == QtCore.Qt.Key_Down :
                self.tweaker().incrementY(-20)
            elif event.key() == QtCore.Qt.Key_Right :
                self.tweaker().incrementX(20 * rtlDir)
            elif event.key() == QtCore.Qt.Key_Left :
                self.tweaker().incrementX(-20 * rtlDir)
        
        elif event.key() == QtCore.Qt.Key_Left or event.key() == QtCore.Qt.Key_Right :
            # Move slot selection.
            if rtl :
                forward = True if event.key() == QtCore.Qt.Key_Left else False
            else :
                forward = True if event.key() == QtCore.Qt.Key_Right else False
                
            if forward :
                newSel = self.currselection + 1
                if newSel >= len(self._pixmaps) : newSel = len(self._pixmaps) - 1
                if newSel != self.currselection :
                    self.changeSelection(newSel)
                    self.tweaker().slotChanged(self.currselection)                
            else :
                newSel = self.currselection - 1
                if newSel < 0 : newSel = 0
                if newSel != self.currselection :
                    self.changeSelection(newSel)
                    self.tweaker().slotChanged(self.currselection)
    
    # end of keyPressEvent
    
                    
#    def snagFocus(self) :
#        print "TweakableRunView::snagFocus"  ###
#        self._scene.setFocus()  # this doesn't seem to actually work
#        if self._scene.hasFocus() :  ###
#            print "TweakableRunView has focus"
#        else :
#            print "TweakableRunView does not have focus"
            
# end of class TweakableRunView

               
# The display of the moveable glyphs in the bottom right-hand pane
class TweakView(QtGui.QWidget) :
    
    # tweaker => Tweaker

    # Communication with the Glyph and Slot tabs
    slotSelected = QtCore.Signal(DataObj, ModelSuper)
    glyphSelected = QtCore.Signal(DataObj, ModelSuper)


    @QtCore.Slot(DataObj, ModelSuper)
    def changeSlot(self, data, model) :
        self.slotSelected.emit(data, model)
        #self.tweaker.changeSlot(...)


    @QtCore.Slot(DataObj, ModelSuper)
    def changeGlyph(self, data, model) :
        self.glyphSelected.emit(data, model)
        if self.currsel and self.currsel != model :
            self.currsel.clearSelected()
        self.currsel = model


    def __init__(self, fontname, size, app = None, parent = None) :
        super(TweakView, self).__init__(parent)
        
        self.app = app
        self.runloaded = False
        self.tweaker = None # set later
        
        self.fontname = fontname
        self.setFont(size)

        if self.fontname and self.fontname != "":
            self._createRunView()
        
        self.currSlotIndex = -1
        self.updateable = True
        
    def _createRunView(self) :
        layout = QtGui.QVBoxLayout(self)
        self.runView = TweakableRunView(self.font, run = None, parent = self)
        self.runView.gview.resize(self.runView.gview.width(), (self.font.pixrect.height() + 5))
        layout.addWidget(self.runView.gview)
        # Ignore runView.tview - text view that shows the glyph names.
        
        
    def updateFromConfigSettings(self, fontname, config) :
        self.fontname = fontname
        self.setFont(configintval(config, 'ui', 'tweakglyphsize'))
        self._createRunView()
        

    def changeFontSize(self, size) :
        self.setFont(size)
        

    def setFont(self, size) :
        if self.fontname and self.fontname != "":
            fontfile = str(self.fontname)
            self.font = GraideFont()
            self.font.loadFont(fontfile, size)
            self.font.loadEmptyGlyphs()        
        

    def setTweaker(self, tweaker) :
        # The Tweaker has all the data in it, which is needed to display the glyphs at their
        # adjusted offsets.
        self.tweaker = tweaker
        

    def setUpdateable(self, state) :
        self.updateable = state
        

    def updateDisplay(self, tweak, slotIndex = 0, highlight = False) :
        if not self.updateable :
            # In the middle of a mouse move - don't regenerate (ie, delete) anything.
            return
            
        jsonResult = self.app.runGraphiteOverString(self.app.fontFileName, None, tweak.text, 10, #self.font.size,
            tweak.rtl, tweak.feats, tweak.lang, tweak.width)
        
        if jsonResult != False :
            self.json = jsonResult
        else :
            print "No Graphite result"
            self.json = None

        self.run = Run(tweak.rtl)
        if self.json :
            self.run.addslots(self.json[-1]['output'])
        self.runView.loadrun(self.run, self.font, resize = False)
        if not self.runloaded :
            try :
                # Don't switch to the Slot tab, but just update the contents.
                self.runView.slotSelected.connect(self.app.tab_slot.changeData)
                self.runView.glyphSelected.connect(self.app.glyphAttrib.changeData)
                self.runloaded = True
            except :
                print "Selection connection failed"

        # Bring the Tweak tab to the front
        self.app.tab_results.setCurrentWidget(self.app.tab_tweakview)
        
        if highlight :
            self.highlightSlot(slotIndex)
        # otherwise done in Tweaker::tweakChanged
    
    # end of updateDisplay
    
    
    def highlightSlot(self, slotIndex) :
        self.currSlotIndex = slotIndex
        self.runView.glyphClicked(None, slotIndex)


#    def snagKeyPress(self, event) :
#        self.runView.keyPressEvent(event)
#        self.runView.snagFocus()

#end of class TweakView
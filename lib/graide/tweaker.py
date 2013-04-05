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
from xml.etree import cElementTree as et
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
    

class TweakableGlyphPixmapItem(GlyphPixmapItem) :

    def __init__(self, index, px, model = None, parent = None, scene = None) :
        super(TweakableGlyphPixmapItem, self).__init__(index, px, model, parent, scene)
        self.shiftx = 0
        self.shifty = 0
        
    def setShifts(self, x, y) :
        self.originalShiftx = x
        self.originalShifty = y
        self.shiftx = x
        self.shifty = y
        
    def revert(self) :
        self.shiftx = originalShiftx
        self.shifty = originalShifty
        # redraw
        
    
class TweakGlyph() :
    
    def __init__(self, name, gclass = None, status = "required", shiftx = 0, shifty = 0) :
        self.name = name
        self.gclass = gclass
        self.status = status
        self.shiftx = shiftx
        self.shifty = shifty
        
        
class Tweak(Test) : 
    
    def __init__(self, text, feats, lang = None, rtl = False, name = None, comment = "", width = 100, bgnd = 'white', \
            glyphs = []) : 
        super(Tweak, self).__init__(text, feats, lang, rtl, name, comment, width, bgnd)
        self.glyphs = glyphs
        
        
    def setGlyphs(self, glyphs) :
        self.glyphs = glyphs


    # Add this tweak to the XML output tree.
    def addXML(self, parent) :
        try :
            e = et.SubElement(parent, 'tweak')
            if self.comment :
                c = et.SubElement(e, 'comment')
                c.text = self.comment
            t = et.SubElement(e, 'string')
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
                
            gl = et.SubElement(e, 'glyphs')
            for twglyph in self.glyphs  :
                gf = et.SubElement(gl, 'glyph')
                gf.set('name', twglyph.name)
                if twglyph.gclass and twglyph.gclass != "" :
                    gf.set('class', twglyph.gclass)
                if twglyph.status and twglyph.status != "required" :
                    gf.set('status', twglyph.status)
                gf.set('shiftx', twglyph.shiftx)
                gf.set('shifty', twglyph.shifty)
                
        except :
            msg = "ERROR: tweak could not be saved: " + self.name
            errorDialog = QtGui.QMessageBox()
            errorDialog.setText(msg)
            errorDialog.exec_()
            
        return e

# The control that handles the list of tweaked strings
class TweakList(QtGui.QWidget) :

    def __init__(self, app, font, xmlfilename = None, parent = None) :
        super(TweakList, self).__init__(parent) # parent = Tweaker

        self.noclick = False
        self.app = app
        self.tweaks = []
        self.fsets = {"\n" : None}
        self.comments = []
        self.fcount = 0
        self.header = None

        self.setActions(app)
        self.vbox = QtGui.QVBoxLayout()
        self.vbox.setContentsMargins(*Layout.buttonMargins)
        self.cbox = QtGui.QWidget(self)
        self.chbox = QtGui.QHBoxLayout()
        self.chbox.setContentsMargins(*Layout.buttonMargins)
        self.chbox.setSpacing(Layout.buttonSpacing)
        self.cbox.setLayout(self.chbox)
        self.combo = QtGui.QComboBox(self.cbox)
        self.chbox.addWidget(self.combo)
        self.chbox.addSpacing(10)
        self.cabutton = QtGui.QToolButton(self.cbox)
        self.cabutton.setIcon(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")))
        self.cabutton.setToolTip('Add tweak group below this group')
        self.cabutton.clicked.connect(self.addGroupClicked)
        self.chbox.addWidget(self.cabutton)
        self.crbutton = QtGui.QToolButton(self.cbox)
        self.crbutton.setIcon(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")))
        self.crbutton.setToolTip('Remove tweak group')
        self.crbutton.clicked.connect(self.delGroupClicked)
        self.chbox.addWidget(self.crbutton)
        self.vbox.addWidget(self.cbox)
        self.list = QtGui.QStackedWidget(self)
        self.vbox.addWidget(self.list)
        self.combo.connect(QtCore.SIGNAL('currentIndexChanged(int)'), self.changeGroup)
        self.addGroup('main')
        self.bbox = QtGui.QWidget(self)
        self.hbbox = QtGui.QHBoxLayout()
        self.bbox.setLayout(self.hbbox)
        self.hbbox.setContentsMargins(*Layout.buttonMargins)
        self.hbbox.setSpacing(Layout.buttonSpacing)
        self.hbbox.insertStretch(0)
        self.vbox.addWidget(self.bbox)
        self.bEdit = QtGui.QToolButton(self.bbox)
        self.bEdit.setDefaultAction(self.aEdit)
        self.hbbox.addWidget(self.bEdit)
        self.bUpp = QtGui.QToolButton(self.bbox)
        self.bUpp.setDefaultAction(self.aUpp)
        self.hbbox.addWidget(self.bUpp)
        self.bDown = QtGui.QToolButton(self.bbox)
        self.bDown.setDefaultAction(self.aDown)
        self.hbbox.addWidget(self.bDown)
        self.bSave = QtGui.QToolButton(self.bbox)
        self.bSave.setDefaultAction(self.aSave)
        self.hbbox.addWidget(self.bSave)
        self.bAdd = QtGui.QToolButton(self.bbox)
        self.bAdd.setDefaultAction(self.aAdd)
        self.hbbox.addWidget(self.bAdd)
        self.bDel = QtGui.QToolButton(self.bbox)
        self.bDel.setDefaultAction(self.aDel)
        self.hbbox.addWidget(self.bDel)
        self.setLayout(self.vbox)

        self.loadTweaks(xmlfilename)

    def setActions(self, app) :
        self.aGAdd = QtGui.QAction(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")), "Add &Group ...", app)
        self.aGAdd.setToolTip('Add tweak group below this group')
        self.aGAdd.triggered.connect(self.addGroupClicked)
        self.aGDel = QtGui.QAction(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")), "&Remove Group", app)
        self.aGDel.setToolTip('Remove tweak group')
        self.aGDel.triggered.connect(self.delGroupClicked)
        self.aEdit = QtGui.QAction(QtGui.QIcon.fromTheme('document-properties', QtGui.QIcon(":/images/document-properties.png")), "&Add Test ...", app)
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
        self.aSave.triggered.connect(self.saveClicked)
        self.aAdd = QtGui.QAction(QtGui.QIcon.fromTheme('list-add', QtGui.QIcon(":/images/list-add.png")), "&Add Tweak ...", app)
        self.aAdd.setToolTip('Add new tweak')
        self.aAdd.triggered.connect(self.addClicked)
        self.aDel = QtGui.QAction(QtGui.QIcon.fromTheme('list-remove', QtGui.QIcon(":/images/list-remove.png")), "&Delete Test", app)
        self.aDel.setToolTip('Delete tweak')
        self.aDel.triggered.connect(self.delClicked)

    def initTweaks(self) :
        self.addGroup('main')  # initial empty group

    def loadTweaks(self, fname):
        self.tweaks = []
        self.combo.clear()
        for i in range(self.list.count() - 1, -1, -1) :
            self.list.removeWidget(self.list.widget(i))
        if not fname or not os.path.exists(fname) : 
            self.initTweaks()
            return
        try :
            e = et.parse(fname)
        except Exception as err:
            reportError("TweaksFile %s: %s" % (fname, str(err)))
            return
        classes = {}
        langs = {}
        self.header = e.find('.//head') 
        if self.header is None : self.header = e.find('.//header')
        for s in e.iterfind('.//style') :
            k = s.get('name')
            v = s.get('feats') or ""
            l = s.get('lang') or ""
            fset = v + "\n" + l
            if fset not in self.fsets : self.fsets[fset] = k
            classes[k] = {}
            if l : langs[k] = l
            for ft in v.split(" ") :
                if '=' in ft :
                    (k1, v1) = ft.split('=')
                    classes[k][k1] = int(v1)
            m = re.match(r'fset([0-9]+)', k)
            if m :
                i = int(m.group(1))
                if i > self.fcount : self.fcount = i
        for g in e.iterfind('tweakgroup') :
            listwidget = self.addGroup(g.get('label'))
            y = g.find('comment')
            self.comments.append(y.text if y else '')
            for t in g.iterfind('tweak') :
                y = t.find('string')
                if y is None : y = t.find('text')
                txt = y.text if y is not None else ""
                y = t.find('comment')
                c = y.text if y is not None else ""
                y = t.get('class')  # named style, group of features
                if y and y in classes :
                    feats = classes[y]
                    lng = langs.get(y)
                else :
                    feats = {}
                    lng = None
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
                        gname = gf.get('name')
                        gclass = gf.get('class')
                        req = gf.get('status')
                        shiftx = gf.get('shiftx')
                        shifty = gf.get('shifty')
                        twglyph = TweakGlyph(gname, gclass, req, shiftx, shifty)
                        twglyphs.append(twglyph)
                tweak.setGlyphs(twglyphs)
                 
                self.appendTweak(tweak, listwidget)

    def addGroup(self, name, index = None, comment = "") :
        listwidget = QtGui.QListWidget()
        #listwidget.itemDoubleClicked.connect(self.runTest)
        listwidget.itemClicked.connect(self.loadTweak)
        res = []
        if index is None :
            self.list.addWidget(listwidget)
            self.combo.addItem(name)
            self.tweaks.append(res)
            self.comments.append(comment)
        else :
            self.list.insertWidget(index, listwidget)
            self.combo.insertItem(index, name)
            self.tweaks.insert(index, res)
            self.comments.insert(index, comment)
        return listwidget

    def appendTweak(self, t, listwidget = None) :
        if not listwidget : listwidget = self.list.currentWidget()
        self.tweaks[self.list.indexOf(listwidget)].append(t)
        w = QtGui.QListWidgetItem(t.name or "",listwidget)
        if t.comment :
            w.setToolTip(t.comment)
        w.setBackground(QtGui.QBrush(t.background))
        
    

    def editTweak(self, index) :
        i = self.list.currentIndex()
        t = self.tweaks[i][index]
        bgndSave = t.background
        if t.editDialog(self.app, True) :
            listwidget = self.list.widget(i)
            listwidget.item(index).setText(t.name)
            listwidget.item(index).setToolTip(t.comment)
            listwidget.item(index).setBackground(QtGui.QBrush(t.background))
            return True
        else :
            # Undo any change to background.
            t.background = bgndSave

    def writeXML(self, fname) :
        e = et.Element('tweak_ftml', {'version' : '1.0'})
        if self.header is not None :
            h = self.header
            if h.tag == 'header' : h.tag = 'head'
            e.append(h)
        else :
            h = et.SubElement(e, 'head')
        fs = h.find('fontsrc')
        if fs is None:
            fs = h.makeelement('fontsrc', {})
            ETinsert(h, fs)
        fs.text = 'url(' + relpath(self.app.fontfile, fname) + ')'
        used = set()
        for i in range(len(self.tweaks)) :
            g = et.SubElement(e, 'tweakgroup')
            g.set('label', self.combo.itemText(i))
            for t in self.tweaks[i] :
                te = t.addXML(g)
                c = self.findClass(t)
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
                st = et.SubElement(s, 'style')
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
        et.ElementTree(ETcanon(e)).write(sio, encoding="utf-8")
        f.write(sio.getvalue().replace(' />', '/>'))
        sio.close()
        f.close()

    @QtCore.Slot(int)
    def changeGroup(self, index) :
        self.list.setCurrentIndex(index)
        if index < len(self.comments) :
            self.combo.setToolTip(self.comments[index])

    def addGroupClicked(self) :
        (name, ok) = QtGui.QInputDialog.getText(self, 'Test Group', 'Test Group Name')
        if ok :
            index = self.combo.currentIndex() + 1
            self.addGroup(name, index)
            self.combo.setCurrentIndex(self.combo.currentIndex() + 1)

    def delGroupClicked(self) :
        index = self.combo.currentIndex()
        self.list.removeWidget(self.list.widget(index))
        self.combo.removeItem(index)
        self.tweaks.pop(index)

    def editClicked(self) :
        self.editTweak(self.list.currentWidget().currentRow())

    def addClicked(self, t = None) :
        i = self.list.currentIndex()
        if not t : t = Test('', self.app.feats[None].fval, rtl = configintval(self.app.config, 'main', 'defaultrtl'))
        self.appendTweak(t)
        res = self.editTweak(len(self.tweaks[i]) - 1)
        if not t.name or not res :
            self.tweaks[i].pop()
            self.list.widget(i).takeItem(len(self.tweaks))

    def saveClicked(self) :
        tname = configval(self.app.config, 'main', 'testsfile')
        if tname : self.writeXML(tname)

    def delClicked(self) :
        j = self.list.currentIndex()
        i = self.list.widget(j).currentRow()
        self.tweaks[j].pop(i)
        self.list.widget(j).takeItem(i)

    def upClicked(self) :
        l = self.list.currentWidget()
        j = self.list.currentIndex()
        i = l.currentRow()
        if i > 0 :
            self.tweaks[j].insert(i - 1, self.tweaks[j].pop(i))
            l.insertItem(i - 1, l.takeItem(i))
            l.setCurrentRow(i - 1)

    def downClicked(self) :
        l = self.list.currentWidget()
        j = self.list.currentIndex()
        i = l.currentRow()
        if i < l.count() - 1 :
            self.tweaks[j].insert(i + 1, self.tweaks[j].pop(i))
            l.insertItem(i + 1, l.takeItem(i))
            l.setCurrentRow(i + 1)

    def loadTweak(self, item) :
        j = self.list.currentIndex()
        i = self.list.currentWidget().currentRow()
        print self.tweaks[i][j].name ###
        #self.app.setRun(self.tweaks[j][i])
        self.showTweak(item)

    def showTweak(self, item) :
        print "show tweak ..."
        j = self.list.currentIndex()
        i = self.list.currentWidget().currentRow()
        self.view.updateDisplay(self.tweaks[j][i])

    def findClass(self, t) :
        k = " ".join(map(lambda x: x + "=" + str(t.feats[x]), sorted(t.feats.keys())))
        k += "\n" + (t.lang or "")
        if k not in self.fsets :
            self.fcount += 1
            self.fsets[k] = "fset%d" % self.fcount
        return self.fsets[k]
        

# Main class to manage tweaking
class Tweaker(QtGui.QWidget) :

    def __init__(self, font, parent = None, xmlfile = None) :
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
        self.infoWidget = PosGlyphInfoWidget("Selected", self.app, True, self)
        self.layout.addWidget(self.infoWidget)

    def setView(self, view) :
        self.view = view  # TweakView - lower-right tab
        self.tweakList.view = view
        
    def updatePositions(self) :
        # TODO
        print "Tweaker::updatePositions()" ###
        
    def writeXML(self, xmlfile) :
        if self.tweakList :
            self.tweakList.writeXML(xmlfile)


# The display of the moveable glyphs in the bottom right-hand pane
class TweakView(QtGui.QWidget) :

    # Communication with the Glyph and Slot tabs
    slotSelected = QtCore.Signal(DataObj, ModelSuper)
    glyphSelected = QtCore.Signal(DataObj, ModelSuper)

    @QtCore.Slot(DataObj, ModelSuper)
    def changeSlot(self, data, model) :
        self.slotSelected.emit(data, model)

    @QtCore.Slot(DataObj, ModelSuper)
    def changeGlyph(self, data, model) :
        self.glyphSelected.emit(data, model)
        if self.currsel and self.currsel != model :
            self.currsel.clear_selected()
        self.currsel = model

    def __init__(self, font, app = None, parent = None) :
        super(TweakView, self).__init__(parent)
                
        self.font = font
        self.app = app
        self.runloaded = False
        
        layout = QtGui.QVBoxLayout(self)
        self.runView = RunView(self.font)
        self.runView.gview.resize(self.runView.gview.width(), self.font.pixrect.height() + 5)
        layout.addWidget(self.runView.gview)
        # Ignore runView.tview - text view that shows the glyph names.
        
    def updateDisplay(self, tweak) :
        print "TweakView::updateDisplay", tweak ###
        jsonResult = self.app.runGraphiteOverString(self.app.fontfile, tweak.text, self.font.size,
            tweak.rtl, tweak.feats, tweak.lang, tweak.width)
        #print jsonResult ###
        
        if jsonResult != False :
            self.json = jsonResult
        else :
            print "No Graphite result" ###

        self.run = Run()
        self.run.addslots(self.json[-1]['output'])
        self.runView.loadrun(self.run, self.font, resize = False)
        if not self.runloaded :
            try :
                self.runView.slotSelected.connect(self.app.slotSelected)
                self.runView.glyphSelected.connect(self.app.glyphAttrib.changeData)
                self.runloaded = True
            except :
                print "Selection connection failed"

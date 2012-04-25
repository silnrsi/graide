from xml.etree.ElementTree import parse
from graide import freetype
import ctypes
from graide.glyph import Glyph
from PySide import QtCore

class Font (object) :
    def __init__(self) :
        self.glyphs = []
        self.names = {}

    def __len__(self) :
        return len(self.glyphs)

    def __getitem__(self, y) :
        try :
            return self.glyphs[y]
        except IndexError :
            return None

    def loadFont(self, fontfile, apfile = None) :
        self.face = freetype.Face(fontfile)
        self.glyphs = [None] * self.face.num_glyphs
        self.upem = self.face.units_per_EM
        if apfile :
            etree = parse(apfile)
            i = 0
            for e in etree.getroot().iterfind("glyph") :
                i = self.addglyph(i, e)
                i += 1
        else :
            for i in range(self.face.num_glyphs) :
                self.addglyph(i)

    def addglyph(self, index, elem = None) :
        if elem is not None :
            name = elem.get('PSName')
            if name :
                i = freetype.FT_Get_Name_Index(self.face._FT_Face, name)
                if i == None :
                    name = None
                else :
                    index = i
        else :
            name = None
        if not name :
            n = ctypes.create_string_buffer(64)
            freetype.FT_Get_Glyph_Name(self.face._FT_Face, index, n, ctypes.sizeof(n))
            name = n.value
        g = Glyph(self, name, index)
        self.names[name] = g
        if elem is not None : g.readAP(elem)
        self.glyphs[index] = g
        return index

    def makebitmaps(self, size) :
#        self.face.set_char_size(height = size * 64)
#        for a in ('xMin', 'xMax', 'yMin', 'yMax') :
#            setattr(self, a, getattr(self.face.bbox, a) * self.face.size.y_scale / 65536 / 64)
        self.pixrect = QtCore.QRect()
        self.top = 0
        self.size = size
        for i, g in enumerate(self.glyphs) :
            if g :
                g.setpixmap(self.face, i, size)
                if g.pixmap :
                    grect = g.pixmap.rect()
                    self.pixrect = self.pixrect | grect
                if g.top > self.top : self.top = g.top
        # print self.pixrect

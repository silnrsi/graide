
from PySide import QtGui
from graide import freetype
import array, re
from graide.attribview import Attribute, AttribModel
from graide.dataobj import DataObj

class Glyph(DataObj) :

    def __init__(self, font, name = None, gid = 0) :
        self.psname = name
        self.gid = gid
        self.properties = {}
        self.gdl_properties = {}
        self.points = {}

    def __str__(self) :
        return self.psname

    def setpixmap(self, face, gid, height = 40) :
        face.set_char_size(height = int(height * 64))
        res = freetype.FT_Load_Glyph(face._FT_Face, gid, freetype.FT_LOAD_RENDER)
        b = face.glyph.bitmap
        self.top = face.glyph.bitmap_top
        self.left = face.glyph.bitmap_left
        if b.rows :
            data = array.array('B', b.buffer)
            mask = QtGui.QImage(data, b.width, b.rows, b.pitch, QtGui.QImage.Format_Indexed8)
            image = QtGui.QImage(b.width, b.rows, QtGui.QImage.Format_Mono)
            image.fill(0)
            image.setAlphaChannel(mask)
            self.pixmap = QtGui.QPixmap(image)
        else :
            self.pixmap = None

    def readAP(self, elem) :
        self.uid = int(elem.get('UID', '0'), 16)
        for p in elem.iterfind('property') :
            n = p.get('name')
            if n.startswith('GDL_') :
                self.gdl_properties[n[4:]] = p.get('value')
            else :
                self.properties[n] = p.get('value')
        for p in elem.iterfind('point') :
            l = p.find('location')
            self.points[p.get('type')] = (int(l.get('x', 0)), int(l.get('y', 0)))
      
    def attribModel(self) :
        res = []
        for a in ['psname', 'gid'] :
            res.append(Attribute(a, self.__getattribute__, None, False, a)) # read-only
        for a in sorted(self.properties.keys()) :
            res.append(Attribute(a, self.getproperty, self.setproperty, False, a))
        for a in sorted(self.gdl_properties.keys()) :
            res.append(Attribute(a, self.getgdlproperty, self.setgdlproperty, False, a))
        pres = []
        for k in self.points.keys() :
            pres.append(Attribute(k, self.getpoint, self.setpoint, False, k))
        resAttrib = AttribModel(res)
        pAttrib = AttribModel(pres, resAttrib)
        resAttrib.add(Attribute('points', None, None, True, pAttrib))
        return resAttrib

    def getproperty(self, key) :
        return self.properties[key]

    def setproperty(self, key, value) :
        if value == None :
            del self.properties[key]
        else :
            self.properties[key] = value

    def getgdlproperty(self, key) :
        return self.gdl_properties[key]

    def setgdlproperty(self, key, value) :
        if value == None :
            del self.gdl_properties[key]
        else :
            self.gdl_properties[key] = value

    def getpoint(self, key) :
        return str(self.points[key])

    def setpoint(self, key, value) :
        if value == None :
            del self.points[key]
        elif value == "" :
            self.points[key] = (0, 0)
        else :
            self.points[key] = map(int, re.split(r",\s*", value[1:-1]))


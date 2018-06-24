import fontforge, os, sys, re
from ConfigParser import RawConfigParser
from graide.config import ConfigDialog
from graide.utils import buildGraphite, configintval
from graide.makegdl.font import Font as gdlFont
from xml.etree import cElementTree as et

producer = 'Fontforge makeap 1.0'

# config file
def getcfg(font) :
    if font.persistent and 'graideconfig' in font.persistent :
        return font.persistent['graideconfig']
    else :
        return u""

def savecfg(font, cfg) :
    if font.persistent is None : font.persistent = {}
    font.persistent['graideconfig'] = cfg

def writecfg(conf, fname) :
    f = file(fname, "w")
    conf.write(f)
    f.close()

def loadConfig(data, font) :
    cfg = getcfg(font)
    cfg = fontforge.openFilename("Graide Configuration file", cfg, "*.cfg")
    savecfg(font, cfg)

def editConfig(data, font) :
    cfg = getcfg(font)
    conf = RawConfigParser()
    if not cfg :
        cfg = fontforge.saveFilename('Graide Configuration file', cfg, '*.cfg')
        savecfg(font, cfg)
        for s in ('main', 'build', 'ui') :
            conf.add_section(s)
        conf.set('main', 'font', font.path[:-4] + '.ttf')
        conf.set('main', 'ap', font.path[:-4] + '.xml')
        conf.set('build', 'makegdlfile', font.path[:-4] + '.gdl')
        conf.set('build', 'usemakegdl', '1')
    else :
        conf.read(cfg)
    from qtpy import QtWidgets
    app = QtWidgets.QApplication([])
    d = ConfigDialog(conf)
    if d.exec_() :
        d.updateConfig(None, conf)
        writecfg(conf, cfg)

# AP file processing
def readAP(font, fname) :
    tree = et.parse(fname)
    root = tree.getroot()
    for ge in root.iterfind('glyph') :
        psname = ge.get('PSName')
        if not psname : continue
        g = font[psname]
        if not g : continue
        i = {'property' : {}, 'points' : {}}
        if not g.temporary :
            g.temporary = {'makeap' : i}
        else :
            g.temporary['makeap'] = i
        for pe in ge.iterfind('property') :
            i['property'][pe.get('name')] = pe.get('value')
        ne = ge.find('notes')
        i['notes'] = ne.text if ne is not None else ''
        for p in ge.iterfind('point') :
            l = p.find('location')
            i['points'][p.get('type')] = (int(l.get('x')), int(l.get('y')))

def makeAPstruct(glyph) :
    res = {'property' : {}, 'points' : {}, 'notes' : ''}
    for a in glyph.anchorPoints :
        name = a[0]
        if a[1] == 'mark' or a[1] == 'basemark' or a[1] == 'entry' : name = "_" + name
        res['points'][name] = (int(a[2]), int(a[3]))
    c = glyph.comment.split("\n")
    while (len(c)) :
        m = re.match(r'^(\w+):\s+(.*?)\s*$', c[0])
        if m :
            c.pop(0)
            res['property'][m.group(1)] = m.group(2)
        else :
            break
    if len(c) :
        res['notes'] = "\n".join(c)
    return res

def mergedict(b, o, t) :
        propkeys = set(b.keys())
        propkeys.update(o.keys())
        propkeys.update(t.keys())
        for k in propkeys :
            if k not in b :
                if k not in o :
                    b[k] = t[k]
                else :
                    b[k] = o[k]
            elif k not in o :
                if k not in t or t[k] == b[k] :
                    del b[k]
                else :
                    b[k] = t[k]
            elif k not in t :
                if b[k] == o[k] :
                    del b[k]
                else :
                    b[k] = o[k]
            elif b[k] == o[k] :
                b[k] = t[k]
            else :
                b[k] = o[k]

def mergeAPInfo(font) :
    for k in font :
        g = font[k]
        if g.persistent is None or 'makeap' not in g.persistent:
            base = {'property' : {}, 'points' : {}, 'notes' : ''}
            if g.persistent is None :
                g.persistent = {'makeap' : base}
            else :
                g.persistent['makeap'] = base
        else :
            base = g.persistent['makeap']
        if g.temporary is None :
            other = {'property' : {}, 'points' : {}, 'notes' : ''}
            g.temporary = {'makeap' : other}
        else :
            other = g.temporary['makeap']
        this = makeAPstruct(g)
        mergedict(base['property'], other['property'], this['property'])
        mergedict(base['points'], other['points'], this['points'])
        if base['notes'] == this['notes'] :
            base['notes'] = other['notes']
        else :
            base['notes'] = this['notes']


# makegdl
missingGlyphs = ((".notdef",), (".null", "uni0000", "glyph1"), ("nonmarkingreturn", "uni000D", "glyph2"))
def fillMissingGlyphs(font) :
    res = []
    for m in missingGlyphs :
        missing = True
        for n in m :
            if n in font :
                res.append(n)
                missing = False
                break
        if missing :
            font.createChar(-1, m[0])
            res.append(m[0])
    return res

class FfFont(gdlFont) :

    def __init__(self, font) :
        super(FfFont, self).__init__()
        self.font = font
        gmap = fillMissingGlyphs(self.font)
        ghash = set(gmap)
        for g in font.glyphs('encoding') :
            if g.glyphname not in ghash :
                gmap.append(g.glyphname)
                ghash.add(g.glyphname)
        esize = len(gmap) - 3
        for g in font.glyphs() :
            if g.glyphname not in ghash and (g.encoding < 0 or g.encoding >= esize) :
                gmap.append(g.glyphname)
                ghash.add(g.glyphname)
        for i, n in enumerate(gmap) :
            fg = font[n]
            g = self.addGlyph(i, n)
            p = fg.persistent['makeap']
            if fg.unicode > 0 : g.uid = "%04X" % fg.unicode
            for k, v in p['property'].items() :
                if k.startswith('GDL_') :
                    g.gdl_properties[k[4:]] = v
                else :
                    g.properties[k] = v
            for k, v in p['points'].items() :
                g.anchors[k] = v
            if p['notes'] :
                g.comment = p['notes']
            if 'classes' in g.properties :
                for c in g.properties['classes'].split() :
                    g.classes.add(c)
                    self.addGlyphClass(c, i, editable = True)

    def emunits(self) :
        return self.font.em


# font generation
def doGenerate(font, outputfont) :
    if 'GDL_generateFlag' not in font.temporary :
        font.temporary['GDL_generateFlag'] = True
        return
    else :
        del font.temporary['GDL_generateFlag']
    cfg = getcfg(font)
    if not cfg : return
    conf = RawConfigParser()
    conf.read(cfg)
    cwd = os.getcwd()
    os.chdir(os.path.dirname(cfg))
    conf.set('main', 'font', outputfont)
    if configintval(conf, 'build', 'usemakegdl') :
        outname = conf.get('main', 'ap')
        if os.path.exists(outname) : readAP(font, outname)
        mergeAPInfo(font)
        myFfFont = FfFont(font)
        buildGraphite(conf, None, myFfFont, outputfont)
    else :
        buildGraphite(conf, None, None, outputfont)
    writecfg(conf, cfg)
    os.chdir(cwd)

def loadFont(font) :
    if getcfg(font) :
        if 'initScriptString' not in font.persistent : font.persistent['initScriptString'] = None
        if not font.temporary : font.temporary = {}
        font.temporary['generateFontPostHook'] = doGenerate

if fontforge.hasUserInterface() :
    fontforge.hooks['loadFontHook'] = loadFont
    fontforge.registerMenuItem(loadConfig, None, None, "Font", None, "Graide", "Load configuration")
    fontforge.registerMenuItem(editConfig, None, None, "Font", None, "Graide", "Edit configuration")
else:
    f = fontforge.open(os.path.abspath(sys.argv[1]))
    cfg = getcfg(f)
    if not cfg :
        print "No configuration, can't build"
        sys.exit(1)
    conf = RawConfigParser()
    conf.read(cfg)
    f.generate(conf.get('main', 'font'), flags = ('opentype',))
    sys.exit(0)

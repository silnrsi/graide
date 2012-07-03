import fontforge
import os
from xml.etree import cElementTree as et

producer = 'Fontforge makeap 1.0'

def readAP(font, fname) :
    tree = et.parse(fname)
    root = tree.getroot()
    for ge in root.iterfind('glyph') :
        g = font[ge.get('PSName')]
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

def ETcanon(et, curr = 0, indent = 4) :
    n = len(et)
    if n :
        et.text = "\n" + (' ' * (curr + indent))
        for i in range(n) :
            ETcanon(et[i], curr + indent, indent)
            et[i].tail = "\n" + (' ' * (curr + indent if i < n - 1 else curr))
    return et

def outputAP(data, font) :
    outname = os.path.splitext(font.path)[0] + ".xml"
    if os.path.exists(outname) : readAP(font, outname)
    mergeAPInfo(font)
    root = et.Element('font')
    root.set('upem', str(font.em))
    root.set('producer', producer)
    for k in font :
        g = font[k]
        e = et.SubElement(root, 'glyph')
        e.set('PSName', g.glyphname)
        if g.unicode >= 0 :
            e.set('UID', "%04X" % g.unicode)
        base = g.persistent['makeap']
        for k, v in base['points'].items() :
            p = et.SubElement(e, 'point')
            p.set('type', k)
            l = et.SubElement(p, 'location')
            l.set('x', str(v[0]))
            l.set('y', str(v[1]))
        for k, v in base['property'].items() :
            p = et.SubElement(e, 'property')
            p.set('name', k)
            p.set('value', v)
        if base['notes'] :
            p = et.SubElement(e, 'notes')
            p.text = notes
    et.ElementTree(ETcanon(root)).write(outname, encoding="UTF-8", xml_declaration=True)

if '__name__' == '__main__' :
    f = fontforge.open(os.path.abspath(sys.argv[1]))
    outputAP(None, f)
else :
    fontforge.registerMenuItem(outputAP, None, None, "Font", None, "Output AP Database")

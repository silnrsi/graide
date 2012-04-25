from xml.etree.ElementTree import iterparse

class Gdx(object) :

    def __init__(self) :
        self.passes = []
        self.passtypes = []
        self.keepelements = False

    def readfile(self, fname) :
        self.file = file(fname)
        for (event, e) in iterparse(self.file, events=('start', 'end')) :
            if event == 'start' :
                if e.tag == 'pass' :
                    self.passes.append([])
                    self.passtypes.append(e.get('table'))
                elif e.tag == 'rule' :
                    self.keepelements = True
            else :
                if e.tag == "rule" :
                    self.keepelements = False
                    self.passes[-1].append(Rule(e))
                if not self.keepelements :
                    e.clear()

class Rule(object) :

    def __init__(self, e) :
        self.srcfile = e.get('inFile')
        self.srcline = int(e.get('atLine'))
        self.pretty = e.get('prettyPrint')
        slots = map(lambda x: int(x.get('slotIndex')), e.findall('rhsSlot'))
        if len(slots) :
            d = slots[0]
            self.slots = map(lambda x : x - d, slots)
        else :
            self.slots = []


from graide.slot import Slot

class Run(list) :

    def __init__(self) :
        pass

    def addslots(self, runinfo) :
        for s in runinfo :
            r = Slot(s)
            self.append(r)
            r.index = len(self) - 1


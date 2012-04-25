
from graide.slot import Slot

class Run(list) :

    def __init__(self) :
        pass

    def addslots(self, runinfo) :
        for s in runinfo :
            r = Slot(s)
            self.append(r)
            r.index = len(self) - 1

    def copy(self) :
        res = Run()
        for s in self :
            res.append(s.copy())
        return res

    def idindex(self, ident) :
        for (i, s) in enumerate(self) :
            if s.id == ident : return i
        return -1

    def replace(self, runinfo, start, end = None) :
        """ Replaces the subrange between a slot with id of start up to but
            not including a slot with id of end (if specified, else the end
            of the run), with the given runinfo.
            Returns the two indices for (start, end) on the input run before
            editing."""
        if not end or end == "0000-00-0000" : fin = len(self)
        for (i, s) in enumerate(self) :
            if s.id == start :
                ini = i
            elif s.id == end :
                fin = i
        res = []
        for r in runinfo :
            s = Slot(r)
            res.append(s)
        self[ini:fin] = res
        for (i, s) in enumerate(self) :
            s.index = i
        return (ini, fin)


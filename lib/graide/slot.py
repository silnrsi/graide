
from graide.dataobj import DataObj
from graide.attribview import Attribute, AttribModel

class Slot(DataObj) :

    def __init__(self, info) :
        for k, v in info.items() :
            setattr(self, k, v)

    def attribModel(self) :
        res = []
        for k in ('index', 'gid', 'break', 'insert') :
            res.append(Attribute(k, self.__getattribute__, None, False, k))
        for k in ('origin', 'advance') :
            res.append(Attribute(k, self.getpos, None, False, k))
        for k in ('before', 'after') :
            res.append(Attribute(k, self.getcharinfo, None, False, k))
        ures = []
        for i in range(len(self.user)) :
            ures.append(Attribute(str(i), self.getuser, None, False, i))
        resAttrib = AttribModel(res)
        uAttrib = AttribModel(ures, resAttrib)
        resAttrib.add(Attribute('user attributes', None, None, True, uAttrib))
        return resAttrib

    def getpos(self, name) :
        res = self.__getattribute__(name)
        return "(%d, %d)" % (res[0], res[1])

    def getcharinfo(self, name) :
        return self.charinfo[name]

    def getuser(self, index) :
        return self.user[index]


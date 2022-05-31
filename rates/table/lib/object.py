

class Object:
    def __init__(self, master, event, objDef, idx):
		self.master = master
        self.event  = event
        self.objDef = objDef
		self.idx    = idx
    def __getattr__(self, name):
        if name[:2] == "__" and name[-2:] == "__": self.master.vb.error("Doing something stupid")
		if not name in self.objDef.variables     : self.master.vb.error("Doing something stupid")
        if name in self.__dict__: return self.__dict__[name]
        value = getattr(self.event, self.objDef.basebranch+self.objDef.separator+name)[self.idx]
		self.__dict__[name] = value
        return value
    def __getitem__(self, attr):
        return self.__getattr__(attr)

class Objectlist:
    def __init__(self, master, event, objDef):
		self.master = master
        self.event  = event
        self.objDef = objDef
		self.length = getattr(event, objDef.lengthBranch)
        self.cache  = {}
    def __getitem__(self, idx):
		if not type(idx) == int: self.master.vb.error("Doing something stupid")
		if idx >= self.length  : self.master.vb.error("Doing something stupid")
		if idx in self.cache.keys(): return self.cache[idx]
		obj = Object(self.master, self.event, self.objDef, idx)
		self.cache[idx] = obj
		return obj
    def __len__(self):
        return self.length





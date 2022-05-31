import os
from functions import *


class CfgObject:
	def __init__(self, name, optstring):
		self.name    = name
		self.options = {}  
		self.loadOpts(optstring)
	def __getattr__(self, key):
		if key in self.options.keys(): return self.options[key]
		return None
	def loadOpts(self, optstring):
		if len(optstring)==0: return
                print "optstring",optstring
		for entry in [so.strip() for so in optstring.split(";")]:
			if len(entry)==0: continue
			se = [see.strip() for see in entry.split(":=")]
                        print "print se",se
			isList = False; isDict = False
			if   se[0][-1:]=="+": isList = True; se[0] = se[0][0:-1]
			elif se[0][-1:]=="#": isDict = True; se[0] = se[0][0:-1]

                        print se[0],se[1],isList,isDict
			self.options[se[0]] = setType(se[1], isList=isList, isDict=isDict)
                        print self.options[se[0]]

class Cfg:
	def __init__(self, path):
		self.path = path
		self.load()
	def load(self):
		if not self.path: return
		if not os.path.exists(self.path): return
		lines = [l.rstrip("\n").strip() for l in open(self.path, "r").readlines()]
		lines = mergeLines(lines)
		for line in lines:
			if len(line) == 0: continue
			if line[0:1] == "#": continue
			fields = [sl.strip() for sl in line.split("::")]
			if len(fields)<2: continue
			if fields[0] in ["variable", "alias"]:
				if len(fields)<3: continue
				if not hasattr(self, fields[0]): setattr(self, fields[0], {})
				getattr(self, fields[0])[fields[1]] = setType(fields[2])
				continue
			if not hasattr(self, fields[0]): setattr(self, fields[0], [])
			getattr(self, fields[0]).append(CfgObject(fields[1], fields[2] if len(fields)>2 else ""))




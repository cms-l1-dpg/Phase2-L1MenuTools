from functions import *
from cfg       import *

import ROOT
import numpy
import math
import collections
import inspect

def _getArgs(trigLeg, selectedByOtherLegs):
	args = [[] for i in range(len(trigLeg.functs.keys()))]
	for iu in range(len(args)):
		#print "iu",iu
		#print "uses",trigLeg.uses[iu]
		selected = [olist for io,olist in enumerate(selectedByOtherLegs) if io+1 in trigLeg.uses[iu]] ## first leg is called "1" not "0"
		nElms    = [len(theobjs) for theobjs in selected]
		nVars    = int(numpy.prod(nElms)) if len(nElms)>0 else 0
		#print "selected",selected
		#print "nElms", nElms
		#print "nVars",nVars
		if nVars == 0: continue
		for iVar in range(nVars):
			args[iu].append([selected[i][(iVar/numpy.prod(nElms[i+1:]))%numpy.prod(nElms[i])] for i in range(len(selected[0:-1]))] + [selected[-1][iVar%nElms[-1]]])
	return args

def _multi(functions, event, trigObjlists, trigLeg, selectedByOtherLegs, onlyThresholdCut=False, exceptThresholdCut=False):
	#print "bam oida"
	objs  = trigObjlists[trigLeg.obj.name]
	nObjs = len(objs)
	if nObjs<trigLeg.num: return [[] for i in range(trigLeg.num)] ## not enough objects in the event

	def objsInArgs(theObjs, args):
		for iu in range(len(args)):
			for iv in range(len(args[iu])):
				if any([x in args[iu][iv] for x in theObjs]):
					return True
		return False

	args = _getArgs(trigLeg, selectedByOtherLegs)
	goodObjs = []
	for io in range(trigLeg.num):
		goodObjs.append([])
		elms = [goodObjs[i] for i in range(io)]
		for i in range(nObjs):
			if objsInArgs([objs[i]], args): continue
			if not trigLeg.apply(functions, objs[i], io, args, elms, False, onlyThresholdCut=False, exceptThresholdCut=False): continue
			goodObjs[io].append(objs[i])

	#print goodObjs

	combinations = []
	nElms = [len(goodObjs[io]) for io in range(trigLeg.num)]
	nVars = int(numpy.prod(nElms))
	#print nVars
	for iVar in range(nVars):
		newentry = [(iVar/numpy.prod(nElms[i+1:]))%numpy.prod(nElms[i]) for i in range(len(nElms)-1)] + [iVar%nElms[-1]]
		if any([x!=1 for x in collections.Counter(newentry).values()]): continue
		if newentry in combinations: continue
		combinations.append(newentry)
	#print "combinations:",len(combinations)


	for comb in combinations:
		theObjs = [goodObjs[io][comb[io]] for io in range(trigLeg.num)]
		#print comb, theObjs
		#print [x.Et for x in theObjs], [x.Eta for x in theObjs], [x.Phi for x in theObjs], [x.zVtx for x in theObjs]

		#if objsInArgs(theObjs, args): continue
		elms = [[x for x in theObjs[0:io]] for io in range(len(theObjs))]

		allpass = True
		for io, obj in enumerate(theObjs):
			if not trigLeg.apply(functions, obj, io, args, elms[io], True, onlyThresholdCut=False, exceptThresholdCut=False): 
				#print "	failed"
				allpass = False
				break
		if not allpass: continue
		result = [[theObjs[i]] for i in range(len(comb))] ## only returning one combination!
		#print "returning", result
		return result

	#print "returning emptiness"
	return [[] for i in range(trigLeg.num)]

	#nObjs = len(objs)
	#idxs = [range(i, nObjs) for i in range(trigLeg.num)]
	#combinations = [(0,1,2,3), (0,1,3,2), (0,2,1,3), (0,2,3,1), (0,3,1,2), (0,3,2,1), 
	#                (1,0,2,3), (1,0,3,2), (1,2,0,3), (1,2,3,0), (1,3,0,2), (1,3,2,0),
	#                (2,1,0,3), (2,1,3,0), (2,0,1,3), (2,0,3,1), (2,3,1,0), (2,3,0,1),
	#                (3,1,2,0), (3,1,0,2), (3,2,1,0), (3,2,0,1), (3,0,1,2), (3,0,2,1)]
	#print idxs
	#tested = []
	#for comb in combinations:
	#	theObjs = [objs[comb[i]] for i in range(len(comb))]
	#	print [comb[i] for i in range(len(comb))] 


	#for iVar in range(nVars):
	#	idxs = [(iVar/numpy.prod(nElms[i+1:]))%nElms[i] for i in range(trigLeg.num-1)] + [iVar%nElms[-1]]
	#	if any(x==idxs[0]

	#	print iVar
	#	print [numpy.prod(nElms[i+1:]) for i in range(trigLeg.num-1)]
	#	print [(iVar/numpy.prod(nElms[i+1:]))%nElms[i] for i in range(trigLeg.num-1)]
	#	combinations.append([objs[(iVar/numpy.prod(nElms[i+1:]))%numpy.prod(nElms[i])] for i in range(trigLeg.num-1)] + [objs[iVar%nElms[-1]]])
	#print combinations


	#combinations = [objs for i in range(trigLeg.num)]
	#for comb in combinations:
	#	if any([o==comb[0] for o in comb[1:]]): continue



	#selected = []
	#for obj in [objs[io] for io in range(objs.length)]:
	#	pargs = []
	#	for iu in range(len(args)): 
	#		pargs.append([])
	#		for iv in range(len(args[iu])):
	#			pargs[iu].append([])
	#			pargs[iu][iv] = [x for x in args[iu][iv] if x!=obj]
	#			#print obj
	#			#print obj==obj
	#			#print obj!=obj
	#			#print "args",args[iu][iv]
	#			#print "pargs",pargs[iu][iv]

	#	print
	#	print "looping on",obj
	#	print obj.Et, obj.Eta, obj.Phi, obj.zVtx
	#	#name = str(obj)
	#	##if "EG" in name and not "TkEG" in name:
	#	##	print math.sqrt(math.pow(abs(abs(obj.Eta)-abs(pargs[3][0][0].Eta)),2)+math.pow(obj.Phi-pargs[3][0][0].Phi,2))
	#	##	print functions["notMatched"](obj.Eta, pargs[3][0][0].Eta, obj.Phi, pargs[3][0][0].Phi)
	#	#if "Tau" in name and not "TkTau" in name:
	#	#	#print pargs[3][0][0].Eta, pargs[3][0][0].Phi
	#	#	#print obj.Phi-pargs[3][0][0].Phi
	#	#	#print math.sqrt(math.pow(abs(abs(obj.Eta)-abs(pargs[3][0][0].Eta)),2)+math.pow(obj.Phi-pargs[3][0][0].Phi,2))
	#	#	#print "bla", math.pow(abs(obj.Phi-pargs[3][0][0].Phi) if abs(obj.Phi-pargs[3][0][0].Phi)<=math.pi else 2*math.pi-abs(obj.Phi-pargs[3][0][0].Phi),2)
	#	#	print functions["deltaR"](obj.Eta, pargs[3][0][0].Eta, obj.Phi, pargs[3][0][0].Phi)
	#	if not trigLeg.apply(functions, obj, pargs): continue
	#	print "selection is true"
	#	selected.append(obj)
	#print "preselected:",selected
	#print "by others:",selectedByOtherLegs

	#result = selected
	#for io,others in enumerate(selectedByOtherLegs):
	#	if len(others)!=1: continue 
	#	if not others[0] in result: continue
	#	result.remove(others[0])

	#print "toremove",result

	#for io,others in enumerate(selectedByOtherLegs):
	#	#print "io",io
	#	if len(others)==1: continue 
	#	wouldremove = []
	#	for obj in result:
	#		if not obj in others: continue
	#		wouldremove.append(obj)
	#	
	#	## below: remove objects from previous legs
	#	## in case the previous leg is using the same object: keep at least one in there
	#	## which is also selected by this leg
	#	keepFirst = (len(result)>1 and trigLeg.prevobjs[io])
	#	if len(wouldremove)>0 and wouldremove[0] in result and keepFirst: 
	#		result.remove(wouldremove[0])
	#	for obj in (wouldremove[1:] if keepFirst else wouldremove):
	#		others.remove(obj)


def _leg(functions, event, trigObjlists, trigLeg, selectedByOtherLegs, onlyThresholdCut=False, exceptThresholdCut=False):
	result = []
	objs = trigObjlists[trigLeg.obj.name]
	#print 
	#print "+"*15
	#print "processing",trigLeg.idx,trigLeg.raw
	#print selectedByOtherLegs
	args = _getArgs(trigLeg, selectedByOtherLegs)


	## this is a bug!!
	## the point is: there can be multiple previously selected objects per leg => only need to find one of them to match 
	## in fact, it would be better to have a loop over the different legs
	## meaning, once the first object of the first leg is found, automatically probe the second leg
	## discard the whole thing if the second leg does not match, and try to find the first one again
	## this is necessary because the second leg could be matched to the first one, and if the first one is wrongly chosen, the event is wrongly selected or discarded

	## careful!
	## when running the second leg, the first leg is already run; it means, the possibilities are already there in selectedByOtherLegs
	## now what needs to be done at the second leg is to find one possibility that works...


	#print args
#	print "blubaaaa",trigLeg.prevobjs
	selected = []
	for obj in [objs[io] for io in range(objs.length)]:
		pargs = []
		for iu in range(len(args)): 
			pargs.append([])
			for iv in range(len(args[iu])):
				pargs[iu].append([])
				pargs[iu][iv] = [x for x in args[iu][iv] if x!=obj]
				#print obj
				#print obj==obj
				#print obj!=obj
				#print "args",args[iu][iv]
				#print "pargs",pargs[iu][iv]

		#print
		#print "looping on",obj
		#print obj.Et, obj.Eta, obj.Phi, obj.zVtx
		#name = str(obj)
		##if "EG" in name and not "TkEG" in name:
		##	print math.sqrt(math.pow(abs(abs(obj.Eta)-abs(pargs[3][0][0].Eta)),2)+math.pow(obj.Phi-pargs[3][0][0].Phi,2))
		##	print functions["notMatched"](obj.Eta, pargs[3][0][0].Eta, obj.Phi, pargs[3][0][0].Phi)
		#if "Tau" in name and not "TkTau" in name:
		#	#print pargs[3][0][0].Eta, pargs[3][0][0].Phi
		#	#print obj.Phi-pargs[3][0][0].Phi
		#	#print math.sqrt(math.pow(abs(abs(obj.Eta)-abs(pargs[3][0][0].Eta)),2)+math.pow(obj.Phi-pargs[3][0][0].Phi,2))
		#	#print "bla", math.pow(abs(obj.Phi-pargs[3][0][0].Phi) if abs(obj.Phi-pargs[3][0][0].Phi)<=math.pi else 2*math.pi-abs(obj.Phi-pargs[3][0][0].Phi),2)
		#	print functions["deltaR"](obj.Eta, pargs[3][0][0].Eta, obj.Phi, pargs[3][0][0].Phi)

		if not trigLeg.apply(functions, obj, pargs, onlyThresholdCut=False, exceptThresholdCut=False): continue
		#print "selection is true"
		selected.append(obj)
	#print "preselected:",selected
	#print "by others:",selectedByOtherLegs

###	result = selected
###	for io,others in enumerate(selectedByOtherLegs):
###		if len(others)!=1: continue 
###		if not others[0] in result: continue
###		result.remove(others[0])
###
###	print "toremove",result
###
###	for io,others in enumerate(selectedByOtherLegs):
###		#print "io",io
###		if len(others)==1: continue 
###		wouldremove = []
###		for obj in result:
###			if not obj in others: continue
###			wouldremove.append(obj)
###		
###		## below: remove objects from previous legs
###		## in case the previous leg is using the same object: keep at least one in there
###		## which is also selected by this leg
###		keepFirst = (len(result)>1 and trigLeg.prevobjs[io])
###		if len(wouldremove)>0 and wouldremove[0] in result and keepFirst: 
###			result.remove(wouldremove[0])
###		for obj in (wouldremove[1:] if keepFirst else wouldremove):
###			others.remove(obj)
		
	for obj in selected:
		used=False
		for io,others in enumerate(selectedByOtherLegs):
			#print "io",io
                        #print "obj",obj
                        #print "others",others
			if obj in others:
				if len(others)==1:   ## in this case, the other trigger leg 
					used=True; break ## would end up with len(objects)==0,
				                     ## which means the event is rejected
				                     ## so the event cannot be removed from
				                     ## that list nor can it be kept for this leg
				others.remove(obj)
		if not used: result.append(obj)
	#print "selected:",result
	#print "others:",selectedByOtherLegs
	#print
	return result



class TriggerObject:
	def __init__(self, master, objDef):
		self.master  = master
		self.name    = objDef.name
		self.opts    = objDef.options
		self.load()
	def load(self):
		## set variables the trigger object needs 
		basebranch   = self.opts["basebranch"  ] if "basebranch"   in self.opts.keys() else "Muon"
		lengthbranch = self.opts["lengthbranch"] if "lengthbranch" in self.opts.keys() else "n"+basebranch
		separator    = self.opts["separator"   ] if "separator"    in self.opts.keys() else ""
		leadingvar   = self.opts["leadingvar"  ] if "leadingvar"   in self.opts.keys() else "Et"
		leadingop    = self.opts["leadingop"   ] if "leadingop"    in self.opts.keys() else ">"
		isFlat       = self.opts["isFlat"      ] if "isFlat"       in self.opts.keys() else False
		fixedIndex   = self.opts["fixedIndex"  ] if "fixedIndex"   in self.opts.keys() else -1
		self.onToOff = self.opts["onToOff"     ] if "onToOff"      in self.opts.keys() else 0
		varnames     = []
		varbranch    = []
		for raw in self.opts["variables"]:
			if "=" in raw:
				sr = raw.split("=")
				varnames .append(sr[0])
				varbranch.append(sr[1])
			else:
				varnames .append(raw)
				varbranch.append(raw)
		if not leadingvar in varnames: 
			self.master.vb.warning("Leading variable ("+leadingvar+") does not exist for object "+self.name+"!\nUsing "+varnames[0]+" with operator "+leadingop+" instead. Results may be different than expected!")
			leadingvar = varnames[0]
		self.branches = {}
		for iv, var in enumerate(varnames):
                        print basebranch + separator + varbranch[iv]
			self.branches[var] = basebranch + separator + varbranch[iv]
			#self.master.vb.talk("Register branch "+self.branches[var]+" with name "+var+" for object "+self.name)
		self.lengthbranch = lengthbranch
		self.leadingvar   = leadingvar
		self.leadingop    = leadingop  
		self.isFlat       = isFlat
		self.fixedIndex   = fixedIndex
	def replaceBranches(self, theString):
		## build TDraw compatible strings from variable names
		for seek, replacement in self.branches.iteritems():
			theString = theString.replace(seek, replacement)
		return theString


class TriggerSelection(object):
	def __init__(self):
		self.thresholdCut = ""
		self.thresholdVar = lambda obj: -1
	def buildCut(self, key, cut):
		if type(cut)==type(True):
			return key, str(cut), False, []
		if isFloat(cut) or isInt(cut):
			cut = "obj."+self.obj.leadingvar+self.obj.leadingop+str(cut)
			return key, cut, False, []
                if ("leading" in cut):
                        cut  = "obj."+self.obj.leadingvar+str(cut.replace("leading",""))
                        if any([x in cut for x in self.master.functions.keys()]):
                                for fname in self.master.functions.keys():
                                        if fname in cut:
                                                cut = re.sub(r"\w*(?<![a-zA-Z])(?<!\.)"+fname, "functions[\""+fname+"\"]", cut)
                        print "test1",key, cut
                        return key, cut, False, []
                        
		if ":" in cut:
			sc = cut.split(":")
			key = sc[0]
			cut = sc[1]
		cut = cut.replace("[","(").replace("]",")")
		uses = list(set([int(i) for i in re.findall(r'\bleg(\d+)\.\b', cut)]))
		elms = list(set([int(i) for i in re.findall(r'\belm(\d+)\.\b', cut)]))
		if not (any([x in cut for x in self.obj.opts["variables"]])): 
			self.master.vb.error("Doing something stupid")
		if any([x in cut for x in self.master.functions.keys()]):
			for fname in self.master.functions.keys():
				if fname in cut:
                                        print "test2",cut
					cut = re.sub(r"\w*(?<![a-zA-Z])(?<!\.)"+fname, "functions[\""+fname+"\"]", cut)
                                        print "test3",cut
		for var in self.obj.opts["variables"]:
			if var in cut:
                                print "test4",cut
				cut = re.sub(r"\w*(?<![a-zA-Z])(?<!\.)"+var, "obj."+var, cut) ## replace only if no letter in front if it (other function?)
                                print "test5",cut
                print "test6",key, cut, len(elms)>0, uses
		return key, cut, len(elms)>0, uses
	def getCutValue(self, rawcut):
		if type(rawcut)==list:
			return [self.getCutValue(rawcut[i]) for i in range(len(rawcut))]
		if "<=" in rawcut: return float(rawcut.split("<=")[1])
		if ">=" in rawcut: return float(rawcut.split(">=")[1])
		if "<"  in rawcut: return float(rawcut.split("<" )[1])
		if ">"  in rawcut: return float(rawcut.split(">" )[1])
		if "!=" in rawcut: return float(rawcut.split("!=")[1])
		if "==" in rawcut: return float(rawcut.split("==")[1])
		return float(rawcut)
	def getCutVar(self, rawcut):
		if type(rawcut)==list:
			return [self.getCutVar(rawcut[i]) for i in range(len(rawcut))]
		if "<=" in rawcut: return float(rawcut.split("<=")[0])
		if ">=" in rawcut: return float(rawcut.split(">=")[0])
		if "<"  in rawcut: return float(rawcut.split("<" )[0])
		if ">"  in rawcut: return float(rawcut.split(">" )[0])
		if "!=" in rawcut: return float(rawcut.split("!=")[0])
		if "==" in rawcut: return float(rawcut.split("==")[0])
		return None
	def setCutValue(self, rawcut, newthreshold):
		if type(rawcut)==list and len(rawcut)==len(newthreshold):
			return [self.setCutValue(rawcut[i], newthreshold[i]) for i in range(len(rawcut))]
		if not any([x in rawcut for x in ["<",">","="]]): return float(newthreshold)
		if "<=" in rawcut: return rawcut.split("<=")[0]+"<="+str(newthreshold)
		if ">=" in rawcut: return rawcut.split(">=")[0]+">="+str(newthreshold)
		if "<"  in rawcut: return rawcut.split("<" )[0]+"<" +str(newthreshold)
		if ">"  in rawcut: return rawcut.split(">" )[0]+">" +str(newthreshold)
		if "!=" in rawcut: return rawcut.split("!=")[0]+"!="+str(newthreshold)
		if "==" in rawcut: return rawcut.split("==")[0]+"=="+str(newthreshold)
		return float(rawcut)
	def setThresholdCut(self, name):
		self.thresholdCut = name
		cutvar            = self.getCutVar(self.cuts[name])
		self.thresholdVar = eval("lambda obj: "+cutvar if cutvar else self.obj.leadingvar)

class TriggerLeg(TriggerSelection):
	def __init__(self, master, obj, cuts, idx):
		super(TriggerLeg,self).__init__()
		self.master   = master
		self.obj      = obj
		self.idx      = int(idx)
		self.raw      = " ".join([str(c) for c in cuts])
		self.uses     = []
		#self.prevobjs = [obj.name==x for x in prevobjs]
		self.buildDef(cuts)
		self.characterize()
	def getThreshold(self, obj):
		return self.thresholdVar(obj)
	def apply(self, functions, obj, args, onlyThresholdCut=False, exceptThresholdCut=False):
		#print "## running trigger leg", self.raw, obj
		#print args
		for name,function in self.functs.iteritems():
			isThresholdCut = (name==self.thresholdCut)
			if (onlyThresholdCut and not isThresholdCut) or (exceptThresholdCut and isThresholdCut): continue
			iu = int(name.replace("cut",""))
			#print name, iu, self.uses[iu], args[iu]
			if len(self.uses[iu])>0 and len(args[iu])==0: return False ## no variations
			if len(args[iu])==0:
				#print "running normal function",name,obj
				if not function(functions, obj): return False
			else:
				#print "running special", args[iu]
				## args[iu] contains all variations of the list of arguments
				## only one variation needs to work to trigger the event
				## N.B. the object selected here, if in a different collection
				## than previous legs (e.g. leg1=TkEG, leg2=EG), can still
				## overlap with the object selected at any of the previous legs
				## but this is no problem since at least one combination of objects
				## needs to work; when probing further legs (e.g. leg3 depending
				## on leg1 and leg2), the proper combination to probe is among
				## the ones that is probed
				anytrue = False
				for arg in args[iu]:
					if len(self.uses[iu])!=len(arg): continue
					#print arg
					#print arg[0].zVtx, obj.zVtx, abs(obj.zVtx-arg[0].zVtx)
					if function(functions, obj, *arg): anytrue=True#; print "true here!"
				if not anytrue: return False
		return True
	def buildDef(self, cuts):
		self.cuts = {}
		for ic,cut in enumerate(cuts):
			key = "cut"+str(ic)
			self.uses.append([])
			key, cut, elms, self.uses[ic] = self.buildCut(key, cut)
			self.cuts[key] = cut
			##if isFloat(cut) or isInt(cut):
			##	self.cuts[key] = "obj."+self.obj.leadingvar+self.obj.leadingop+str(cut)
			##	self.uses.append([])
			##	continue
			##if ":" in cut:
			##	sc = cut.split(":")
			##	key = sc[0]
			##	cut = sc[1]
			##self.uses.append(list(set([int(i) for i in re.findall(r'\bleg(\d+)\.\b', cut)])))
			##if not any([x in cut for x in self.obj.opts["variables"]]): 
			##	self.master.vb.error("Doing something stupid")
			##if any([x in cut for x in self.master.functions.keys()]):
			##	for fname in self.master.functions.keys():
			##		if fname in cut:
			##			cut = re.sub(r"\w*(?<![a-zA-Z])(?<!\.)"+fname, "functions[\""+fname+"\"]", cut)
			##for var in self.obj.opts["variables"]:
			##	if var in cut:
			##		cut = re.sub(r"\w*(?<![a-zA-Z])(?<!\.)"+var, "obj."+var, cut) ## replace only if no letter in front if it (other function?)
			##self.cuts[key] = cut
		self.functs  = {}
		for key,cut in self.cuts.iteritems():
			iu = int(key.replace("cut",""))
			toUse = self.uses[iu]
			#print "DONE:",iu,key,cut,"lambda functions, obj"+(", "+", ".join("leg"+str(i) for i in toUse) if len(toUse)>0 else "")+": "+cut
			self.functs[key] = eval("lambda functions, obj"+(", "+", ".join("leg"+str(i) for i in toUse) if len(toUse)>0 else "")+": "+cut)
	def characterize(self):
		## find the id of the virtual leg
		self.legId = [self.master.getLegId(["leg", self.obj.name] + [c for k,c in self.cuts.iteritems()])]


class TriggerMulti(TriggerSelection):
	def __init__(self, master, obj, num, cuts, idx):
		super(TriggerMulti,self).__init__()
		self.master   = master
		self.obj      = obj
		self.num      = int(num)
		self.idx      = int(idx)
		self.raw      = " ".join([str(c) for c in cuts])
		self.uses     = []
		self.elms     = []
		self.buildDef(cuts)
		self.characterize()
	def apply(self, functions, obj, io, args, elms, onlyWithElms=True, onlyThresholdCut=False, exceptThresholdCut=False):
		#print "## running trigger leg", self.raw, obj, io
		#print args
		for name,function in self.functs.iteritems():
			iu = int(name.replace("cut",""))
			isThresholdCut = (name==self.thresholdCut)
			if (onlyThresholdCut and not isThresholdCut) or (exceptThresholdCut and isThresholdCut): continue
			if (onlyWithElms and not self.elms[iu]) or (not onlyWithElms and self.elms[iu]): continue
			#print name, function, iu, self.uses[iu], args[iu], self.elms[iu]
			if len(self.uses[iu])>0 and len(args[iu])==0: return False ## no variations
			if len(args[iu])==0:
				#print "running normal function",name,io,function
				if len(elms)==0:
					if not function[io](functions, obj): return False
				else:
					if not function[io](functions, obj, *elms): return False
			else:
				#print "running special", args[iu]
				## args[iu] contains all variations of the list of arguments
				## only one variation needs to work to trigger the event
				## N.B. the object selected here, if in a different collection
				## than previous legs (e.g. leg1=TkEG, leg2=EG), can still
				## overlap with the object selected at any of the previous legs
				## but this is no problem since at least one combination of objects
				## needs to work; when probing further legs (e.g. leg3 depending
				## on leg1 and leg2), the proper combination to probe is among
				## the ones that is probed
				anytrue = False
				for arg in args[iu]:
					if len(self.uses[iu])!=len(arg): continue
					#print arg
					#print arg[0].zVtx, obj.zVtx, abs(obj.zVtx-arg[0].zVtx)
					myargs = arg + elms
					if function[io](functions, obj, *myargs): anytrue=True#; print "true here!"
				if not anytrue: return False
		return True
	def buildDef(self, cuts):
		self.cuts = {}
		for ic,cut in enumerate(cuts):
			key = "cut"+str(ic)
			self.cuts[key] = [True for i in range(self.num)]
			self.uses.append([])
			self.elms.append([])
			if type(cut)==list:
				for ii, c in enumerate(cut):
					key, cutstring, self.elms[ic], self.uses[ic] = self.buildCut(key, c)
					self.cuts[key][ii] = cutstring
			else:
				for ii in range(self.num):
					key, cutstring, self.elms[ic], self.uses[ic] = self.buildCut(key, cut)
					self.cuts[key][ii] = cutstring
		self.functs = {}
		for key,cut in self.cuts.iteritems():
			print key, cut
			self.functs[key] = [{} for i in range(self.num)]
			iu = int(key.replace("cut",""))
			toUseL = self.uses[iu]
			for ic in range(self.num):
				astring = ", ".join("leg"+str(i) for i in toUseL       ) if len(toUseL)>0 else ""
				estring = ", ".join("elm"+str(i) for i in range(1,ic+1)) if ic>0          else ""
				full = ", "+astring+", "+estring if astring!="" and estring!="" else ", "+astring if astring!="" else ", "+estring if estring!="" else ""
				print "DONE:",iu,ic,key,cut[ic],"lambda functions, obj"+full+": "+cut[ic]
				self.functs[key][ic] = eval("lambda functions, obj"+full+": "+cut[ic])
				#self.functs[key][ic] = eval("lambda functions, obj"+(", ("+", ".join("leg"+str(i) for i in toUseL)+")" if len(toUseL)>0 else "")+(", ("+", ".join("elm"+str(ii) for ii in range(ic))+")" if ic>0 else "")+": "+cut[ic])
	def characterize(self):
		## find the id of the virtual leg
		self.legId = []
		for io in range(self.num):
			self.legId.append(self.master.getLegId(["multi"+str(io), self.obj.name] + [c[io] for k,c in self.cuts.iteritems()]))


class Trigger:
	def __init__(self, master, trigDef):
                print "init Trigger"+trigDef.name
                print trigDef.options
		self.master   = master
		self.name     = trigDef.name
		self.opts     = trigDef.options
		self.parent   = None
		self.trigVar  = {}
                print "load Trigger"+trigDef.name
		self.load()
                print "characterize Trigger"+trigDef.name
		self.characterize()
                print "Done with Trigger"+trigDef.name
	def apply(self, event, trigObjlists, onlyThresholds=False, exceptThresholds=False):
		legs = []
		for leg in self.legs.values():
			legs.append(_leg(self.master.functions, event, trigObjlists, leg, legs))
		for mul in self.multis.values():
			multi = _multi(self.master.functions, event, trigObjlists, mul, legs)
			legs.extend(multi)
		#print "RESULT BELOW:"
		#print legs
		if any([len(l)==0 for l in legs]): return False
		#print legs
		#print event.entry
		return True 
	def characterize(self):
		legIds = []
		for leg in self.legs.values():
			legIds.extend(leg.legId)
		for leg in self.multis.values():
			legIds.extend(leg.legId)
		## check this look up of the trigger id again, especially for the variation case!!
		self.triggerId = self.master.getTrigId(["single"] + legIds)
	def getCutValue(self, legname, cutname):
		#print legname, self.legnames, cutname, self.multis[legname].cuts.keys()
		#print legname, self.legnames, cutname, self.legs[legname].cuts.keys()
		if not legname in self.legnames: return None
		collection = self.multis if "multi" in legname else self.legs
		if not cutname in collection[legname].cuts.keys(): return None
		rawExpr = collection[legname].cuts[cutname]
		print rawExpr
		return collection[legname].getCutValue(rawExpr)
	def getLegNameByIdx(self, legidx):
		if legidx>=len(self.legnames): return None
		return self.legnames[legidx]
	def getLegByName(self, legname):
		if not legname in self.legnames: return None
		return self.legs[legname] if "leg" in legname else self.multis[legname]
	def makeVar(self, varname, varleg, varcut, varvalue):
		## create a copy of the trigger with a varied cut 
		print
		print "make new var", varvalue
		newDef    = CfgObject(self.name+"_"+varname,"")
		varvalue  = float(varvalue)
		legToVary = self.legnames[0] if varleg=="any" else varleg
		theLeg    = self.multis[legToVary] if "multi" in legToVary else self.legs[legToVary]
		add       = 2 if "multi" in legToVary else 1 ## entry 0 = object, entry 1 = first cut, +1 in multi
		cutIdx    = int(varcut.replace("cut",""))-1
		cutToVary = "cut"+str(cutIdx)
		#cutToVary = int(varcut.replace("cut",""))+add
		## when multiple legs are present, varleg and varvalue will only affect one of the legs
		## thus need to keep the ratio of these cuts fixed and vary all other legs accordingly !!!
		print self.legnames, cutToVary, add
		oldvalues = [self.getCutValue(ln, cutToVary) for ln in self.legnames]
		print oldvalues
		newvalues = oldvalues[:]
		refs      = oldvalues[self.legnames.index(legToVary)]
		varvalues = [varvalue]
		if type(refs)!=list: refs = [refs]
		print refs
		if "multi" in legToVary and len(refs)>1: 
			## if only one value is given for a multi-leg, it means that it is the leading value, 
			## and all other legs must be scaled up too accordingly 
			for ie in range(1,len(refs)):
				varvalues.append(refs[ie]*(varvalue/refs[0]))
		print "after newvarvalue",varvalues
		scales = [varvalues[i]/refs[i] for i in range(len(varvalues))]
		print "scales is",scales
		if sum(scales)==len(scales): 
			self.varValue = varvalue
			print "RETURNING",self.triggerId
			return self
		for iv,oldvalue in enumerate(oldvalues):
			if type(oldvalue)==list:
				newvalues[iv] = []
				for ie,elm in enumerate(oldvalue):
					newvalues[iv].append(theLeg.setCutValue(cutToVary, scales[ie]*elm))
				continue
			newvalues[iv] = theLeg.setCutValue(cutToVary, scales[0]*oldvalue) 
			## this is necessary in case the cut you want to vary contains an expression, not just a float or int value
		print varname, varleg, varcut, varvalue
		for key in self.opts.keys():
			##print "probing",key
			if not key in self.legnames: 
				newDef.options[key] = self.opts[key]
				continue
			idx = self.legnames.index(key)
			##print "i am here"
			newleg              = self.opts[key]
			newleg[cutIdx+add]  = newvalues[idx]
			newDef.options[key] = newleg
			print "my varied leg:",key,newleg
		print "MAKING NEW VARIATION WITH",
		print newDef.options
		newTrig = Trigger(self.master, newDef)
		newTrig.parent   = self
		newTrig.varName  = varname
		newTrig.varLeg   = varleg  
		newTrig.varCut   = varcut  
		newTrig.varValue = varvalue
		self.trigVar[varname] = newTrig
		print newTrig.triggerId
		return newTrig
	def load(self):
		## prepare the functions and all other constraints
		## builds list of trigger legs and event selection, each of them functions to be 
		## executed the apply(evt, trigObjlists) then runs all of them with trigObjlists the 
		## actual Objectlists instantiated for a given event
		## for a leg, it takes a _leg(evt, trigObjlists, legDef)
		## for a evt, it takes a _evt(evt, trigObjlists, legs  , evtDef)
                print "loading trigger"
		objnames         = [o.name for o in self.master.menu.objects]
		self.legs        = {}
		self.multis      = {}
		self.ranges      = {}
		self.legnames    = []
		self.legentities = []
		for key in self.opts.keys():
			if "leg" in key:
				args = self.opts[key]
				if not args[0] in objnames:
					self.master.vb.warning("Cannot find trigger object "+args[0]+" for "+key+" of path "+self.name+"\nSkipping this leg! Results may be different than expected!")
					continue
				obj = self.master.menu.objects[objnames.index(args[0])]
				self.legs[key] = TriggerLeg(self.master, obj, args[1:], int(key[3:]))
				self.legnames   .append(key)
				self.legentities.append(self.legs[key])
				##self.legs[key] = TriggerLeg(self.master, obj, args[1:], int(key[3:]), [x.obj.name for x in self.legs.values()])

			if "multi" in key:
				args = self.opts[key]
				if not args[0] in objnames:
					self.master.vb.warning("Cannot find trigger object "+args[0]+" for "+key+" of path "+self.name+"\nSkipping this leg! Results may be different than expected!")
					continue
				obj = self.master.menu.objects[objnames.index(args[0])]
				self.multis[key] = TriggerMulti(self.master, obj, args[1], args[2:], int(key[5:]))
				self.legnames   .append(key)
				self.legentities.append(self.multis[key])

			if "evt" in key:
				pass ## not implemented currently

			if "range" in key:
				args = self.opts[key]
				if len(args)<3:
					self.master.vb.warning("Not enough arguments for "+key+" of path "+self.name+"\nSkipping this range!")
					continue
				if not args[0] in self.legs.keys() and not args[0] in self.multis.keys():
					self.master.vb.warning("Cannot find leg "+args[0]+" for "+key+" of path "+self.name+"\nSkipping this range!")
					continue
				self.ranges[key] = args
	def setThresholdCuts(self):
		varCut = "cut"+str(self.master.cfg.variable["varCut"])
		for leg   in self.legs  .values():
			leg  .setThresholdCut(varCut)
		for multi in self.multis.values():
			multi.setThresholdCut(varCut)
	def setThresholdValues(self, legsresults):
		self.thresholdValues = []
		for i,legresult in enumerate(legsresults):
			self.thresholdValues.append([])
			theLeg = self.legentities[i]
			if len(legresult)==0: self.thresholdValues[i] = [-1]; continue
			for legobj in legresult:
				self.thresholdValues.append(theLeg.getThreshold(legobj))
	def getThresholdValues(self, trig):
		return self.thresholdValues
	

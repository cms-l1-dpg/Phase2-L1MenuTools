import types
import time
import ROOT
import pandas

from functions           import *
from functionsTreeReader import *


class Event:
	def __init__(self, master, tree, entry):
		self.master = master
		self.tree   = tree
		self.entry  = entry
		self.objs   = {}
		self.load()
	def __getattr__(self, key):
		if key in self.objs: return self.objs[key]
		#if hasattr(self.tree, key): return getattr(self.tree, key)
		return readBranch(self.tree, key)
	def __getitem__(self, attr):
		return self.__getattr__(attr)
	def getVector(self, key, index):
		return readBranch(self.tree, key, index)
	def load(self):
		if self.tree.entry == self.entry: return
		if self.tree.entry == self.entry-1: self.tree._ttreereader.Next()
		else: self.tree._ttreereader.SetEntry(self.entry)
		self.tree.entry = self.entry


class Object:
	def __init__(self, master, event, objDef, index):
		self.master = master
		self.event  = event
		self.objDef = objDef
		self.index  = index
		self.values = {}
	def __eq__(self, other):
		if other.__class__.__name__!="Object": return False
		if self is other      : return True
		if self.Et==other.Et and self.Eta==other.Eta and self.Phi==other.Phi: return True
		return False
	def __ne__(self, other):
		if other.__class__.__name__!="Object": return True
		if self is other      : return False
		if self.Et==other.Et and self.Eta==other.Eta and self.Phi==other.Phi: return False
		return True
	def __getattr__(self, key):
		if key in self.values.keys(): return self.values[key]
                if key in self.objDef.branches.keys():
                  value = self.event.getVector(self.objDef.branches[key], self.index)
		  self.values[key] = value
		  return value
                else:
                  return -9999
	def __getitem__(self, attr):
		return self.__getattr__(attr)
	def p4(self, pt = 0):
		ret = ROOT.TLorentzVector()
		if pt > 0: ret.SetPtEtaPhiM(pt     ,self.eta,self.phi,self.mass)
		else     : ret.SetPtEtaPhiM(self.pt,self.eta,self.phi,self.mass)
		return ret
	def __repr__(self):
		return ("<%s[%s]>" % (self.objDef.name, self.index) if self.index != None else ("<%s>" % self.objDef.name))
	def __str__(self):
		return self.__repr__()


class Objectlist:
	def __init__(self, master, event, objDef):
		self.master = master
		self.event  = event
		self.objDef = objDef
		self.name   = objDef.name
		if objDef.isFlat:
			self.length = 1
		else:
			self.length = int(getattr(event, objDef.lengthbranch))
			self.length = self.length if self.length else 0
                if self.length==1 and objDef.fixedIndex>0:
                        self.fixedIndex=objDef.fixedIndex
                else:
                        self.fixedIndex=-1
		self.objs   = {}
	def __getitem__(self, index):
		if type(index) == int and index in self.objs: 
                        return self.objs[index]
		if index >= self.length: 
                        self.master.vb.error("Invalid index %r (length is %r) for object %s" % (index, self.length, self.objDef.name))        
                if (self.fixedIndex>0):
                        obj = Object(self.master, self.event, self.objDef, self.fixedIndex)
                else:
                        obj = Object(self.master, self.event, self.objDef, index)
		self.objs[index] = obj
		return obj
	def __len__(self):
		return self.length



####class VirtualTrigger:
####	def __init__(self, master, trigger, sample, thresholdvar):
####		self.master  = master
####		self.trigger = trigger
####		self.sample  = sample
####	def apply(self):
####		:wq
####vi 
####		if 
####	def retrieveLists(self):
####		toRetrieve = self.master.getListsToRetrieve(self.name)
####		if len(toRetrieve.values())==0: return
####		for rkey, rlist in toRetrieve.iteritems():
####			if rkey in self.lists.keys(): continue
####			self.lists[rkey] = rlist


class Sample:
	def __init__(self, master, sampleDef):
		self.master  = master
		self.name    = sampleDef.name
		self.opts    = sampleDef.options
		self.opened  = False
		self.lists   = {} # ROOT TEventList
		self.buffers = {} # Pandas DataFrame
		self.characterize()
		self.retrieveLists()
	def analyze(self, triggers):
		if not self.opened: self.load()
		self.setEntries()
		toRun = []
		for trigger in triggers:
			if trigger.triggerId in self.lists  .keys() and not self.master.getOpt("force"): continue
			self.lists  [trigger.triggerId] = ROOT.TEventList()
			toRun.append(trigger.triggerId)
		if len(toRun)==0: return
		t0       = time.clock()
		tlast    = t0
		for ievt in xrange(self.getEntries()):
			#if ievt!=2417: continue
			event       = Event(self.master, self.tree, ievt)
			#print event.tkMuonEt
			trigObjects = {}
			for objDef in self.master.menu.objects:
				###objs = Objectlist(self.master, event, objDef)
				trigObjects[objDef.name] = Objectlist(self.master, event, objDef)
				#print objDef.name, len(trigObjects[objDef.name])
			for it,trigger in enumerate([x for x in triggers if x.triggerId in toRun]):
				if trigger.apply(event, trigObjects): 
					#print ievt
					self.lists[trigger.triggerId].Enter(ievt)
			if ievt>0 and ievt%10000 == 0: ## FIXME: customize the sh** out of this!
				t1 = time.clock()
				self.master.vb.talk("Processed %8d/%8d entries of this tree (elapsed time %7.1fs, curr speed %8.3f kHz, avg speed %8.3f kHz)" % (ievt, self.entries, t1-t0, (10.000)/(max(t1-tlast,1e-9)),ievt/1000./(max(t1-t0,1e-9))))
				tlast = t1
		for newId in toRun:
			self.master.addList(newId, self.sampleId, self.lists[newId])
	def analyzePairing(self, triggers):
		if not self.opened: self.load()
		self.setEntries()
		toRun = []
		for trigger in triggers:
			if trigger.triggerId in self.buffers.keys(): continue
			cols = [l for l in trigger.legs.keys()] + [m for m in trigger.multis.keys()]
			self.buffers[trigger.triggerId] = pandas.DataFrame(columns=[trigger.triggerId+"_"+l for l in cols])
			trigger.setThresholdCuts() ### ==> the thing is, i need to collect all threshold c
			toRun.append(trigger.triggerId)
		if len(toRun)==0: return
		t0       = time.clock()
		tlast    = t0
		for ievt in xrange(self.getEntries()):
			#if ievt!=2417: continue
			event       = Event(self.master, self.tree, ievt)
			#print event.tkMuonEt
			trigObjects = {}
			for objDef in self.master.menu.objects:
				###objs = Objectlist(self.master, event, objDef)
				trigObjects[objDef.name] = Objectlist(self.master, event, objDef)
				#print objDef.name, len(trigObjects[objDef.name])
			### here need to put the pairing and store that in the data frame!!!!
			###for it,trigger in enumerate([x for x in triggers if x.triggerId in toRun]):
			###	if trigger.apply(event, trigObjects, exceptThresholds=True): 
			###		self.buffers[trigger.triggerId].append(trigger.getThresholdValues())
			###		if trigger.apply(event, trigObjects, onlyThresholds=True):
			###			#print ievt
			###			self.lists[trigger.triggerId].Enter(ievt)
			if ievt>0 and ievt%10000 == 0: ## FIXME: customize the sh** out of this!
				t1 = time.clock()
				self.master.vb.talk("Processed %8d/%8d entries of this tree (elapsed time %7.1fs, curr speed %8.3f kHz, avg speed %8.3f kHz)" % (ievt, self.entries, t1-t0, (10.000)/(max(t1-tlast,1e-9)),ievt/1000./(max(t1-t0,1e-9))))
				tlast = t1
	def apply(self, trigger):
		if not trigger.triggerId in self.lists.keys(): 
			self.analyze([trigger])
		return self.lists[trigger.triggerId].GetN()
	def characterize(self):
		self.sampleId = self.master.getSampleId(self.opts["path"])
	def close(self):
		if not self.opened: return
		self.tfile.Close()
		self.opened = False	
	def createBuffer(self, triggers):
		if len(triggers)==0: return
		pass
	def getEntries(self):
		if not hasattr(self, "entries"): self.setEntries()
		return self.entries
	def init(self):
		self.tree.entry = -1
		self.tree._ttreereader = ROOT.TTreeReader(self.tree)
		self.tree._ttreereader.SetEntry(0)
		self.tree._ttrvs = {}
		self.tree._ttras = {}
		self.tree._leafTypes = {}
		self.tree._ttreereaderversion = 1
		self.tree.arrayReader = types.MethodType(getArrayReader, self.tree)
		self.tree.valueReader = types.MethodType(getValueReader, self.tree)
		self.tree.readBranch  = types.MethodType(readBranch    , self.tree)
	def intersect(self, triggers):
		toRun = []
		for trigger in triggers:
			if trigger.triggerId in self.lists: continue
			toRun.append(trigger)
		if len(toRun)>0: self.analyze(toRun)
		newId = self.master.getTrigIdFromList(triggers, False)
		lists = [self.lists[trigger.triggerId] for trigger in triggers]
		intersected = lists[0].Clone(newId)
		for thelist in lists[1:]:
			intersected.Intersect(thelist)
		self.lists[newId] = intersected
		self.master.addList(newId, self.sampleId, intersected)
		return intersected.GetN()
	def load(self):
		self.open()
		self.init()
	def merge(self, triggers):
		toRun = []
		for trigger in triggers:
			if trigger.triggerId in self.lists: continue
			toRun.append(trigger)
		if len(toRun)>0: self.analyze(toRun)
		newId = self.master.getTrigIdFromList(triggers, True)
		lists = [self.lists[trigger.triggerId] for trigger in triggers]
		merged = lists[0].Clone(newId)
		for thelist in lists[1:]:
			merged.Add(thelist)
		self.lists[newId] = merged
		self.master.addList(newId, self.sampleId, merged)
		return merged.GetN()
	def open(self):
		if self.opened: return
		self.tfile  = ROOT.TFile.Open(self.opts["path"],"read")
		self.tree   = getRootObj(self.tfile, self.opts["tree"])
		self.opened = True
	def retrieveLists(self):
		## find all virtual trigger ids that contain this sample path
		## then compile a list of teventlists that apply to this sample
		self.lists = self.master.getListsToRetrieve(self.sampleId)
	def setEntries(self):
		if not self.opened: self.load()
		self.entries = self.tree.GetEntries()



		## NO:
		## save an event list per trigger, which carries the name of IDs of the individual legs
		## NO: save event lists indeed per leg, retrieve and apply them per leg (i.e. 
		## intersections, or the analyze is still the trigger.apply but remember which legs to run and which ones not to run
		## then, when varying thresholds, can copy a trigger leg and replace one or more cuts
		## this gives a new character and a new possibility to have a leg for that sample
		## STILL: when varying the thresholds, new triggers need to be analyzed, right? on top of the original event lists (lower thresholds) or completely new?
		## the filename where the lists are stored is the name of the sample + its ID that is stored somewhere related to its path



from functions     import *
from cfg           import *
from menu          import *
from sample        import *
from samplemanager import *
from vb            import *

import os

class Master:
	def __init__(self, args, opts, opts_no_defaults):
		self.args      = args
		self.opts      = opts
		self.optsndef  = opts_no_defaults
		self.cfg       = Cfg(self.args[0])
		self.homedir   = os.path.dirname(os.path.dirname(os.path.realpath(__file__)).rstrip("/"))
		self.cachedir  = absPath(self.getOpt("cachedir") if self.getOpt("cachedir") else "cache", self.homedir)
		self.outdir    = absPath(self.getOpt("outdir")   if self.getOpt("outdir")   else "out"  , self.homedir)
		bdate          = self.getOpt("bundledate") if self.getOpt("bundledate") else shortstamp()
		self.bundle    = bdate+"_"+os.path.basename(self.args[0])
		self.bundledir = self.outdir+"/"+self.bundle
		mkdir(self.cachedir )
		mkdir(self.cachedir+"/lists"   )
		mkdir(self.cachedir+"/virtuals")
		mkdir(self.outdir   )
		mkdir(self.bundledir)
		self.vb        = Verbose(self, self.getOpt("verbose"))
	def getOpt(self, key, default=None):
		if hasattr(self.optsndef, key)    : return getattr(self.optsndef, key)
		if key in self.cfg.variable.keys(): return self.cfg.variable[key]
		if hasattr(self.opts    , key)    : return getattr(self.opts    , key)
		return default
	def sequence(self):
		## this is the main sequence
		#self.loadBundle()
		self.loadVirtualLegs    ()
		self.loadVirtualSamples ()
		self.loadVirtualTriggers()
		self.loadLists          ()
		self.loadFunctions      ()
		self.loadTriggers       ()
		self.loadSamples        ()
		self.checkTasks         ()
		##self.doBuffer           () ## not fully working yet
		self.doThresholds       ()
		self.doVariations       ()
		##self.doBandwidth        () ## not fully working yet
		self.end                ()
	## ---------------------------------------------
	def addList(self, trigId, sampleId, theList):
		theList.SetName(trigId+"_::_"+sampleId)
		if not sampleId in self.retrievableLists.keys(): self.retrievableLists[sampleId] = {}
		self.retrievableLists[sampleId][trigId] = theList
	def checkConstraints(self):
		## check if trigger menu is overconstrained
		pass
	def checkTasks(self):
		self.tasks = []
		## do this via init
		allTiers = ["thresholds", "bandwidth", "buffer", "variations"]
		cfgTiers = self.getOpt("tiers")
		exclude  = self.getOpt("exclude")
		required = []
		if self.getOpt("runThresholds"): required.append("thresholds")
		if self.getOpt("runBandwidth" ): required.append("bandwidth" )
		if self.getOpt("runVariations"): required.append("variations")
		if self.getOpt("runBuffer"    ): required.append("buffer"    )
		for tier in allTiers:
			if (tier in cfgTiers or tier in required) and not tier in exclude: 
				self.tasks.append(tier) 
	def doBandwidth(self):
		mkdir(self.bundledir+"/bandwidth")
		if not "bandwidth" in self.tasks: return
		self.vb.talk("Starting fixed bandwidth tier")
		self.menu.computeThresholdsPerRatesIndiv()
		self.menu.computeThresholdsPerRatesFull()
		self.menu.computeThresholds()
		self.menu.dump(self.bundledir+"/bandwidth")
	def doBuffer(self):
		if not "buffer" in self.tasks: return
		self.vb.talk("Starting to prepare the buffers")
		self.samples.createBuffer()
	def doThresholds(self):
		mkdir(self.bundledir+"/thresholds")
		if not "thresholds" in self.tasks: return
		self.vb.talk("Starting fixed threshold tier")
		self.menu.computeRate()
		self.menu.dump(self.bundledir+"/thresholds")
	def doVariations(self):
		mkdir(self.bundledir+"/variations")
		if not "variations" in self.tasks: return
		self.vb.talk("Starting variations tier")
		self.menu.computeRatesPerThresholds()
		self.menu.fillVariationTable("variations")
		self.menu.dump(self.bundledir+"/variations")
	def dump(self):
		pass
	def end(self):
		self.saveVirtualLegs    ()
		self.saveVirtualSamples ()
		self.saveVirtualTriggers()
		self.saveLists()
		self.samples.closeAll()
		self.vb.close()
	def getLegId(self, character):
		if len(character)==0: return None
		for k,v in self.virtuallegs.iteritems():
			if v == character: return k
		newId = int(timestamp(False))
		while str(newId) in self.virtuallegs.keys():
			newId += 1
		self.virtuallegs[str(newId)] = character
		return str(newId)
	def getListsToRetrieve(self, sampleid):
		if not sampleid: return {}
		if not sampleid in self.retrievableLists.keys(): return {}
		return self.retrievableLists[sampleid]
	def getSampleId(self, path):
		if not path or not os.path.exists(path): return None
		if path[0:1]!="/": path = absPath(path, self.homedir)
		sampleId = [k for k,v in self.virtualsamples.iteritems() if v==path]
		if len(sampleId)==1: return sampleId[0]
		newId = int(timestamp(False))
		while str(newId) in self.virtualsamples.keys():
			#print newId
			newId += 1
		self.virtualsamples[str(newId)] = path
		return str(newId)
	def getTrigId(self, character):
		if len(character)==0: return None
		for k,v in self.virtualtriggers.iteritems():
			if v == character: return k
		newId = int(timestamp(False))
		while str(newId) in self.virtualtriggers.keys():
			newId += 1
		self.virtualtriggers[str(newId)] = character
		return str(newId)
	def getTrigIdFromList(self, listOfTrigs, logicalOr = False):
		if len(listOfTrigs)==0: return None
		if len(listOfTrigs)==1: return listOfTrigs[0].triggerId
		trigids  = [trig.triggerId for trig in listOfTrigs]
		trigtype = "multior" if logicalOr else "multiand"
		newEntry = [trigtype] + trigids
		for k,v in self.virtualtriggers.iteritems():
			if v == newEntry: return k
		newId = timestamp(False)
		self.virtualtriggers[newId] = newEntry
		return newId
	def loadVirtualLegs(self):
		self.virtuallegs     = readCache(self.cachedir+"/virtuals/legs.txt"    , "1:")
	def loadVirtualSamples(self):
		self.virtualsamples  = readCache(self.cachedir+"/virtuals/samples.txt" , "1" )
	def loadVirtualTriggers(self):
		self.virtualtriggers = readCache(self.cachedir+"/virtuals/triggers.txt", "1:", selection=lambda x: all([n in self.virtuallegs.keys() for n in x[2:]]))
	def loadLists(self):
		self.retrievableLists = {}
		for fname in os.listdir(self.cachedir+"/lists"):
			if not ".root" in fname: continue
			f    = ROOT.TFile.Open(self.cachedir+"/lists/"+fname,"read")
			objs = readObjsFromRootFile(f)
			for obj in objs:
				if not obj.ClassName()=="TEventList": continue
				sn = obj.GetName().split("_::_")
				if not sn[0] in self.virtualtriggers .keys(): continue
				if not sn[1] in self.virtualsamples  .keys(): continue
				if not sn[1] in self.retrievableLists.keys(): self.retrievableLists[sn[1]] = {} 
				self.retrievableLists[sn[1]][sn[0]] = obj
			f.Close()
	def loadFunctions(self):
		self.functions = {}
		for f in self.cfg.function:
			if not "lambda" in f.options or not "args" in f.options: continue
			#print "lambda "+",".join(f.options["args"])+": "+f.options["lambda"]
			self.functions[f.name] = eval("lambda "+",".join(f.options["args"])+": "+f.options["lambda"])
	def loadSamples(self):
		self.samples = SampleManager(self)
		for sampDef in self.cfg.sample:
			self.samples.addSample(sampDef)
	def loadTriggers(self):
		self.menu = Menu(self)
		for objDef in self.cfg.object:
			self.menu.addTrigObject(objDef)
		for trigDef in self.cfg.trigger:
			self.menu.addTrigger(trigDef)
	def saveLists(self):
		if len(self.retrievableLists.values())==0: return
		cleandir(self.cachedir+"/lists")
		for sname in self.retrievableLists.keys():
			f = ROOT.TFile.Open(self.cachedir+"/lists/list_"+sname+".root","recreate")
			f.cd()
			for tname, elist in self.retrievableLists[sname].iteritems():
				elist.SetName(tname+"_::_"+sname)
				elist.Write()
			f.Close()
	def saveVirtualLegs(self):
		writeCache(self.cachedir+"/virtuals/legs.txt"    , self.virtuallegs    )
	def saveVirtualSamples(self):
		writeCache(self.cachedir+"/virtuals/samples.txt" , self.virtualsamples , False)
	def saveVirtualTriggers(self):
		writeCache(self.cachedir+"/virtuals/triggers.txt", self.virtualtriggers)
		



## legID  :: LegType :: Object :: Cut1 :: Cut2 :: Cut3
## LegType = leg, multi, evt

## trigID :: TrigType :: leg1ID :: leg2ID :: leg3ID
## TrigType = multior, multiand (a collection of triggers) or single (a single trigger)
## sampleID :: samplePath

## list files are called list_<bundlename>.root
## list objects are called trigID_::_sampleID

## the cuts need to have the functional expressions replaced!




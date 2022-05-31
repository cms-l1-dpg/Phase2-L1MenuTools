from sample import *


class SampleManager:
	def __init__(self, master):
		self.master  = master
		self.samples = []
		self.alias   = []
		self.yields  = {}
		self.nEvts   = 0.
	def addSample(self, sampleDef):
		self.samples.append(Sample(self.master, sampleDef))
	def analyze(self, triggers):
		for sample in self.samples:
			sample.analyze(triggers)
	def apply(self, trigger):
		## apply every trigger separately
		if trigger.triggerId in self.yields.keys(): return self.yields[trigger.triggerId]
		weight = 0.
		for sample in self.samples:
			weight += sample.apply(trigger)
		self.yields[trigger.triggerId] = weight
		return weight
	def applyAll(self, triggers):
		## apply all of them together in one iteration
		return sum([s.intersect(triggers) for s in self.samples])
	def applyAny(self, triggers):
		## apply any of them
		return sum([s.merge(triggers) for s in self.samples])
	def applySum(self, triggers):
		## apply all of them separately
		name = "_".join([t.name for t in triggers])+"_sum"
		if name in self.yields.keys(): return self.yields[name]
		weight = 0.
		for sample in self.samples:
			for trigger in triggers:
				weight += sample.apply(trigger)
		self.yields[name] = weight
		return weight
	def closeAll(self):
		for sample in self.samples:
			sample.close()
	def createBuffer(self):
		for sample in self.samples:
			sample.createBuffer(self.master.menu.triggers)
	def getNEvts(self):
		if self.nEvts != 0: return self.nEvts
		for sample in self.samples:
			self.nEvts += sample.getEntries()
		return self.nEvts
		



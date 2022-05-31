from trigger import *
import ROOT
import numpy


class Memory:
	def __init__(self):
		self.items = []
	def append(self, item):
		self.items.append(item)
	def dump(self, outdir):
		for item in self.items:
			item.dump(outdir)
	def find(self, typename, iteration=0):
		found = 0
		for attr in self.items:
			if type(attr)==typename and found==iteration: return attr
		return None
	def free(self, exceptions=[]):
		for attr in self.items:
			if attr in exceptions: continue
			self.items.remove(attr)
	def get(self, typename, freeTheRest=False):
		if self.has(typename): 
			keep = self.find(typename)
			self.free([keep.name])
			return keep
		return None
	def has(self, typename):
		for attr in self.items:
			if type(attr)==typename: return True
		return False
	

class MenuTable:
	def __init__(self, master, name = ""):
		self.master       = master
		self.name         = name
		self.rates        = {}
		self.yields       = {}
		self.raw          = {}
		self.correlations = {}
	def setCorrelations(self, trigger, ctrigger, totYield):
		if not  trigger in self.triggers: self.master.vb.error("MenuTable: Trigger not found!")
		if not ctrigger in self.triggers: self.master.vb.error("MenuTable: Trigger not found!")
		self.correlations[(trigger.triggerId, ctrigger.triggerId)] = totYield/self.yields[trigger.triggerId] if self.yields[trigger.triggerId]>0 else 0
	def setFullMenu(self, totYield, rawYield):
		self.setRates(None, totYield)
		self.setRates(None, rawYield, "menuraw")
	def setNEvts(self, nevts):
		self.nEvts = nevts
	def setRates(self, trigger, totYield, name=None):
		if trigger and not trigger in self.triggers: self.master.vb.error("MenuTable: Trigger not found!")
		name = name if name else trigger.triggerId if trigger else "menu"
		self.yields[name] = float(totYield)
		self.raw   [name] = float(totYield)/self.nEvts if self.nEvts>0 else 0
		self.rates [name] = self.master.menu.rateFactor*self.raw[name]
	def setTriggers(self, listOfTriggers):
		self.triggers = listOfTriggers
	def dump(self, outdir):
		## dumping it into a file using self.name
		maxlength = max([len(x) for x in self.yields.keys()])+5
                for k in range(len(self.yields)):
                  print k
                  if not self.master.menu.getTriggerById(k): continue
                  print self.yields[k]
                  #print self.master.menu.getTriggerById(k).name
                refs = {self.master.menu.getTriggerById(k).name: k for k in self.yields.keys() if self.master.menu.getTriggerById(k)}
                print refs
		names = refs.keys()[:]
		names.sort()
		fs = "%-"+str(maxlength)+"s:  %9.2f"
		fss = fs + "      %1.5f      %3.3f"
		print 
		print "MENU RESULT:"
		for tname in names:
			print fss%(tname, self.yields[refs[tname]], self.raw[refs[tname]], self.rates[refs[tname]])
		print "-"*55
		print fss%("total menu", self.yields["menu"   ], self.raw["menu"   ], self.rates["menu"   ])
		print fss%("total raw" , self.yields["menuraw"], self.raw["menuraw"], self.rates["menuraw"])
		print fs %("total"     , self.nEvts)
		print
		f = open(outdir+"/menu.csv","w")
		for tname in names:
			f.write(fss%(tname, self.yields[refs[tname]], self.raw[refs[tname]], self.rates[refs[tname]])+"\n")
		f.write(fss%("total menu", self.yields["menu"], self.raw["menu"], self.rates["menu"])+"\n")
		f.write(fss%("total raw" , self.yields["menu"], self.raw["menu"], self.rates["menu"])+"\n")
		f.write(fs %("total"     , self.nEvts)+"\n")
		f.close()

		xtrigs = list(set([(self.master.menu.getTriggerById(k[0]).name, k[0]) for k in self.correlations.keys()]))
		ytrigs = list(set([(self.master.menu.getTriggerById(k[1]).name, k[1]) for k in self.correlations.keys()]))
		xtrigs.sort()
		ytrigs.sort()
		h = ROOT.TH2F("correlations","",len(xtrigs),0,len(xtrigs),len(ytrigs),0,len(ytrigs))
		for ix,xtrig in enumerate(xtrigs):
			for iy,ytrig in enumerate(ytrigs):
				h.SetBinContent(ix+1,iy+1,1 if xtrig[1]==ytrig[1] else self.correlations[(xtrig[1],ytrig[1])])
		for ix,xtrig in enumerate(xtrigs):
			h.GetXaxis().SetBinLabel(ix+1, xtrig[0])
		for iy,ytrig in enumerate(ytrigs):
			h.GetYaxis().SetBinLabel(iy+1, ytrig[0])
		h.GetXaxis().LabelsOption("v")
		f = ROOT.TFile(outdir+"/correlations.root","recreate")
		f.cd()
		h.Write()
		f.Close()

		f = open(outdir+"/correlations_xtrigs.txt","w")
		for xtrig in xtrigs:
			f.write(xtrig[0]+"\n")
		f.close()

		f = open(outdir+"/correlations_ytrigs.txt","w")
		for ytrig in ytrigs:
			f.write(ytrig[0]+"\n")
		f.close()

		print "printing correlations"
		print self.correlations


class VariationTable:
	def __init__(self, master, name = ""):
		self.master    = master
		self.name      = name
		self.fitResult = {}
	def dump(self, outdir):
		f = ROOT.TFile(outdir+"/variations_"+self.name+".root","recreate")
		f.cd()
		for variation in self.indivRatesPerThresholds:
			variation.dump(f)
		for variation in self.totalRatesPerThresholds:
			variation.dump(f)
		f.Close()
	def setFitResult(self, fitResult):
		pass	
	def setIndividualRates(self, ratesPerThresholds):
		self.indivRatesPerThresholds = []
		for trigId,rvals in ratesPerThresholds.iteritems():
			for rname,variations in rvals.iteritems():
				self.indivRatesPerThresholds.append(Variation(self, self.master.menu.getTriggerById(trigId), "indiv", rname, [x[1] for x in variations], [x[2] for x in variations]))
	def setTotalRates(self, ratesPerThresholds):
		self.totalRatesPerThresholds = []
		for trigId,rvals in ratesPerThresholds.iteritems():
			for rname,variations in rvals.iteritems():
				self.totalRatesPerThresholds.append(Variation(self, self.master.menu.getTriggerById(trigId), "total", rname, [x[1] for x in variations], [x[2] for x in variations]))

## setFitResult
## self.primaryFitResult[trigger.triggerId][totalRate] = theVars[it].varValue



class Variation:
	def __init__(self, table, trigger, prefix, rname, thresholds, rates):
		self.table      = table
		self.master     = table.master
		self.trigger    = trigger
		self.name       = trigger.name+"_"+prefix+"_"+rname
		self.rname      = rname
		self.thresholds = thresholds
		self.rates      = rates
	def dump(self, rootfile):
		print 
		print "VARIATION "+self.table.name+" "+self.name
		fs = "%5.2f => %3.3f"
		for i in range(len(self.thresholds)):
			print fs%(self.thresholds[i], self.rates[i])

		factor = self.master.menu.rateFactor / self.master.samples.getNEvts()
		errors = [math.sqrt(factor**2*(r/factor)) for r in self.rates]
		up, dn = getPoissonErrors(self.rates, errors)
		syst   = self.master.getOpt("varError",0.2)

		onToOff = 0
		if self.rname in self.trigger.ranges.keys():
			#print self.trigger.ranges[self.rname][0]
			obj     = self.trigger.getLegByName(self.trigger.ranges[self.rname][0]).obj
			onToOff = float(obj.onToOff)

		gon   = ROOT.TGraphAsymmErrors()
		gon  .SetName("variation_"+self.table.name+"_"+self.name+"_on"  )
		goff  = ROOT.TGraphAsymmErrors()
		goff .SetName("variation_"+self.table.name+"_"+self.name+"_off" )
		gone  = ROOT.TGraph()
		gone .SetName("variation_"+self.table.name+"_"+self.name+"_one" )
		goffe = ROOT.TGraph()
		goffe.SetName("variation_"+self.table.name+"_"+self.name+"_offe")
		for i in range(len(self.thresholds)):
			edn = math.sqrt(dn[i]**2 + (self.rates[i]*syst)**2)
			eup = math.sqrt(up[i]**2 + (self.rates[i]*syst)**2)
			off = self.thresholds[i] + onToOff
			gon  .SetPoint     (i, self.thresholds[i], self.rates[i])
			gon  .SetPointError(i, 0, 0, edn, eup)
			goff .SetPoint     (i, off               , self.rates[i])
			goff .SetPointError(i, 0, 0, edn, eup)
			gone .SetPoint     (i, self.thresholds[i], self.rates[i]-edn)
			goffe.SetPoint     (i, off               , self.rates[i]-edn)
		for i in reversed(range(len(self.thresholds))):
			edn = math.sqrt(dn[i]**2 + (self.rates[i]*syst)**2)
			eup = math.sqrt(up[i]**2 + (self.rates[i]*syst)**2)
			off = self.thresholds[i] + onToOff
			gone .SetPoint(gone .GetN(), self.thresholds[i], self.rates[i]+eup)
			goffe.SetPoint(goffe.GetN(), off               , self.rates[i]+eup)
		edn = math.sqrt(dn[0]**2 + (self.rates[0]*syst)**2)
		eup = math.sqrt(up[0]**2 + (self.rates[0]*syst)**2)
		gone .SetPoint(gone .GetN(), self.thresholds[0]        , self.rates[i]-edn)
		goffe.SetPoint(goffe.GetN(), self.thresholds[0]+onToOff, self.rates[i]-edn)
	
		rootfile.cd()
		gon  .Write()
		goff .Write()
		gone .Write()
		goffe.Write()
		





class Menu:
	def __init__(self, master):
		self.master     = master
		self.memory     = Memory()
		self.objects    = []
		self.triggers   = []
		self.rateFactor = float(self.master.cfg.variable["nBunches"])*float(self.master.cfg.variable["revFreq"])/1000
	def addTrigObject(self, objDef):
                print "adding object"
		self.objects.append(TriggerObject(self.master, objDef))
	def addTrigger(self, trigDef):
		self.triggers.append(Trigger(self.master, trigDef))
	def getTriggerById(self, trigId):
		trigs = filter(lambda x: x.triggerId==trigId, self.triggers)
		if len(trigs)==1: return trigs[0]
		return None
	def computeRate(self):
		## for fixed thresholds per trigger, compute the total bandwidth
		self.memory.free()
		table = MenuTable(self.master, "fixedThresholds")
		table.setTriggers(self.triggers)
		table.setNEvts   (self.master.samples.getNEvts())
		self.master.samples.analyze(self.triggers)
		for trigger in self.triggers:
			table.setRates(trigger, self.master.samples.apply(trigger))
		table.setFullMenu(self.master.samples.applyAny(self.triggers), self.master.samples.applySum(self.triggers))
		for trigger in self.triggers:
			for ctrigger in self.triggers:
				if trigger == ctrigger: continue
				table.setCorrelations(trigger, ctrigger, self.master.samples.applyAll([trigger, ctrigger]))
		self.memory.append(table)
	def computeRatesPerThresholds(self, rangeDef={}):
		## for fixed set of thresholds per trigger, compute the individual and total bandwidths
		factor = self.rateFactor / self.master.samples.getNEvts()
		variations  = {}
		alltogether = []
		for trigger in self.triggers:
			variations[trigger.triggerId] = {}
			theDict = rangeDef[trigger.triggerId] if trigger.triggerId in rangeDef.keys() and len(rangeDef[trigger.triggerId].keys())>0 else trigger.ranges
			for rname,rdef in theDict.iteritems():
				variations[trigger.triggerId][rname] = []
				existing = [x[1] for x in self.ratesPerThresholds[trigger.triggerId][rname]] if hasattr(self, "ratesPerThresholds") and trigger.triggerId in self.ratesPerThresholds.keys() and rname in self.ratesPerThresholds[trigger.triggerId].keys() else []
				for value in rdef[2:]:
					if value in existing: continue
					#print rdef
					variations[trigger.triggerId][rname].append(trigger.makeVar(rname, rdef[0], rdef[1], value))
				alltogether += variations[trigger.triggerId][rname]
		#print alltogether
		self.master.samples.analyze(alltogether)
		if not hasattr(self, "ratesPerThresholds"     ): self.ratesPerThresholds      = {}
		if not hasattr(self, "totalRatesPerThresholds"): self.totalRatesPerThresholds = {}
		for trigger in self.triggers:
			if not trigger.triggerId in self.ratesPerThresholds     : self.ratesPerThresholds     [trigger.triggerId] = {}
			if not trigger.triggerId in self.totalRatesPerThresholds: self.totalRatesPerThresholds[trigger.triggerId] = {}
			for rname in variations[trigger.triggerId].keys():
				if not rname in self.ratesPerThresholds     [trigger.triggerId].keys(): self.ratesPerThresholds     [trigger.triggerId][rname] = []
				if not rname in self.totalRatesPerThresholds[trigger.triggerId].keys(): self.totalRatesPerThresholds[trigger.triggerId][rname] = []
				for var in variations[trigger.triggerId][rname]:
					self.ratesPerThresholds     [trigger.triggerId][rname].append((var, var.varValue, factor * self.master.samples.apply(var)))
					updatedSet = updateTriggers(self.triggers, var)
					self.totalRatesPerThresholds[trigger.triggerId][rname].append((var, var.varValue, factor * self.master.samples.applyAny(updatedSet)))
		for trigId in self.ratesPerThresholds.keys():
			for rname in self.ratesPerThresholds[trigId].keys():
				self.ratesPerThresholds     [trigId][rname].sort(key=lambda x: x[1])
				self.totalRatesPerThresholds[trigId][rname].sort(key=lambda x: x[1])
		print "printing varied rates"
		print self.ratesPerThresholds
		print self.totalRatesPerThresholds


	def computeThresholds(self):
		## for one fixed bandwidth, compute thresholds of all paths
		return
		table = self.memory.get("MenuTable", True)
		if not table:
			self.computeRate()
			table = self.memory.get("MenuTable")
		table.name = "fixedBandwidth"
		## in principle: run self.computeThresholdsPerRatesFull([float(self.master.cfg.variable["totalBandwidth"])]):
	def computeThresholdsPerRatesFull(self):
		## for a fixed set of bandwidths, compute the trigger thresholds with fixed fraction
		return
		varBins = self.master.cfg.variable["varBins"] ## leave this stuff here in order to add additional bins if you like
		if len(varBins)==0: return
		triggersToUse = filter(lambda x: "bwFraction" in x.opts.keys() and x.opts["bwFraction"], self.triggers)
		if len(triggersToUse)==0: return
		table = self.memory.get("MenuTable")
		fit = MenuFitter(self.master, "full", triggersToUse, varBins)
		additionals = fit.checkRatesPerThresholds(self.ratesPerThresholds if hasattr(self, "ratesPerThresholds") else {})
		self.computeRatesPerThresholds(additionals)
		fit.setNominalResult(table)
		self.thresholdsPerRatesFull = fit.secondaryProcedure(self.ratesPerThresholds)
		#print self.thresholdsPerRatesFull
	def computeThresholdsPerRatesIndiv(self):
		## for a fixed set of bandwidths, compute the trigger thresholds without fixed fraction
		varBins = self.master.cfg.variable["varBins"]
		if len(varBins)==0: return
		table = self.memory.get("MenuTable")
		fit = MenuFitter(self.master, "indiv", self.triggers, varBins)
		additionals = fit.checkRatesPerThresholds(self.totalRatesPerThresholds if hasattr(self, "totalRatesPerThresholds") else {})
		self.computeRatesPerThresholds(additionals)
		fit.setNominalResult(table)
		self.thresholdsPerRatesIndiv = fit.primaryProcedure(self.totalRatesPerThresholds, False)
		#print self.thresholdsPerRatesIndiv
	def dump(self, outdir):
		self.memory.dump(outdir)
	def fillVariationTable(self, name = ""):
		table = VariationTable(self.master, name)
		table.setIndividualRates(self.ratesPerThresholds     )
		table.setTotalRates     (self.totalRatesPerThresholds)
		self.memory.append(table)






## ==============================================================
## ==============================================================
## ==============================================================
## ==============================================================
## ==============================================================
## MENU FITTER DEVELOPMENT:


## Indiv
## * search for self.totalRatePerThresholds for every trigger
##   - if found (i.e. the user specified the thresholds), take it
##   - if not found, make it up yourself (from nominal, maybe some step size variable in cfg)
## * for every trigger
##   - check amount of available steps in both cases if it is enough for the interpolation (depends on varInterpol)
##   - if no, add the missing pieces in step 1
## * primary fit interation
##   - for every trigger
##     + do the interpolation according to varInterpol
##     + recompute the total effective rate (overlaps!)
##     + compute the difference to the target rate (current-target)
##     + check
##       - if the absolute value of the difference is within the precision -> done!
##       - if the difference > 0 (current too high): lower the factor of the trigger and reiterate
##       - if the difference < 0 (current too low ): increase the factor of the trigger and reiterate

## Full
## * check if bwFraction add up to 100% or not
## * search for self.ratesPerThresholds for every trigger
##   - if found (i.e. the user specified the thresholds), take it
##   - if not found, make it up yourself (from nominal, maybe some step size variable in cfg)
## * for every trigger: 
##   - check amount of available steps in both cases if it is enough for the interpolation (depends on varInterpol)
##   - if no, add the missing pieces in step 1
## * primary fit iterations
##   - for every trigger
##     + do interpolation using self.ratesPerThresholds according to varInterpol for a given desiredRate of that trigger
##   - recompute the total effective rate
##   - compute the difference to the target rate (current-target)
##   - check
##     + if the absolute value of the difference is within the precision -> done!
##     + if the difference changes sign and it is at least iteration 2 -> go to step 2!
##     + if the difference > 0 (current too high): lower all factors of the triggers simultaneously and reiterate
##     + if the difference < 0 (current too low ): increase all factors of the triggers simultaneously and reiterate
## * secondary fit iteration
##   - for every trigger
##     + from the previously recorded thresholds and total rates, interpolate according to varInterpol for every trigger the threshold
##   - recompute the total effective rate
##     + add these values to the sample for the next iteration
##   - compute the difference to the target rate (current-target)
##   - check
##     + if the absolute value of the difference is within the precision -> done!
##     + if the difference > 0 (current too high): lower all factors of the triggers simultaneously and reiterate
##     + if the difference < 0 (current too low ): increase all factors of the triggers simultaneously and reiterate


class MenuFitter:
	def __init__(self, master, name, triggers, varBins):
		self.name          = name
		self.master        = master
		self.triggers      = triggers
		self.varBins       = varBins
		self.method        = self.master.cfg.variable["varInterpol"]
		self.varLeg        = int(self.master.cfg.variable["varLeg"])-1
		self.varCut        = "cut"+str(self.master.cfg.variable["varCut"])
		self.varCutM1      = "cut"+str(self.master.cfg.variable["varCut"]-1)
		self.varIterations = int(self.master.cfg.variable["varIterations"])
		self.precision     = float(self.master.cfg.variable["varPrecision"])
		self.useNominalBwF = self.master.cfg.variable["useNominalBwF"]
		self.factor        = self.master.menu.rateFactor / self.master.samples.getNEvts()

	## ---- public functions ----------
	def checkRatesPerThresholds(self, ratesPerThresholdRaw):
		## search for total or individual rates per trigger threshold
		## also check if there are enough variations available to do an interpolation later
		## here: check from CFG arguments if the variations will suffice or not, otherwise add them as additionals!
		theGoodName = None
		require = {}
		for trigId,rvar in ratesPerThresholdRaw.iteritems():
			trigger = self.master.menu.getTriggerById(trigId)
			trigLeg = trigger.getLegNameByIdx(self.varLeg)
			require[trigId] = {}
			isOk=False
			for rname,rvalues in rvar.iteritems():
				if not rvalues[0][0].varLeg==trigLeg: continue
				if not rvalues[0][0].varCut==self.varCut: continue
				theGoodName = rname
				if len(rvalues)==1:
					nominal = trigger.getCutValue(trigLeg, self.varCutM1)
					if rvalues[0][1]==nominal: newvalues = [nominal*0.5, nominal*1.5]
					else                     : newvalues = [nominal    , nominal*1.5]
					require[trigId][rname] = [rvalues[0][0].varLeg, rvalues[0][0].varCut]+newvalues
					isOk=True
				if len(rvalues)==2: 
					theValues = [x[1] for x in rvalues]
					maxvalue = max(theValues)
					require[trigId][rname] = [rvalues[0][0].varLeg, rvalues[0][0].varCut]+[maxvalue*1.5]
					isOk=True
				if len(rvalues)>2:
					isOk=True
			if not isOk:
				nominal = trigger.getCutValue(trigLeg, self.varCutM1)
				val1 = [n*0.5 for n in nominal] if type(nominal)==list else nominal*0.5
				val2 = [n*1.5 for n in nominal] if type(nominal)==list else nominal*1.5
				require[trigId][theGoodName if theGoodName else "required1"] = [trigLeg, self.varCut, val1, nominal, val2]
		#print "REQUIRE!"
		#print require
		return require

	def primaryProcedure(self, ratesPerThreshold, useBwF):
		## running primary fit only
		self.prepare(ratesPerThreshold)
		self.primaryFit(useBwF)
		return self.primaryFitResult
	def secondaryProcedure(self, ratesPerThreshold):
		## running primary and secondary fit
		self.prepare(ratesPerThreshold)
		self.primaryFit(True)
		self.secondaryFit()
		theResult = {}
		for totalRate in self.varBins:
			for trigger in self.triggers:
				if not trigger.triggerId in theResult.keys(): theResult[trigger.triggerId] = {}
				if not totalRate in theResult[trigger.triggerId].keys(): theResult[trigger.triggerId][totalRate] = 0
				if trigger.triggerId in self.secondaryFitResult.keys():
					if totalRate in self.secondaryFitResult[trigger.triggerId].keys():
						theResult[trigger.triggerId][totalRate] = self.secondaryFitResult[trigger.triggerId][totalRate]
				if theResult[trigger.triggerId][totalRate] == 0 and trigger.triggerId in self.primaryFitResult.keys():
					if totalRate in self.primaryFitResult[trigger.triggerId].keys():
						theResult[trigger.triggerId][totalRate] = self.primaryFitResult[trigger.triggerId][totalRate]
		return theResult
	def setNominalResult(self, menutable):
		## set nominal result to extract nominal BwF 
		pass


	## ---- private functions ---------
	def getNominalBwF(self, trigger):
		## get nominal BwF from nominal menu table
		pass
	def interpolate(self, collection, rate):
		## interpolate the rate to extract an estimate for the threshold
		## collection = [(threshold1, rate1), (threshold2, rate2), ...]
		thresholds = [x[0][0] if type(x[0])==list else x[0] for x in collection]
		rates      = [x[1]                                  for x in collection]
		## exponential fit
		if self.method == "exponential":
			result = numpy.polyfit(rates, numpy.log(thresholds), 1, w=numpy.sqrt(thresholds))
			return float(math.exp(result[1])*exp(result[0]*rate))
		## linear fit
		#print "i am here!"
		lower = findIntersectionIdx(rates, rate)
		#print "my lower bin:",lower
		if lower<0: ## outside of boundary (lower edge)
			lower = 0
		if lower>=len(thresholds): ## outside of boundary (upper edge)
			lower = len(thresholds)-2
		#print "using:",lower
		y1 = thresholds[lower]; y2 = thresholds[lower+1]
		x1 = rates     [lower]; x2 = rates     [lower+1]
		#print "corresponds to [",x1,x2,"], [",y1,y2,"]"
		result = numpy.polyfit([x1,x2], [y1,y2], 1, w=numpy.sqrt([y1, y2]))
		return float(result[0]*rate + result[1])
	def interpolationFactor(difference, desiredValue, precision):
		## problem: the precision acts upon the TOTAL rate, while this factor
		## extracted here acts upon the INDIVIDUAL trigger
		if difference>precision*10: return desiredValue/(precision*10)
		return desiredValue/precision
	def prepare(self, ratesPerThresholdRaw):
		## here make a newcollection that has the "range" step integrated out (only one variation per trigger!)
		#print "preperare:",ratesPerThresholdRaw
		self.ratesPerThreshold = {}
		for trig,rvar in ratesPerThresholdRaw.iteritems():
			for rname,rvalues in rvar.iteritems():
				if not rvalues[0][0].varCut==self.varCut: continue
				self.ratesPerThreshold[trig] = [(x[1],x[2]) for x in rvalues]
				break
		#print "I AM HERE!"
		#print self.ratesPerThreshold
	def primaryFit(self, useBwF, returnAtSignChange=False):
		## this is the primary fit as done for most variation cases
		## the fit here is done on the basis of the ratesPerThreshold
		#print "primary FIT"
		#print self.ratesPerThreshold
		self.primaryFitResult  = {trigger.triggerId: {} for trigger in self.triggers}
		self.primaryFitTests   = {trigger.triggerId: {} for trigger in self.triggers}
		self.primarySignChange = {trigger.triggerId: {} for trigger in self.triggers}
		if len(self.triggers)==0: return
		bwf = [float(trigger.opts["bwFraction"]) for trigger in self.triggers] if useBwF and not self.useNominalBwF else \
		      [self.getNominalBwF(trigger)       for trigger in self.triggers] if useBwF else \
		      [1.0                               for trigger in self.triggers]
		for totalRate in self.varBins:
			factors = [1.0   for i in range(len(self.triggers))]
			diffs   = [99999 for i in range(len(self.triggers))]
			need    = [True  for i in range(len(self.triggers))]
			for it, trigger in enumerate(self.triggers):
				self.primaryFitTests[trigger.triggerId][totalRate] = []
			iteration = -1
			while any(need):
				iteration += 1
				if iteration==self.varIterations: break
				#print "primary iteration",iteration
				theVars     = {}
				runTriggers = []
				for it, trigger in enumerate(self.triggers):
					if not need[it]: continue
					#print "interpolating trigger",trigger.triggerId
					#print totalRate,bwf[it],factors[it],
					thisThreshold = self.interpolate(self.ratesPerThreshold[trigger.triggerId], totalRate*bwf[it]*factors[it]) 
					#print thisThreshold
					#print self.name+"_"+str(totalRate)+"_"+str(iteration), "all", self.varCut, thisThreshold
					theVars[it]   = trigger.makeVar(self.name+"_"+str(totalRate)+"_"+str(iteration), "any", self.varCut, thisThreshold)
					#print theVars[it].varValue
					runTriggers.append(theVars[it])
				if len(runTriggers) == 0: break
				self.master.samples.analyze(runTriggers)
				for it, trigger in enumerate(self.triggers):
					if not need[it]: continue
					updatedSet  = updateTriggers(self.triggers, theVars[it])
					thisRate    = self.factor * self.master.samples.applyAny(updatedSet)
					self.primaryFitTests[trigger.triggerId][totalRate].append((theVars[it].varValue, thisRate))
					previous    = diffs[it]
					diffs[it]   = thisRate - totalRate
					#print "this rate is",thisRate,totalRate,diffs[it],self.precision
					if abs(diffs[it]) < self.precision:
						self.primaryFitResult[trigger.triggerId][totalRate] = theVars[it].varValue
						need[it] = False
					elif returnAtSignChange and diffs[it]*previous<0:
						self.primarySignChange[trigger.triggerId][totalRate] = True
						need[it] = False
					else:
						factors[it] *= totalRate/thisRate
#						factors[it] = getInterpolFactor(diffs[it], totalRate, precision)
					#print need[it]
					#print
	def secondaryFit(self): 
		self.secondaryFitResult = {trigger.triggerId: {} for trigger in self.triggers}
		if len(self.triggers)==0: return
		toRun = {}
		for trigId,rvals in signChanges.iteritems():
			self.thresholdsPerRatesFull[trigId] = {}
			for rate,sign in rvals.iteritems():
				if not sign: continue
				if not rate in toRun.keys(): toRun[rate] = []
				toRun[rate].append(self.menu.getTriggerById(trigId))
		for totalRate in toRun.keys():
			factors = [1.0   for i in range(len(toRun[totalRate]))]
			diffs   = [99999 for i in range(len(toRun[totalRate]))]
			need    = [True  for i in range(len(toRun[totalRate]))]
			iteration = -1
			while any(need):
				iteration += 1
				if iteration==self.varIterations: break
				theVars     = {}
				runTriggers = []
				for it, trigger in enumerate(toRun[totalRate]):
					if not need[it]: continue
					thisThreshold = self.interpolate(self.primaryFitTests[trigger.triggerId][totalRate], totalRate*factors[it])
					theVars[it]   = trigger.makeVar(self.name+"fit2_"+str(totalRate)+"_"+str(iteration), "all", self.varCut, thisThreshold)
					runTriggers.append(theVars[it])
				if len(runTriggers) == 0: break
				self.master.samples.analyze(runTriggers)
				for it, trigger in enumerate(self.triggers):
					if not need[it]: continue
					updatedSet  = updateTriggers(self.triggers, theVars[it])
					previous    = diffs[it]
					diffs[it]   = thisRate - totalRate
					if abs(diffs[it]) < self.precision:
						self.secondaryFitResult[trigger.triggerId][totalRate] = theVars[it].varValue
						need[it] = False
					else:
						factors[it] *= totalRate/thisRate



			


##	def computeThresholds(self):
##		## for a fixed bandwidth, compute thresholds of all paths
##		table = self.memory.get("MenuTable", True)
##		if not table:
##			self.computeRate()
##			table = self.memory.get("MenuTable")
##		table.name = "fixedBandwidth"
##		## in principle: run self.computeThresholdsPerRatesFull([float(self.master.cfg.variable["totalBandwidth"])]):
##
##
#		desiredRate = float(self.master.cfg.variable["totalBandwidth"])
#		require = {}
#		for trigger in self.triggers:
#			desiredBw = float(self.variable["bwFraction"])*desiredRate
#			require[trigger.triggerId] = {"var1": []}




## constraints:
## * thresholds are given
## * objects are given
## * bandwidth is given
## * trigger name is not "menu" or "total"
## * revolution frequency
## * number of bunches
		



# How does it work "under the hood"?

## TurnOns

### Choosing the reference object
- For each event select the *highest pT* particle/jet within given eta range
- If isolation is given, throw out event whose particle/jet does not fulfill iso requirement
- Which values for the isolation are used?
  - See in [Google Sheet](https://docs.google.com/spreadsheets/d/14CVVhA6ITSTmv0x0Z2BRJ7cLgMKabi6TWsDXbyffGBg/edit#gid=462890739)
- Step by step process:
  1. Apply eta cut
  2. Select obj with highest pt
  3. Check if selected object fulfils isolation, otherwise throw out


### Choosing the reference object
- One test object per reference object
- Step by step process:
  1. Apply all selections
	  - Eta cuts
	  - Min pt cuts
	  - Region
	  - Isolation
	  - Quality
	2. Calculate dR of reference object to remaining test objects
  3. Choose highest test object in pT among the ones within the specified dR cone

#### Isolation
- Choose that cut so that 98.2% or 94.6% (depending on object) pass the selection

#### Eta and Type / Region
- Efficiency as function of eta: apply cut on test object region on the region branch whereas for the turnons cut on eta and not on region to have same cuts in numerator and denominator
- Eta min/max from config applied to both reference and test objects

#### Meaning of config table columns
- L1 PT Min: PT cut on test object
- DR Cut: Matching between test and reference
- Type/Region: 1,2,3,4 corresponding to "barrel", "endcap", "overlap", "forward" to select test object from a specific path finder, correspondign to branch in L1 Ntuple (basically another cut)
  - For EG no region, but flag from HGCal that says whether object is barrel or endcap
- IsolationBB,EC (Barrel, Endcap) mostly for EG objects, apply different isolations in different regions

#### Different plots
- Iso plots to derive IsoBB/EC numbers, look cumulative percentage
- Plot dxy for displaced muons as "final output" as well

- What are the definitions of "barrel", "endcap", "overlap", "forward" for the different objects?
  - See Twiki by Jaana 
  - Are they the same for all the objects? --> No

## Scalings
- Points used for scaling [here](https://github.com/FHead/Phase2-L1MenuTools/blob/ff1d21889d9b87497a0cca8d8e0ec52377e12f52/ObjectPerformances/TurnOnScaling/source/MakeScalingPlot.cpp#L107) but are updated when things change
- Include as many points as possible *but* ignore outliers
- There are cases in which scaling is *quadratic* (very rarely) --> see last argument
- Is 95% with respect to the plateau or wrt the absolute value?
		- Case by case: some enforce 100 some not, for String model always enforce 100%, for fits, find palteau

### Methods
- String model with certain Tension (only used for turnon curves that saturate at 100%)
- Fit of Tanh
- Fit of custom function in l 92 (used in L1 TDR)
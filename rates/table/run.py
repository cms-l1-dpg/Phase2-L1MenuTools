import os, sys, ROOT

##ROOT.gSystem.Load("libFWCoreFWLite.so")
##ROOT.gSystem.Load("libDataFormatsFWLite.so")
##ROOT.gSystem.Load("libDataFormatsPatCandidates.so")

import optparse
from lib import master
from lib import functions

parser = optparse.OptionParser(usage="%prog cfg [options]")
parser.add_option("-o", dest="outdir" , type="string"      , default=None , help="Custom output directory")
parser.add_option("-v", dest="verbose", type="int"         , default=2    , help="Set verbosity level")
parser.add_option("-M", dest="tiers"  , action="append"    , default=[]   , help="Run a module by name")
parser.add_option("-X", dest="exclude", action="append"    , default=[]   , help="Exclude a module by name")
parser.add_option("-S", "--buffer"    , dest="runBuffer"    , action="store_true", default=False, help="Run the skim module")
parser.add_option("-T", "--thresholds", dest="runThresholds", action="store_true", default=False, help="Run the fixed thresholds module")
parser.add_option("-B", "--bandwidth" , dest="runBandwidth" , action="store_true", default=False, help="Run the fixed bandwidth module")
parser.add_option("-V", "--variations", dest="runVariations", action="store_true", default=False, help="Run the variation of the thresholds module")
parser.add_option("-f", "--force"     , dest="force"        , action="store_true", default=False, help="Rerun triggers even if they already have been processed")

#(opts, args) = parser.parse_args()
opts_no_defaults = optparse.Values()
__, args = parser.parse_args(values=opts_no_defaults)
opts = optparse.Values(parser.get_default_values().__dict__)
opts._update_careful(opts_no_defaults.__dict__)

if len(args)<1:
	print "Please provide a config file!"
	sys.exit()

MM = master.Master(args, opts, opts_no_defaults)
MM.sequence()
MM.dump()




import os, sys, glob, fnmatch, re, optparse
from array import array
from ROOT import *
gROOT.SetBatch(True)

def parseOptions():
    global observalbesTags, modelTags, runAllSteps

    usage = ('usage: %prog [options]\n'
             + '%prog -h for help')
    parser = optparse.OptionParser(usage)

    # input options
    parser.add_option('-c', '--cfg', dest='CFG', type='string',default='', help='cfg file')
    parser.add_option('-r', '--rates', dest='RATES', type='string',default='', help='csv file with rates')

    global opt, args
    (opt, args) = parser.parse_args()


def printNice():

  paths = []
  with open(opt.CFG,'r') as cfgfile:
    for line in cfgfile:
      if ("Set:" in line): paths.append(line)
      if (not line.startswith("trigger")): continue
      paths.append(line.split('::')[1].rstrip().lstrip())
  

  with open(opt.RATES,'r') as ratefile:

    for path in paths:

      if ("Set:" in path): print path; continue
  
      for line in ratefile:
        if (path==line.split(':')[0].rstrip().lstrip()):
          pathrate = line.replace(':',' :').split(':')[1].split()[2]
          print path+"   "+str(round(float(pathrate),1))

      ratefile.seek(0)

      

if __name__ == "__main__":

    global opt, args
    parseOptions()

    printNice()


#[dsperka@lxplus008 L1MM]$ ls out/2018-07-18_v7p3_madrid/thresholds/menu.csv 
#out/2018-07-18_v7p3_madrid/thresholds/menu.csv
#[dsperka@lxplus008 L1MM]$ ls cfg/v7p3_madrid
#cfg/v7p3_madrid

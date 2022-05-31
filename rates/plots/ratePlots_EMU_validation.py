import sys, os
import argparse

from ROOT import *
from array import *

import time
timestr = time.strftime("%Y%m%d")

parser = argparse.ArgumentParser()
parser.add_argument("--outdir", default="/eos/user/j/jheikkil/www/", help="Choose the output directory. Default='%(default)s'")
parser.add_argument("--indir", default="testOutput", help="Choose the input directory. Default='%(default)s'")
parser.add_argument("--online", dest='runOnline', action='store_true')
parser.add_argument("--tag", default="", help="Choose tag for the legend. Default='%(default)s'")


args = parser.parse_args()

runOnline = args.runOnline

outDir = args.outdir
inDir = args.indir
tag = args.tag

if not os.path.isdir(inDir):
    print("The input directory doesn't exist!")
    exit()

outPath = outDir+"/"+inDir+"_"+timestr
if not os.path.isdir(outPath):
    print("The out directory doesn't exist, creating it!")
    os.mkdir(outPath)
    command='cp '+outDir+'/index.php '+outPath
    print command
    os.system(command)

sys.path.append(inDir)
from rates import *

gStyle.SetOptStat(0)
TAxis().SetMoreLogLabels(1)

#runOnline = False

#off = {}
#offrate = {}
#onl = {}
#onlrate = {}

g_off = {}
g_onl = {}

h = {}


plots = {

#0: ['standaloneMuonBarrel', 'standaloneMuonOverlap', 'standaloneMuonEndcap']
#0: ['gmtMuonBarrel', 'gmtMuonOverlap', 'gmtMuonEndcap']
   #  0 : ['standaloneElectron', 'tkElectron', 'tkIsoElectron', 'tkPhotonIso'],
#  1 : ['trackerJet', 'puppiPhase1Jet', 'seededConePuppiJet', 'caloJet'], 
  #9 : ['trackerJet', 'puppiPhase1Jet', 'seededConePuppiJet'],
#  2 : ['puppiPhase1JetExt', 'seededConePuppiJetExt', 'caloJetExt'], 
  #10 : ['puppiPhase1JetExt', 'seededConePuppiJetExt'],
#  3 : ['puppiPhase1HT', 'trackerHT', 'caloHT'],  
  #4 : ['puppiPhase1HT', 'trackerHT'],  
  #5 : ['puppiPhase1MHT', 'trackerMHT'],
  #6 : ['puppiMET', 'trackerMET'], #'trackerMET_FBE'],
#6 : ['trackerMET'],
#  7 : ['standaloneMuon', 'tkMuon', 'tkMuonStub'], 
  #8 : ['gmtMuon', 'gmtTkMuon'],
  #11 : ['CaloTau', 'NNPuppiTauLoose'], #, 'NNPuppiTau2vtxLoose'],
12: ['CaloTau','CaloTauBarrel','CaloTauEndcap']
}

labels = {

'standaloneElectron' : 'calorimeter-only electron',
'tkElectron' : 'track-matched electron',
'tkIsoElectron' : 'track-matched + charged iso. electron',
'tkPhotonIso' : 'charged iso. photon',
'standaloneMuon' : 'standalone muon',
'tkMuon' : 'track-matched muon (tkMuon)',
'tkMuonStub' : 'track-matched muon (tkMuonStub)',
'trackerJet' : 'tracker jet',
'caloJet' : 'calo jet',
'puppiPhase1Jet' : 'histogr. puppi jet',
'seededConePuppiJet' : 'seeded cone puppi jet',
'caloJetExt' : 'calo jet (|#eta|<5)',
'puppiPhase1JetExt' : 'histogr. puppi jet (|#eta|<5)',
'seededConePuppiJetExt' : 'seeded cone puppi jet (|#eta|<5)',
'puppiPhase1HT' : 'histogr. puppi jets H_{T}',
'trackerHT' : 'tracker H_{T}',
'caloHT' : 'calo H_{T}',
'puppiPhase1MHT' : 'histogr. puppi jets #slash{H}_{T}',
'trackerMHT' : 'tracker #slash{H}_{T}',
'puppiMET' : 'puppi #slash{E}_{T}',
'trackerMET' : 'tracker #slash{E}_{T}',
'gmtMuon' : 'GMT standalone muon',
'gmtTkMuon' : 'GMT track-matched muon',
'CaloTau' : 'calo tau',
'CaloTauEndcap' : 'calo tau, endcap',
'CaloTauBarrel' : 'calo tau, barrel',
'NNPuppiTauLoose' : 'nnPuppi tau (loose WP)',
'NNPuppiTau2vtxLoose' : 'nnPuppi tau (loose WP, 2vtx)',

}


for key,list_plot in plots.iteritems():
  name=''
  color=0
  label=''
  for obj in list_plot:

#    print obj
    name+=obj+'_'

    color+=1

    if "JetExt" in obj and obj==list_plot[0]:
        color+=1
    if (color==3): color+=1
    if (color==5): color+=1
    if (color==10): color+=1

    if (obj==list_plot[0]):
      maxVal = 10e5
      minVal = 0
      if runOnline==False and (obj in off): 
          maxVal = max(off[obj])
          minVal = min(off[obj])
      elif runOnline==True and (obj in onl):  
          maxVal = max(onl[obj])
          minVal = min(onl[obj])  
      if "MHT" in obj:
          maxVal = 340
      h = TH1F("","",1,minVal,maxVal*1.05)
      #h = TH1F("","",1,10.0,max(onl[obj])*1.05)
      h.SetBinContent(1,0.0001)
      if "MHT" in obj:
          h.SetMaximum(10000)
      else:
          h.SetMaximum(500000.0)
      h.SetMinimum(1.0);
      c1 = TCanvas("c1","",800,800)
      c1.SetLeftMargin(0.11) #0.15 David
      c1.SetLogy()
      c1.SetGridx()
      c1.SetGridy()
      c1.SetTickx()
      c1.SetTicky()
      if runOnline == True:
          h.GetXaxis().SetTitle("Online p_{T} [GeV]")
      else:
          h.GetXaxis().SetTitle("Offline p_{T} [GeV]")
      h.GetYaxis().SetTitle("Rate [kHz]")
      h.Draw("hist")

      leg = TLegend(0.35,0.65,0.85,0.85)
      if tag:
          leg.SetHeader(tag,"C");

    if (obj==list_plot[len(list_plot)-1]):
      leg.Draw("same")

    if (obj in off):
        g_off[obj]= TGraph(len(off[obj])-1,off[obj],offrate[obj])

        g_off[obj].SetMarkerColor(color)
        g_off[obj].SetLineColor(color)

        g_off[obj].SetMarkerStyle(20)
        g_off[obj].SetMarkerSize(1.2)

    elif runOnline == False:
	continue

    if (obj in onl):
        g_onl[obj]= TGraph(len(onl[obj])-1,onl[obj],onlrate[obj])

        g_onl[obj].SetMarkerColor(color)
        g_onl[obj].SetLineColor(color)

        g_onl[obj].SetMarkerStyle(20)
        g_onl[obj].SetMarkerSize(1.2)


    elif runOnline == True:
        
	continue


    if runOnline == True:
        g_onl[obj].Draw("lpsame")
    else:
        g_off[obj].Draw("lpsame")


    if obj in labels: 
        label = labels[obj]
    else:
        label = obj

    if runOnline == True:
      leg.AddEntry(g_onl[obj],label,"lp")
    else:
      leg.AddEntry(g_off[obj],label,"lp")
  

    tex = TLatex()
    tex.SetTextSize(0.03)
    tex.DrawLatexNDC(0.11,0.91,"#scale[1.5]{CMS} Phase-2 Simulation")
    tex.Draw("same")

    tex2 = TLatex()
    tex2.SetTextSize(0.035)
    tex2.SetTextAlign(31)
    toDisplay = TString("#scale[0.8]{14 TeV, 7.5x10^{34}cm^{-2}s^{-1}, 200 PU}")
    tex2.DrawLatexNDC(0.90,0.91,toDisplay.Data())
    tex2.Draw("same")

  if runOnline == True:
      c1.SaveAs(outPath+"/"+name+"_rate_vs_threshold_test_onl.pdf")
      c1.SaveAs(outPath+"/"+name+"_rate_vs_threshold_test_onl.png")
  else:
      c1.SaveAs(outPath+"/"+name+"_rate_vs_threshold_test_off.pdf")
      c1.SaveAs(outPath+"/"+name+"_rate_vs_threshold_test_off.png")









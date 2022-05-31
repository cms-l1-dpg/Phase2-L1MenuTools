import sys, os
import argparse

from ROOT import *
from array import *

gStyle.SetOptStat(0)
TAxis().SetMoreLogLabels(1)

parser = argparse.ArgumentParser()
parser.add_argument("--outdir", default="testOutput", help="Choose the output directory. Default='%(default)s'")

args = parser.parse_args()	

outDir = args.outdir
if not os.path.isdir(outDir):
    os.mkdir(outDir)
pathToRates = outDir+"/rates.py"

rates_file = open(pathToRates, 'w')


rates_file.write("from array import *\n\n")

rates_file.write("off = {}\n")
rates_file.write("offrate = {}\n")
rates_file.write("onl = {}\n")
rates_file.write("onlrate = {}\n\n")


f = TFile("/eos/cms/store/cmst3/group/l1tr/phase2Menu/EmuDev/minbias_merged_nTuplesEmu_v22_2.root","READ")
 
t = f.Get("l1PhaseIITree/L1PhaseIITree")

ntot = t.GetEntriesFast()

off = {}
offrate = {}
onl = {}
onlrate = {}
g_off = {}
g_onl = {}

h = {}

#isolation WPs

iso_EG_barrel = 0.13
iso_EG_endcap = 0.28

iso_gamma_barrel = 0.24
iso_gamma_endcap = 0.205

#tk EG hwQual
tkEG_hwQual = 3

#scalings


### Muons EMU

#function :: GMTTkMuonOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-0.903751)/1.039495 if abs(Eta)<0.83 else (Et>(offline-0.894300)/1.044889 if abs(Eta)<1.24 else (Et>(offline-0.796396)/1.040808))
#function :: GMTMuonQualOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-2.827822)/0.994950 if abs(Eta)<0.83 else (Et>(offline-0.228463)/1.280758 if abs(Eta)<1.24 else (Et>(offline-7.261232)/0.895232))

def gmtMuonOfflineEtCutBarrel(offline) : return (offline-2.827822)/0.994950
def gmtMuonOfflineEtCutOverlap(offline) : return (offline-0.228463)/1.280758
def gmtMuonOfflineEtCutEndcap(offline) : return (offline-7.261232)/0.895232

def gmtTkMuonOfflineEtCutBarrel(offline) : return (offline-0.903751)/1.039495
def gmtTkMuonOfflineEtCutOverlap(offline) : return (offline-0.894300)/1.044889
def gmtTkMuonOfflineEtCutEndcap(offline) : return (offline-0.796396)/1.040808


##New scalings by Yi in December 2021

#function :: Phase1PuppiJetOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-12.381481)/1.331251 if abs(Eta)<1.5 else (Et>(offline-21.649515)/1.372602 if abs(Eta)<2.4 else (Et>(offline-35.609357)/1.493540))
def Phase1PuppiJetOfflineEtCutBarrel(offline) : return (offline-12.381481)/1.331251
def Phase1PuppiJetOfflineEtCutEndcap(offline) : return (offline-21.649515)/1.372602
def Phase1PuppiJetOfflineEtCutForward(offline) : return (offline-35.609357)/1.493540

#function :: Phase1PuppiMHTOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+9.724987)/1.037459
#function :: Phase1PuppiHT090OfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-46.674588)/1.113875
def Phase1PuppiHTOfflineEtCut(offline) : return (offline-46.674588)/1.113875 
def Phase1PuppiMHTOfflineEtCut(offline) : return (offline+9.724987)/1.037459

#function :: PuppiMET090OfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-62.120627)/1.382451
def PuppiMETOfflineEtCut(offline) : return (offline-62.120627)/1.382451

#function :: CaloJetOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+15.342718)/1.568946 if abs(Eta)<1.5 else (Et>(offline+2.230990)/1.561868 if abs(Eta)<2.4 else (Et>(offline-107.928530)/1.181014))
def CaloJetOfflineEtCutBarrel(offline) : return (offline+15.342718)/1.568946
def CaloJetOfflineEtCutEndcap(offline) : return (offline+2.230990)/1.561868
def CaloJetOfflineEtCutForward(offline) : return (offline-107.928530)/1.181014

#THESE ARE WRONG!!!
#function :: CaloHT090OfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+51.666047)/1.027086
#function :: CaloHTOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+212.262823)/1.038718
def CaloHTOfflineEtCut(offline) : return (offline+51.666047)/1.027086

#function :: SeededConePuppiJetOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-14.869526)/1.291966 if abs(Eta)<1.5 else (Et>(offline-24.500087)/1.449829 if abs(Eta)<2.4 else (Et>(offline-53.029951)/1.140808))
def SeededConePuppiJetOfflineEtCutBarrel(offline) : return (offline-14.869526)/1.291966
def SeededConePuppiJetOfflineEtCutEndcap(offline) : return (offline-24.500087)/1.449829
def SeededConePuppiJetOfflineEtCutForward(offline) : return (offline-53.029951)/1.140808

#function :: TrackerJetOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+52.278067)/10.213742 if abs(Eta)<1.5 else (Et>(offline+93.926334)/14.412352)
def TrackerJetOfflineEtCutBarrel(offline) : return (offline+52.278067)/10.213742
def TrackerJetOfflineEtCutEndcap(offline) : return (offline+93.926334)/14.412352

#function :: TrackerMHTOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+72.185871)/3.431230
#function :: TrackerHT090OfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+3.448948)/3.780727
#function :: TrackerMET090OfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+4.460475)/7.139687
def TrackerHTOfflineEtCut(offline) : return (offline+3.448948)/3.780727
def TrackerMHTOfflineEtCut(offline) : return (offline+72.185871)/3.431230
def TrackerMETOfflineEtCut(offline) : return (offline+4.460475)/7.139687


#function :: EGElectronOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-2.870789)/1.165597 if abs(Eta)<1.5 else (Et>(offline-2.720773)/1.228424)
#function :: TkElectronOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-0.617835)/1.182946 if abs(Eta)<1.5 else (Et>(offline-0.336402)/1.275834)
#function :: TkIsoElectronOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-0.189054)/1.211045 if abs(Eta)<1.5 else (Et>(offline-0.822056)/1.239274)
#function :: TkIsoPhotonOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-2.330926)/1.093568 if abs(Eta)<1.5 else (Et>(offline-4.565565)/1.077261)
def EGElectronOfflineEtCutBarrel(offline) : return (offline-2.870789)/1.165597
def EGElectronOfflineEtCutEndcap(offline) : return (offline-2.720773)/1.228424

def TkElectronOfflineEtCutBarrel(offline) : return (offline-0.617835)/1.182946
def TkElectronOfflineEtCutEndcap(offline) : return (offline-0.336402)/1.275834

def TkIsoElectronOfflineEtCutBarrel(offline) : return (offline-0.189054)/1.211045
def TkIsoElectronOfflineEtCutEndcap(offline) : return (offline-0.822056)/1.239274

def TkIsoPhotonOfflineEtCutBarrel(offline) : return (offline-2.330926)/1.093568
def TkIsoPhotonOfflineEtCutEndcap(offline) : return (offline-4.565565)/1.077261


#TAUS
#function :: CaloTau050OfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+12.754931)/1.247281 if abs(Eta)<1.5 else (Et>(offline+18.755528)/1.373550)
#function :: NNPuppiTau050OfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+3.439358)/1.141044 if abs(Eta)<1.5 else (Et>(offline+0.756022)/1.146415)
#function :: CaloTau090OfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+6.720396)/1.510317 if abs(Eta)<1.5 else (Et>(offline+5.499322)/1.898208)
#function :: NNPuppiTau090OfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-3.778738)/1.642246 if abs(Eta)<1.5 else (Et>(offline-14.808886)/1.716542)

def CaloTauOfflineEtCutBarrel(offline) : return (offline+6.720396)/1.510317
def CaloTauOfflineEtCutEndcap(offline) : return	(offline+5.499322)/1.898208

def NNTauLooseOfflineEtCutBarrel(offline) : return (offline-3.778738)/1.642246
def NNTauLooseOfflineEtCutEndcap(offline) : return (offline-14.808886)/1.716542

#def NNTau2vtxLooseOfflineEtCutBarrel(offline) : return (offline-3.430488)/1.644274
#def NNTau2vtxLooseOfflineEtCutEndcap(offline) : return (offline-14.530580)/1.728148


cutrange = {


'tkMuon':[0.0,78.0,3.0],
'tkMuonBarrel':[0.0,60.0,3.0],
'tkMuonOverlap':[0.0,60.0,3.0],
'tkMuonEndcap':[0.0,60.0,3.0],

'standaloneMuonBarrel':[0.0,60.0,3.0],
'standaloneMuonOverlap':[0.0,60.0,3.0],
'standaloneMuonEndcap':[0.0,60.0,3.0],
'standaloneMuon':[0.0,78.0,3.0],

'gmtTkMuon':[0.0,78.0,3.0],
'gmtTkMuonBarrel':[0.0,60.0,3.0],
'gmtTkMuonOverlap':[0.0,60.0,3.0],
'gmtTkMuonEndcap':[0.0,60.0,3.0],

'gmtMuon':[0.0,78.0,3.0],
'gmtMuonBarrel':[0.0,60.0,3.0],
'gmtMuonOverlap':[0.0,60.0,3.0],
'gmtMuonEndcap':[0.0,60.0,3.0],

'tkElectron':[10.0,100.0,3.0],
'tkIsoElectron':[10.0,100.0,3.0],
'standaloneElectron':[10.0,100.0,3.0],
'standaloneElectronExt':[10.0,100.0,3.0],

'tkElectronBarrel':[10.0,70.0,3.0],
'tkIsoElectronBarrel':[10.0,70.0,3.0],
'standaloneElectronBarrel':[10.0,70.0,4.0],

'tkElectronEndcap':[10.0,70.0,3.0],
'tkIsoElectronEndcap':[10.0,70.0,3.0],
'standaloneElectronEndcap':[10.0,70.0,3.0],

'tkPhotonIso':[10.0,100.0,3.0],
'standalonePhoton':[10.0,70.0,3.0],

'tkPhotonIsoBarrel':[10.0,70.0,3.0],
'standalonePhotonBarrel':[10.0,70.0,3.0],

'tkPhotonIsoEndcap':[10.0,70.0,3.0],
'standalonePhotonEndcap':[10.0,70.0,3.0],

'puppiPhase1HT':[50.0,1000.0,25.0],
'trackerHT':[50.0,1000.0,25.0],
'caloHT':[50.0,1000.0,25.0],

'puppiPhase1MHT':[50.0,1000.0,25.0],
'trackerMHT':[50.0,1000.0,25.0],

'puppiMET':[50.0,500.0,25.0],
'trackerMET':[50.0,500.0,25.0],
#'trackerMET':[0.0,500.0,5.0],


'seededConePuppiJet':[40.0,440.0,20.0],
'seededConePuppiJetExt':[40.0,440.0,20.0],
'puppiPhase1Jet':[40.0,440.0,20.0],
'puppiPhase1JetExt':[40.0,440.0,20.0],
'trackerJet':[40.0,440.0,20.0],
'caloJet':[40.0,440.0,20.0],
'caloJetExt':[40.0,440.0,20.0],


'NNPuppiTauLoose':[10.0,160.0,5.0],
'NNPuppiTau2vtxLoose':[10.0,160.0,5.0],
'CaloTau':[10.0,160.0,5.0],
'CaloTauBarrel':[10.0,160.0,5.0],
'CaloTauEndcap':[10.0,160.0,5.0],


}

list_calc = [
  'gmtTkMuon',
  'gmtMuon',
#   'gmtMuonEndcap',
#   'gmtMuonBarrel',
#   'gmtMuonOverlap',
  'tkElectron',
  'tkIsoElectron',
  'standaloneElectron',
  'tkPhotonIso',
  'seededConePuppiJet',
  'seededConePuppiJetExt',
  'puppiPhase1Jet',
  'puppiPhase1JetExt',
  'trackerJet',
  'caloJet',
  'caloJetExt',
  'puppiPhase1HT',
  'trackerHT',
  'caloHT',
  'puppiPhase1MHT',
  'trackerMHT',
  'puppiMET',
  'trackerMET',
  'NNPuppiTauLoose',
#   'NNPuppiTau2vtxLoose',
  'CaloTau',
'CaloTauBarrel',
'CaloTauEndcap',

]




for obj in list_calc:

  off[obj] = array('d',[])
  offrate[obj] = array('d',[])
  onl[obj] = array('d',[])
  onlrate[obj] = array('d',[])
  
  x = cutrange[obj][0]
  while (x<cutrange[obj][1]):


########################################
#######################################


#-------------muons--------------
    if (obj=='gmtTkMuon'):
      offlinescalingcut = "( ( abs(gmtTkMuonEta[])<0.83 && gmtTkMuonPt[]>("+str(gmtTkMuonOfflineEtCutBarrel(x))+")) || (abs(gmtTkMuonEta[])>0.83 && abs(gmtTkMuonEta[])<1.24 && gmtTkMuonPt[]>("+str(gmtTkMuonOfflineEtCutOverlap(x))+")) || (abs(gmtTkMuonEta[])>1.24 &&  abs(gmtTkMuonEta[])<2.4 && gmtTkMuonPt[]>("+str(gmtTkMuonOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+"  && abs(gmtTkMuonEta[])<2.4)>0"
      onlinecut  = "Sum$( gmtTkMuonPt[]>"+str(x)+" && gmtTkMuonBx[]==0 && abs(gmtTkMuonEta[])<2.4)>0"


    if (obj=='gmtMuon'):
      offlinescalingcut = "( ( abs(gmtMuonEta[])<0.83 && gmtMuonPt[]>("+str(gmtMuonOfflineEtCutBarrel(x))+")) || (abs(gmtMuonEta[])>0.83 && abs(gmtMuonEta[])<1.24 && gmtMuonQual[]>=12 && gmtMuonPt[]>("+str(gmtMuonOfflineEtCutOverlap(x))+")) || (abs(gmtMuonEta[])>1.24 &&  abs(gmtMuonEta[])<2.4 && gmtMuonPt[]>("+str(gmtMuonOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(gmtMuonEta[])<2.4)>0"
      onlinecut  = "Sum$( gmtMuonPt[]>"+str(x)+" && gmtMuonBx[]==0  && abs(gmtMuonEta[])<2.4 && ( ( abs(gmtMuonEta[])<0.83 ) || (abs(gmtMuonEta[])>0.83 && abs(gmtMuonEta[])<1.24 && gmtMuonQual[]>=12 ) || (abs(gmtMuonEta[])>1.24 && abs(gmtMuonEta[])<2.4) ) )>0"

    if (obj=='gmtMuonOverlap'):
      offlinescalingcut = "( ( abs(gmtMuonEta[])<0.83 && gmtMuonPt[]>("+str(gmtMuonOfflineEtCutBarrel(x))+")) || (abs(gmtMuonEta[])>0.83 && abs(gmtMuonEta[])<1.24 && gmtMuonQual[]>=12 && gmtMuonPt[]>("+str(gmtMuonOfflineEtCutOverlap(x))+")) || (abs(gmtMuonEta[])>1.24 &&  abs(gmtMuonEta[])<2.4 && gmtMuonPt[]>("+str(gmtMuonOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(gmtMuonEta[])>0.83 && abs(gmtMuonEta[])<1.24)>0"
      onlinecut = "Sum$( gmtMuonPt[]>"+str(x)+" && gmtMuonBx[]==0 && gmtMuonQual[]>=12 && abs(gmtMuonEta[])>0.83 && abs(gmtMuonEta[])<1.24 )>0"

    if (obj=='gmtMuonBarrel'):
      offlinescalingcut = "( ( abs(gmtMuonEta[])<0.83 && gmtMuonPt[]>("+str(gmtMuonOfflineEtCutBarrel(x))+")) || (abs(gmtMuonEta[])>0.83 && gmtMuonQual[]>=12 && abs(gmtMuonEta[])<1.24 && gmtMuonPt[]>("+str(gmtMuonOfflineEtCutOverlap(x))+")) || (abs(gmtMuonEta[])>1.24 &&  abs(gmtMuonEta[])<2.4 && gmtMuonPt[]>("+str(gmtMuonOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(gmtMuonEta[])<0.83 )>0"
      onlinecut = "Sum$( gmtMuonPt[]>"+str(x)+" && gmtMuonBx[]==0  && abs(gmtMuonEta[])<0.83)>0"

    if (obj=='gmtMuonEndcap'):
      offlinescalingcut = "( ( abs(gmtMuonEta[])<0.83 && gmtMuonPt[]>("+str(gmtMuonOfflineEtCutBarrel(x))+")) || (abs(gmtMuonEta[])>0.83 && gmtMuonQual[]>=12 && abs(gmtMuonEta[])<1.24 && gmtMuonPt[]>("+str(gmtMuonOfflineEtCutOverlap(x))+")) || (abs(gmtMuonEta[])>1.24 &&  abs(gmtMuonEta[])<2.4 && gmtMuonPt[]>("+str(gmtMuonOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(gmtMuonEta[])>1.24 && abs(gmtMuonEta[])<2.4)>0"
      onlinecut = "Sum$( gmtMuonPt[]>"+str(x)+" && gmtMuonBx[]==0  && abs(gmtMuonEta[])>1.24 &&  abs(gmtMuonEta[])<2.4 )>0"


#---------------eg-----------------


    if (obj=='tkElectron'):
      offlinescalingcut = "( (abs(tkElectronEta[])<1.479 && tkElectronEt[]>("+str(TkElectronOfflineEtCutBarrel(x))+")) || (abs(tkElectronEta[])>1.479 && tkElectronEt[]>("+str(TkElectronOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && tkElectronBx[]==0 && tkElectronPassesLooseTrackID[] && abs(tkElectronEta[])<2.4)>0"
      onlinecut  = "Sum$( tkElectronEt[]>"+str(x)+" && tkElectronBx[]==0 && tkElectronPassesLooseTrackID[] && abs(tkElectronEta[])<2.4)>0"

    if (obj=='tkIsoElectron'):
      offlinescalingcut = "( (abs(tkElectronEta[])<1.479 && tkElectronEt[]>("+str(TkIsoElectronOfflineEtCutBarrel(x))+") && tkElectronTrkIso[]<("+str(iso_EG_barrel)+") ) || (abs(tkElectronEta[])>1.479 && tkElectronEt[]>("+str(TkIsoElectronOfflineEtCutEndcap(x))+") && tkElectronTrkIso[]<("+str(iso_EG_endcap)+") && tkElectronHwQual[]=="+str(tkEG_hwQual)+" ) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && tkElectronBx[]==0 &&  abs(tkElectronEta[])<2.4)>0"
      onlinecut  = "Sum$( ((abs(tkElectronEta[])<1.479 && tkElectronEt[]>("+str(x)+") && tkElectronTrkIso[]<("+str(iso_EG_barrel)+")) || (abs(tkElectronEta[])>1.479 && tkElectronEt[]>("+str(x)+") && tkElectronTrkIso[]<("+str(iso_EG_endcap)+") && tkElectronHwQual[]=="+str(tkEG_hwQual)+")) && tkElectronBx[]==0 && abs(tkElectronEta[])<2.4)>0"

    if (obj=='standaloneElectron'):
      offlinescalingcut = "( (abs(EGEta[])<1.479 && EGEt[]>("+str(EGElectronOfflineEtCutBarrel(x))+")) || (abs(EGEta[])>1.479 && EGEt[]>("+str(EGElectronOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && EGBx[]==0 && EGPassesLooseTrackID[] && abs(EGEta[])<2.4)>0"
      onlinecut  = "Sum$( EGEt[]>"+str(x)+" && EGBx[]==0 && EGPassesLooseTrackID[] && abs(EGEta[])<2.4)>0"


    if (obj=='tkPhotonIso'):
      offlinescalingcut = "( (abs(tkPhotonEta[])<1.479 && tkPhotonEt[]>("+str(TkIsoPhotonOfflineEtCutBarrel(x))+")) || (abs(tkPhotonEta[])>1.479 && tkPhotonEt[]>("+str(TkIsoPhotonOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" &&  ( (abs(tkPhotonEta[])<1.479 && tkPhotonTrkIso[]<"+str(iso_gamma_barrel)+"  ) || (abs(tkPhotonEta[])>1.479 && tkPhotonTrkIso[]<"+str(iso_gamma_endcap)+") ) && tkPhotonBx[]==0 && tkPhotonPassesLooseTrackID[] && abs(tkPhotonEta[])<2.4)>0"
      onlinecut  = "Sum$( tkPhotonEt[]>"+str(x)+" && ( (abs(tkPhotonEta[])<1.479 && tkPhotonTrkIso[]<"+str(iso_gamma_barrel)+" ) || (abs(tkPhotonEta[])>1.479 && tkPhotonTrkIso[]<"+str(iso_gamma_endcap)+") ) && tkPhotonBx[]==0 && tkPhotonPassesLooseTrackID[] && abs(tkPhotonEta[])<2.4)>0"



#---------------taus----------------TO BE FILLED

    if (obj=='NNPuppiTauLoose'):
      offlinescalingcut = "( (abs(nnTauEta[])<1.5 && nnTauEt[]>("+str(NNTauLooseOfflineEtCutBarrel(x))+")) || (abs(nnTauEta[])>1.5 && nnTauEt[]>("+str(NNTauLooseOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && nnTauPassLooseNN[]>0 && abs(nnTauEta[])<2.4)>0"
      onlinecut  = "Sum$( nnTauEt[]>"+str(x)+"  && nnTauPassLooseNN[]>0 && abs(nnTauEta[])<2.4)>0"

    if (obj=='NNPuppiTau2vtxLoose'):
      offlinescalingcut = "( (abs(nnTau2vtxEta[])<1.5 && nnTau2vtxEt[]>("+str(NNTau2vtxLooseOfflineEtCutBarrel(x))+")) || (abs(nnTau2vtxEta[])>1.5 && nnTau2vtxEt[]>("+str(NNTau2vtxLooseOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && nnTau2vtxPassLooseNN[]>0 && abs(nnTau2vtxEta[])<2.4)>0"
      onlinecut  = "Sum$( nnTau2vtxEt[]>"+str(x)+"  && nnTau2vtxPassLooseNN[]>0 && abs(nnTau2vtxEta[])<2.4)>0"

    if (obj=='CaloTau'):
      offlinescalingcut = "( (abs(caloTauEta[])<1.5 && caloTauEt[]>("+str(CaloTauOfflineEtCutBarrel(x))+")) || (abs(caloTauEta[])>1.5 && caloTauEt[]>("+str(CaloTauOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(caloTauEta[])<2.4)>0"
      onlinecut  = "Sum$( caloTauEt[]>"+str(x)+"  && abs(caloTauEta[])<2.4)>0"

    if (obj=='CaloTauBarrel'):
      offlinescalingcut = "( (abs(caloTauEta[])<1.5 && caloTauEt[]>("+str(CaloTauOfflineEtCutBarrel(x))+")) || (abs(caloTauEta[])>1.5 && caloTauEt[]>("+str(CaloTauOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(caloTauEta[])<1.5)>0"
      onlinecut  = "Sum$( caloTauEt[]>"+str(x)+"  && abs(caloTauEta[])<1.5)>0"

    if (obj=='CaloTauEndcap'):
      offlinescalingcut = "( (abs(caloTauEta[])<1.5 && caloTauEt[]>("+str(CaloTauOfflineEtCutBarrel(x))+")) || (abs(caloTauEta[])>1.5 && caloTauEt[]>("+str(CaloTauOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(caloTauEta[])>1.5 && abs(caloTauEta[])<2.4)>0"
      onlinecut  = "Sum$( caloTauEt[]>"+str(x)+" && abs(caloTauEta[])>1.5  && abs(caloTauEta[])<2.4)>0"


#----------------jets---------------

    if (obj=='seededConePuppiJet'):
      offlinescalingcut = "( (abs(seededConePuppiJetEta[])<1.5 && seededConePuppiJetEt[]>("+str(SeededConePuppiJetOfflineEtCutBarrel(x))+")) || (abs(seededConePuppiJetEta[])>1.5 && abs(seededConePuppiJetEta[])<2.4 && seededConePuppiJetEt[]>("+str(SeededConePuppiJetOfflineEtCutEndcap(x))+")) || (abs(seededConePuppiJetEta[])>2.4 && seededConePuppiJetEt[]>("+str(SeededConePuppiJetOfflineEtCutForward(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(seededConePuppiJetEta[])<2.4)>0"
      onlinecut  = "Sum$( seededConePuppiJetEt[]>"+str(x)+" && abs(seededConePuppiJetEta[])<2.4)>0"

    if (obj=='seededConePuppiJetExt'):
      offlinescalingcut = "( (abs(seededConePuppiJetEta[])<1.5 && seededConePuppiJetEt[]>("+str(SeededConePuppiJetOfflineEtCutBarrel(x))+")) || (abs(seededConePuppiJetEta[])>1.5 && abs(seededConePuppiJetEta[])<2.4 && seededConePuppiJetEt[]>("+str(SeededConePuppiJetOfflineEtCutEndcap(x))+")) || (abs(seededConePuppiJetEta[])>2.4 && seededConePuppiJetEt[]>("+str(SeededConePuppiJetOfflineEtCutForward(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(seededConePuppiJetEta[])<5)>0"
      onlinecut  = "Sum$( seededConePuppiJetEt[]>"+str(x)+" && abs(seededConePuppiJetEta[])<5)>0"

    if (obj=='puppiPhase1Jet'):
      offlinescalingcut = "( (abs(phase1PuppiJetEta[])<1.5 && phase1PuppiJetEt[]>("+str(Phase1PuppiJetOfflineEtCutBarrel(x))+")) || (abs(phase1PuppiJetEta[])>1.5 && abs(phase1PuppiJetEta[])<2.4 && phase1PuppiJetEt[]>("+str(Phase1PuppiJetOfflineEtCutEndcap(x))+")) || (abs(phase1PuppiJetEta[])>2.4 && phase1PuppiJetEt[]>("+str(Phase1PuppiJetOfflineEtCutForward(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(phase1PuppiJetEta[])<2.4)>0"
      onlinecut  = "Sum$( phase1PuppiJetEt[]>"+str(x)+" && abs(phase1PuppiJetEta[])<2.4)>0"

    if (obj=='puppiPhase1JetExt'):
      offlinescalingcut = "( (abs(phase1PuppiJetEta[])<1.5 && phase1PuppiJetEt[]>("+str(Phase1PuppiJetOfflineEtCutBarrel(x))+")) || (abs(phase1PuppiJetEta[])>1.5 && abs(phase1PuppiJetEta[])<2.4 && phase1PuppiJetEt[]>("+str(Phase1PuppiJetOfflineEtCutEndcap(x))+")) || (abs(phase1PuppiJetEta[])>2.4 && phase1PuppiJetEt[]>("+str(Phase1PuppiJetOfflineEtCutForward(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(phase1PuppiJetEta[])<5)>0"
      onlinecut  = "Sum$( phase1PuppiJetEt[]>"+str(x)+" && abs(phase1PuppiJetEta[])<5)>0"

    if (obj=='trackerJet'):
      offlinescalingcut = "( (abs(trackerJetEta[])<1.5 && trackerJetPt[]>("+str(TrackerJetOfflineEtCutBarrel(x))+")) || (abs(trackerJetEta[])>1.5 && trackerJetPt[]>("+str(TrackerJetOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(trackerJetEta[])<2.4)>0"
      onlinecut  = "Sum$( trackerJetPt[]>"+str(x)+" && abs(trackerJetEta[])<2.4)>0"

    if (obj=='caloJet'):
      offlinescalingcut = "( (abs(caloJetEta[])<1.5 && caloJetEt[]>("+str(CaloJetOfflineEtCutBarrel(x))+")) || (abs(caloJetEta[])>1.5 && abs(caloJetEta[])<2.4 && caloJetEt[]>("+str(CaloJetOfflineEtCutEndcap(x))+")) || (abs(caloJetEta[])>2.4 && caloJetEt[]>("+str(CaloJetOfflineEtCutForward(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(caloJetEta[])<2.4)>0"
      onlinecut  = "Sum$( caloJetEt[]>"+str(x)+" && abs(caloJetEta[])<2.4)>0"

    if (obj=='caloJetExt'):
      offlinescalingcut = "( (abs(caloJetEta[])<1.5 && caloJetEt[]>("+str(CaloJetOfflineEtCutBarrel(x))+")) || (abs(caloJetEta[])>1.5 && abs(caloJetEta[])<2.4 && caloJetEt[]>("+str(CaloJetOfflineEtCutEndcap(x))+")) || (abs(caloJetEta[])>2.4 && caloJetEt[]>("+str(CaloJetOfflineEtCutForward(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(caloJetEta[])<5)>0"
      onlinecut  = "Sum$( caloJetEt[]>"+str(x)+" && abs(caloJetEta[])<5)>0"




#--------------------HT--------------------

    #if (obj=='seededConePuppiHT'):
      #Not available
    #  offlinescalingcut = "(seededConePuppiHT[0]>("+str(seededConePuppiHTOfflineEtCut(x))+"))"
    #  offlinecut = offlinescalingcut
    #  onlinecut  = " seededConePuppiHT[0]>"+str(x)

    if (obj=='puppiPhase1HT'):
      offlinescalingcut = "(phase1PuppiHT[0]>("+str(Phase1PuppiHTOfflineEtCut(x))+"))"
      offlinecut = offlinescalingcut
      onlinecut  = " phase1PuppiHT[0]>"+str(x)

    if (obj=='trackerHT'):
      offlinescalingcut = "(trackerHT[0]>("+str(TrackerHTOfflineEtCut(x))+"))"
      offlinecut = offlinescalingcut
      onlinecut  = " trackerHT[0]>"+str(x)

    if (obj=='caloHT'): 
      offlinescalingcut = "(caloJetHT[0]>("+str(CaloHTOfflineEtCut(x))+"))"
      offlinecut = offlinescalingcut
      onlinecut  = " caloJetHT[0]>"+str(x)

#--------------------MHT-----------------

    #if (obj=='seededConePuppiMHT'):
      #Not available
    #  offlinescalingcut = "(seededConePuppiMHT[0]>("+str(seededConePuppiMHTOfflineEtCut(x))+"))"
    #  offlinecut = offlinescalingcut
    #  onlinecut  = " seededConePuppiMHT[0]>"+str(x)

    if (obj=='puppiPhase1MHT'):
      offlinescalingcut = "(phase1PuppiMHTEt[0]>("+str(Phase1PuppiMHTOfflineEtCut(x))+"))"
      offlinecut = offlinescalingcut
      onlinecut  = " phase1PuppiMHTEt[0]>"+str(x)

    if (obj=='trackerMHT'):
      offlinescalingcut = "(trackerMHT[0]>("+str(TrackerMHTOfflineEtCut(x))+"))"
      offlinecut = offlinescalingcut
      onlinecut  = " trackerMHT[0]>"+str(x)

    #if (obj=='caloMHT'):
      # Not available
    #  offlinescalingcut = "(caloJetMHT[0]>("+str(CaloMHTOfflineEtCut(x))+"))"
    #  offlinecut = offlinescalingcut
    #  onlinecut  = " caloJetMHT[0]>"+str(x)


#--------------------MET--------------

    if (obj=='puppiMET'):
      offlinescalingcut = "(puppiMETEt>("+str(PuppiMETOfflineEtCut(x))+"))"
      offlinecut = offlinescalingcut
      onlinecut  = " puppiMETEt>"+str(x)

    if (obj=='trackerMET'):
      offlinescalingcut = "(trackerMET>("+str(TrackerMETOfflineEtCut(x))+"))"
      offlinecut = offlinescalingcut
      onlinecut  = " trackerMET>"+str(x)


  

    npass = t.GetEntries(offlinecut)
    off[obj].append(x)
    offrate[obj].append(round(float(npass)/float(ntot)*31038.,1))
   
    #print x,round(float(npass)/float(ntot)*31038.,1)

    npass = t.GetEntries(onlinecut)
    onl[obj].append(x)
    onlrate[obj].append(round(float(npass)/float(ntot)*31038.,1))
   
 
    x+=cutrange[obj][2]

  

  print ""
  print ""
  print obj
  print "off['"+obj+"'] = ",off[obj]
  print "offrate['"+obj+"'] = ",offrate[obj]
  print "onl['"+obj+"'] = ",onl[obj]
  print "onlrate['"+obj+"'] = ",onlrate[obj]

  rates_file.write("off['"+obj+"'] = "+str(off[obj]))
  rates_file.write("\n")
  rates_file.write("offrate['"+obj+"'] = "+str(offrate[obj]))
  rates_file.write("\n")
  rates_file.write("onl['"+obj+"'] = "+str(onl[obj]))
  rates_file.write("\n")
  rates_file.write("onlrate['"+obj+"'] = "+str(onlrate[obj]))
  rates_file.write("\n")
  rates_file.write("\n") 
  rates_file.flush()
  os.fsync(rates_file.fileno())
   
rates_file.close()
f.Close()






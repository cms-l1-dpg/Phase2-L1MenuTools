from ROOT import *
from array import *

gStyle.SetOptStat(0)
TAxis().SetMoreLogLabels(1)

#f = TFile("/eos/cms/store/group/cmst3/group/l1tr/cepeda/triggerntuples10X/NeutrinoGun_E_10GeV/NeutrinoGun_E_10GeV_V7_5_2_MERGED.root","READ")
#f = TFile("/eos/cms/store/cmst3/user/botta/NeutrinoGun_E_10GeV_V8_2_MERGED.root","READ")  ### Maria reproduce the right one for photons: /eos/cms/store/group/cmst3/group/l1tr/cepeda/triggerntuples10X/NeutrinoGun_E_10GeV/NuGun_V8_5.root 
#f = TFile("/eos/cms/store/cmst3/user/botta/NeutrinoGun_E_10GeV_V8_2_106X_MERGED.root","READ")   
#f = TFile("/eos/cms/store/cmst3/user/botta/NeutrinoGun_E_10GeV_V9_MERGED.root","READ")   
#f = TFile("/eos/cms/store/cmst3/user/botta/NeutrinoGun_E_10GeV_V10p3_MERGED.root","READ") 
#f = TFile("/eos/cms/store/cmst3/user/botta/NeutrinoGun_E_10GeV_V10p4_MERGED.root","READ") 
f = TFile("/eos/cms/store/cmst3/user/botta/NeutrinoGun_E_10GeV_V10p7_MERGED.root","READ") 


  
t = f.Get("l1PhaseIITree/L1PhaseIITree")

ntot = t.GetEntriesFast()

off = {}
offrate = {}
onl = {}
onlrate = {}
g_off = {}
g_onl = {}


h = {}



###### SCALINGS



## HT

#function :: PuppiHTOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-4.63573)/1.0087
#function :: TTbarPuppiHTOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline+12.84)/1.03535
#function :: PFPhase1HTOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-7.00327)/1.01015
#function :: TTbarPFPhase1HTOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline+5.29584)/1.03089
#function :: TrackerHTOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline+2.47118)/1.95961
#function :: TTbarTrackerHTOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline+46.31)/2.20021
#function :: CaloHTOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline+73.8289)/0.923594
#function :: TTbarCaloHTOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline+90.1537)/0.957146
#function :: PuppiHT090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-47.9233)/1.08345
#function :: PFPhase1HT090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-53.7549)/1.08834
#function :: TrackerHT090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-35.1578)/2.66569
#function :: CaloHT090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline+1.30634)/0.997298
#function :: TTbarPuppiHT090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-42.6661)/1.0753
#function :: TTbarPFPhase1HT090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-53.7965)/1.07331
#function :: TTbarTrackerHT090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-15.5172)/2.76786
#function :: TTbarCaloHT090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline+9.15257)/1.06462

#function :: HadronicTTbarPuppiHTOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline+6.18248)/1.03343
#function :: HadronicTTbarPFPhase1HTOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-2.19174)/1.03043
#function :: HadronicTTbarTrackerHTOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline+38.7746)/2.13034
#function :: HadronicTTbarCaloHTOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline+88.5201)/0.93691

#function :: HadronicTTbarPuppiHT090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-51.8588)/1.06447
#function :: HadronicTTbarPFPhase1HT090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-64.5616)/1.06039
#function :: HadronicTTbarTrackerHT090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-9.34255)/2.64851
#function :: HadronicTTbarCaloHT090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline+9.37574)/1.02455


#choose ttbar 50%
#def PuppiHTOfflineEtCut(offline): return (offline+12.84)/1.03535
#def PFPhase1HTOfflineEtCut(offline): return (offline+5.29584)/1.03089
#def TrackerHTOfflineEtCut(offline): return (offline+46.31)/2.20021
#def CaloHTOfflineEtCut(offline): return (offline+90.1537)/0.957146

#choose ttbar 90% --test on February 17 by Jaana
#def PuppiHTOfflineEtCut(offline): return (offline-42.6661)/1.0753
#def PFPhase1HTOfflineEtCut(offline): return (offline-53.7965)/1.07331
#def TrackerHTOfflineEtCut(offline): return (offline-15.5172)/2.76786
#def CaloHTOfflineEtCut(offline): return (offline+9.15257)/1.06462

#choose ttbar hadronic 50%
#def PuppiHTOfflineEtCut(offline): return (offline+12.84)/1.03535
#def PFPhase1HTOfflineEtCut(offline): return (offline+5.29584)/1.03089
#def TrackerHTOfflineEtCut(offline): return (offline+46.31)/2.20021
#def CaloHTOfflineEtCut(offline): return (offline+90.1537)/0.957146

#choose ttbar hadronic 90% #these were used for the L1 TDR table
def PuppiHTOfflineEtCut(offline): return (offline-51.8588)/1.06447
def PFPhase1HTOfflineEtCut(offline): return (offline-64.5616)/1.06039
def TrackerHTOfflineEtCut(offline): return (offline-9.34255)/2.64851
def CaloHTOfflineEtCut(offline): return (offline+9.37574)/1.02455

#Update from Jaana on Feb17 for scalings, using the ttbar 90 instead now

## MET

## tracker MET high values for scaling
#function :: PuppiMETOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-19.1432)/1.07251
#function :: TrackerMETOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-97.9892)/1.55151
#function :: TTbarPuppiMETOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline+6.79552)/1.23709
#function :: TTbarTrackerMETOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-11.7906)/1.97972
#function :: PuppiMET090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-87.0446)/1.1511
#function :: TrackerMET090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-154.856)/3.71756
#function :: TTbarPuppiMET090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-51.5627)/1.36698
#function :: TTbarTrackerMET090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-186.324)/2.28745

## tracker MET low values for scaling
#function :: PuppiMETOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-19.1432)/1.07251
#function :: TrackerMETOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline+0.600811)/3.11669
#function :: TTbarPuppiMETOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline+6.79552)/1.23709
#function :: TTbarTrackerMETOfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline+104.886)/3.73323
#function :: PuppiMET090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-87.0446)/1.1511
#function :: TrackerMET090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-221.122)/2.74021
#function :: TTbarPuppiMET090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline-51.5627)/1.36698
#function :: TTbarTrackerMET090OfflineEtCut :: args:=(offline,Et); lambda:=Et>(offline+14.2411)/5.21706


#choose VBFHinv 50%
#def PuppiMETOfflineEtCut(offline): return (offline-19.1432)/1.07251
#def TrackerMETOfflineEtCut(offline): return (offline+0.600811)/3.11669

#choose VBFHinv 90%
#def PuppiMETOfflineEtCut(offline): return (offline-87.0446)/1.1511
#def TrackerMETOfflineEtCut(offline): return (offline-221.122)/2.74021

#choose ttbar 50%
#def PuppiMETOfflineEtCut(offline): return (offline+6.79552)/1.23709
#def TrackerMETOfflineEtCut(offline): return (offline+104.886)/3.73323

#choose ttbar 90%
def PuppiMETOfflineEtCut(offline): return (offline-51.5627)/1.36698
def TrackerMETOfflineEtCut(offline): return (offline+14.2411)/5.21706






## Taus V6HH

#function :: PFTauOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+1.02859)/1.04655 if abs(Eta)<1.5 else Et>(offline+0.873734)/1.12528
#function :: PFIsoTauOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+0.715016)/1.0354 if abs(Eta)<1.5 else Et>(offline-0.619152)/1.07797
#function :: NNTauTightOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+1.22271)/1.02652 if abs(Eta)<1.5 else Et>(offline+4.45279)/1.12063
#function :: NNTauLooseOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-0.0282565)/1.00757 if abs(Eta)<1.5 else Et>(offline+1.7323)/1.07902
#function :: TkEGTauOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+0.200375)/1.01773 if abs(Eta)<1.5 else Et>(offline+1.68334)/1.22362
#function :: CaloTauOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+6.604)/1.14519 if abs(Eta)<1.5 else Et>(offline+4.19867)/1.06606
#function :: PFTau090OfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+11.5292)/2.08813 if abs(Eta)<1.5 else Et>(offline-2.45302)/1.85321
#function :: PFIsoTau090OfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+4.72956)/1.80821 if abs(Eta)<1.5 else Et>(offline-11.0478)/1.55742
#function :: NNTauTight090OfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+21.3166)/1.84293 if abs(Eta)<1.5 else Et>(offline+1.47361)/1.39273
#function :: NNTauLoose090OfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+9.16702)/1.69784 if abs(Eta)<1.5 else Et>(offline-3.12516)/1.36535
#function :: TkEGTau090OfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+91.7613)/5.12908 if abs(Eta)<1.5 else Et>(offline+13.6892)/3.89439
#function :: CaloTau090OfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline+0.937512)/1.38032 if abs(Eta)<1.5 else Et>(offline-1.92178)/1.26272


#choose HH 50%
#def PFTauOfflineEtCutBarrel(offline): return (offline+1.02859)/1.04655
#def PFTauOfflineEtCutEndcap(offline): return (offline+0.873734)/1.12528

#def PFIsoTauOfflineEtCutBarrel(offline): return (offline+0.715016)/1.0354
#def PFIsoTauOfflineEtCutEndcap(offline): return (offline-0.619152)/1.07797

#def NNTauTightOfflineEtCutBarrel(offline): return (offline+1.22271)/1.02652
#def NNTauTightOfflineEtCutEndcap(offline): return (offline+4.45279)/1.12063

#def NNTauLooseOfflineEtCutBarrel(offline): return (offline-0.0282565)/1.00757
#def NNTauLooseOfflineEtCutEndcap(offline): return (offline+1.7323)/1.07902

#def TkEGTauOfflineEtCutBarrel(offline): return (offline+0.200375)/1.01773
#def TkEGTauOfflineEtCutEndcap(offline): return (offline+1.68334)/1.22362

#def CaloTauOfflineEtCutBarrel(offline): return (offline+6.604)/1.14519
#def CaloTauOfflineEtCutEndcap(offline): return (offline+4.19867)/1.06606


#choose HH 90%
def PFTauOfflineEtCutBarrel(offline): return (offline+11.5292)/2.08813
def PFTauOfflineEtCutEndcap(offline): return (offline-2.45302)/1.85321

def PFIsoTauOfflineEtCutBarrel(offline): return (offline+4.72956)/1.80821
def PFIsoTauOfflineEtCutEndcap(offline): return (offline-11.0478)/1.55742

def NNTauTightOfflineEtCutBarrel(offline): return (offline+21.3166)/1.84293
def NNTauTightOfflineEtCutEndcap(offline): return (offline+1.47361)/1.39273

def NNTauLooseOfflineEtCutBarrel(offline): return (offline+9.16702)/1.69784
def NNTauLooseOfflineEtCutEndcap(offline): return (offline-3.12516)/1.36535

def TkEGTauOfflineEtCutBarrel(offline): return (offline+91.7613)/5.12908
def TkEGTauOfflineEtCutEndcap(offline): return (offline+13.6892)/3.89439

def CaloTauOfflineEtCutBarrel(offline): return (offline+0.937512)/1.38032
def CaloTauOfflineEtCutEndcap(offline): return (offline-1.92178)/1.26272



#V4
# def PFTauOfflineEtCutBarrel(offline): return (offline+1.08865)/1.06336
# def PFTauOfflineEtCutEndcap(offline): return (offline+0.267099)/1.11537

# def PFIsoTauOfflineEtCutBarrel(offline): return (offline+0.723147)/1.04974
# def PFIsoTauOfflineEtCutEndcap(offline): return (offline-1.57412)/1.05859

# def NNTauTightOfflineEtCutBarrel(offline): return (offline+10.2033)/1.36891
# def NNTauTightOfflineEtCutEndcap(offline): return (offline+9.02217)/1.34075

# def NNTauLooseOfflineEtCutBarrel(offline): return (offline+7.93117)/1.45874
# def NNTauLooseOfflineEtCutEndcap(offline): return (offline+5.25829)/1.39801

# def TkEGTauOfflineEtCutBarrel(offline): return (offline-0.016095)/1.02482
# def TkEGTauOfflineEtCutEndcap(offline): return (offline+2.21268)/1.27027

# def CaloTauOfflineEtCutBarrel(offline): return (offline+6.53017)/1.15518
# def CaloTauOfflineEtCutEndcap(offline): return (offline+4.59066)/1.07214



# def HPSTauOfflineEtCutBarrel(offline): return (offline-1.99747)/0.990751
# def HPSTauOfflineEtCutEndcap(offline): return (offline-1.401)/1.08257
# def HPSIsoTauOfflineEtCutBarrel(offline): return (offline-1.02907)/1.00135
# def HPSIsoTauOfflineEtCutEndcap(offline): return (offline-1.19503)/1.07426


## Jets
# function :: PuppiJetOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-39.7621)/1.10472 if abs(Eta)<1.5 else (Et>(offline-59.4759)/1.05225 if abs(Eta)<2.4 else Et>(offline-6.47801)/1.99057)
# function :: PFPhase1JetOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-35.6078)/1.2042 if abs(Eta)<1.5 else (Et>(offline-61.8214)/1.09898 if abs(Eta)<2.4 else Et>(offline-1.08496)/2.15502)
# function :: CaloJetOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-24.8298)/1.1863 if abs(Eta)<1.5 else (Et>(offline-26.8634)/1.17171 if abs(Eta)<2.4 else Et>(offline+31.0189)/2.16122)
# function :: TrackerJetOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-39.5772)/4.3296 if abs(Eta)<1.5 else Et>(offline-52.663)/5.63404

# function :: TTbarPuppiJetOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-16.2875)/1.25257 if abs(Eta)<1.5 else (Et>(offline-25.8625)/1.24229 if abs(Eta)<2.4 else Et>(offline-9.68567)/1.94574)
# function :: TTbarPFPhase1JetOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-12.7315)/1.37302 if abs(Eta)<1.5 else (Et>(offline-25.211)/1.35985 if abs(Eta)<2.4 else Et>(offline-15.711)/1.88226)
# function :: TTbarCaloJetOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-17.4134)/1.29985 if abs(Eta)<1.5 else (Et>(offline-49.7045)/1.09395 if abs(Eta)<2.4 else Et>(offline-3.99523)/1.68789)
# function :: TTbarTrackerJetOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-45.6922)/4.2229 if abs(Eta)<1.5 else Et>(offline-97.3989)/4.27346

##choose ttbar 
def PuppiJetOfflineEtCutBarrel(offline): return (offline-16.2875)/1.25257
def PuppiJetOfflineEtCutEndcap(offline): return (offline-25.8625)/1.24229
def PuppiJetOfflineEtCutForward(offline): return (offline-9.68567)/1.94574

def PFPhase1JetOfflineEtCutBarrel(offline): return (offline-12.7315)/1.37302
def PFPhase1JetOfflineEtCutEndcap(offline): return (offline-25.211)/1.35985
def PFPhase1JetOfflineEtCutForward(offline): return (offline-15.711)/1.88226

def CaloJetOfflineEtCutBarrel(offline): return (offline-17.4134)/1.29985
def CaloJetOfflineEtCutEndcap(offline): return (offline-49.7045)/1.09395
def CaloJetOfflineEtCutForward(offline): return (offline-3.99523)/1.68789

def TrackerJetOfflineEtCutBarrel(offline): return (offline-45.6922)/4.2229
def TrackerJetOfflineEtCutEndcap(offline): return (offline-97.3989)/4.27346


### Muons
# function :: StandaloneMuonOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-3.89083)/1.0142 if abs(Eta)<0.9 else (Et>(offline-0.712226)/1.09458 if abs(Eta)<1.2 else Et>(offline-2.72037)/0.993461)
# function :: TkMuonOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-0.485737)/1.05306 if abs(Eta)<0.9 else (Et>(offline-0.841831)/1.03697 if abs(Eta)<1.2 else Et>(offline-0.78699)/1.03252)
# function :: TkMuonStubOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-0.726357)/1.04175 if abs(Eta)<0.9 else (Et>(offline-0.735574)/1.04424 if abs(Eta)<1.2 else Et>(offline-0.543297)/1.04428)

#Update with no quality a part from OverlapSta, and including forward Stubs
# function :: StandaloneMuonOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-3.88566)/1.01712 if abs(Eta)<0.9 else (Et>(offline+1.16016)/1.31345 if abs(Eta)<1.2 else (Et>(offline-0.389879)/1.18579 if abs(Eta)<2.4 else Et>(offline+28.4221)/5.51244))
# function :: TkMuonOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-0.480586)/1.05326 if abs(Eta)<0.9 else (Et>(offline-0.789258)/1.03509 if abs(Eta)<1.2 else Et>(offline-0.784553)/1.03251)
# function :: TkMuonStubOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-0.710744)/1.04185 if abs(Eta)<0.9 else (Et>(offline-0.805149)/1.04062 if abs(Eta)<1.2 else Et>(offline-0.554819)/1.04354)



def StandaloneMuonOfflineEtCutBarrel(offline): return (offline-3.88566)/1.01712
def TkMuonOfflineEtCutBarrel(offline): return (offline-0.480586)/1.05326
def TkMuonStubOfflineEtCutBarrel(offline): return (offline-0.710744)/1.04185

def StandaloneMuonOfflineEtCutOverlap(offline): return (offline+1.16016)/1.31345
def TkMuonOfflineEtCutOverlap(offline): return (offline-0.789258)/1.03509 
def TkMuonStubOfflineEtCutOverlap(offline): return (offline-0.805149)/1.04062

def StandaloneMuonOfflineEtCutEndcap(offline): return (offline-0.389879)/1.18579
def TkMuonOfflineEtCutEndcap(offline): return (offline-0.784553)/1.03251
def TkMuonStubOfflineEtCutEndcap(offline): return (offline-0.554819)/1.04354

def TkMuonStubOfflineEtCutForward(offline): return (offline+28.4221)/5.51244


## EG
# function :: EGPhotonOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-2.80694)/0.979067 if abs(Eta)<1.5 else (Et>(offline-7.66012)/1.03665 if abs(Eta)<2.4 else Et>(offline-2.63103)/1.4081)
# function :: EGElectronOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-2.95953)/1.0434 if abs(Eta)<1.5 else (Et>(offline-7.79311)/1.10045 if abs(Eta)<2.4 else Et>(offline-5.43055)/1.28648)
# function :: TkElectronOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-0.252031)/1.09043 if abs(Eta)<1.5 else Et>(offline-5.27586)/1.16298
# function :: TkIsoElectronOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-0.315819)/1.08834 if abs(Eta)<1.5 else Et>(offline-4.62976)/1.16961
# function :: TkIsoPhotonOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-1.92377)/1.01512 if abs(Eta)<1.5 else Et>(offline-5.92531)/1.05584


def StandalonePhotonOfflineEtCutBarrel(offline): return (offline-2.80694)/0.979067
def StandalonePhotonOfflineEtCutEndcap(offline): return (offline-7.66012)/1.03665

def StandaloneElectronOfflineEtCutBarrel(offline): return (offline-2.95953)/1.0434
def StandaloneElectronOfflineEtCutEndcap(offline): return (offline-7.79311)/1.10045
def StandaloneElectronOfflineEtCutForward(offline): return (offline-5.43055)/1.28648



def TkElectronOfflineEtCutBarrel(offline): return (offline-0.252031)/1.09043
def TkElectronOfflineEtCutEndcap(offline): return (offline-5.27586)/1.16298

def TkIsoElectronOfflineEtCutBarrel(offline): return (offline-0.315819)/1.08834
def TkIsoElectronOfflineEtCutEndcap(offline): return (offline-4.62976)/1.16961

def TkIsoPhotonOfflineEtCutBarrel(offline): return (offline-1.92377)/1.01512
def TkIsoPhotonOfflineEtCutEndcap(offline): return (offline-5.92531)/1.05584


cutrange = {

#'tkMuon':[0.0,60.0,3.0],
#'tkMuonStub':[0.0,60.0,3.0],
#'tkMuonStubExt':[0.0,60.0,3.0],
#'standaloneMuon':[0.0,60.0,3.0],

'tkMuon':[0.0,78.0,3.0],
'tkMuonStub':[0.0,78.0,3.0],
'standaloneMuon':[0.0,78.0,3.0],

'tkMuonBarrel':[0.0,60.0,3.0],
'tkMuonStubBarrel':[0.0,60.0,3.0],
'standaloneMuonBarrel':[0.0,60.0,3.0],

'tkMuonOverlap':[0.0,60.0,3.0],
'tkMuonStubOverlap':[0.0,60.0,3.0],
'standaloneMuonOverlap':[0.0,60.0,3.0],

'tkMuonEndcap':[0.0,60.0,3.0],
'tkMuonStubEndcap':[0.0,60.0,3.0],
'standaloneMuonEndcap':[0.0,60.0,3.0],

#'tkElectron':[10.0,70.0,3.0],
#'tkIsoElectron':[10.0,70.0,3.0],
#'standaloneElectron':[10.0,70.0,3.0],
#'standaloneElectronExt':[10.0,70.0,3.0],

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

#'tkPhotonIso':[10.0,70.0,3.0],
'tkPhotonIso':[10.0,100.0,3.0],
'standalonePhoton':[10.0,70.0,3.0],

'tkPhotonIsoBarrel':[10.0,70.0,3.0],
'standalonePhotonBarrel':[10.0,70.0,3.0],

'tkPhotonIsoEndcap':[10.0,70.0,3.0],
'standalonePhotonEndcap':[10.0,70.0,3.0],

'puppiHT':[50.0,500.0,25.0],
'puppiPhase1HT':[50.0,500.0,25.0],
'trackerHT':[50.0,500.0,25.0],
'caloHT':[50.0,500.0,25.0],

'puppiHT':[50.0,1000.0,25.0],
'puppiPhase1HT':[50.0,1000.0,25.0],
'trackerHT':[50.0,1000.0,25.0],
'caloHT':[50.0,1000.0,25.0],

'puppiMET':[50.0,500.0,25.0],
'trackerMET':[0.0,500.0,5.0],

'puppiJet':[40.0,440.0,20.0],
'puppiJetExt':[40.0,440.0,20.0],
'puppiPhase1Jet':[40.0,440.0,20.0],
'puppiPhase1JetExt':[40.0,440.0,20.0],
'trackerJet':[40.0,440.0,20.0],
'caloJet':[40.0,440.0,20.0],
'caloJetExt':[40.0,440.0,20.0],

'HPSPFTau1':[10.0,160.0,5.0],
'HPSPFTau1Medium':[10.0,160.0,5.0],
'HPSPFTau2':[10.0,160.0,5.0],
'HPSPFTau2Tight':[10.0,160.0,5.0],
'NNPuppiTauLoose':[10.0,160.0,5.0],
'NNPuppiTauTight':[10.0,160.0,5.0],
'TkEGTau':[10.0,160.0,5.0],
'CaloTau':[10.0,160.0,5.0],

'DiHPSPFTau1':[10.0,80.0,5.0],
'DiHPSPFTau1Medium':[10.0,80.0,5.0],
'DiNNPuppiTauLoose':[10.0,80.0,5.0],
'DiNNPuppiTauTight':[10.0,80.0,5.0],
'DiTkEGTau':[10.0,80.0,5.0],
'DiCaloTau':[10.0,80.0,5.0],





}

list_calc = [
#  'tkMuon',
  #'tkMuonStub',
  #'tkMuonStubExt',
  #'standaloneMuon',
  
  # 'tkMuonBarrel',
  # 'tkMuonStubBarrel',
  # 'standaloneMuonBarrel',
  
  # 'tkMuonOverlap',
  # 'tkMuonStubOverlap',
  # 'standaloneMuonOverlap',
  
  # 'tkMuonEndcap',
  # 'tkMuonStubEndcap',
  # 'standaloneMuonEndcap',

  #'tkElectron',
  #'tkIsoElectron',
  # 'standaloneElectron',
  # 'standaloneElectronExt',

  # 'tkElectronBarrel',
  # 'tkIsoElectronBarrel',
  # 'standaloneElectronBarrel',
  
  # 'tkElectronEndcap',
  # 'tkIsoElectronEndcap',
  # 'standaloneElectronEndcap',
 
  #'tkPhotonIso',
  # 'standalonePhoton',
  
  # 'tkPhotonIsoBarrel',
  # 'standalonePhotonBarrel',

  # 'tkPhotonIsoEndcap',
  # 'standalonePhotonEndcap',

  # 'puppiHT',
#   'puppiPhase1HT',
#   'trackerHT',
  # 'caloHT',
  # 'puppiMET',
   'trackerMET',

  # 'puppiJet',
  # 'puppiJetExt',
  # 'puppiPhase1Jet',
  # 'puppiPhase1JetExt',
 #  'trackerJet',
 #  'caloJet',
 #  'caloJetExt',

  # 'HPSPFTau1',
  # 'HPSPFTau1Medium',
  ## 'HPSPFTau2',
  ## 'HPSPFTau2Tight',
#  'NNPuppiTauLoose',
  #'NNPuppiTauTight',
  #'TkEGTau',
#  'CaloTau',

]





# off['tkMuon'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['tkMuon'] =  array('d', [11230.9, 9787.0, 1217.6, 270.7, 93.8, 42.2, 23.6, 13.9, 8.4, 5.1, 3.9, 3.2, 2.1, 1.8, 1.5, 1.3, 1.1, 1.0, 0.9, 0.9])
# onl['tkMuon'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['tkMuon'] =  array('d', [11230.9, 5012.5, 719.7, 182.4, 65.6, 34.2, 19.0, 10.5, 6.7, 4.3, 3.3, 2.3, 1.9, 1.5, 1.4, 1.1, 1.0, 0.9, 0.9, 0.8])
# off['tkMuonStub'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['tkMuonStub'] =  array('d', [28416.9, 21678.0, 1334.9, 300.1, 106.8, 49.0, 26.6, 16.2, 10.3, 6.9, 5.2, 4.3, 3.1, 2.8, 2.3, 2.1, 1.7, 1.4, 1.4, 1.3])
# onl['tkMuonStub'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['tkMuonStub'] =  array('d', [28416.9, 9979.5, 806.4, 205.2, 74.4, 38.9, 21.5, 12.5, 8.5, 5.5, 4.4, 3.2, 2.8, 2.3, 2.2, 1.7, 1.4, 1.4, 1.3, 1.3])
# off['tkMuonStubExt'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['tkMuonStubExt'] =  array('d', [29055.6, 23928.4, 8080.6, 6808.7, 6166.2, 5605.8, 5586.7, 5257.7, 5253.3, 4397.3, 4395.3, 4394.7, 3991.6, 3991.1, 3990.5, 3990.2, 3284.8, 3284.4, 3284.4, 3284.3])
# onl['tkMuonStubExt'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['tkMuonStubExt'] =  array('d', [29156.2, 15608.4, 7672.1, 5412.1, 4050.8, 3316.5, 2713.0, 2704.7, 2384.3, 2381.7, 2380.7, 2379.5, 1763.1, 1762.6, 1762.4, 1761.9, 1761.7, 1761.7, 1761.6, 1761.6])
# off['standaloneMuon'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['standaloneMuon'] =  array('d', [15048.8, 13635.6, 3007.3, 1247.1, 501.4, 225.8, 112.5, 76.6, 59.3, 48.7, 42.4, 33.6, 29.7, 25.1, 22.8, 21.5, 19.0, 18.1, 17.1, 15.8])
# onl['standaloneMuon'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['standaloneMuon'] =  array('d', [15048.8, 5231.0, 1343.3, 405.0, 195.3, 97.2, 70.7, 50.9, 45.8, 34.3, 31.8, 25.2, 20.7, 20.1, 18.3, 17.8, 15.8, 13.7, 13.2, 12.8])
# off['tkMuonBarrel'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['tkMuonBarrel'] =  array('d', [864.9, 796.5, 344.6, 99.2, 36.7, 17.5, 10.8, 7.0, 4.2, 2.3, 1.9, 1.6, 1.1, 0.9, 0.9, 0.9, 0.7, 0.7, 0.6, 0.6])
# onl['tkMuonBarrel'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['tkMuonBarrel'] =  array('d', [864.9, 683.8, 247.0, 71.2, 25.9, 14.9, 8.9, 5.0, 3.2, 2.1, 1.7, 1.2, 0.9, 0.9, 0.9, 0.7, 0.7, 0.6, 0.6, 0.6])
# off['tkMuonStubBarrel'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['tkMuonStubBarrel'] =  array('d', [589.2, 589.2, 306.7, 105.5, 40.2, 19.2, 11.8, 7.7, 4.8, 3.1, 2.7, 2.3, 1.6, 1.5, 1.3, 1.2, 0.9, 0.9, 0.8, 0.8])
# onl['tkMuonStubBarrel'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['tkMuonStubBarrel'] =  array('d', [589.2, 589.2, 222.5, 73.2, 28.0, 15.9, 9.8, 5.5, 4.0, 2.8, 2.4, 1.6, 1.5, 1.3, 1.3, 0.9, 0.9, 0.8, 0.8, 0.8])
# off['standaloneMuonBarrel'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['standaloneMuonBarrel'] =  array('d', [1513.2, 1513.2, 1513.2, 781.1, 289.9, 106.7, 52.4, 32.9, 26.2, 20.6, 16.3, 14.6, 12.1, 11.5, 10.0, 9.6, 8.8, 8.3, 8.1, 7.1])
# onl['standaloneMuonBarrel'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['standaloneMuonBarrel'] =  array('d', [1513.2, 1513.2, 526.1, 170.8, 75.8, 39.9, 30.2, 22.3, 19.2, 15.1, 14.2, 11.8, 10.0, 9.8, 9.1, 8.8, 8.2, 7.1, 7.1, 7.0])
# off['tkMuonOverlap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['tkMuonOverlap'] =  array('d', [836.5, 807.8, 181.6, 33.4, 10.2, 5.2, 3.2, 1.8, 1.4, 0.9, 0.6, 0.6, 0.4, 0.4, 0.4, 0.2, 0.2, 0.1, 0.1, 0.1])
# onl['tkMuonOverlap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['tkMuonOverlap'] =  array('d', [836.5, 612.7, 97.0, 20.8, 7.1, 4.4, 2.4, 1.8, 1.1, 0.7, 0.6, 0.5, 0.4, 0.4, 0.3, 0.2, 0.1, 0.1, 0.1, 0.1])
# off['tkMuonStubOverlap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['tkMuonStubOverlap'] =  array('d', [766.2, 711.2, 155.2, 30.5, 9.7, 4.7, 3.1, 1.6, 1.3, 0.7, 0.5, 0.4, 0.3, 0.3, 0.3, 0.1, 0.1, 0.0, 0.0, 0.0])
# onl['tkMuonStubOverlap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['tkMuonStubOverlap'] =  array('d', [766.2, 492.4, 82.8, 19.0, 6.4, 3.8, 2.2, 1.6, 0.9, 0.5, 0.4, 0.4, 0.3, 0.3, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0])
# off['standaloneMuonOverlap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['standaloneMuonOverlap'] =  array('d', [559.9, 559.9, 320.6, 106.7, 72.4, 46.3, 22.0, 17.7, 14.8, 12.8, 12.8, 8.4, 8.4, 6.7, 6.7, 6.7, 5.5, 5.5, 4.7, 4.7])
# onl['standaloneMuonOverlap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['standaloneMuonOverlap'] =  array('d', [559.9, 559.9, 226.2, 72.6, 46.3, 21.9, 17.7, 12.8, 12.8, 8.4, 8.4, 6.7, 5.5, 5.5, 4.7, 4.7, 3.8, 3.0, 3.0, 3.0])
# off['tkMuonEndcap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['tkMuonEndcap'] =  array('d', [10169.6, 8714.2, 709.8, 139.5, 47.1, 19.5, 9.5, 5.0, 2.8, 1.9, 1.4, 1.0, 0.6, 0.4, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3])
# onl['tkMuonEndcap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['tkMuonEndcap'] =  array('d', [10169.6, 3933.2, 382.2, 91.1, 32.7, 14.9, 7.7, 3.7, 2.4, 1.6, 1.0, 0.6, 0.5, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.1])
# off['tkMuonStubEndcap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['tkMuonStubEndcap'] =  array('d', [28315.9, 21317.2, 889.5, 165.9, 57.2, 25.1, 11.8, 6.8, 4.1, 3.1, 2.0, 1.6, 1.2, 1.0, 0.8, 0.8, 0.6, 0.6, 0.6, 0.5])
# onl['tkMuonStubEndcap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['tkMuonStubEndcap'] =  array('d', [28315.9, 9270.2, 507.2, 113.9, 40.2, 19.3, 9.6, 5.4, 3.5, 2.2, 1.6, 1.2, 1.0, 0.8, 0.8, 0.6, 0.6, 0.6, 0.5, 0.5])
# off['standaloneMuonEndcap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['standaloneMuonEndcap'] =  array('d', [13982.6, 12469.0, 1300.7, 385.0, 148.3, 76.1, 39.6, 27.3, 19.5, 16.1, 13.9, 10.6, 9.2, 6.9, 6.2, 5.2, 4.7, 4.4, 4.3, 4.0])
# onl['standaloneMuonEndcap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['standaloneMuonEndcap'] =  array('d', [13982.6, 3470.8, 630.4, 169.7, 76.1, 36.9, 24.1, 16.8, 14.4, 10.8, 9.2, 6.7, 5.2, 4.8, 4.5, 4.3, 3.8, 3.5, 3.1, 2.8])


# off['puppiMET'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
# offrate['puppiMET'] =  array('d', [5249.8, 709.3, 125.2, 30.3, 10.7, 5.2, 3.2, 1.9, 1.6, 1.3, 0.9, 0.6, 0.5, 0.5, 0.3, 0.3, 0.2, 0.2])
# onl['puppiMET'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
# onlrate['puppiMET'] =  array('d', [836.4, 128.2, 27.9, 9.8, 4.9, 2.8, 1.8, 1.5, 1.1, 0.7, 0.5, 0.5, 0.4, 0.3, 0.2, 0.2, 0.1, 0.1])
# off['trackerMET'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
# offrate['trackerMET'] =  array('d', [31038.0, 31038.0, 27941.1, 7958.0, 1112.5, 169.7, 41.8, 15.0, 7.9, 5.5, 4.2, 3.2, 2.5, 2.3, 1.4, 0.4, 0.3, 0.2])
# onl['trackerMET'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
# onlrate['trackerMET'] =  array('d', [162.6, 22.9, 7.9, 4.5, 3.0, 2.4, 0.9, 0.3, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.1, 0.1, 0.1])
# off['tkMuon'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['tkMuon'] =  array('d', [11827.7, 9915.1, 1200.1, 272.2, 93.0, 40.3, 21.4, 12.0, 7.0, 4.1, 3.2, 2.4, 1.6, 1.4, 1.1, 1.0, 0.9, 0.7, 0.7, 0.7])
# onl['tkMuon'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['tkMuon'] =  array('d', [11827.7, 4582.4, 715.4, 181.9, 64.1, 32.5, 17.1, 8.8, 5.4, 3.4, 2.5, 1.7, 1.4, 1.1, 1.1, 0.9, 0.7, 0.7, 0.7, 0.7])
# off['tkMuonStub'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['tkMuonStub'] =  array('d', [28415.0, 21459.1, 1395.4, 303.0, 103.1, 45.9, 23.6, 14.0, 8.7, 5.4, 3.7, 2.9, 2.2, 1.9, 1.4, 1.3, 1.2, 1.0, 0.9, 0.8])
# onl['tkMuonStub'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['tkMuonStub'] =  array('d', [28415.0, 9954.8, 835.8, 204.3, 71.3, 35.6, 18.8, 10.8, 7.0, 4.1, 3.1, 2.2, 1.9, 1.4, 1.4, 1.2, 1.0, 0.9, 0.8, 0.8])
# off['standaloneMuon'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['standaloneMuon'] =  array('d', [9439.9, 9439.9, 4628.3, 1210.7, 447.8, 167.2, 81.5, 48.7, 36.8, 30.2, 21.7, 18.7, 14.3, 13.0, 10.9, 10.2, 9.2, 7.9, 7.4, 6.0])
# onl['standaloneMuon'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['standaloneMuon'] =  array('d', [9439.9, 4733.4, 1078.7, 333.9, 152.0, 71.4, 48.7, 34.0, 28.9, 20.6, 18.3, 14.0, 11.5, 11.0, 9.6, 9.2, 7.9, 6.3, 6.0, 5.7])
# off['tkMuonBarrel'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['tkMuonBarrel'] =  array('d', [329.5, 329.5, 306.9, 94.2, 34.1, 16.3, 9.6, 5.9, 3.5, 1.9, 1.6, 1.2, 0.9, 0.7, 0.7, 0.7, 0.6, 0.6, 0.5, 0.5])
# onl['tkMuonBarrel'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['tkMuonBarrel'] =  array('d', [329.5, 329.4, 226.4, 67.1, 23.9, 13.8, 7.8, 4.2, 2.7, 1.6, 1.3, 0.9, 0.7, 0.7, 0.7, 0.6, 0.6, 0.5, 0.5, 0.5])
# off['tkMuonStubBarrel'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['tkMuonStubBarrel'] =  array('d', [574.6, 574.6, 377.8, 108.9, 37.0, 16.6, 8.8, 5.7, 3.4, 1.7, 1.4, 1.0, 0.7, 0.6, 0.4, 0.4, 0.4, 0.4, 0.3, 0.3])
# onl['tkMuonStubBarrel'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['tkMuonStubBarrel'] =  array('d', [574.6, 538.6, 252.2, 72.1, 25.0, 12.8, 7.2, 4.0, 2.7, 1.4, 1.1, 0.7, 0.6, 0.4, 0.4, 0.4, 0.4, 0.3, 0.3, 0.3])
# off['standaloneMuonBarrel'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['standaloneMuonBarrel'] =  array('d', [1454.6, 1454.6, 1454.6, 732.3, 261.0, 86.3, 34.7, 19.3, 14.1, 9.4, 7.3, 5.6, 4.5, 3.9, 3.4, 3.0, 2.7, 2.7, 2.6, 2.2])
# onl['standaloneMuonBarrel'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['standaloneMuonBarrel'] =  array('d', [1454.6, 1454.6, 486.8, 145.4, 55.5, 24.5, 16.5, 11.3, 8.0, 6.1, 5.2, 4.2, 3.6, 3.4, 3.0, 2.7, 2.7, 2.2, 2.2, 2.1])
# off['tkMuonOverlap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['tkMuonOverlap'] =  array('d', [316.6, 285.4, 123.6, 28.5, 9.0, 4.1, 2.8, 1.5, 1.2, 0.7, 0.6, 0.4, 0.3, 0.3, 0.3, 0.2, 0.2, 0.1, 0.1, 0.1])
# onl['tkMuonOverlap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['tkMuonOverlap'] =  array('d', [316.6, 216.1, 75.1, 17.8, 5.9, 3.5, 2.1, 1.4, 1.0, 0.6, 0.4, 0.4, 0.3, 0.3, 0.2, 0.2, 0.1, 0.1, 0.1, 0.1])
# off['tkMuonStubOverlap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['tkMuonStubOverlap'] =  array('d', [766.8, 682.5, 151.3, 29.7, 9.7, 4.6, 3.1, 1.7, 1.4, 0.7, 0.5, 0.4, 0.3, 0.3, 0.2, 0.1, 0.1, 0.0, 0.0, 0.0])
# onl['tkMuonStubOverlap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['tkMuonStubOverlap'] =  array('d', [766.8, 493.1, 83.0, 19.1, 6.4, 3.9, 2.2, 1.6, 0.9, 0.5, 0.4, 0.4, 0.3, 0.2, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0])
# off['standaloneMuonOverlap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['standaloneMuonOverlap'] =  array('d', [560.8, 560.8, 432.3, 106.5, 72.0, 30.6, 21.7, 14.8, 12.8, 12.8, 8.5, 8.5, 6.5, 6.5, 5.4, 5.4, 4.7, 3.8, 3.8, 3.0])
# onl['standaloneMuonOverlap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['standaloneMuonOverlap'] =  array('d', [560.8, 560.8, 226.0, 72.3, 46.1, 21.9, 17.6, 12.8, 12.8, 8.5, 8.5, 6.5, 5.4, 5.4, 4.7, 4.7, 3.8, 3.0, 3.0, 3.0])
# off['tkMuonEndcap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['tkMuonEndcap'] =  array('d', [11435.7, 9507.6, 783.8, 150.9, 50.1, 19.9, 9.0, 4.6, 2.2, 1.5, 1.1, 0.7, 0.4, 0.3, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
# onl['tkMuonEndcap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['tkMuonEndcap'] =  array('d', [11435.7, 4120.4, 419.6, 97.6, 34.3, 15.3, 7.3, 3.2, 1.7, 1.2, 0.7, 0.4, 0.4, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
# off['tkMuonStubEndcap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['tkMuonStubEndcap'] =  array('d', [28314.2, 21098.5, 885.8, 165.9, 56.6, 24.7, 11.6, 6.6, 4.0, 3.0, 1.9, 1.5, 1.1, 1.0, 0.7, 0.7, 0.6, 0.6, 0.6, 0.5])
# onl['tkMuonStubEndcap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['tkMuonStubEndcap'] =  array('d', [28314.2, 9268.8, 508.2, 113.9, 39.9, 18.9, 9.3, 5.2, 3.4, 2.1, 1.5, 1.1, 1.0, 0.7, 0.7, 0.6, 0.6, 0.6, 0.5, 0.5])
# off['standaloneMuonEndcap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# offrate['standaloneMuonEndcap'] =  array('d', [8024.1, 8024.1, 2990.6, 399.2, 123.8, 53.3, 26.5, 16.0, 10.8, 8.7, 6.0, 4.6, 3.2, 2.5, 2.1, 1.8, 1.7, 1.3, 1.0, 0.8])
# onl['standaloneMuonEndcap'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
# onlrate['standaloneMuonEndcap'] =  array('d', [8024.1, 2990.6, 399.2, 123.8, 53.3, 26.5, 16.0, 10.8, 8.7, 6.0, 4.6, 3.2, 2.5, 2.2, 1.9, 1.7, 1.4, 1.1, 0.8, 0.6])


# off['tkElectron'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# offrate['tkElectron'] =  array('d', [884.8, 570.0, 332.7, 200.4, 112.2, 76.5, 54.9, 40.3, 27.1, 22.4, 17.4, 14.0, 11.8, 9.5, 7.4, 6.2, 5.3, 4.2, 3.6, 3.2])
# onl['tkElectron'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# onlrate['tkElectron'] =  array('d', [617.2, 330.0, 193.4, 113.7, 67.7, 47.6, 35.8, 23.7, 19.2, 14.3, 11.2, 9.5, 7.4, 5.6, 4.6, 4.2, 3.4, 2.9, 2.3, 2.2])
# off['tkIsoElectron'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# offrate['tkIsoElectron'] =  array('d', [470.7, 280.3, 150.9, 92.2, 51.1, 35.3, 26.8, 20.2, 14.3, 12.1, 10.4, 8.5, 7.4, 6.3, 5.4, 4.6, 3.6, 3.0, 2.3, 1.9])
# onl['tkIsoElectron'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# onlrate['tkIsoElectron'] =  array('d', [301.2, 153.3, 86.5, 53.0, 32.0, 22.2, 17.6, 13.0, 10.8, 8.7, 6.8, 5.9, 4.9, 4.2, 3.4, 3.1, 2.4, 1.7, 1.4, 1.4])
# off['standaloneElectron'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# offrate['standaloneElectron'] =  array('d', [21717.3, 19090.3, 5528.6, 1861.1, 886.8, 430.3, 263.6, 172.5, 113.9, 78.4, 58.3, 44.8, 34.5, 27.9, 22.7, 18.2, 14.0, 11.3, 8.7, 7.0])
# onl['standaloneElectron'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# onlrate['standaloneElectron'] =  array('d', [4286.7, 1887.6, 997.4, 535.5, 284.8, 182.4, 129.5, 80.3, 58.5, 44.6, 34.2, 27.5, 21.4, 16.6, 13.1, 10.8, 7.9, 6.4, 5.0, 4.5])
# off['standaloneElectronExt'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# offrate['standaloneElectronExt'] =  array('d', [24897.8, 21230.9, 6382.8, 2132.9, 1002.8, 490.5, 300.2, 196.0, 130.5, 90.7, 68.2, 53.0, 40.9, 33.5, 27.4, 22.1, 17.3, 13.8, 10.8, 9.1])
# onl['standaloneElectronExt'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# onlrate['standaloneElectronExt'] =  array('d', [4605.5, 1994.6, 1046.2, 562.2, 301.8, 193.9, 138.4, 86.9, 63.9, 48.8, 37.7, 30.0, 23.5, 18.6, 14.5, 12.0, 8.9, 7.2, 5.8, 5.3])
# off['tkElectronBarrel'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# offrate['tkElectronBarrel'] =  array('d', [620.3, 364.7, 209.6, 133.7, 74.0, 51.0, 38.7, 28.8, 19.3, 15.8, 12.2, 10.2, 8.4, 6.9, 5.2, 4.5, 3.9, 3.5, 2.9, 2.6])
# onl['tkElectronBarrel'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# onlrate['tkElectronBarrel'] =  array('d', [514.9, 279.3, 163.4, 95.8, 56.0, 39.9, 29.7, 19.3, 15.5, 11.6, 9.1, 7.9, 6.3, 5.0, 4.0, 3.7, 3.0, 2.6, 2.0, 1.9])
# off['tkIsoElectronBarrel'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# offrate['tkIsoElectronBarrel'] =  array('d', [301.0, 167.2, 89.9, 58.4, 32.7, 23.0, 17.7, 13.8, 10.0, 8.4, 7.2, 6.0, 5.2, 4.6, 4.1, 3.6, 2.9, 2.7, 2.0, 1.6])
# onl['tkIsoElectronBarrel'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# onlrate['tkIsoElectronBarrel'] =  array('d', [244.2, 125.4, 70.3, 43.1, 25.3, 18.0, 14.0, 10.0, 8.4, 6.7, 5.4, 4.9, 4.4, 3.9, 3.1, 2.8, 2.2, 1.6, 1.3, 1.2])
# off['standaloneElectronBarrel'] =  array('d', [10.0, 14.0, 18.0, 22.0, 26.0, 30.0, 34.0, 38.0, 42.0, 46.0, 50.0, 54.0, 58.0, 62.0, 66.0])
# offrate['standaloneElectronBarrel'] =  array('d', [10009.0, 2844.5, 1158.1, 569.1, 237.8, 139.3, 81.9, 51.2, 36.3, 25.6, 19.6, 14.6, 11.0, 8.2, 6.0])
# onl['standaloneElectronBarrel'] =  array('d', [10.0, 14.0, 18.0, 22.0, 26.0, 30.0, 34.0, 38.0, 42.0, 46.0, 50.0, 54.0, 58.0, 62.0, 66.0])
# onlrate['standaloneElectronBarrel'] =  array('d', [3431.4, 1284.6, 603.4, 242.5, 138.8, 77.5, 49.0, 34.6, 24.7, 18.4, 13.3, 9.9, 7.0, 4.9, 4.1])
# off['tkElectronEndcap'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# offrate['tkElectronEndcap'] =  array('d', [271.7, 209.7, 124.9, 67.7, 38.3, 25.7, 16.3, 11.6, 7.9, 6.6, 5.2, 3.9, 3.4, 2.6, 2.1, 1.7, 1.4, 0.7, 0.6, 0.6])
# onl['tkElectronEndcap'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# onlrate['tkElectronEndcap'] =  array('d', [105.2, 51.7, 30.5, 18.1, 11.8, 7.7, 6.1, 4.5, 3.7, 2.7, 2.1, 1.6, 1.1, 0.6, 0.6, 0.6, 0.4, 0.3, 0.3, 0.3])
# off['tkIsoElectronEndcap'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# offrate['tkIsoElectronEndcap'] =  array('d', [171.4, 113.6, 61.3, 34.0, 18.6, 12.5, 9.1, 6.4, 4.2, 3.7, 3.2, 2.5, 2.1, 1.7, 1.4, 1.0, 0.6, 0.3, 0.3, 0.3])
# onl['tkIsoElectronEndcap'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# onlrate['tkIsoElectronEndcap'] =  array('d', [57.4, 28.1, 16.4, 10.1, 6.9, 4.3, 3.7, 3.0, 2.4, 1.9, 1.4, 1.0, 0.6, 0.3, 0.3, 0.2, 0.2, 0.1, 0.1, 0.1])
# off['standaloneElectronEndcap'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# offrate['standaloneElectronEndcap'] =  array('d', [17519.5, 17519.5, 3999.0, 917.6, 327.1, 152.4, 83.4, 50.2, 32.3, 22.9, 16.3, 11.5, 9.2, 7.2, 6.0, 4.7, 3.3, 2.6, 2.0, 1.5])
# onl['standaloneElectronEndcap'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# onlrate['standaloneElectronEndcap'] =  array('d', [995.6, 317.0, 138.4, 74.2, 43.2, 27.7, 19.4, 13.4, 9.8, 7.6, 6.0, 4.7, 3.2, 2.3, 1.6, 1.3, 0.9, 0.6, 0.6, 0.6])
# off['tkPhotonIso'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# offrate['tkPhotonIso'] =  array('d', [8821.6, 3483.2, 977.4, 473.2, 242.3, 149.9, 104.3, 75.8, 51.7, 39.4, 31.0, 24.7, 20.5, 17.4, 13.5, 10.7, 8.3, 6.4, 5.2, 3.9])
# onl['tkPhotonIso'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# onlrate['tkPhotonIso'] =  array('d', [1469.6, 685.3, 402.9, 235.3, 140.1, 95.3, 72.9, 49.4, 36.6, 29.4, 23.4, 18.9, 15.3, 12.1, 9.8, 7.8, 5.9, 4.7, 3.7, 3.3])
# off['standalonePhoton'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# offrate['standalonePhoton'] =  array('d', [19600.1, 16897.1, 3420.1, 1038.1, 425.7, 222.5, 132.7, 84.9, 55.6, 38.3, 28.2, 21.0, 16.6, 13.1, 10.3, 7.7, 6.2, 4.5, 3.1, 2.6])
# onl['standalonePhoton'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# onlrate['standalonePhoton'] =  array('d', [2709.7, 1079.4, 554.3, 299.2, 161.0, 100.9, 69.9, 45.5, 32.4, 23.9, 18.4, 14.6, 11.3, 8.3, 6.6, 5.4, 3.8, 2.9, 2.2, 2.1])
# off['tkPhotonIsoBarrel'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# offrate['tkPhotonIsoBarrel'] =  array('d', [1867.0, 824.5, 462.7, 295.5, 158.1, 103.3, 74.2, 55.5, 37.1, 27.9, 23.0, 18.2, 15.3, 13.1, 10.2, 8.5, 6.9, 5.2, 4.2, 3.3])
# onl['tkPhotonIsoBarrel'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# onlrate['tkPhotonIsoBarrel'] =  array('d', [1063.1, 539.5, 333.1, 194.9, 114.5, 77.8, 59.9, 39.6, 29.6, 23.6, 18.9, 15.5, 13.1, 10.5, 8.7, 6.9, 5.3, 4.3, 3.3, 2.9])
# off['standalonePhotonBarrel'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# offrate['standalonePhotonBarrel'] =  array('d', [4951.0, 1523.5, 690.3, 382.4, 186.4, 107.4, 67.7, 45.1, 29.1, 19.9, 15.1, 11.2, 9.0, 7.2, 5.4, 4.4, 3.6, 2.7, 1.7, 1.6])
# onl['standalonePhotonBarrel'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# onlrate['standalonePhotonBarrel'] =  array('d', [1783.5, 774.8, 419.1, 226.1, 118.0, 73.2, 50.5, 32.1, 22.6, 16.3, 12.4, 9.8, 8.2, 6.0, 5.0, 4.1, 2.9, 2.2, 1.6, 1.5])
# off['tkPhotonIsoEndcap'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# offrate['tkPhotonIsoEndcap'] =  array('d', [7397.7, 2737.3, 524.1, 180.4, 85.2, 47.2, 30.3, 20.4, 14.7, 11.7, 8.2, 6.7, 5.4, 4.5, 3.4, 2.3, 1.6, 1.2, 0.9, 0.6])
# onl['tkPhotonIsoEndcap'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# onlrate['tkPhotonIsoEndcap'] =  array('d', [423.2, 149.7, 71.2, 41.0, 25.9, 17.7, 13.2, 9.9, 7.2, 5.9, 4.6, 3.6, 2.4, 1.7, 1.2, 0.9, 0.6, 0.4, 0.4, 0.4])
# off['standalonePhotonEndcap'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# offrate['standalonePhotonEndcap'] =  array('d', [17519.5, 16192.1, 2800.5, 666.9, 241.7, 115.8, 65.2, 39.8, 26.5, 18.4, 13.1, 9.8, 7.6, 6.0, 4.9, 3.3, 2.6, 1.8, 1.3, 0.9])
# onl['standalonePhotonEndcap'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
# onlrate['standalonePhotonEndcap'] =  array('d', [995.6, 317.0, 138.4, 74.2, 43.2, 27.7, 19.4, 13.4, 9.8, 7.6, 6.0, 4.7, 3.2, 2.3, 1.6, 1.3, 0.9, 0.6, 0.6, 0.6])




# off['puppiHT'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
# offrate['puppiHT'] =  array('d', [2224.7, 1198.3, 669.1, 382.6, 230.8, 142.4, 94.3, 64.7, 44.9, 32.5, 22.1, 16.1, 12.4, 10.2, 8.1, 6.2, 4.5, 3.4])
# onl['puppiHT'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
# onlrate['puppiHT'] =  array('d', [2657.2, 1553.3, 830.6, 461.6, 268.8, 160.8, 103.4, 69.7, 47.9, 33.5, 23.1, 16.1, 12.4, 10.2, 8.1, 5.9, 4.3, 3.2])
# off['puppiPhase1HT'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
# offrate['puppiPhase1HT'] =  array('d', [1925.8, 1171.2, 657.2, 383.0, 227.9, 143.4, 93.0, 65.1, 45.8, 31.6, 22.3, 16.7, 13.1, 10.0, 8.2, 6.1, 4.5, 3.8])
# onl['puppiPhase1HT'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
# onlrate['puppiPhase1HT'] =  array('d', [2131.7, 1253.0, 691.9, 395.0, 231.7, 143.3, 91.7, 63.9, 44.2, 30.2, 21.2, 15.9, 12.2, 9.7, 7.6, 5.7, 4.4, 3.6])
# off['trackerHT'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
# offrate['trackerHT'] =  array('d', [4445.5, 1961.5, 946.7, 500.9, 287.8, 177.7, 113.7, 77.7, 53.0, 38.0, 27.8, 21.1, 16.7, 13.6, 10.8, 8.1, 6.9, 5.5])
# onl['trackerHT'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
# onlrate['trackerHT'] =  array('d', [2808.5, 586.2, 182.0, 73.2, 34.1, 18.9, 11.3, 7.0, 4.4, 2.6, 1.4, 1.1, 0.9, 0.6, 0.6, 0.5, 0.4, 0.4])
# off['caloHT'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
# offrate['caloHT'] =  array('d', [7982.9, 6120.2, 4548.0, 3333.4, 2464.7, 1812.0, 1318.4, 956.4, 687.6, 484.5, 345.5, 242.8, 170.6, 118.2, 80.0, 53.7, 37.5, 24.7])
# onl['caloHT'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
# onlrate['caloHT'] =  array('d', [20441.3, 16137.6, 13490.9, 10284.4, 7663.8, 5925.7, 4486.2, 3324.9, 2492.0, 1855.7, 1371.8, 1009.5, 733.0, 530.8, 382.1, 273.7, 195.7, 138.2])
# off['puppiJet'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
# offrate['puppiJet'] =  array('d', [27200.2, 6870.5, 1949.4, 751.7, 338.5, 170.4, 92.4, 54.6, 32.7, 21.2, 13.0, 8.3, 6.2, 4.6, 3.4, 2.5, 1.9, 1.4, 1.3, 1.0])
# onl['puppiJet'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
# onlrate['puppiJet'] =  array('d', [3285.8, 938.8, 343.0, 148.9, 70.8, 37.9, 21.0, 12.3, 7.4, 5.2, 3.6, 2.3, 1.7, 1.4, 1.0, 0.7, 0.5, 0.4, 0.4, 0.4])
# off['puppiJetExt'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
# offrate['puppiJetExt'] =  array('d', [27568.9, 8450.2, 2939.7, 1331.0, 639.5, 330.6, 185.0, 111.3, 70.0, 46.1, 30.1, 21.1, 15.8, 12.5, 9.9, 7.8, 6.3, 4.9, 4.2, 3.4])
# onl['puppiJetExt'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
# onlrate['puppiJetExt'] =  array('d', [3982.4, 1150.0, 412.3, 177.2, 84.1, 45.1, 26.3, 16.3, 10.0, 6.9, 4.7, 3.2, 2.5, 1.9, 1.3, 0.7, 0.6, 0.4, 0.4, 0.4])
# off['puppiPhase1Jet'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
# offrate['puppiPhase1Jet'] =  array('d', [16323.8, 5363.9, 2084.7, 847.0, 393.1, 205.6, 115.5, 70.2, 45.9, 28.8, 18.3, 12.5, 8.2, 6.2, 4.9, 3.6, 2.6, 2.1, 1.8, 1.5])
# onl['puppiPhase1Jet'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
# onlrate['puppiPhase1Jet'] =  array('d', [2999.1, 890.8, 322.5, 140.0, 69.4, 37.1, 20.5, 11.6, 7.0, 5.2, 3.5, 2.2, 1.8, 1.3, 1.0, 0.8, 0.5, 0.4, 0.4, 0.4])
# off['puppiPhase1JetExt'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
# offrate['puppiPhase1JetExt'] =  array('d', [17492.9, 6543.3, 2936.6, 1401.4, 671.6, 346.3, 199.0, 120.6, 79.6, 51.6, 33.8, 24.1, 17.6, 13.9, 11.2, 8.9, 7.3, 6.2, 5.5, 5.0])
# onl['puppiPhase1JetExt'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
# onlrate['puppiPhase1JetExt'] =  array('d', [3597.3, 1068.3, 384.0, 166.7, 82.9, 44.9, 25.9, 16.2, 11.0, 8.2, 5.5, 3.9, 2.9, 2.2, 1.7, 1.2, 0.9, 0.5, 0.5, 0.5])
# off['trackerJet'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
# offrate['trackerJet'] =  array('d', [31036.4, 31036.4, 30914.8, 30680.3, 22387.4, 8426.2, 3885.6, 2065.0, 1190.8, 731.9, 474.6, 320.8, 221.4, 155.7, 111.9, 83.7, 63.9, 50.0, 38.1, 30.7])
# onl['trackerJet'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
# onlrate['trackerJet'] =  array('d', [501.6, 118.2, 37.6, 15.0, 7.8, 5.0, 3.9, 3.0, 1.6, 0.5, 0.5, 0.4, 0.4, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2])
# off['caloJet'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
# offrate['caloJet'] =  array('d', [31038.0, 31038.0, 26158.9, 5042.5, 947.8, 340.0, 159.3, 83.6, 47.2, 29.4, 18.6, 12.2, 7.5, 5.8, 3.8, 2.8, 2.1, 1.6, 1.2, 1.1])
# onl['caloJet'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
# onlrate['caloJet'] =  array('d', [12844.5, 1956.2, 538.8, 209.6, 92.5, 46.7, 27.0, 15.4, 8.6, 5.4, 3.7, 2.3, 1.5, 1.2, 1.1, 0.7, 0.5, 0.5, 0.3, 0.1])
# off['caloJetExt'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
# offrate['caloJetExt'] =  array('d', [31038.0, 31038.0, 26306.9, 5484.5, 1167.9, 448.8, 215.3, 112.9, 65.2, 39.2, 24.7, 16.0, 10.3, 7.7, 5.0, 3.5, 2.5, 2.1, 1.5, 1.4])
# onl['caloJetExt'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
# onlrate['caloJetExt'] =  array('d', [14707.9, 2359.7, 643.8, 242.8, 105.6, 51.5, 29.3, 16.7, 8.8, 5.5, 4.0, 2.6, 1.5, 1.2, 1.1, 0.7, 0.5, 0.5, 0.3, 0.1])
# off['HPSPFTau1'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
# offrate['HPSPFTau1'] =  array('d', [31031.0, 28203.3, 15063.7, 6260.3, 2730.0, 1392.9, 801.5, 504.9, 330.9, 227.4, 157.8, 117.2, 87.4, 67.1, 53.6, 41.9, 33.6, 26.4, 21.6, 17.8, 14.6, 12.3, 10.3, 8.8, 7.6, 6.5, 5.7, 4.4, 3.6, 3.1])
# onl['HPSPFTau1'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
# onlrate['HPSPFTau1'] =  array('d', [31035.3, 28386.5, 13935.1, 5145.2, 2171.0, 1114.8, 644.8, 408.7, 267.7, 183.6, 129.1, 95.1, 70.2, 55.1, 43.9, 32.7, 26.3, 21.0, 17.1, 14.0, 11.7, 9.9, 8.3, 7.3, 6.2, 5.0, 4.0, 3.5, 2.8, 2.5])
# off['HPSPFTau1Medium'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
# offrate['HPSPFTau1Medium'] =  array('d', [31034.4, 28625.1, 15003.9, 5611.4, 2280.6, 1130.5, 620.7, 391.8, 256.7, 177.5, 126.6, 96.6, 74.6, 59.3, 50.0, 39.3, 31.2, 24.6, 20.4, 16.9, 13.9, 11.5, 10.0, 8.3, 7.3, 6.3, 5.2, 3.9, 3.6, 2.8])
# onl['HPSPFTau1Medium'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
# onlrate['HPSPFTau1Medium'] =  array('d', [31035.0, 28143.8, 12978.2, 4472.5, 1807.4, 903.6, 514.8, 327.4, 214.5, 150.6, 109.5, 83.6, 64.6, 52.9, 43.9, 32.7, 26.3, 21.0, 17.1, 14.0, 11.7, 9.9, 8.3, 7.3, 6.2, 5.0, 4.0, 3.5, 2.8, 2.5])
# off['NNPuppiTauLoose'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
# offrate['NNPuppiTauLoose'] =  array('d', [2398.4, 1930.0, 1297.5, 744.4, 458.4, 301.2, 201.9, 140.6, 102.2, 78.1, 61.0, 48.8, 41.1, 33.6, 29.3, 25.6, 21.9, 18.6, 15.9, 14.6, 12.6, 11.2, 10.2, 9.4, 8.8, 8.2, 7.2, 6.4, 5.8, 5.2])
# onl['NNPuppiTauLoose'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
# onlrate['NNPuppiTauLoose'] =  array('d', [2642.1, 2627.8, 2147.7, 1211.4, 626.7, 353.1, 216.8, 141.6, 93.3, 66.6, 50.3, 39.8, 31.7, 25.5, 22.1, 17.6, 14.7, 13.0, 10.4, 9.3, 7.7, 6.4, 5.4, 4.7, 4.0, 3.4, 2.9, 2.7, 2.3, 2.1])
# off['NNPuppiTauTight'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
# offrate['NNPuppiTauTight'] =  array('d', [219.6, 219.6, 219.6, 218.1, 173.0, 119.6, 79.6, 57.0, 41.3, 31.7, 24.7, 18.8, 15.4, 12.0, 10.2, 8.8, 7.4, 6.2, 5.4, 5.0, 4.8, 4.7, 4.2, 4.0, 3.7, 3.7, 3.1, 2.6, 2.6, 2.4])
# onl['NNPuppiTauTight'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
# onlrate['NNPuppiTauTight'] =  array('d', [219.6, 219.5, 212.5, 190.4, 153.6, 110.0, 74.5, 51.5, 34.5, 24.6, 18.8, 15.6, 12.3, 10.0, 8.8, 7.0, 5.9, 5.2, 4.1, 3.7, 3.4, 3.0, 2.9, 2.6, 2.2, 1.9, 1.5, 1.4, 1.4, 1.2])
# off['TkEGTau'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
# offrate['TkEGTau'] =  array('d', [22722.2, 9511.6, 3934.6, 1701.9, 779.0, 391.1, 205.4, 118.8, 73.9, 47.4, 30.7, 20.4, 13.1, 9.5, 6.4, 4.7, 3.2, 1.9, 1.5, 1.1, 0.8, 0.7, 0.7, 0.6, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
# onl['TkEGTau'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
# onlrate['TkEGTau'] =  array('d', [21763.8, 8251.6, 3250.4, 1347.1, 608.0, 297.5, 157.8, 90.6, 54.8, 35.6, 22.2, 14.2, 9.3, 6.4, 3.9, 2.7, 1.7, 1.1, 1.0, 0.9, 0.7, 0.6, 0.6, 0.5, 0.5, 0.4, 0.3, 0.3, 0.3, 0.3])
# off['CaloTau'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
# offrate['CaloTau'] =  array('d', [30969.6, 27397.8, 16013.6, 7443.0, 3635.2, 1984.6, 1202.9, 782.2, 537.2, 387.0, 287.8, 212.9, 165.8, 130.5, 102.3, 82.1, 67.2, 55.3, 45.6, 38.5, 32.3, 27.4, 22.2, 18.3, 16.1, 14.0, 12.5, 10.8, 9.3, 8.0])
# onl['CaloTau'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
# onlrate['CaloTau'] =  array('d', [31037.9, 30775.5, 23728.5, 11433.2, 5007.4, 2421.7, 1341.6, 821.5, 539.3, 374.8, 268.8, 195.5, 147.8, 113.5, 88.8, 70.5, 56.5, 46.5, 37.9, 31.5, 25.2, 20.7, 16.8, 14.6, 12.8, 11.0, 9.3, 7.9, 6.9, 6.4])







# off['DiHPSPFTau1'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0])
# #offrate['DiHPSPFTau1'] =  array('d', [15961.6, 2444.7, 157.8, 25.1, 6.7, 2.6, 1.2, 0.7, 0.3, 0.2, 0.2, 0.1, 0.1, 0.0])
# #novtx
# offrate['DiHPSPFTau1'] =  array('d', [30924.1, 20045.5, 3943.7, 792.5, 261.7, 123.1, 63.9, 37.9, 23.7, 16.7, 11.3, 8.4, 6.4, 4.3])

# off['DiHPSPFTau1Medium'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0])
# #offrate['DiHPSPFTau1Medium'] =  array('d', [15731.8, 2522.2, 125.3, 16.3, 4.0, 1.4, 0.9, 0.3, 0.1, 0.1, 0.1, 0.0, 0.0, 0.0])
# #novtx
# offrate['DiHPSPFTau1Medium'] =  array('d', [30953.7, 20770.8, 3549.5, 561.5, 155.5, 69.5, 33.8, 19.8, 12.3, 8.5, 6.3, 5.2, 4.3, 3.3])

# off['DiNNPuppiTauLoose'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0])
# offrate['DiNNPuppiTauLoose'] =  array('d', [135.0, 94.5, 53.2, 25.3, 13.1, 7.8, 4.7, 3.4, 2.6, 2.3, 2.1, 1.9, 1.8, 1.8])

# off['DiNNPuppiTauTight'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0])
# offrate['DiNNPuppiTauTight'] =  array('d', [2.2, 2.2, 2.2, 2.2, 1.7, 0.9, 0.7, 0.4, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2])

# off['DiTkEGTau'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0])
# #offrate['DiTkEGTau'] =  array('d', [3655.4, 569.9, 150.5, 44.6, 13.8, 5.0, 2.4, 1.1, 0.3, 0.2, 0.1, 0.0, 0.0, 0.0])
# #novtx
# offrate['DiTkEGTau'] =  array('d', [10327.2, 1613.6, 333.9, 77.2, 20.6, 6.7, 3.2, 1.2, 0.4, 0.3, 0.1, 0.0, 0.0, 0.0])

# off['DiCaloTau'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0])
# offrate['DiCaloTau'] =  array('d', [30492.9, 19387.7, 5443.8, 1393.7, 516.0, 271.3, 164.4, 107.7, 74.7, 53.7, 38.8, 29.4, 23.7, 17.9])









# onl['DiHPSPFTau1'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0])
# onlrate['DiHPSPFTau1'] =  array('d', [15961.6, 2444.7, 157.8, 25.1, 6.7, 2.6, 1.2, 0.7, 0.3, 0.2, 0.2, 0.1, 0.1, 0.0])
# #novtx
# onlrate['DiHPSPFTau1'] =  array('d', [30924.1, 20045.5, 3943.7, 792.5, 261.7, 123.1, 63.9, 37.9, 23.7, 16.7, 11.3, 8.4, 6.4, 4.3])


# onl['DiHPSPFTau1Medium'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0])
# #onlrate['DiHPSPFTau1Medium'] =  array('d', [15731.8, 2522.2, 125.3, 16.3, 4.0, 1.4, 0.9, 0.3, 0.1, 0.1, 0.1, 0.0, 0.0, 0.0])
# #novtx
# onlrate['DiHPSPFTau1Medium'] =  array('d', [30953.7, 20770.8, 3549.5, 561.5, 155.5, 69.5, 33.8, 19.8, 12.3, 8.5, 6.3, 5.2, 4.3, 3.3])

# onl['DiNNPuppiTauLoose'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0])
# onlrate['DiNNPuppiTauLoose'] =  array('d', [135.0, 94.5, 53.2, 25.3, 13.1, 7.8, 4.7, 3.4, 2.6, 2.3, 2.1, 1.9, 1.8, 1.8])

# onl['DiNNPuppiTauTight'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0])
# onlrate['DiNNPuppiTauTight'] =  array('d', [2.2, 2.2, 2.2, 2.2, 1.7, 0.9, 0.7, 0.4, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2])

# onl['DiTkEGTau'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0])
# #onlrate['DiTkEGTau'] =  array('d', [3655.4, 569.9, 150.5, 44.6, 13.8, 5.0, 2.4, 1.1, 0.3, 0.2, 0.1, 0.0, 0.0, 0.0])
# #novtx
# onlrate['DiTkEGTau'] =  array('d', [10327.2, 1613.6, 333.9, 77.2, 20.6, 6.7, 3.2, 1.2, 0.4, 0.3, 0.1, 0.0, 0.0, 0.0])


# onl['DiCaloTau'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0])
# onlrate['DiCaloTau'] =  array('d', [30492.9, 19387.7, 5443.8, 1393.7, 516.0, 271.3, 164.4, 107.7, 74.7, 53.7, 38.8, 29.4, 23.7, 17.9])



############## For approval


off['tkMuon'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
offrate['tkMuon'] =  array('d', [11230.9, 9787.0, 1217.6, 270.7, 93.8, 42.2, 23.6, 13.9, 8.4, 5.1, 3.9, 3.2, 2.1, 1.8, 1.5, 1.3, 1.1, 1.0, 0.9, 0.9])
onl['tkMuon'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
onlrate['tkMuon'] =  array('d', [11230.9, 5012.5, 719.7, 182.4, 65.6, 34.2, 19.0, 10.5, 6.7, 4.3, 3.3, 2.3, 1.9, 1.5, 1.4, 1.1, 1.0, 0.9, 0.9, 0.8])

off['tkMuonStub'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
offrate['tkMuonStub'] =  array('d', [28416.9, 21678.0, 1334.9, 300.1, 106.8, 49.0, 26.6, 16.2, 10.3, 6.9, 5.2, 4.3, 3.1, 2.8, 2.3, 2.1, 1.7, 1.4, 1.4, 1.3])
onl['tkMuonStub'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
onlrate['tkMuonStub'] =  array('d', [28416.9, 9979.5, 806.4, 205.2, 74.4, 38.9, 21.5, 12.5, 8.5, 5.5, 4.4, 3.2, 2.8, 2.3, 2.2, 1.7, 1.4, 1.4, 1.3, 1.3])
off['standaloneMuon'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
offrate['standaloneMuon'] =  array('d', [15048.8, 13635.6, 3007.3, 1247.1, 501.4, 225.8, 112.5, 76.6, 59.3, 48.7, 42.4, 33.6, 29.7, 25.1, 22.8, 21.5, 19.0, 18.1, 17.1, 15.8])
onl['standaloneMuon'] =  array('d', [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0])
onlrate['standaloneMuon'] =  array('d', [15048.8, 5231.0, 1343.3, 405.0, 195.3, 97.2, 70.7, 50.9, 45.8, 34.3, 31.8, 25.2, 20.7, 20.1, 18.3, 17.8, 15.8, 13.7, 13.2, 12.8])
off['tkElectron'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
offrate['tkElectron'] =  array('d', [884.4, 570.6, 334.0, 201.8, 112.9, 76.9, 55.2, 40.5, 27.3, 22.5, 17.4, 14.0, 11.8, 9.5, 7.4, 6.2, 5.3, 4.2, 3.5, 3.2])
onl['tkElectron'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
onlrate['tkElectron'] =  array('d', [618.0, 330.4, 194.2, 114.3, 68.1, 47.9, 35.9, 23.9, 19.2, 14.3, 11.3, 9.6, 7.4, 5.6, 4.6, 4.2, 3.3, 2.9, 2.3, 2.1])
off['tkIsoElectron'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
offrate['tkIsoElectron'] =  array('d', [470.6, 281.0, 151.7, 92.9, 51.8, 35.7, 27.2, 20.5, 14.5, 12.3, 10.6, 8.6, 7.5, 6.4, 5.5, 4.7, 3.6, 3.0, 2.3, 2.0])
onl['tkIsoElectron'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
onlrate['tkIsoElectron'] =  array('d', [301.4, 153.7, 87.0, 53.6, 32.3, 22.5, 17.9, 13.2, 11.0, 8.8, 6.9, 6.0, 5.0, 4.3, 3.5, 3.1, 2.4, 1.8, 1.4, 1.4])
off['standaloneElectron'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
offrate['standaloneElectron'] =  array('d', [21719.7, 19089.8, 5527.7, 1862.3, 887.7, 431.0, 264.0, 173.0, 114.4, 78.7, 58.4, 44.8, 34.6, 28.0, 22.7, 18.2, 14.0, 11.3, 8.7, 7.0])
onl['standaloneElectron'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
onlrate['standaloneElectron'] =  array('d', [4287.3, 1887.4, 998.8, 535.8, 285.0, 182.6, 130.1, 80.8, 58.7, 44.7, 34.3, 27.5, 21.3, 16.6, 13.1, 10.8, 7.9, 6.3, 4.9, 4.5])
off['standaloneElectronExt'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
offrate['standaloneElectronExt'] =  array('d', [25587.9, 21709.3, 6607.4, 2224.5, 1047.6, 514.7, 313.2, 204.0, 135.6, 94.0, 70.3, 54.5, 41.8, 34.3, 27.8, 22.5, 17.6, 14.1, 11.0, 9.1])
onl['standaloneElectronExt'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
onlrate['standaloneElectronExt'] =  array('d', [4706.1, 2035.2, 1065.7, 571.3, 306.8, 196.9, 140.6, 88.2, 64.8, 49.3, 38.2, 30.4, 23.7, 18.6, 14.5, 12.0, 8.9, 7.2, 5.7, 5.2])
off['tkPhotonIso'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
offrate['tkPhotonIso'] =  array('d', [8825.4, 3482.5, 978.1, 474.4, 243.0, 150.3, 104.5, 76.1, 52.0, 39.4, 31.0, 24.8, 20.5, 17.4, 13.4, 10.7, 8.3, 6.3, 5.1, 3.8])
onl['tkPhotonIso'] =  array('d', [10.0, 13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0, 58.0, 61.0, 64.0, 67.0])
onlrate['tkPhotonIso'] =  array('d', [1470.2, 686.1, 403.9, 235.8, 140.4, 95.7, 73.4, 49.7, 36.7, 29.4, 23.5, 19.0, 15.3, 12.0, 9.8, 7.7, 5.9, 4.7, 3.7, 3.2])
off['puppiPhase1HT'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
offrate['puppiPhase1HT'] =  array('d', [31038.0, 5536.7, 4481.5, 1790.8, 1099.2, 629.6, 372.8, 226.0, 143.9, 94.2, 66.4, 47.5, 32.7, 23.5, 17.4, 13.8, 10.5, 8.5])
onl['puppiPhase1HT'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
onlrate['puppiPhase1HT'] =  array('d', [2133.6, 1254.3, 692.4, 395.6, 232.4, 143.8, 91.7, 63.8, 44.1, 30.2, 21.2, 15.8, 12.2, 9.6, 7.6, 5.7, 4.3, 3.5])
off['trackerHT'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
offrate['trackerHT'] =  array('d', [27857.3, 17890.9, 9170.4, 4480.2, 2252.9, 1212.2, 693.2, 420.3, 266.3, 179.7, 123.8, 88.4, 64.4, 48.1, 36.7, 28.2, 22.2, 18.4])
onl['trackerHT'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
onlrate['trackerHT'] =  array('d', [2809.5, 586.8, 182.1, 73.1, 34.2, 18.8, 11.3, 7.0, 4.4, 2.6, 1.4, 1.1, 0.9, 0.6, 0.6, 0.5, 0.4, 0.4])
off['caloHT'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
offrate['caloHT'] =  array('d', [20275.1, 15173.6, 12163.9, 9764.8, 7278.0, 5558.7, 4265.6, 3188.0, 2398.7, 1801.8, 1339.2, 991.8, 726.1, 529.6, 383.7, 278.1, 200.6, 141.6])
onl['caloHT'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
onlrate['caloHT'] =  array('d', [20439.3, 16139.0, 13494.1, 10286.9, 7665.9, 5926.6, 4486.9, 3323.6, 2492.4, 1855.9, 1372.6, 1009.7, 732.9, 531.0, 381.5, 273.6, 195.6, 137.9])
off['puppiMET'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
offrate['puppiMET'] =  array('d', [31038.0, 13791.6, 2921.4, 620.2, 156.9, 48.3, 18.1, 9.2, 5.3, 3.4, 2.2, 1.8, 1.5, 1.3, 1.0, 0.7, 0.6, 0.5])
onl['puppiMET'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
onlrate['puppiMET'] =  array('d', [837.2, 127.7, 27.6, 9.7, 4.8, 2.8, 1.8, 1.5, 1.1, 0.7, 0.5, 0.5, 0.4, 0.3, 0.3, 0.2, 0.1, 0.1])
off['trackerMET'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
offrate['trackerMET'] =  array('d', [13268.1, 8221.6, 4763.9, 2641.6, 1442.3, 792.3, 439.4, 255.7, 152.8, 96.2, 63.0, 44.5, 30.9, 23.1, 16.9, 13.5, 11.0, 8.9])
onl['trackerMET'] =  array('d', [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0])
onlrate['trackerMET'] =  array('d', [162.4, 22.8, 7.7, 4.4, 3.0, 2.4, 0.9, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.1, 0.1, 0.1])
off['puppiPhase1Jet'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
offrate['puppiPhase1Jet'] =  array('d', [16324.4, 5363.9, 2085.5, 847.5, 393.2, 205.5, 115.6, 70.1, 45.7, 28.8, 18.3, 12.5, 8.2, 6.2, 4.9, 3.6, 2.6, 2.1, 1.8, 1.5])
onl['puppiPhase1Jet'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
onlrate['puppiPhase1Jet'] =  array('d', [3001.4, 892.0, 322.6, 140.0, 69.1, 37.2, 20.5, 11.6, 7.1, 5.2, 3.5, 2.2, 1.8, 1.3, 1.0, 0.8, 0.5, 0.4, 0.4, 0.4])
off['puppiPhase1JetExt'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
offrate['puppiPhase1JetExt'] =  array('d', [17492.9, 6541.9, 2936.1, 1401.1, 670.8, 345.8, 198.3, 119.9, 78.9, 51.1, 33.5, 23.9, 17.5, 13.8, 11.1, 8.9, 7.2, 6.2, 5.5, 5.0])
onl['puppiPhase1JetExt'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
onlrate['puppiPhase1JetExt'] =  array('d', [3599.0, 1068.7, 383.3, 166.2, 82.5, 44.8, 25.8, 16.2, 11.0, 8.2, 5.5, 4.0, 3.0, 2.2, 1.8, 1.3, 0.9, 0.5, 0.5, 0.5])
off['trackerJet'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
offrate['trackerJet'] =  array('d', [31036.5, 31036.5, 30915.7, 30680.9, 22388.0, 8428.3, 3884.0, 2065.0, 1190.5, 731.1, 474.2, 320.4, 221.5, 156.0, 112.2, 84.1, 64.2, 50.1, 38.1, 30.6])
onl['trackerJet'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
onlrate['trackerJet'] =  array('d', [501.4, 118.3, 37.5, 15.1, 7.8, 5.0, 3.9, 3.0, 1.6, 0.5, 0.5, 0.4, 0.4, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3])
off['caloJet'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
offrate['caloJet'] =  array('d', [31038.0, 31038.0, 26155.6, 5045.0, 948.3, 340.7, 159.3, 83.5, 47.2, 29.5, 18.6, 12.2, 7.5, 5.8, 3.8, 2.8, 2.1, 1.6, 1.2, 1.1])
onl['caloJet'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
onlrate['caloJet'] =  array('d', [12842.3, 1955.9, 539.3, 209.7, 92.6, 46.7, 27.1, 15.5, 8.6, 5.4, 3.7, 2.3, 1.5, 1.2, 1.1, 0.8, 0.5, 0.5, 0.3, 0.1])
off['caloJetExt'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
offrate['caloJetExt'] =  array('d', [31038.0, 31038.0, 26303.9, 5485.8, 1167.2, 449.1, 214.9, 112.4, 65.1, 39.4, 24.8, 16.1, 10.5, 7.7, 5.0, 3.5, 2.5, 2.1, 1.5, 1.4])
onl['caloJetExt'] =  array('d', [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0, 340.0, 360.0, 380.0, 400.0, 420.0])
onlrate['caloJetExt'] =  array('d', [14705.0, 2358.7, 643.6, 242.6, 105.7, 51.5, 29.5, 16.9, 8.9, 5.5, 4.0, 2.6, 1.5, 1.2, 1.1, 0.8, 0.5, 0.5, 0.3, 0.1])
off['HPSPFTau1'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
offrate['HPSPFTau1'] =  array('d', [31035.9, 30959.8, 30256.7, 27248.2, 20953.9, 13612.0, 8332.0, 5186.0, 3274.6, 2132.8, 1468.2, 1070.7, 801.3, 619.1, 485.6, 390.2, 312.9, 257.0, 210.8, 174.5, 147.6, 124.3, 107.8, 92.9, 77.9, 68.0, 59.8, 54.0, 48.1, 43.0])
onl['HPSPFTau1'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
onlrate['HPSPFTau1'] =  array('d', [31035.4, 28388.8, 13940.1, 5145.3, 2169.4, 1114.7, 645.0, 409.1, 268.3, 183.8, 129.2, 95.3, 70.3, 55.4, 44.1, 32.9, 26.6, 21.2, 17.3, 14.2, 11.8, 10.1, 8.5, 7.4, 6.3, 5.1, 4.0, 3.5, 2.8, 2.5])
off['HPSPFTau1Medium'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
offrate['HPSPFTau1Medium'] =  array('d', [31037.8, 31031.8, 30773.1, 29458.8, 25268.7, 17652.4, 9527.8, 4973.1, 2737.6, 1668.2, 1069.4, 727.1, 519.6, 392.0, 301.7, 235.3, 191.5, 153.6, 127.2, 105.7, 90.9, 78.7, 67.5, 59.3, 52.8, 47.6, 42.1, 35.1, 30.9, 27.0])
onl['HPSPFTau1Medium'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
onlrate['HPSPFTau1Medium'] =  array('d', [31035.0, 28146.7, 12982.5, 4472.2, 1805.5, 903.4, 514.9, 327.8, 215.2, 150.8, 109.6, 83.8, 64.7, 53.2, 44.1, 32.9, 26.6, 21.2, 17.3, 14.2, 11.8, 10.1, 8.5, 7.4, 6.3, 5.1, 4.0, 3.5, 2.8, 2.5])
off['NNPuppiTauLoose'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
offrate['NNPuppiTauLoose'] =  array('d', [2406.3, 2182.7, 1846.7, 1449.3, 1049.6, 726.3, 525.7, 387.3, 294.1, 224.5, 179.0, 141.8, 115.2, 93.5, 79.0, 69.1, 58.7, 50.9, 44.7, 39.4, 35.3, 31.0, 28.4, 25.8, 23.4, 21.3, 19.1, 17.6, 16.3, 15.4])
onl['NNPuppiTauLoose'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
onlrate['NNPuppiTauLoose'] =  array('d', [2644.3, 2629.9, 2150.0, 1213.0, 626.8, 353.2, 217.3, 142.1, 93.9, 66.9, 50.6, 40.0, 31.7, 25.7, 22.2, 17.8, 14.8, 13.1, 10.5, 9.3, 7.7, 6.5, 5.5, 4.8, 4.0, 3.5, 2.9, 2.7, 2.3, 2.1])
off['NNPuppiTauTight'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
offrate['NNPuppiTauTight'] =  array('d', [218.9, 218.9, 218.9, 218.9, 208.2, 187.4, 152.7, 120.6, 92.9, 73.6, 59.1, 48.3, 38.6, 34.3, 29.5, 24.9, 21.6, 18.5, 15.9, 13.4, 11.3, 10.3, 9.5, 8.5, 8.0, 7.3, 6.5, 6.2, 5.9, 5.5])
onl['NNPuppiTauTight'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
onlrate['NNPuppiTauTight'] =  array('d', [218.9, 218.8, 211.7, 189.4, 153.0, 109.6, 74.4, 51.8, 34.6, 24.6, 18.9, 15.7, 12.4, 10.1, 8.9, 7.1, 5.9, 5.3, 4.2, 3.8, 3.4, 3.0, 2.9, 2.6, 2.2, 2.0, 1.5, 1.4, 1.4, 1.2])
off['TkEGTau'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
offrate['TkEGTau'] =  array('d', [29720.4, 26159.3, 20596.4, 15055.1, 10640.5, 7521.9, 5403.9, 3967.9, 2967.1, 2276.9, 1758.1, 1383.1, 1093.4, 870.2, 707.8, 579.2, 479.6, 404.8, 337.2, 285.8, 241.4, 206.4, 178.7, 156.8, 136.6, 120.7, 107.1, 95.9, 85.5, 76.0])
onl['TkEGTau'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
onlrate['TkEGTau'] =  array('d', [21763.8, 8253.0, 3253.5, 1347.4, 608.1, 298.1, 158.1, 90.9, 55.0, 35.8, 22.4, 14.2, 9.3, 6.2, 3.8, 2.6, 1.6, 0.9, 0.9, 0.8, 0.6, 0.5, 0.5, 0.4, 0.4, 0.4, 0.3, 0.3, 0.3, 0.3])
off['CaloTau'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
offrate['CaloTau'] =  array('d', [31037.9, 31037.6, 30857.6, 27058.4, 17349.8, 9348.6, 5053.3, 2881.1, 1778.3, 1179.3, 826.7, 601.5, 450.0, 345.6, 271.4, 211.1, 171.7, 139.3, 114.4, 93.6, 78.7, 66.1, 56.7, 48.0, 41.4, 36.2, 31.0, 26.8, 22.7, 19.1])
onl['CaloTau'] =  array('d', [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0])
onlrate['CaloTau'] =  array('d', [31037.9, 30775.8, 23729.0, 11431.6, 5007.3, 2421.8, 1342.8, 822.4, 540.0, 375.5, 269.2, 195.9, 147.9, 113.5, 88.8, 70.5, 56.4, 46.5, 37.8, 31.4, 25.1, 20.5, 16.6, 14.6, 12.8, 11.1, 9.3, 7.9, 6.9, 6.4])






for obj in list_calc:

  off[obj] = array('d',[])
  offrate[obj] = array('d',[])
  onl[obj] = array('d',[])
  onlrate[obj] = array('d',[])
  
  x = cutrange[obj][0]
  while (x<cutrange[obj][1]):


########################################
#######################################


    if (obj=='tkMuon'):
      offlinescalingcut = "( (abs(tkMuonEta[])<0.83 && tkMuonPt[]>("+str(TkMuonOfflineEtCutBarrel(x))+")) || (abs(tkMuonEta[])<1.24 && abs(tkMuonEta[])>0.83 && tkMuonPt[]>("+str(TkMuonOfflineEtCutOverlap(x))+")) || (abs(tkMuonEta[])>1.24 && tkMuonPt[]>("+str(TkMuonOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && tkMuonBx[]==0  && abs(tkMuonEta[])<2.4)>0"
      onlinecut  = "Sum$( tkMuonPt[]>"+str(x)+" && tkMuonBx[]==0  && abs(tkMuonEta[])<2.4)>0"

    if (obj=='tkMuonStub'):
      offlinescalingcut = "( (abs(tkMuonStubsEta[])<0.83 && tkMuonStubsPt[]>("+str(TkMuonStubOfflineEtCutBarrel(x))+")) || (abs(tkMuonStubsEta[])<1.24 && abs(tkMuonStubsEta[])>0.83 && tkMuonStubsPt[]>("+str(TkMuonStubOfflineEtCutOverlap(x))+")) || (abs(tkMuonStubsEta[])>1.24 && tkMuonStubsPt[]>("+str(TkMuonStubOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && tkMuonStubsBx[]==0 && abs(tkMuonStubsEta[])<2.4)>0"
      onlinecut  = "Sum$( tkMuonStubsPt[]>"+str(x)+" && tkMuonStubsBx[]==0 && abs(tkMuonStubsEta[])<2.4)>0"


    if (obj=='tkMuonStubExt'):
      offlinescalingcut = "( (abs(tkMuonStubsEta[])<0.83 && tkMuonStubsPt[]>("+str(TkMuonStubOfflineEtCutBarrel(x))+")) || (abs(tkMuonStubsEta[])<1.24 && abs(tkMuonStubsEta[])>0.83 && tkMuonStubsPt[]>("+str(TkMuonStubOfflineEtCutOverlap(x))+")) || (abs(tkMuonStubsEta[])>1.24 && abs(tkMuonStubsEta[])<2.4 && tkMuonStubsPt[]>("+str(TkMuonStubOfflineEtCutEndcap(x))+")) || (abs(tkMuonStubsEta[])>2.4 && tkMuonStubsPt[]>("+str(TkMuonStubOfflineEtCutForward(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && tkMuonStubsBx[]==0 && abs(tkMuonStubsEta[])<2.8)>0"
      onlinecut  = "Sum$( tkMuonStubsPt[]>"+str(x)+" && tkMuonStubsBx[]==0 && abs(tkMuonStubsEta[])<2.8)>0"
  

    if (obj=='standaloneMuon'):
      offlinescalingcut = "( (abs(standaloneMuonEta[])<0.83 && standaloneMuonPt[]>("+str(StandaloneMuonOfflineEtCutBarrel(x))+")) || (abs(standaloneMuonEta[])<1.24 && abs(standaloneMuonEta[])>0.83 && standaloneMuonPt[]>("+str(StandaloneMuonOfflineEtCutOverlap(x))+")) || (abs(standaloneMuonEta[])>1.24 && standaloneMuonPt[]>("+str(StandaloneMuonOfflineEtCutEndcap(x))+")) )"
      qualitycut = "( (abs(standaloneMuonEta[])<0.83 && standaloneMuonQual[]>=0 && standaloneMuonRegion[]==1) || (abs(standaloneMuonEta[])<1.24 && abs(standaloneMuonEta[])>0.83 && standaloneMuonQual[]>=12 && standaloneMuonRegion[]==2) || (abs(standaloneMuonEta[])>1.24 && standaloneMuonQual[]>=0 && standaloneMuonRegion[]==3))"
      offlinecut = "Sum$( "+offlinescalingcut+" && "+qualitycut+" && standaloneMuonBx[]==0  && abs(standaloneMuonEta[])<2.4)>0"
      onlinecut  = "Sum$( "+qualitycut+" && standaloneMuonPt[]>"+str(x)+" && standaloneMuonBx[]==0  && abs(standaloneMuonEta[])<2.4)>0"
      

    if (obj=='tkMuonBarrel'):
      offlinescalingcut = "(tkMuonPt[]>("+str(TkMuonOfflineEtCutBarrel(x))+"))"
      offlinecut = "Sum$( "+offlinescalingcut+" && tkMuonBx[]==0  && abs(tkMuonEta[])<0.83)>0"
      onlinecut  = "Sum$( tkMuonPt[]>"+str(x)+" && tkMuonBx[]==0  && abs(tkMuonEta[])<0.83)>0"

    if (obj=='tkMuonStubBarrel'):
      offlinescalingcut = "(tkMuonStubsPt[]>("+str(TkMuonStubOfflineEtCutBarrel(x))+"))"
      offlinecut = "Sum$( "+offlinescalingcut+" && tkMuonStubsBx[]==0 && abs(tkMuonStubsEta[])<0.83)>0"
      onlinecut  = "Sum$( tkMuonStubsPt[]>"+str(x)+" && tkMuonStubsBx[]==0 && abs(tkMuonStubsEta[])<0.83)>0"

    if (obj=='standaloneMuonBarrel'):
      offlinescalingcut = "(standaloneMuonPt[]>("+str(StandaloneMuonOfflineEtCutBarrel(x))+"))"
      offlinecut = "Sum$( "+offlinescalingcut+" && standaloneMuonBx[]==0  && abs(standaloneMuonEta[])<0.83)>0"
      onlinecut  = "Sum$( standaloneMuonPt[]>"+str(x)+" && standaloneMuonBx[]==0  && abs(standaloneMuonEta[])<0.83)>0"

    if (obj=='tkMuonOverlap'):
      offlinescalingcut = "(tkMuonPt[]>("+str(TkMuonOfflineEtCutOverlap(x))+"))"
      offlinecut = "Sum$( "+offlinescalingcut+" && tkMuonBx[]==0  && abs(tkMuonEta[])>0.83 && abs(tkMuonEta[])<1.24)>0"
      onlinecut  = "Sum$( tkMuonPt[]>"+str(x)+" && tkMuonBx[]==0  && abs(tkMuonEta[])>0.83 && abs(tkMuonEta[])<1.24)>0"

    if (obj=='tkMuonStubOverlap'):
      offlinescalingcut = "(tkMuonStubsPt[]>("+str(TkMuonStubOfflineEtCutOverlap(x))+"))"
      offlinecut = "Sum$( "+offlinescalingcut+" && tkMuonStubsBx[]==0 && abs(tkMuonStubsEta[])>0.83 && abs(tkMuonStubsEta[])<1.24)>0"
      onlinecut  = "Sum$( tkMuonStubsPt[]>"+str(x)+" && tkMuonStubsBx[]==0 && abs(tkMuonStubsEta[])>0.83 && abs(tkMuonStubsEta[])<1.24)>0"

    if (obj=='standaloneMuonOverlap'):
      offlinescalingcut = "(standaloneMuonPt[]>("+str(StandaloneMuonOfflineEtCutOverlap(x))+"))"
      offlinecut = "Sum$( "+offlinescalingcut+" && standaloneMuonBx[]==0  && standaloneMuonQual[]>=12 && abs(standaloneMuonEta[])>0.83 && abs(standaloneMuonEta[])<1.24)>0"
      onlinecut  = "Sum$( standaloneMuonPt[]>"+str(x)+" && standaloneMuonBx[]==0  && standaloneMuonQual[]>=12 && abs(standaloneMuonEta[])>0.83 && abs(standaloneMuonEta[])<1.24)>0"

    if (obj=='tkMuonEndcap'):
      offlinescalingcut = "(tkMuonPt[]>("+str(TkMuonOfflineEtCutEndcap(x))+"))"
      offlinecut = "Sum$( "+offlinescalingcut+" && tkMuonBx[]==0  && abs(tkMuonEta[])>1.24 && abs(tkMuonEta[])<2.4)>0"
      onlinecut  = "Sum$( tkMuonPt[]>"+str(x)+" && tkMuonBx[]==0  && abs(tkMuonEta[])>1.24 && abs(tkMuonEta[])<2.4)>0"

    if (obj=='tkMuonStubEndcap'):
      offlinescalingcut = "(tkMuonStubsPt[]>("+str(TkMuonStubOfflineEtCutEndcap(x))+"))"
      offlinecut = "Sum$( "+offlinescalingcut+" && tkMuonStubsBx[]==0 && abs(tkMuonStubsEta[])>1.24 && abs(tkMuonStubsEta[])<2.4)>0"
      onlinecut  = "Sum$( tkMuonStubsPt[]>"+str(x)+" && tkMuonStubsBx[]==0 && abs(tkMuonStubsEta[])>1.24 && abs(tkMuonStubsEta[])<2.4)>0"

    if (obj=='standaloneMuonEndcap'):
      offlinescalingcut = "(standaloneMuonPt[]>("+str(StandaloneMuonOfflineEtCutEndcap(x))+"))"
      offlinecut = "Sum$( "+offlinescalingcut+" && standaloneMuonBx[]==0  && abs(standaloneMuonEta[])>1.24 && abs(standaloneMuonEta[])<2.4)>0"
      onlinecut  = "Sum$( standaloneMuonPt[]>"+str(x)+" && standaloneMuonBx[]==0  && abs(standaloneMuonEta[])>1.24 && abs(standaloneMuonEta[])<2.4)>0"
  

    #### Still displaced and extended Eta missing

    # if (obj=='displacedMuonBarrel'):
    #   offlinescalingcut = "(standaloneMuonPt2[]>("+str(StandaloneDisplacedMuonOfflineEtCut(x))+"))"
    #   offlinecut = "Sum$( "+offlinescalingcut+" && standaloneMuonBx[]==0  && abs(standaloneMuonEta[])<0.83)>0"
    #   onlinecut  = "Sum$( standaloneMuonPt2[]>"+str(x)+" && standaloneMuonBx[]==0  && abs(standaloneMuonEta[])<0.83)>0"



#######################################


    if (obj=='tkElectron'):
      offlinescalingcut = "( (abs(tkElectronV2Eta[])<1.479 && tkElectronV2Et[]>("+str(TkElectronOfflineEtCutBarrel(x))+")) || (abs(tkElectronV2Eta[])>1.479 && tkElectronV2Et[]>("+str(TkElectronOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && tkElectronV2Bx[]==0 && tkElectronV2PassesLooseTrackID[] && abs(tkElectronV2Eta[])<2.4)>0"
      onlinecut  = "Sum$( tkElectronV2Et[]>"+str(x)+" && tkElectronV2Bx[]==0 && tkElectronV2PassesLooseTrackID[] && abs(tkElectronV2Eta[])<2.4)>0"

    if (obj=='tkIsoElectron'):
      offlinescalingcut = "( (abs(tkElectronV2Eta[])<1.479 && tkElectronV2Et[]>("+str(TkIsoElectronOfflineEtCutBarrel(x))+") && tkElectronV2TrkIso[]<0.10) || (abs(tkElectronV2Eta[])>1.479 && tkElectronV2Et[]>("+str(TkIsoElectronOfflineEtCutEndcap(x))+") && tkElectronV2TrkIso[]<0.125 && tkElectronV2HwQual[]==5) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && tkElectronV2Bx[]==0 &&  abs(tkElectronV2Eta[])<2.4)>0"
      onlinecut  = "Sum$( ((abs(tkElectronV2Eta[])<1.479 && tkElectronV2Et[]>("+str(x)+") && tkElectronV2TrkIso[]<0.10) || (abs(tkElectronV2Eta[])>1.479 && tkElectronV2Et[]>("+str(x)+") && tkElectronV2TrkIso[]<0.125 && tkElectronV2HwQual[]==5)) && tkElectronV2Bx[]==0 && abs(tkElectronV2Eta[])<2.4)>0"

    if (obj=='standaloneElectron'):
      offlinescalingcut = "( (abs(EGEta[])<1.479 && EGEt[]>("+str(StandaloneElectronOfflineEtCutBarrel(x))+")) || (abs(EGEta[])>1.479 && EGEt[]>("+str(StandaloneElectronOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && EGBx[]==0 && EGPassesLooseTrackID[] && abs(EGEta[])<2.4)>0"
      onlinecut  = "Sum$( EGEt[]>"+str(x)+" && EGBx[]==0 && EGPassesLooseTrackID[] && abs(EGEta[])<2.4)>0"

    if (obj=='standaloneElectronExt'):
      offlinescalingcut = "( (abs(EGEta[])<1.479 && EGEt[]>("+str(StandaloneElectronOfflineEtCutBarrel(x))+")) || (abs(EGEta[])>1.479 && abs(EGEta[])<2.4 && EGEt[]>("+str(StandaloneElectronOfflineEtCutEndcap(x))+")) || (abs(EGEta[])>2.4 && EGEt[]>("+str(StandaloneElectronOfflineEtCutForward(x))+")))"
      offlinecut = "Sum$( "+offlinescalingcut+" && EGBx[]==0 && EGPassesLooseTrackID[] && abs(EGEta[])<3)>0"
      onlinecut  = "Sum$( EGEt[]>"+str(x)+" && EGBx[]==0 && EGPassesLooseTrackID[] && abs(EGEta[])<3)>0"

    
    if (obj=='tkElectronBarrel'):
      offlinescalingcut = "( (abs(tkElectronV2Eta[])<1.479 && tkElectronV2Et[]>("+str(TkElectronOfflineEtCutBarrel(x))+")) || (abs(tkElectronV2Eta[])>1.479 && tkElectronV2Et[]>("+str(TkElectronOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && tkElectronV2Bx[]==0 && tkElectronV2PassesLooseTrackID[] && abs(tkElectronV2Eta[])<1.479)>0"
      onlinecut  = "Sum$( tkElectronV2Et[]>"+str(x)+" && tkElectronV2Bx[]==0 && tkElectronV2PassesLooseTrackID[] && abs(tkElectronV2Eta[])<1.479)>0"

    if (obj=='tkIsoElectronBarrel'):
      offlinescalingcut = "( (abs(tkElectronV2Eta[])<1.479 && tkElectronV2Et[]>("+str(TkIsoElectronOfflineEtCutBarrel(x))+") && tkElectronV2TrkIso[]<0.10) || (abs(tkElectronV2Eta[])>1.479 && tkElectronV2Et[]>("+str(TkIsoElectronOfflineEtCutEndcap(x))+") && tkElectronV2TrkIso[]<0.125 && tkElectronV2HwQual[]==5) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && tkElectronV2Bx[]==0 &&  abs(tkElectronV2Eta[])<1.479)>0"
      onlinecut  = "Sum$( ((abs(tkElectronV2Eta[])<1.479 && tkElectronV2Et[]>("+str(x)+") && tkElectronV2TrkIso[]<0.10) || (abs(tkElectronV2Eta[])>1.479 && tkElectronV2Et[]>("+str(x)+") && tkElectronV2TrkIso[]<0.125 && tkElectronV2HwQual[]==5)) && tkElectronV2Bx[]==0 && abs(tkElectronV2Eta[])<1.479)>0"

    if (obj=='standaloneElectronBarrel'):
      offlinescalingcut = "( (abs(EGEta[])<1.479 && EGEt[]>("+str(StandaloneElectronOfflineEtCutBarrel(x))+")) || (abs(EGEta[])>1.479 && EGEt[]>("+str(StandaloneElectronOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && EGBx[]==0 && EGPassesLooseTrackID[] && abs(EGEta[])<1.479)>0"
      onlinecut  = "Sum$( EGEt[]>"+str(x)+" && EGBx[]==0 && EGPassesLooseTrackID[] && abs(EGEta[])<1.479)>0"


    if (obj=='tkElectronEndcap'):
      offlinescalingcut = "( (abs(tkElectronV2Eta[])<1.479 && tkElectronV2Et[]>("+str(TkElectronOfflineEtCutBarrel(x))+")) || (abs(tkElectronV2Eta[])>1.479 && tkElectronV2Et[]>("+str(TkElectronOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && tkElectronV2Bx[]==0 && tkElectronV2PassesLooseTrackID[] && abs(tkElectronV2Eta[])>1.479 && abs(tkElectronV2Eta[])<2.4)>0"
      onlinecut  = "Sum$( tkElectronV2Et[]>"+str(x)+" && tkElectronV2Bx[]==0 && tkElectronV2PassesLooseTrackID[] && abs(tkElectronV2Eta[])>1.479 && abs(tkElectronV2Eta[])<2.4)>0"

    if (obj=='tkIsoElectronEndcap'):
      offlinescalingcut = "( (abs(tkElectronV2Eta[])<1.479 && tkElectronV2Et[]>("+str(TkIsoElectronOfflineEtCutBarrel(x))+") && tkElectronV2TrkIso[]<0.10) || (abs(tkElectronV2Eta[])>1.479 && tkElectronV2Et[]>("+str(TkIsoElectronOfflineEtCutEndcap(x))+") && tkElectronV2TrkIso[]<0.125 && tkElectronV2HwQual[]==5) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && tkElectronV2Bx[]==0 &&  abs(tkElectronV2Eta[])>1.479 && abs(tkElectronV2Eta[])<2.4)>0"
      onlinecut  = "Sum$( ((abs(tkElectronV2Eta[])<1.479 && tkElectronV2Et[]>("+str(x)+") && tkElectronV2TrkIso[]<0.10) || (abs(tkElectronV2Eta[])>1.479 && tkElectronV2Et[]>("+str(x)+") && tkElectronV2TrkIso[]<0.125 && tkElectronV2HwQual[]==5)) && tkElectronV2Bx[]==0 && abs(tkElectronV2Eta[])>1.479 && abs(tkElectronV2Eta[])<2.4)>0"

    if (obj=='standaloneElectronEndcap'):
      offlinescalingcut = "( (abs(EGEta[])<1.479 && EGEt[]>("+str(StandaloneElectronOfflineEtCutBarrel(x))+")) || (abs(EGEta[])>1.479 && EGEt[]>("+str(StandaloneElectronOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && EGBx[]==0 && EGPassesLooseTrackID[] && abs(EGEta[])>1.479 && abs(EGEta[])<2.4)>0"
      onlinecut  = "Sum$( EGEt[]>"+str(x)+" && EGBx[]==0 && EGPassesLooseTrackID[] && abs(EGEta[])>1.479 && abs(EGEta[])<2.4)>0"


    if (obj=='tkPhotonIso'):
      offlinescalingcut = "( (abs(tkPhotonEta[])<1.479 && tkPhotonEt[]>("+str(TkIsoPhotonOfflineEtCutBarrel(x))+")) || (abs(tkPhotonEta[])>1.479 && tkPhotonEt[]>("+str(TkIsoPhotonOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" &&  ( (abs(tkPhotonEta[])<1.479 && tkPhotonTrkIso[]<0.29) || (abs(tkPhotonEta[])>1.479 && tkPhotonTrkIso[]<0.39) ) && tkPhotonBx[]==0 && tkPhotonPassesLooseTrackID[] && abs(tkPhotonEta[])<2.4)>0"
      onlinecut  = "Sum$( tkPhotonEt[]>"+str(x)+" && ( (abs(tkPhotonEta[])<1.479 && tkPhotonTrkIso[]<0.29) || (abs(tkPhotonEta[])>1.479 && tkPhotonTrkIso[]<0.39) ) && tkPhotonBx[]==0 && tkPhotonPassesLooseTrackID[] && abs(tkPhotonEta[])<2.4)>0"

      
    if (obj=='standalonePhoton'):
      offlinescalingcut = "( (abs(EGEta[])<1.479 && EGEt[]>("+str(StandalonePhotonOfflineEtCutBarrel(x))+")) || (abs(EGEta[])>1.479 && EGEt[]>("+str(StandalonePhotonOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && EGBx[]==0 && EGPassesPhotonID[] && abs(EGEta[])<2.4)>0"
      onlinecut  = "Sum$( EGEt[]>"+str(x)+" && EGBx[]==0 && EGPassesPhotonID[] && abs(EGEta[])<2.4)>0"


    if (obj=='tkPhotonIsoBarrel'):
      offlinescalingcut = "( (abs(tkPhotonEta[])<1.479 && tkPhotonEt[]>("+str(TkIsoPhotonOfflineEtCutBarrel(x))+")) || (abs(tkPhotonEta[])>1.479 && tkPhotonEt[]>("+str(TkIsoPhotonOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" &&  ( (abs(tkPhotonEta[])<1.479 && tkPhotonTrkIso[]<0.29) || (abs(tkPhotonEta[])>1.479 && tkPhotonTrkIso[]<0.39) ) && tkPhotonBx[]==0 && tkPhotonPassesLooseTrackID[] && abs(tkPhotonEta[])<1.479)>0"
      onlinecut  = "Sum$( tkPhotonEt[]>"+str(x)+" && ( (abs(tkPhotonEta[])<1.479 && tkPhotonTrkIso[]<0.29) || (abs(tkPhotonEta[])>1.479 && tkPhotonTrkIso[]<0.39) ) && tkPhotonBx[]==0 && tkPhotonPassesLooseTrackID[] && abs(tkPhotonEta[])<1.479)>0"


    if (obj=='standalonePhotonBarrel'):
      offlinescalingcut = "( (abs(EGEta[])<1.479 && EGEt[]>("+str(StandalonePhotonOfflineEtCutBarrel(x))+")) || (abs(EGEta[])>1.479 && EGEt[]>("+str(StandalonePhotonOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && EGBx[]==0 && EGPassesPhotonID[] && abs(EGEta[])<1.479)>0"
      onlinecut  = "Sum$( EGEt[]>"+str(x)+" && EGBx[]==0 && EGPassesPhotonID[] && abs(EGEta[])<1.479)>0"


    if (obj=='tkPhotonIsoEndcap'):
      offlinescalingcut = "( (abs(tkPhotonEta[])<1.479 && tkPhotonEt[]>("+str(TkIsoPhotonOfflineEtCutBarrel(x))+")) || (abs(tkPhotonEta[])>1.479 && tkPhotonEt[]>("+str(TkIsoPhotonOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" &&  ( (abs(tkPhotonEta[])<1.479 && tkPhotonTrkIso[]<0.29) || (abs(tkPhotonEta[])>1.479 && tkPhotonTrkIso[]<0.39) ) && tkPhotonBx[]==0 && tkPhotonPassesLooseTrackID[] && abs(tkPhotonEta[])<2.4 && abs(tkPhotonEta[])>1.479)>0"
      onlinecut  = "Sum$( tkPhotonEt[]>"+str(x)+" && ( (abs(tkPhotonEta[])<1.479 && tkPhotonTrkIso[]<0.29) || (abs(tkPhotonEta[])>1.479 && tkPhotonTrkIso[]<0.39) ) && tkPhotonBx[]==0 && tkPhotonPassesLooseTrackID[] && abs(tkPhotonEta[])<2.4 && abs(tkPhotonEta[])>1.479)>0"


    if (obj=='standalonePhotonEndcap'):
      offlinescalingcut = "( (abs(EGEta[])<1.479 && EGEt[]>("+str(StandalonePhotonOfflineEtCutBarrel(x))+")) || (abs(EGEta[])>1.479 && EGEt[]>("+str(StandalonePhotonOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && EGBx[]==0 && EGPassesPhotonID[] && abs(EGEta[])<2.4 && abs(EGEta[])>1.479)>0"
      onlinecut  = "Sum$( EGEt[]>"+str(x)+" && EGBx[]==0 && EGPassesPhotonID[] && abs(EGEta[])<2.4 && abs(EGEta[])>1.479)>0"


################################



    if (obj=='HPSPFTau1'):
      offlinescalingcut = "( (abs(pfTauEta[])<1.5 && pfTauEt[]>("+str(PFTauOfflineEtCutBarrel(x))+")) || (abs(pfTauEta[])>1.5 && pfTauEt[]>("+str(PFTauOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(pfTauEta[])<2.4)>0"
      onlinecut  = "Sum$( pfTauEt[]>"+str(x)+"  && abs(pfTauEta[])<2.4)>0"


    if (obj=='HPSPFTau1Medium'):
      offlinescalingcut = "( (abs(pfTauEta[])<1.5 && pfTauEt[]>("+str(PFIsoTauOfflineEtCutBarrel(x))+")) || (abs(pfTauEta[])>1.5 && pfTauEt[]>("+str(PFIsoTauOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && pfTauPassesMediumIso[]>0 && abs(pfTauEta[])<2.4)>0"
      onlinecut  = "Sum$( pfTauEt[]>"+str(x)+"  && pfTauPassesMediumIso[]>0 && abs(pfTauEta[])<2.4)>0"

   
    if (obj=='HPSPFTau2'):
      offlinescalingcut = "( (abs(hpsTauEta[])<1.5 && hpsTauEt[]>("+str(HPSTauOfflineEtCutBarrel(x))+")) || (abs(hpsTauEta[])>1.5 && hpsTauEt[]>("+str(HPSTauOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+"  && abs(hpsTauEta[])<2.4)>0"
      onlinecut  = "Sum$( hpsTauEt[]>"+str(x)+"  && abs(hpsTauEta[])<2.4)>0"


    if (obj=='HPSPFTau2Tight'):
      offlinescalingcut = "( (abs(hpsTauEta[])<1.5 && hpsTauEt[]>("+str(HPSIsoTauOfflineEtCutBarrel(x))+")) || (abs(hpsTauEta[])>1.5 && hpsTauEt[]>("+str(HPSIsoTauOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+"  && hpsTauPassTightRelIso[]>0 && abs(hpsTauEta[])<2.4)>0"
      onlinecut  = "Sum$( hpsTauEt[]>"+str(x)+"  && hpsTauPassTightRelIso[]>0 && abs(hpsTauEta[])<2.4)>0"
      

    if (obj=='NNPuppiTauLoose'):
      offlinescalingcut = "( (abs(nnTauEta[])<1.5 && nnTauEt[]>("+str(NNTauLooseOfflineEtCutBarrel(x))+")) || (abs(nnTauEta[])>1.5 && nnTauEt[]>("+str(NNTauLooseOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && nnTauPassLooseNN[]>0 && abs(nnTauEta[])<2.4)>0"
      onlinecut  = "Sum$( nnTauEt[]>"+str(x)+"  && nnTauPassLooseNN[]>0 && abs(nnTauEta[])<2.4)>0"


    if (obj=='NNPuppiTauTight'):
      offlinescalingcut = "( (abs(nnTauEta[])<1.5 && nnTauEt[]>("+str(NNTauTightOfflineEtCutBarrel(x))+")) || (abs(nnTauEta[])>1.5 && nnTauEt[]>("+str(NNTauTightOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && nnTauPassTightNN[]>0 && abs(nnTauEta[])<2.4)>0"
      onlinecut  = "Sum$( pfTauEt[]>"+str(x)+"  && nnTauPassTightNN[]>0 && abs(nnTauEta[])<2.4)>0"
  

    if (obj=='CaloTau'):
      offlinescalingcut = "( (abs(caloTauEta[])<1.5 && caloTauEt[]>("+str(CaloTauOfflineEtCutBarrel(x))+")) || (abs(caloTauEta[])>1.5 && caloTauEt[]>("+str(CaloTauOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(caloTauEta[])<2.4)>0"
      onlinecut  = "Sum$( caloTauEt[]>"+str(x)+"  && abs(caloTauEta[])<2.4)>0"


    if (obj=='TkEGTau'):
      offlinescalingcut = "( (abs(tkEGTauEta[])<1.5 && tkEGTauEt[]>("+str(TkEGTauOfflineEtCutBarrel(x))+")) || (abs(tkEGTauEta[])>1.5 && tkEGTauEt[]>("+str(TkEGTauOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(tkEGTauEta[])<2.4)>0"
      onlinecut  = "Sum$( tkEGTauEt[]>"+str(x)+"  && abs(tkEGTauEta[])<2.4)>0"  
  


   


################################


    if (obj=='puppiJet'):
      offlinescalingcut = "( (abs(puppiJetEta[])<1.5 && puppiJetEt[]>("+str(PuppiJetOfflineEtCutBarrel(x))+")) || (abs(puppiJetEta[])>1.5 && abs(puppiJetEta[])<2.4 && puppiJetEt[]>("+str(PuppiJetOfflineEtCutEndcap(x))+")) || (abs(puppiJetEta[])>2.4 && puppiJetEt[]>("+str(PuppiJetOfflineEtCutForward(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(puppiJetEta[])<2.4)>0"
      onlinecut  = "Sum$( puppiJetEt[]>"+str(x)+" && abs(puppiJetEta[])<2.4)>0"

    if (obj=='puppiJetExt'):
      offlinescalingcut = "( (abs(puppiJetEta[])<1.5 && puppiJetEt[]>("+str(PuppiJetOfflineEtCutBarrel(x))+")) || (abs(puppiJetEta[])>1.5 && abs(puppiJetEta[])<2.4 && puppiJetEt[]>("+str(PuppiJetOfflineEtCutEndcap(x))+")) || (abs(puppiJetEta[])>2.4 && puppiJetEt[]>("+str(PuppiJetOfflineEtCutForward(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(puppiJetEta[])<5)>0"
      onlinecut  = "Sum$( puppiJetEt[]>"+str(x)+" && abs(puppiJetEta[])<5)>0"

    if (obj=='puppiPhase1Jet'):
      offlinescalingcut = "( (abs(pfPhase1L1JetEta[])<1.5 && pfPhase1L1JetEt[]>("+str(PFPhase1JetOfflineEtCutBarrel(x))+")) || (abs(pfPhase1L1JetEta[])>1.5 && abs(pfPhase1L1JetEta[])<2.4 && pfPhase1L1JetEt[]>("+str(PFPhase1JetOfflineEtCutEndcap(x))+")) || (abs(pfPhase1L1JetEta[])>2.4 && pfPhase1L1JetEt[]>("+str(PFPhase1JetOfflineEtCutForward(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(pfPhase1L1JetEta[])<2.4)>0"
      onlinecut  = "Sum$( pfPhase1L1JetEt[]>"+str(x)+" && abs(pfPhase1L1JetEta[])<2.4)>0"

    if (obj=='puppiPhase1JetExt'):
      offlinescalingcut = "( (abs(pfPhase1L1JetEta[])<1.5 && pfPhase1L1JetEt[]>("+str(PFPhase1JetOfflineEtCutBarrel(x))+")) || (abs(pfPhase1L1JetEta[])>1.5 && abs(pfPhase1L1JetEta[])<2.4 && pfPhase1L1JetEt[]>("+str(PFPhase1JetOfflineEtCutEndcap(x))+")) || (abs(pfPhase1L1JetEta[])>2.4 && pfPhase1L1JetEt[]>("+str(PFPhase1JetOfflineEtCutForward(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(pfPhase1L1JetEta[])<5)>0"
      onlinecut  = "Sum$( pfPhase1L1JetEt[]>"+str(x)+" && abs(pfPhase1L1JetEta[])<5)>0"

    if (obj=='trackerJet'):
      offlinescalingcut = "( (abs(trackerJetEta[])<1.5 && trackerJetEt[]>("+str(TrackerJetOfflineEtCutBarrel(x))+")) || (abs(trackerJetEta[])>1.5 && trackerJetEt[]>("+str(TrackerJetOfflineEtCutEndcap(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(trackerJetEta[])<2.4)>0"
      onlinecut  = "Sum$( trackerJetEt[]>"+str(x)+" && abs(trackerJetEta[])<2.4)>0"

    if (obj=='caloJet'):
      offlinescalingcut = "( (abs(caloJetEta[])<1.5 && caloJetEt[]>("+str(CaloJetOfflineEtCutBarrel(x))+")) || (abs(caloJetEta[])>1.5 && abs(caloJetEta[])<2.4 && caloJetEt[]>("+str(CaloJetOfflineEtCutEndcap(x))+")) || (abs(caloJetEta[])>2.4 && caloJetEt[]>("+str(CaloJetOfflineEtCutForward(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(caloJetEta[])<2.4)>0"
      onlinecut  = "Sum$( caloJetEt[]>"+str(x)+" && abs(caloJetEta[])<2.4)>0"

    if (obj=='caloJetExt'):
      offlinescalingcut = "( (abs(caloJetEta[])<1.5 && caloJetEt[]>("+str(CaloJetOfflineEtCutBarrel(x))+")) || (abs(caloJetEta[])>1.5 && abs(caloJetEta[])<2.4 && caloJetEt[]>("+str(CaloJetOfflineEtCutEndcap(x))+")) || (abs(caloJetEta[])>2.4 && caloJetEt[]>("+str(CaloJetOfflineEtCutForward(x))+")) )"
      offlinecut = "Sum$( "+offlinescalingcut+" && abs(caloJetEta[])<5)>0"
      onlinecut  = "Sum$( caloJetEt[]>"+str(x)+" && abs(caloJetEta[])<5)>0"


###########################


    if (obj=='puppiHT'):
      offlinescalingcut = "(puppiHT[0]>("+str(PuppiHTOfflineEtCut(x))+"))"
      offlinecut = offlinescalingcut
      onlinecut  = " puppiHT[0]>"+str(x)

    if (obj=='puppiPhase1HT'):
      offlinescalingcut = "(pfPhase1L1HT[0]>("+str(PFPhase1HTOfflineEtCut(x))+"))"
      offlinecut = offlinescalingcut
      onlinecut  = " pfPhase1L1HT[0]>"+str(x)

    if (obj=='trackerHT'):
      offlinescalingcut = "(trackerHT[0]>("+str(TrackerHTOfflineEtCut(x))+"))"
      offlinecut = offlinescalingcut
      onlinecut  = " trackerHT[0]>"+str(x)


    if (obj=='caloHT'):
      offlinescalingcut = "(caloJetHT[0]>("+str(CaloHTOfflineEtCut(x))+"))"
      offlinecut = offlinescalingcut
      onlinecut  = " caloJetHT[0]>"+str(x)


    if (obj=='puppiMET'):
      offlinescalingcut = "(puppiMETEt>("+str(PuppiMETOfflineEtCut(x))+"))"
      offlinecut = offlinescalingcut
      onlinecut  = " puppiMETEt>"+str(x)

    if (obj=='trackerMET'):
      offlinescalingcut = "(trackerMetEt>("+str(TrackerMETOfflineEtCut(x))+"))"
      offlinecut = offlinescalingcut
      onlinecut  = " trackerMetEt>"+str(x)


    npass = t.GetEntries(offlinecut)
    off[obj].append(x)
    offrate[obj].append(round(float(npass)/float(ntot)*31038.,1))

    print x,round(float(npass)/float(ntot)*31038.,1)
    
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


plots = {


  # 0 : ['tkMuon', 'tkMuonStub' , 'standaloneMuon'],
  #0 : ['tkMuonStub'],
  # 1 : ['tkMuon', 'tkMuonStub' , 'tkMuonStubExt', 'standaloneMuon'],
  # 2 : ['tkMuonBarrel', 'tkMuonStubBarrel', 'standaloneMuonBarrel'],
  # 3 : ['tkMuonOverlap', 'tkMuonStubOverlap', 'standaloneMuonOverlap'],
  # 4 : ['tkMuonEndcap', 'tkMuonStubEndcap', 'standaloneMuonEndcap'],

  #2 : ['standaloneMuonBarrel', 'tkMuonStubBarrel', 'tkMuonBarrel' ],
  #3 : ['standaloneMuonOverlap','tkMuonStubOverlap', 'tkMuonOverlap'],
  #4 : ['standaloneMuonEndcap', 'tkMuonStubEndcap', 'tkMuonEndcap' ],

  # 4 : ['tkElectron', 'tkIsoElectron', 'standaloneElectron', 'standaloneElectronExt' ],
  # 4 : ['tkElectron', 'tkIsoElectron', 'standaloneElectron', 'standaloneElectronExt', 'tkPhotonIso']
  #4 : ['tkElectron'],
  # 5 : ['tkElectronBarrel', 'tkIsoElectronBarrel', 'standaloneElectronBarrel'],
  # 6 : ['tkElectronEndcap', 'tkIsoElectronEndcap', 'standaloneElectronEndcap'],
  # 7 : ['tkPhotonIso', 'standalonePhoton'],
  # 8 : ['tkPhotonIsoBarrel', 'standalonePhotonBarrel'],
  # 9 : ['tkPhotonIsoEndcap', 'standalonePhotonEndcap'],

  #10 : ['HPSPFTau1', 'HPSPFTau1Medium', 'NNPuppiTauLoose', 'NNPuppiTauTight', 'TkEGTau', 'CaloTau'],
  #11 : ['puppiPhase1Jet', 'trackerJet', 'caloJet'], #removed 'puppiJet'
  #12 : ['puppiPhase1JetExt', 'caloJetExt'], #removed 'puppiJetExt'
  #13 : ['caloHT', 'puppiPhase1HT', 'trackerHT'], #removed 'puppiHT'
  #14 : ['puppiMET', 'trackerMET'],


  # 1 : ['DiHPSPFTau1', 'DiHPSPFTau1Medium', 'DiNNPuppiTauLoose', 'DiNNPuppiTauTight', 'DiTkEGTau', 'DiCaloTau'],

##  4 : ['standaloneMuonBarrel', 'displacedMuonBarrel'],
##  11 : ['HPSPFTau1', 'HPSPFTau1Medium', 'HPSPFTau2', 'HPSPFTau2Tight', 'NNPuppiTauLoose', 'NNPuppiTauTight', 'TkEGTau', 'CaloTau'],
##  12 : ['HPSPFTau1', 'HPSPFTau1Medium', 'HPSPFTau2', 'HPSPFTau2Tight', 'TkEGTau', 'CaloTau'],
##  11 : ['doublePFTau', 'doublePFIsoTau'],
##  12 : ['doublePFTauBarrel', 'doublePFIsoTauBarrel', 'doubleTkTauBarrel',  'doubleCaloTkTauBarrel', 'doubleTkEGTauBarrel'], 
##  12 : ['PFTauBarrel', 'PFIsoTauBarrel', 'TkTauBarrel',  'CaloTkTauBarrel', 'TkEGTauBarrel'], 
##  13 : ['pfJet',  'caloJet'],
##  14 : ['pfJetCentral',  'caloJetCentral']
##  13 : ['puppiJet', 'puppiJetExt', 'puppiPhase1Jet', 'puppiPhase1JetExt', 'trackerJet', 'caloJet', 'caloJetExt'],




}

for key,list_plot in plots.iteritems():
  color=1
  name=''
  for obj in list_plot:
    
    name+=obj+'_'
    if (color==3): color+=1
    if (color==5): color+=1
    if (color==10): color+=1
  
    g_off[obj] = TGraph(len(off[obj])-1,off[obj],offrate[obj]);
    g_off[obj].SetMarkerColor(color)
    g_off[obj].SetMarkerStyle(20)
    g_off[obj].SetMarkerSize(1.2)
    g_off[obj].SetLineColor(color)
    
    g_onl[obj] = TGraph(len(onl[obj])-1,onl[obj],onlrate[obj]);
    g_onl[obj].SetMarkerColor(color)
    g_onl[obj].SetMarkerStyle(20)
    g_onl[obj].SetMarkerSize(1.2)
    g_onl[obj].SetLineColor(color)
    g_onl[obj].SetLineStyle(2)

  
    if (obj==list_plot[0]):
      h = TH1F("","",1,0.0,max(off[obj])*1.05)
      #h = TH1F("","",1,10.0,max(off[obj])*1.05)
      h.SetBinContent(1,0.0001)
      h.SetMaximum(500000.0)
      h.SetMinimum(1.0);
      c1 = TCanvas("c1","",800,800)
      c1.SetLeftMargin(0.11) #0.15 David
      c1.SetLogy()
      c1.SetGridx()
      c1.SetGridy()
      c1.SetTickx()
      c1.SetTicky()
      h.GetXaxis().SetTitle("Online or Offline p_{T} [GeV]")
      h.GetYaxis().SetTitle("Rate [kHz]")
      h.Draw("hist")
      
    g_onl[obj].Draw("lpsame")
    g_off[obj].Draw("lpsame")

    if (obj==list_plot[0]):
      leg = TLegend(0.45,0.65,0.85,0.85)
      #leg = TLegend(0.35,0.55,0.85,0.85)
  
    leg.AddEntry(g_onl[obj],obj+" (Online)","lp")
    leg.AddEntry(g_off[obj],obj+" (Offline)","lp")
  
    if (obj==list_plot[len(list_plot)-1]):
      leg.Draw("same")
  
    color+=1
    
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

  
  #c1.SaveAs("/afs/cern.ch/work/d/dsperka/www/private/L1/Mar25_v7p5p2/"+name+"_rate_vs_threshold.pdf")
  #c1.SaveAs("/afs/cern.ch/work/d/dsperka/www/private/L1/Mar25_v7p5p2/"+name+"_rate_vs_threshold.png")
  
  #c1.SaveAs("/afs/cern.ch/user/b/botta/www/L1Trigger/TDR/v7p5_Madrid_corr/"+name+"_rate_vs_threshold.pdf")
  #c1.SaveAs("/afs/cern.ch/user/b/botta/www/L1Trigger/TDR/v7p5_Madrid_corr/"+name+"_rate_vs_threshold.png")

  #c1.SaveAs("/afs/cern.ch/user/b/botta/www/L1Trigger/TDR/v8p2_oldScalingEG/"+name+"_rate_vs_threshold.pdf")
  #c1.SaveAs("/afs/cern.ch/user/b/botta/www/L1Trigger/TDR/v8p2_oldScalingEG/"+name+"_rate_vs_threshold.png")

  #c1.SaveAs("/afs/cern.ch/user/b/botta/www/L1Trigger/TDR/v8p2/"+name+"_rate_vs_threshold.pdf")
  #c1.SaveAs("/afs/cern.ch/user/b/botta/www/L1Trigger/TDR/v8p2/"+name+"_rate_vs_threshold.png")
  
  #c1.SaveAs("/afs/cern.ch/user/b/botta/www/L1Trigger/TDR/v8p2_NewRelease/"+name+"_rate_vs_threshold.pdf")
  #c1.SaveAs("/afs/cern.ch/user/b/botta/www/L1Trigger/TDR/v8p2_NewRelease/"+name+"_rate_vs_threshold.png")
  
  #c1.SaveAs("/afs/cern.ch/user/b/botta/www/L1Trigger/TDR/v9/"+name+"_rate_vs_threshold.pdf")
  #c1.SaveAs("/afs/cern.ch/user/b/botta/www/L1Trigger/TDR/v9/"+name+"_rate_vs_threshold.png")


  c1.SaveAs(name+"_AnnualReview_caloCheck.pdf")
  c1.SaveAs(name+"_AnnualReview_caloCheck.png")
  #c1.SaveAs("/afs/cern.ch/user/b/botta/www/L1Trigger/TDR/v10p7_ApprovalExt/"+name+"_rate_vs_threshold.pdf")
  #c1.SaveAs("/afs/cern.ch/user/b/botta/www/L1Trigger/TDR/v10p7_ApprovalExt/"+name+"_rate_vs_threshold.png")
  









# CMS Phase-2 Level-1 Object

## <u>Genpart</u> 
## GenPart
- **Matching ΔR**: 0.15
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.479]
  - **endcap**: [1.479, 5]

### IDs:
#### electron
- **Label**: "Gen Electron"
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 3
    - (({statusFlags}>>7)&1) == 1
    - abs({pdgId}) == 11

#### muon
- **Label**: "Gen Muon"
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 3
    - (({statusFlags}>>7)&1) == 1
    - abs({pdgId}) == 13


## GenVisTau
- **Matching ΔR**: 0.3
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.5]
  - **endcap**: [1.5, 5]
- **Label**: "GenVisTau"

### IDs:
#### default
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4




## <u>Electrons</u> 
## L1tkElectron
- **Matching ΔR**: 0.15
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.479]
  - **endcap**: [1.479, 5]
>ets 1<br>test 2

### IDs:
#### NoIso
- **Label**: "TkElectron"
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4
  - **endcap**:
    - ({eleId} == 1) | ({pt} < 25)
  - **barrel**:
    - {eleId} == 1

#### NoIsoForIso
- **Label**: "TkElectron, no ID"
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4

#### Iso
- **Label**: "TkIsoElectron"
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4
  - **barrel**:
    - abs({relIso}) < 0.13
  - **endcap**:
    - abs({relIso}) < 0.28


## L1EG
- **Matching ΔR**: 0.2
- **Eta Ranges** (funny comment):
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.479]
  - **endcap**: [1.479, 3.0]
- **Label**: "EG"

### IDs:
#### default
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 3.0
  - **barrel**:
    - {eleId} == 1
  - **endcap**:
    - {saId} == 1
>insert comment here




## <u>Jets</u> 
## L1caloJet
- **Matching ΔR**: 0.3
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.5]
  - **endcap**: [1.5, 2.4]
  - **forward**: [2.4, 5]
- **Label**: "Calo Jet"

### IDs:
#### default
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 7


## L1puppiExtJetSC4
- **Matching ΔR**: 0.35
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.5]
  - **endcap**: [1.5, 2.4]
  - **forward**: [2.4, 5]
- **Label**: "Ext. SC4"

### IDs:
#### default
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 5

#### PtGe25
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 7
    - abs({pt}) >= 25
>comment 1<br>comment 2

#### bjetnn
- **Label**: "Ext. SC4, BtagScore > 0.71"
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4
    - {btagScore} > 0.71


## L1puppiJetHisto
- **Matching ΔR**: 0.3
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.5]
  - **endcap**: [1.5, 2.4]
  - **forward**: [2.4, 5]
- **Label**: "Histogrammed PuppiJet"

### IDs:
#### default
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 7


## L1puppiJetSC4
- **Matching ΔR**: 0.35
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.5]
  - **endcap**: [1.5, 2.4]
  - **forward**: [2.4, 5]
- **Label**: "SC4"

### IDs:
#### default
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 7

#### PtGe25
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 7
    - abs({pt}) >= 25


## L1puppiJetSC4NG
- **Matching ΔR**: 0.35
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.5]
  - **endcap**: [1.5, 2.4]
  - **forward**: [2.4, 5]
- **Label**: "NG SC4"

### IDs:
#### default
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 7

#### PtGe25
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 7
    - abs({pt}) >= 25

#### bjetnn
- **Label**: "NG SC4, BtagScore > 0.15"
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4
    - {bTagScore} > 0.15

#### cjetnn
- **Label**: "NG SC4, CtagScore > 0.099"
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4
    - {cTagScore} > 0.099

#### gjetnn
- **Label**: "NG SC4, GtagScore > 0.59"
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4
    - {gTagScore} > 0.59

#### lightjetnn
- **Label**: "NG SC4, LighttagScore > 0.54"
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4
    - {udsTagScore} > 0.54


## L1puppiJetSC8
- **Matching ΔR**: 0.35
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.5]
  - **endcap**: [1.5, 2.4]
  - **forward**: [2.4, 5]
- **Label**: "Seeded Cone PuppiJet 8"

### IDs:
#### default
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 7


## L1TrackJet
- **Matching ΔR**: 0.4
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.5]
  - **endcap**: [1.5, 2.4]
- **Label**: "Tracker Jet"

### IDs:
#### default
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 7




## <u>Met_ht_mht</u> 
## L1puppiMET
- **Label**: "Puppi MET"

### IDs:
#### default


## L1puppiMLMET
- **Label**: "Puppi MLMET"

### IDs:
#### default


## L1puppiJetSC4sums

### IDs:
#### HT
- **Label**: "SeededCone HT"
- **Cuts**:
  - **inclusive**:
    - {sumType} == 0

#### MHT
- **Label**: "SeededCone MHT"
- **Cuts**:
  - **inclusive**:
    - {sumType} == 1


## L1puppiHistoJetSums

### IDs:
#### HT
- **Label**: "Histogrammed Puppi HT"
- **Cuts**:
  - **inclusive**:
    - {sumType} == 0

#### MHT
- **Label**: "Histogrammed Puppi MHT"
- **Cuts**:
  - **inclusive**:
    - {sumType} == 1


## L1TrackHT

### IDs:
#### HT
- **Label**: "Tracker HT"

#### MHT
- **Label**: "Tracker MHT"


## L1ExtTrackHT

### IDs:
#### HT
- **Label**: "ext. Tracker HT"

#### MHT
- **Label**: "ext. Tracker MHT"


## L1TrackMET
- **Label**: "Tracker MET"

### IDs:
#### default


## L1TrackTripletWord
- **Label**: "Track Triplet for W3Pi"

### IDs:
#### default




## <u>Muons</u> 
## L1gmtTkMuon
- **Matching ΔR**: 0.1
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 0.83]
  - **overlap**: [0.83, 1.24]
  - **endcap**: [1.24, 2.4]
- **Label**: "GMT TkMuon"

### IDs:
#### default
- **Label**: "GMT TkMuon"
- **Cuts**:
  - **inclusive**: (Loose (bit 2) for pt < 8 VLoose (bit 1) for pt > 8)
    - (({hwQual}>>1)&1 == 1) | (({pt} > 8) & (({hwQual}>>0)&1 == 1))

#### VLoose (x.numberOfMatches() > 0)
- **Label**: "GMT TkMuon, VLoose ID"
- **Cuts**:
  - **inclusive**:
    - ({hwQual}>>0)&1 == 1

#### Loose (x.numberOfMatches() >1)
- **Label**: "GMT TkMuon, Loose ID"
- **Cuts**:
  - **inclusive**:
    - ({hwQual}>>1)&1 == 1

#### Medium (x.stubs().size()>1)
- **Label**: "GMT TkMuon, Medium ID"
- **Cuts**:
  - **inclusive**:
    - ({hwQual}>>2)&1 == 1

#### Tight (x.numberOfMatches()>2)
- **Label**: "GMT TkMuon, Tight ID"
- **Cuts**:
  - **inclusive**:
    - ({hwQual}>>3)&1 == 1


## L1gmtMuon
- **Matching ΔR**: 0.6
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 0.83]
  - **overlap**: [0.83, 1.24]
  - **endcap**: [1.24, 2.4]
- **Label**: "GMT Muon"

### IDs:
#### default
- **Cuts**:
  - **overlap**:
    - {hwQual} >= 12
  - **endcap**:
    - {hwQual} >= 14

#### dR0p6
- **Label**: "GMT Muon, match dR < 0.6"
- **Cuts**:


## L1gmtDispMuon
- **Matching ΔR**: 0.6
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 0.83]
  - **overlap**: [0.83, 1.24]
  - **endcap**: [1.24, 2.4]
- **Label**: "GMT Displaced Muon"

### IDs:
#### default

#### dXYge8
- **Label**: "Disp. Muon, dXY>8"
- **Cuts**:
  - **endcap**:
    - {d0} >= 8

#### dXYge8Qual15
- **Label**: "Disp. Muon, dXY>8, qual>=15"
- **Cuts**:
  - **endcap**:
    - {hwQual} >= 15
    - {d0} >= 8

#### qual15
- **Label**: "Disp. Muon, qual>=15"
- **Cuts**:
  - **endcap**:
    - {hwQual} >= 15

#### qual15_Eta2p0
- **Label**: "Disp. Muon, eta < 2, qual>=15"
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2
  - **endcap**:
    - {hwQual} >= 15


## L1MuonKMTF
- **Matching ΔR**: 0.3
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 0.83]
  - **overlap**: [0.83, 1.24]
  - **endcap**: [1.24, 2.4]
- **Label**: "KMTF Muon"

### IDs:
#### default


## L1MuonOMTF
- **Matching ΔR**: 0.3
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 0.83]
  - **overlap**: [0.83, 1.24]
  - **endcap**: [1.24, 2.4]
- **Label**: "OMTF Muon"

### IDs:
#### default


## L1MuonEMTF
- **Matching ΔR**: 0.3
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 0.83]
  - **overlap**: [0.83, 1.24]
  - **endcap**: [1.24, 2.4]
- **Label**: "EMTF Muon"

### IDs:
#### default




## <u>Photons</u> 
## L1tkPhoton
- **Matching ΔR**: 0.15
- **Eta Ranges**:
  - **inclusive**: [0, 5]
  - **barrel**: [0, 1.479]
  - **endcap**: [1.479, 2.4]

### IDs:
#### NoIso
- **Label**: "L1tkPhoton"
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4
    - {pt} > 5
  - **barrel**:
    - {eleId} == 1
  - **endcap**:
    - {phoId} == 1

#### NoIsoPt30
- **Label**: "L1tkPhoton, pt>30"
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4
    - {pt} > 30
  - **barrel**:
    - {eleId} == 1
  - **endcap**:
    - {phoId} == 1

#### Iso
- **Label**: "L1tkIsoPhoton"
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4
    - {pt} > 5
  - **barrel**:
    - abs({relIso}) < 0.25
    - {eleId} == 1
  - **endcap**:
    - abs({relIso}) < 0.205
    - {phoId} == 1

#### IsoPt30
- **Label**: "L1tkIsoPhoton, Pt>30"
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4
    - {pt} > 30
  - **barrel**:
    - abs({relIso}) < 0.25
    - {eleId} == 1
  - **endcap**:
    - abs({relIso}) < 0.205
    - {phoId} == 1




## <u>Pv</u> 
## L1PV
- **Label**: "Primary Vertex"

### IDs:
#### default




## <u>Taus</u> 
## L1nnPuppiTau
- **Matching ΔR**: 0.1
- **Eta Ranges** (keys):
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.5]
  - **endcap**: [1.5, 2.4] (values)
>etst
- **Label**: "NN Tau"

### IDs:
#### default
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4
    - {chargedIso} > 0.22
>Current IB (22 Feb recipe) does not have updated WP, so cut on NN score rather than checking passLooseNN


## L1hpsTau
- **Matching ΔR**: 0.1
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.5]
  - **endcap**: [1.5, 2.4]
>etst
- **Label**: "HPS Tau"

### IDs:
#### default
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4
>test


## L1caloTau
- **Matching ΔR**: 0.3
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.5]
  - **endcap**: [1.5, 2.4]
- **Label**: "Calo Tau"

### IDs (test):
#### default
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4


## L1nnCaloTau
- **Matching ΔR**: 0.3
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.5]
  - **endcap**: [1.5, 2.4]
- **Label**: "NN Calo Tau"

### IDs:
#### default
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4
    - {hwQual}==3
>comment<br>comment





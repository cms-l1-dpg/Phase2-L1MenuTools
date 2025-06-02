# CMS Phase-2 Level-1 Object Definitions

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
  - **inclusive**:
    - (({hwQual}>>1)&1 == 1) | (({pt} > 8) & (({hwQual}>>0)&1 == 1))

#### VLoose
- **Label**: "GMT TkMuon, VLoose ID"
- **Cuts**:
  - **inclusive**:
    - ({hwQual}>>0)&1 == 1

#### Loose
- **Label**: "GMT TkMuon, Loose ID"
- **Cuts**:
  - **inclusive**:
    - ({hwQual}>>1)&1 == 1

#### Medium
- **Label**: "GMT TkMuon, Medium ID"
- **Cuts**:
  - **inclusive**:
    - ({hwQual}>>2)&1 == 1

#### Tight
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



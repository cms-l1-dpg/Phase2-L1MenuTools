# CMS Phase-2 Level-1 Object Definitions

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



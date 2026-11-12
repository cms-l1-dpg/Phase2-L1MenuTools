# CMS Phase-2 Level-1 Object Definitions

## L1nnPuppiTau
- **Matching ΔR**: 0.1
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.5]
  - **endcap**: [1.5, 2.4]
- **Label**: "NN Tau"

### IDs:

#### default
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4
    - {chargedIso} > 0.22


## L1hpsTau
- **Matching ΔR**: 0.1
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.5]
  - **endcap**: [1.5, 2.4]
- **Label**: "HPS Tau"

### IDs:

#### default
- **Cuts**:
  - **inclusive**:
    - abs({eta}) < 2.4


## L1caloTau
- **Matching ΔR**: 0.3
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.5]
  - **endcap**: [1.5, 2.4]
- **Label**: "Calo Tau"

### IDs:

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



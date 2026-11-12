# CMS Phase-2 Level-1 Object Definitions

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



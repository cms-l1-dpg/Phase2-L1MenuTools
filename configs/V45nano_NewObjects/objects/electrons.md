# CMS Phase-2 Level-1 Object Definitions

## L1tkElectron
- **Matching ΔR**: 0.15
- **Eta Ranges**:
  - **inclusive**: [0, 7]
  - **barrel**: [0, 1.479]
  - **endcap**: [1.479, 5]

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
- **Eta Ranges**:
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



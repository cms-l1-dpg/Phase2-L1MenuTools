# CMS Phase-2 Level-1 Object Definitions

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



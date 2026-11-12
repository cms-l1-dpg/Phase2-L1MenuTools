# CMS Phase-2 Level-1 Triggers

## <u>Step1_cfg.yml</u> 
## version

## sample

## menu_config

## table_fname



## <u>Step1_menu_cfg.yml</u> 
## L1_PFHTT
- **Object**: L1puppiJetSC4sums:HT

  - **Threshold**: offline_pt >= 450.0

- **Cross Masks**: None

## L1_PFMHTT
- **Object**: L1puppiJetSC4sums:MHT

  - **Threshold**: offline_pt >= 135.5

- **Cross Masks**: None

## L1_PFMet
- **Object**: L1puppiMET:default

  - **Threshold**: offline_pt >= 200.0

- **Cross Masks**: None

## L1_DoubleTkMu4p5er2p0_SQ_OS_Mass7to18
- **Object 1**: L1gmtTkMuon:default

  - **Threshold**: pt >= 4.4

- **Object 2**: L1gmtTkMuon:default

  - **Threshold**: pt >= 4.4

- **Cross Masks**:

  - (((leg1+leg2).mass > 7.0) & (leg1.deltaR(leg2) > 0))

  - (((leg1+leg2).mass < 18.0) & (leg1.deltaR(leg2) > 0))

  - ((leg1.charge*leg2.charge < 0.0) & (leg1.deltaR(leg2) > 0))

  - ((abs(leg2.z0-leg1.z0) < 1) & (leg1.deltaR(leg2) > 0))


## L1_TkMu_PfJet_dRMax_DoubleJet_dEtaMax
- **Object 1**: L1PV:default

- **Object 2**: L1gmtTkMuon:default

  - **Threshold**: offline_pt >= 12.0

- **Object 3**: L1puppiJetSC4:default

  - **Threshold**: offline_pt >= 40.0

- **Object 4**: L1puppiJetSC4:default

  - **Threshold**: offline_pt >= 40.0

- **Object 5**: L1puppiJetSC4:default

  - **Threshold**: offline_pt >= 40.0

- **Cross Masks**:

  - abs(leg2.eta) < 2.4

  - abs(leg2.z0-leg1.z0) < 1

  - leg2.deltaR(leg3) < 0.4

  - abs(leg5.eta-leg4.eta) < 1.6


## L1_DoubleTkMu0er1p5_SQ_OS_dR_Max1p4
- **Object 1**: L1gmtTkMuon:default

  - **Threshold**: pt >= 0

- **Object 2**: L1gmtTkMuon:default

  - **Threshold**: pt >= 0

- **Cross Masks**:

  - (abs(leg1.eta) < 1.5)

  - (abs(leg2.eta) < 1.5)

  - ((leg1.deltaR(leg2) < 1.4))

  - ((leg1.charge*leg2.charge < 0.0))

  - ((abs(leg2.z0-leg1.z0) < 1))

  - ((leg1.deltaR(leg2) > 0))


## L1_SingleTkPhoIso
- **Object**: L1tkPhoton:Iso

  - **Threshold**: offline_pt >= 36.0

- **Cross Masks**: None

## L1_DoubleTkPhoIso
- **Object 1**: L1tkPhoton:Iso

  - **Threshold**: offline_pt >= 22.0

- **Object 2**: L1tkPhoton:Iso

  - **Threshold**: offline_pt >= 12.0

- **Cross Masks**: None

## L1_PFTau_PFTau
- **Object 1**: L1caloTau:default

  - **Threshold**: offline_pt > 90.0

- **Object 2**: L1caloTau:default

  - **Threshold**: offline_pt > 90.0

- **Cross Masks**:

  - leg1.deltaR(leg2) > 0.5


## L1_SingleEGEle
- **Object**: L1EG:default:inclusive

  - **Threshold**: offline_pt >= 51.0

- **Cross Masks**: None

## L1_SinglePFTau
- **Object**: L1caloTau:default

  - **Threshold**: offline_pt > 150.0

- **Cross Masks**: None

## L1_SinglePfJet
- **Object**: L1puppiJetSC4:default

  - **Threshold**: offline_pt >= 230.0

- **Cross Masks**: None

## L1_SingleTkEle
- **Object**: L1tkElectron:NoIso:inclusive

  - **Threshold**: offline_pt >= 36.0

- **Cross Masks**: None

## L1_SingleTkEleIso
- **Object**: L1tkElectron:Iso:inclusive

  - **Threshold**: offline_pt > 28.0

- **Cross Masks**: None

## L1_SingleTkMu
- **Object**: L1gmtTkMuon:default

  - **Threshold**: offline_pt >= 22.0

- **Cross Masks**: None

## L1_TkEleIso_EG
- **Object 1**: L1tkElectron:Iso:inclusive

  - **Threshold**: offline_pt >= 22.0

- **Object 2**: L1EG:default:inclusive

  - **Threshold**: offline_pt >= 12.0

- **Cross Masks**:

  - leg1.deltaR(leg2) > 0.1


## L1_TkEleIso_PFHTT
- **Object 1**: L1PV:default

- **Object 2**: L1tkElectron:Iso:inclusive

  - **Threshold**: offline_pt >= 26.0

- **Object 3**: L1puppiJetSC4sums:HT

  - **Threshold**: offline_pt >= 190.0

- **Cross Masks**:

  - abs(leg2.z0-leg1.z0) < 1


## L1_TkEleIso_PFIsoTau
- **Object 1**: L1PV:default

- **Object 2**: L1tkElectron:Iso:inclusive

  - **Threshold**: offline_pt >= 22.0

- **Object 3**: L1nnPuppiTau:default

  - **Threshold**: offline_pt >= 45.0

- **Cross Masks**:

  - abs(leg2.z0-leg1.z0) < 1


## L1_TkEle_PFJet_dRMin
- **Object 1**: L1PV:default

- **Object 2**: L1tkElectron:NoIso:inclusive

  - **Threshold**: offline_pt >= 28.0

- **Object 3**: L1puppiJetSC4:default

  - **Threshold**: offline_pt >= 40.0

- **Cross Masks**:

  - abs(leg2.z0-leg1.z0) < 1

  - leg2.deltaR(leg3) > 0.3


## L1_TkEle_TkMu
- **Object 1**: L1tkElectron:NoIso:inclusive

  - **Threshold**: offline_pt >= 10.0

- **Object 2**: L1gmtTkMuon:default

  - **Threshold**: offline_pt >= 20.0

- **Cross Masks**:

  - abs(leg2.z0-leg1.z0) < 1


## L1_TkMu_DoubleTkEle
- **Object 1**: L1gmtTkMuon:default

  - **Threshold**: pt >= 6

- **Object 2**: L1tkElectron:NoIso:inclusive

  - **Threshold**: offline_pt >= 17.0

- **Object 3**: L1tkElectron:NoIso:inclusive

  - **Threshold**: offline_pt >= 17.0

- **Cross Masks**:

  - abs(leg2.z0-leg1.z0) < 1

  - abs(leg3.z0-leg1.z0) < 1


## L1_TkMu_PfHTT
- **Object 1**: L1PV:default

- **Object 2**: L1gmtTkMuon:default

  - **Threshold**: pt >= 6

- **Object 3**: L1puppiJetSC4sums:HT

  - **Threshold**: offline_pt >= 320.0

- **Cross Masks**:

  - abs(leg2.z0-leg1.z0) < 1


## L1_TkMu_PfJet_PfMet
- **Object 1**: L1PV:default

- **Object 2**: L1gmtTkMuon:default

  - **Threshold**: pt >= 3

- **Object 3**: L1puppiJetSC4:default

  - **Threshold**: offline_pt >= 110.0

- **Object 4**: L1puppiMET:default

  - **Threshold**: offline_pt >= 120.0

- **Cross Masks**:

  - abs(leg2.z0-leg1.z0) < 1


## L1_TkMu_TkEle
- **Object 1**: L1gmtTkMuon:default

  - **Threshold**: pt >= 7

- **Object 2**: L1tkElectron:NoIso:inclusive

  - **Threshold**: offline_pt >= 23.0

- **Cross Masks**:

  - abs(leg2.z0-leg1.z0) < 1


## L1_TkMu_TkEleIso
- **Object 1**: L1gmtTkMuon:default

  - **Threshold**: pt >= 7

- **Object 2**: L1tkElectron:Iso:inclusive

  - **Threshold**: offline_pt >= 20.0

- **Cross Masks**:

  - abs(leg2.z0-leg1.z0) < 1


## L1_TripleTkMu
- **Object 1**: L1gmtTkMuon:default

  - **Threshold**: pt >= 5

- **Object 2**: L1gmtTkMuon:default

  - **Threshold**: pt >= 3

- **Object 3**: L1gmtTkMuon:default

  - **Threshold**: pt >= 3

- **Cross Masks**:

  - abs(leg2.z0-leg1.z0) < 1

  - abs(leg3.z0-leg1.z0) < 1


## L1_TripleTkMu_5SQ_3SQ_0OQ_DoubleMu_5_3_SQ_OS_Mass_Max9
- **Object 1**: L1gmtTkMuon:default

  - **Threshold**: pt >= 5

- **Object 2**: L1gmtTkMuon:default

  - **Threshold**: pt >= 3

- **Object 3**: L1gmtTkMuon:default

  - **Threshold**: pt >= 0

- **Cross Masks**:

  - (leg1+leg2).mass < 9.0

  - leg1.charge*leg2.charge < 0.0

  - abs(leg2.z0-leg1.z0) < 1

  - abs(leg3.z0-leg1.z0) < 1


## L1_TripleTkMu_5_3p5_2p5_OS_Mass_5to17
- **Object 1**: L1gmtTkMuon:default

  - **Threshold**: pt >= 5

- **Object 2**: L1gmtTkMuon:default

  - **Threshold**: pt >= 3.5

- **Object 3**: L1gmtTkMuon:default

  - **Threshold**: pt >= 2.5

- **Cross Masks**:

  - abs(leg2.z0-leg1.z0) < 1

  - leg1.charge*leg3.charge < 0.0

  - (leg1+leg3).mass > 5.0

  - (leg1+leg3).mass < 17.0

  - abs(leg3.z0-leg1.z0) < 1


## L1_DoubleTkEle_PFHTT
- **Object 1**: L1PV:default

- **Object 2**: L1tkElectron:NoIso:inclusive

  - **Threshold**: offline_pt > 8.0

- **Object 3**: L1tkElectron:NoIso:inclusive

  - **Threshold**: offline_pt > 8.0

- **Object 4**: L1puppiJetSC4sums:HT

  - **Threshold**: offline_pt > 390.0

- **Cross Masks**:

  - (abs(leg2.z0-leg1.z0) < 1 & (leg2.deltaR(leg3) > 0))

  - (abs(leg3.z0-leg1.z0) < 1 & (leg2.deltaR(leg3) > 0))

  - (leg3.deltaR(leg2) > 0)


## L1_DoubleEGEle
- **Object 1**: L1EG:default:inclusive

  - **Threshold**: offline_pt >= 37.0

- **Object 2**: L1EG:default:inclusive

  - **Threshold**: offline_pt >= 24.0

- **Cross Masks**:

  - leg1.deltaR(leg2) > 0.1


## L1_DoublePFJet_MassMin
- **Object 1**: L1puppiJetSC4:default

  - **Threshold**: offline_pt >= 160.0

- **Object 2**: L1puppiJetSC4:default

  - **Threshold**: offline_pt >= 35.0

- **Cross Masks**:

  - (leg1 + leg2).mass > 620


## L1_DoublePFJet_dEtaMax
- **Object 1**: L1puppiJetSC4:default

  - **Threshold**: leg1.offline_pt >= 112.0

- **Object 2**: L1puppiJetSC4:default

  - **Threshold**: leg2.offline_pt >= 112.0

- **Cross Masks**:

  - abs(leg2.eta-leg1.eta) < 1.6


## L1_DoubleTkEle
- **Object 1**: L1tkElectron:NoIso:inclusive

  - **Threshold**: offline_pt >= 25.0

- **Object 2**: L1tkElectron:NoIso:inclusive

  - **Threshold**: offline_pt >= 12.0

- **Cross Masks**:

  - abs(leg2.z0-leg1.z0) < 1


## L1_DoubleTkMu
- **Object 1**: L1gmtTkMuon:default

  - **Threshold**: offline_pt > 15.0

- **Object 2**: L1gmtTkMuon:default

  - **Threshold**: pt >= 7

- **Cross Masks**:

  - ((abs(leg1.z0-leg2.z0) < 1) & (leg1.deltaR(leg2) > 0))


## L1_DoubleTkMu4_SQ_OS_dR_Max1p2
- **Object 1**: L1gmtTkMuon:default

  - **Threshold**: pt >= 4

- **Object 2**: L1gmtTkMuon:default

  - **Threshold**: pt >= 4

- **Cross Masks**:

  - ((leg1.deltaR(leg2) < 1.2) & (leg1.deltaR(leg2) > 0))

  - ((leg1.charge*leg2.charge < 0.0) & (leg1.deltaR(leg2) > 0))

  - ((abs(leg2.z0-leg1.z0) < 1) & (leg1.deltaR(leg2) > 0))


## L1_DoubleTkMu_PfHTT
- **Object 1**: L1PV:default

- **Object 2**: L1gmtTkMuon:default

  - **Threshold**: pt >= 3

- **Object 3**: L1gmtTkMuon:default

  - **Threshold**: pt >= 3

- **Object 4**: L1puppiJetSC4sums:HT

  - **Threshold**: offline_pt >= 300.0

- **Cross Masks**:

  - (abs(leg2.z0-leg1.z0) < 1 & (leg3.deltaR(leg2) > 0))

  - (abs(leg3.z0-leg1.z0) < 1 & (leg3.deltaR(leg2) > 0))

  - (leg3.deltaR(leg2) > 0)


## L1_DoubleTkMu_PfJet_PfMet
- **Object 1**: L1PV:default

- **Object 2**: L1gmtTkMuon:default

  - **Threshold**: pt >= 3

- **Object 3**: L1gmtTkMuon:default

  - **Threshold**: pt >= 3

- **Object 4**: L1puppiJetSC4:default

  - **Threshold**: offline_pt >= 60.0

- **Object 5**: L1puppiMET:default

  - **Threshold**: offline_pt >= 130.0

- **Cross Masks**:

  - abs(leg2.z0-leg1.z0) < 1

  - abs(leg3.z0-leg1.z0) < 1


## L1_DoubleTkMu_TkEle
- **Object 1**: L1gmtTkMuon:default

  - **Threshold**: pt >= 5

- **Object 2**: L1gmtTkMuon:default

  - **Threshold**: pt >= 5

- **Object 3**: L1tkElectron:NoIso:inclusive

  - **Threshold**: offline_pt >= 9.0

- **Cross Masks**:

  - abs(leg2.z0-leg1.z0) < 1

  - abs(leg3.z0-leg1.z0) < 1


## L1_PFHTT_QuadJet
- **Object 1**: L1puppiJetSC4sums:HT

  - **Threshold**: offline_pt >= 400.0

- **Object 2**: L1puppiJetSC4:default

  - **Threshold**: offline_pt >= 70.0

- **Object 3**: L1puppiJetSC4:default

  - **Threshold**: offline_pt >= 55.0

- **Object 4**: L1puppiJetSC4:default

  - **Threshold**: offline_pt >= 40.0

- **Object 5**: L1puppiJetSC4:default

  - **Threshold**: offline_pt >= 40.0

- **Cross Masks**: None

## L1_PFIsoTau_PFIsoTau
- **Object 1**: L1nnPuppiTau:default

  - **Threshold**: offline_pt >= 52.0

- **Object 2**: L1nnPuppiTau:default

  - **Threshold**: offline_pt >= 52.0

- **Cross Masks**:

  - leg1.deltaR(leg2) > 0.5


## L1_PFIsoTau_PFMet
- **Object 1**: L1nnPuppiTau:default

  - **Threshold**: offline_pt >= 55.0

- **Object 2**: L1puppiMET:default

  - **Threshold**: offline_pt >= 190.0

- **Cross Masks**: None

## L1_PFIsoTau_TkMu
- **Object 1**: L1PV:default

- **Object 2**: L1nnPuppiTau:default

  - **Threshold**: offline_pt >= 42.0

- **Object 3**: L1gmtTkMuon:default

  - **Threshold**: offline_pt >= 18.0

- **Cross Masks**:

  - abs(leg3.z0-leg1.z0) < 1




## <u>Tau_only.yml</u> 
## version

## sample

## menu_config

## table_fname



## <u>Tau_only_menu.yml</u> 
## L1_PFIsoTau_PFIsoTau
- **Object 1**: L1nnPuppiTau:default

  - **Threshold**: offline_pt >= 52.0

- **Object 2**: L1nnPuppiTau:default

  - **Threshold**: offline_pt >= 52.0

- **Cross Masks**:

  - leg1.deltaR(leg2) > 0.5


## L1_SinglePFTau
- **Object**: L1caloTau:default

  - **Threshold**: offline_pt > 150.0

- **Cross Masks**: None

## L1_PFTau_PFTau
- **Object 1**: L1caloTau:default

  - **Threshold**: offline_pt > 90.0

- **Object 2**: L1caloTau:default

  - **Threshold**: offline_pt > 90.0

- **Cross Masks**:

  - leg1.deltaR(leg2) > 0.5




## <u>Test_for_p2gt.yml</u> 
## version

## sample

## menu_config

## table_fname



## <u>Step2_cfg.yml</u> 
## version

## sample

## menu_config

## table_fname



## <u>Step2_menu_cfg.yml</u> 
>B Jet Seeds
## L1_PFHTT_QuadJet_BTagNNScore
- **Object 1**: L1puppiJetSC4sums:HT

  - **Threshold**: offline_pt >= 299.0

- **Object 2**: L1puppiExtJetSC4:default

  - **Threshold**: pt >= 25

- **Object 3**: L1puppiExtJetSC4:default

  - **Threshold**: pt >= 25

- **Object 4**: L1puppiExtJetSC4:default

  - **Threshold**: pt >= 25

- **Object 5**: L1puppiExtJetSC4:default

>test
  - **Threshold**: pt >= 25

- **Cross Masks** (test):

>test
  - (leg2.btagScore + leg3.btagScore + leg4.btagScore + leg5.btagScore) > 2.20


## L1_PFHTT_QuadJetNG_BTagNNScore
- **Object 1**: L1puppiJetSC4NGsums:HT
 (test)
  - **Threshold**: offline_pt >= 299.0

- **Object 2**: L1puppiJetSC4NG:default

  - **Threshold**: pt >= 25

- **Object 3**: L1puppiJetSC4NG:default

  - **Threshold**: pt >= 25

- **Object 4**: L1puppiJetSC4NG:default

  - **Threshold**: pt >= 25

- **Object 5**: L1puppiJetSC4NG:default

  - **Threshold**: pt >= 25

- **Cross Masks**:

  - (leg2.bTagScore + leg3.bTagScore + leg4.bTagScore + leg5.bTagScore) > 2.20





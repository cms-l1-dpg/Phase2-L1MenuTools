# Objects

The objects for both the performance and the rate studies are defined
centrally, by default at

```
configs/<VERSION>/objects
```

All objects defined in yaml files in this directory will be found by
the code.

## Object configuration
Below is an example for an object definition. The outermost key (`gmtMuon`)
references the name of the object in the NTuples. Then `ids` can be defined.
All other key-value pairs at the top level of the definition (`label`,
`match_dR` etc.) are merely defaults that are overwritten by whatever is
defined in a specific id. In addition `eta_ranges` defines the detector regions
on which `cuts` can be defined in the `ids`, e.g. the `oldRateID` applies a cut
on `quality` only in the `overlap` region, which is defined in `eta_ranges`.
A default ID is also defined in the example below, which does not add any
cuts or criteria to the default values.

```yaml
gmtMuon:
  label: "GMT Muon"
  match_dR: 0.3 
  eta_ranges:
    inclusive: [0, 7]
    barrel: [0, 0.83]
    overlap: [0.83, 1.24]
    endcap: [1.24, 2.4]
  ids:
    default: {}
    oldRateID:
      label: "GMT Muon, Qual>=12 in OMTF"
      cuts:
        overlap:
          - "{quality} >= 12"
```

Cut strings are python expressions in which `{field}` stands for a field of the object
(e.g. `{pt}`); several fields can appear in one expression, e.g. `"{ecalIso} < 9 + 0.02*{pt}"`.
The cuts listed under an eta range apply only to objects in that range.

## HLT objects

The Phase-2 HLT collections of the L1+HLT nanos (`hltMuon`, `hltElectron`, `hltPhoton`,
`hltAK4PuppiJet` and its JEC-corrected version `hltAK4PuppiJetCorr`, `hltHpsPFTau`, the HLT HT/MHT
`hltPuppiJetCorrSums`, `hltPFPuppiHT` and `hltPuppiJetSums`, see below) are defined in `configs/V50nano/objects/hlt.yaml`, with ids
that approximate the HLT menu selections (`HLTrigger/Configuration/python/HLT_75e33`, e.g.
`hltElectron:WPTight` for `HLT_Ele32_WPTight_Unseeded`, `hltHpsPFTau:MediumDeepTau` for
`HLT_DoubleMediumDeepTauPFTauHPS35_eta2p1`). The yaml comments give the HLT filter behind every
cut and what the nano cannot reproduce (e.g. the HGCAL e/gamma variables in the endcap); such ids
are labelled "(approx.)". Objects whose name starts with `hlt` are treated as trigger objects like
the `L1*` ones (axis labels say "HLT"; scaling thresholds from the `HLT<group>` entries of
`configs/scaling_thresholds.yaml`). Plot configs: `configs/V50nano/object_performance/hlt_*.yaml`.

### HLT jet energy corrections

The nano stores `hltAK4PFPuppiJets`, the HLT AK4 PUPPI jets *before* the jet energy corrections
(`hltAK4PuppiJet`, pT ~0.8 x gen), while the HLT paths cut on `hltAK4PFPuppiJetsCorrected`.
`menu_tools/caching/make_hlt_jets_corr.py` (a post-caching step, run by
`scripts/condor/caching_170pre6HLT_post.sh`) applies the HLT correction and writes two objects:

* `hltAK4PuppiJetCorr`: the jets with corrected `pt` and `mass` (all other fields copied, plus
  `rawPt` and `jecFactor`), sorted by corrected pT. These are the HLT jets used in the plots.
* `hltPuppiJetCorrSums` (`L1puppiJetSC4sums` layout, ids `HT` / `MHT`): HT and MHT with the
  definitions of the HLT menu producers, HT as `hltPFPuppiHT` (`HLT_PFPuppiHT1070`: jet pT > 30 GeV,
  |eta| < 2.4, pT sum) and MHT as `hltPFPuppiMHT` (jet E_T > 30 GeV, |eta| < 5, E_T vector sum).

The HLT correction chain (`HLT_75e33/modules/hltAK4PFPuppiJetCorrector*_cfi.py`) is
L1FastJet x L2Relative x L3Absolute with payload `AK4PFPuppiHLT`. In the global tag of the
production, `auto:phase2_realistic_T35`, L1FastJet and L3Absolute are the constant 1 (no rho
needed) and only L2Relative, a function of the raw (pT, eta), is non-trivial. The payloads are in
`configs/V50nano/cache_objects/hlt_jec/` (dumped with `cmsRun dump_jec_cfg.py` there, in a
CMSSW_17_0_0_pre6 area); a production with another global tag needs a new dump.

Validation on ttbar (100k events): the corrected-jet E_T sum (E_T > 30, |eta| < 5) reproduces the
nano `hltPFPuppiHT` (the sumEt of `hltPFPuppiMHT`) within 0.5 GeV in 99.9% of the events; emulated
HT > 1070 agrees with `HLT_PFPuppiHT1070` event by event (409/409) and a corrected jet with
pT > 520, |eta| < 5 with `HLT_AK4PFPuppiJet520` (355/355; 3 more events with a jet at
|eta| 2.4-2.7 fail the |eta| < 2.4 L1 seed included in the bit); every
`HLT_PFPuppiMETTypeOne140_PFPuppiMHT140` event has emulated MHT > 140 (10973/10974).
The corrected response (median pT / gen pT, ttbar) is ~1.0-1.1 above 100 GeV for |eta| < 2.4
and up to ~1.15 at 30-50 GeV; in 2.4 < |eta| < 3 the raw response is already ~1.3-1.5 and the
correction raises it further.

### HLT energy sums

`hltPuppiJetCorrSums:HT` / `:MHT` (above) are the HLT HT and MHT. For comparison:
`hltPFPuppiHT:default` is the nano's `hltPFPuppiHT_pt`, one value per event (used like
`L1puppiMET:default`), the sumEt of `hltPFPuppiMHT` (corrected jets E_T > 30, |eta| < 5, E_T
sum), i.e. not the HT `HLT_PFPuppiHT1070` cuts on; `hltPuppiJetSums` (`make_hlt_sums.py`) is HT /
MHT from the uncorrected jets (pT > 30, |eta| < 2.4, ~0.77 x gen). `hltPFPuppiMET` (the type-1
PUPPI sumEt in 17_0_0_pre6 nanos) is not cached.

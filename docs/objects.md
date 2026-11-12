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
`hltAK4PuppiJet`, `hltHpsPFTau`, and the `hltPuppiJetSums` HT/MHT built by
`menu_tools/caching/make_hlt_sums.py`) are defined in `configs/V50nano/objects/hlt.yaml`, with ids
that approximate the HLT menu selections (`HLTrigger/Configuration/python/HLT_75e33`, e.g.
`hltElectron:WPTight` for `HLT_Ele32_WPTight_Unseeded`, `hltHpsPFTau:MediumDeepTau` for
`HLT_DoubleMediumDeepTauPFTauHPS35_eta2p1`). The yaml comments give the HLT filter behind every
cut and what the nano cannot reproduce (e.g. the HGCAL e/gamma variables in the endcap); such ids
are labelled "(approx.)". Objects whose name starts with `hlt` are treated as trigger objects like
the `L1*` ones (axis labels say "HLT"; scaling thresholds from the `HLT<group>` entries of
`configs/scaling_thresholds.yaml`). Plot configs: `configs/V50nano/object_performance/hlt_*.yaml`.

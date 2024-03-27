# Objects

The objects for both the performance and the rate studies are defined
centrally, by default at

```
configs/<VERSION>/objects
```

All objects found in yaml files in this directory will be found by
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

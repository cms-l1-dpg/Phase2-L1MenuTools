# HLT ParT (AK4 ParticleTransformer) for τ and b tagging, p2nano v2

This folder holds the HLT ParT tagger on HLT AK4 PUPPI jets, added to the menu-tools τ and b-tag plots.
It uses only the p2nano **v2** L1+HLT production (CMSSW_17_0_0_pre6, `P2Nano_L1HLT_noSel_v2`).
v1 stored ParT only in events where the ParT path ran, so v1 ParT is biased.
v2 stores ParT and DeepFlavour for every HLT jet with pT > 5 and |η| < 2.1 (`ParT_inputFilled`). Other jets get −10.

Plots: https://alobanov.web.cern.ch/L1T/Phase2/menu/Validation/MenuTools_AR26/V50nano_170pre6HLTv2/

## Samples and cache

The cache version is `V50nano_170pre6HLTv2` (`configs/V50nano/cache_objects/caching_170pre6_HLTv2.yaml`). It has the v1 objects plus all ParT and DeepFlavour branches, hadron/parton flavour, GenVisTau, GenJet and GenPart.

| Sample | Events | Note |
|---|---|---|
| MinBias | 1,998,400 (2,094 files) | rate normalisation, 15.53 Hz/event |
| DYLL_M50 | 985,000 | 5× v1 (v1 had 200k) |
| TT | 300,000 | **inclusive tt̄**; v1 was tt̄ → 2ℓ2ν, so these are different events |
| HHTo2B2Tau | 49,103 | the same events as v1 |
| HHTo4B | — | v2 was still running (3 files on 2026-11-16); not included |

Post-processing steps:
- `make_hlt_jets_corr`, now streamed by row group, writes `hltAK4PuppiJetCorr`. It checks the JEC factor against the nano `jecFactor`: they agree to < 1.4e-4, except 74 of 227k jets at |η| bin edges.
- `make_hlt_jets_part` (new) writes `hltAK4PuppiJetParT`. It keeps jets with `ParT_inputFilled` and raw pT > 10. Its pT is the **raw** pT, as in the HLT path; `ptCorr` holds the corrected pT.
- `scripts/part/event_ids.py` writes `<version>_<sample>_EventID.parquet` with (run, luminosityBlock, event).
- `scripts/part/part_wps.py` sets the ParT working points (WPs) and writes the `HLTEMU` record of emulated ParT paths (bits `HLT_EMU_*`). `path_efficiency.py` reads `HLT_EMU_*` bits from this record.

## ParT τ ID

The reference path is `HLT_DoubleMediumPFPuppiParTTauh30_eta2p1`. It requires ≥ 2 **uncorrected** `hltAK4PFPuppiJets` with pT > 30 and |η| < 2.1 and `TauvsAll` > 0.11645. Its L1 seed is `L1_pDoublePuppiTau52_52`. It has no ΔR matching to the seed.
The emulation from the stored jets reproduces the HLT bit:
- HH: 8433/8433 events;
- minimum bias: 11/11;
- TT: 7852/7852;
- DY: 52,495 events in both; 5 only in HLT and 2 only in the emulation, from the 10-bit stored precision.

WPs (`objects/hlt.yaml`, object `hltAK4PuppiJetParT`, all with |η| < 2.1). The per-jet efficiency is for HH τh (GenVisTau, ΔR < 0.3); the fake rate is per minimum-bias jet.

| id | cut | definition | HH τ eff. | MB jet fake |
|---|---|---|---|---|
| MediumParT | 0.11645 | the HLT Medium WP | 0.952 | 6.3% |
| ParT1kHz | 0.01834 | ≤ 64 MB events (seed ∧ ≥ 2 jets pT > 30) | 0.976 | 19% |
| ParT1kHz35 | 0.01102 | same at jet pT > 35 | 0.981 | 25% |
| ParTEff90 | 0.4194 | 90% per-jet efficiency | 0.900 | 2.2% |
| ParTEff80 | 0.7651 | 80% per-jet efficiency | 0.800 | 0.75% |

Minimum-bias rates of the full paths (seed ∧ HLT): rate = 31,038 kHz × fraction, with Garwood 68% intervals.

| path | MB events | rate (kHz) |
|---|---|---|
| L1 seed | 1305 | 20.27 [19.71, 20.84] |
| HLT DeepTau (HPS 35) | 66 | 1.03 [0.90, 1.17] |
| HLT ParT Medium (jets 30) | 11 | 0.17 [0.12, 0.24] |
| ParT 1 kHz, jets 30 | 64 | 0.99 [0.87, 1.13] |
| ParT 1 kHz, jets 35 | 64 | 0.99 [0.87, 1.13] |
| ParT Eff90 / Eff80 | 2 / 0 | 0.03 / < 0.03 |

The rates rest on O(10–60) minimum-bias events. The MB/NuGun samples reuse pileup collisions, so the effective count can be lower than the event count. The 64 ParT 1 kHz events have 64 distinct leading tagged jets, so no repeated collision is visible at that level.

Path efficiency in the acceptance of ≥ 2 GenVisTau with pT > 25 and |η| < 2.1, at the same HLT rate of about 1 kHz (68% CL):

| path | HH (9,595 ev.) | DY v2 (13,583 ev.) |
|---|---|---|
| HLT DeepTau | 0.429 (4120) | 0.057 (778) |
| HLT ParT Medium (0.17 kHz) | 0.515 (4940) | 0.094 (1283) |
| ParT 1 kHz, jets 30 | **0.556** (5335) [0.551, 0.561] | **0.099** (1343) |
| ParT 1 kHz, jets 35 | 0.527 (5061) | 0.077 (1051) |

Paired against ParT 1 kHz on HH, HLT DeepTau gains 303 events and loses 1518.

## ParT b tag (tt̄, v2)

`btag_tt.yaml` now shows two ParT discriminants next to DeepFlavour prob(b) and L1:
- `ParT b/(b+c+uds+g)`;
- `ParT prob(b)`.

New WPs on `hltAK4PuppiJetCorr` at the v2 light mis-id:
- `bTagParTLight10` / `bTagParTLight1` (b/(b+c+uds+g));
- `bTagParTbLight10` / `bTagParTbLight1` (prob(b)).

The block `BTagTT_eta2p1` is the same plot restricted to |η| < 2.1. In |η| < 2.4, ParT leaves jets with |η| 2.1–2.4 untagged.

b-jet efficiency at fixed light mis-id, jet pT > 30:

| region | light mis-id | DeepFlavour prob(b) | ParT b/(b+c+uds+g) | ParT prob(b) | L1 |
|---|---|---|---|---|---|
| \|η\| < 2.4 | 1% | 0.707 | 0.751 | 0.790 | 0.071 |
| \|η\| < 2.4 | 5% | 0.843 | 0.853 | 0.870 | 0.239 |
| \|η\| < 2.4 | 10% | 0.892 | 0.885 | 0.893 | |
| \|η\| < 2.1 | 1% | 0.746 | 0.792 | 0.832 | |
| \|η\| < 2.1 | 5% | 0.871 | 0.900 | 0.920 | |

ParT gains most at high pT: at 1% light mis-id with pT > 100 and |η| < 2.1, ParT reaches 0.864 against 0.722 for DeepFlavour.

## Cross-checks v1 vs v2

- Events are matched by (run, luminosityBlock, event) with `scripts/part/compare_v1_v2.py`:
  - HH has the same 49,103 events.
  - DY v2 is a superset of v1.
  - MB: 1,998,240 events are common; 800 v1-only and 160 v2-only.
- Event by event, the v1 objects are identical except for a few events. The v2 production README says the L1 emulation is not bit-reproducible. Events that differ:

  | sample | HLT bits | L1 seed | HPS τ | jets | L1nnPuppiTau |
  |---|---|---|---|---|---|
  | HH (of 49,103) | 1 | 2 | 20 | 24 | |
  | DY (of 200k) | 2 | 3 | 24 | 141 | |
  | MB | 0 | 1 | 2 | | 776 |

- Outputs are compared with `scripts/part/compare_outputs.py` → `compare_v1_v2_outputs.csv`, curve by curve against the published v1 JSON outputs:
  - HH, 370 curves: max |pull| 0.28.
  - DY, 221 curves: v2 has 5× the events; max |pull| 3.8 (L1 barrel turn-on), mean χ²/ndf 0.53.
  - The DeepTau and DeepFlavour curves agree within statistics.
- DeepFlavour WPs defined on v1 (tt̄→2ℓ2ν):
  - b efficiency is unchanged on v2: 0.888 / 0.682 at bTagLight10 / bTagLight1.
  - Light mis-id is lower on v2 inclusive tt̄: 0.093 vs 0.100 and 0.0078 vs 0.0100. The sample is different; the b-tag curves are on v2 TT and not comparable 1:1 with v1.

## Reproduce

```bash
export _myschedd_POOL=eossubmit _condor_CONDOR_HOST="tweetybird04.cern.ch, tweetybird03.cern.ch"
condor_submit scripts/condor/caching_170pre6HLTv2_minbias.sub     # MB chunks, 140 jobs
condor_submit scripts/condor/caching_170pre6HLTv2_signal.sub      # DY / TT / HH chunks
condor_submit scripts/condor/caching_170pre6HLTv2_post.sub        # merge, sums, jets Corr, ParT
for s in HHTo2B2Tau DYLL_M50 MinBias; do                             # EventID records
  python3 scripts/part/event_ids.py configs/V50nano/cache_objects/caching_170pre6_HLTv2.yaml --sample $s; done
python3 scripts/part/part_wps.py                                 # WPs, HLTEMU, part_*.csv
condor_submit scripts/condor/menu_runs_jobsh.sub joblist=scripts/condor/part_170pre6HLTv2.txt
python3 scripts/part/compare_outputs.py <v1 outputs>/V50nano_170pre6HLT/object_performance \
    outputs/V50nano_170pre6HLTv2/object_performance --subdirs turnons path_efficiency resolution \
    --csv configs/V50nano/object_performance/part/compare_v1_v2_outputs.csv
```

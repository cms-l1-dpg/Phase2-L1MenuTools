# GitLab CI object-performance workflow

The menu-validation pipeline separates Nano caching from plotting so several
`object_performance` jobs can reuse the same selected columns. It runs matching
efficiency and trigger turn-on plots only; no rate jobs are included.

## Sample-specific caches

Four cache jobs start independently:

- `cache_jet_objects`: TT input for jets, MET, HT, and MHT.
- `cache_tau_objects`: VBF $H\to\tau\tau$ input for taus.
- `cache_dy_objects`: DY input shared by electrons and muons.
- `cache_photon_objects`: $H\to\gamma\gamma$ input for photons.

Each job caches only its sample and uploads its part of `cache/V50nano_170` as
an artifact. DY and photon caching also runs the standard barrel/endcap L1 EG
merge required by the V50 object definitions.

The input variables are `JET_NANO_GLOB`, `TAU_NANO_GLOB`, `DY_NANO_GLOB`, and
`PHOTON_NANO_GLOB`. Each can contain one local or remote ROOT file or a local or
remote filesystem glob. Public V50-compatible samples are the defaults.

A sample is optional. If its variable is empty or its glob matches no files, its
cache job exits successfully without an availability marker, and the dependent
plotting jobs report that they were skipped. This supports pipelines containing,
for example, only a new VBF tau Nano. Once a file matches, access failures,
missing branches, and processing failures remain job failures rather than being
silently skipped. Set unused variables to an empty string when starting a
pipeline if their public defaults should not be processed.

## Plotting jobs

Once the relevant cache succeeds, the following jobs start automatically:

- `jet_matching_efficiency` and `jet_trigger_turnons`.
- `event_sum_turnons` for PUPPI MET, HT, and MHT, with track-only controls where
  the upstream configuration includes them.
- `tau_matching_efficiency` and `tau_trigger_turnons`.
- `electron_matching_efficiency` and `electron_trigger_turnons`.
- `muon_matching_efficiency` and `muon_trigger_turnons`.
- `photon_matching_efficiency` and `photon_trigger_turnons`.

The jobs use the upstream V50 object-performance configurations, including their
configured scaling extraction. The `dev_ar26` implementation prepares and
matches each object collection once, then reuses it across thresholds. Specialist
eta, isolation, purity, muon track-finder, and ID-comparison configurations are
not part of this initial CI set.

Each plotting job uploads its PNG, PDF, JSON, and plot-configuration outputs as
an artifact. Scaling YAML files are prefixed with the CI job name before upload,
so electron and photon L1 EG scalings cannot overwrite one another when artifacts
are combined. The optional manual `publish_plots` job downloads all plot artifacts
and copies their combined `V50nano_170` output, together with CI provenance, to
a unique EOS directory under:

```text
/eos/cms/store/group/dpg_trigger/comm_trigger/L1Trigger/cmsl1dpg/MenuTools/<branch>/pipeline-<id>/
```

The pipeline ID prevents one run from overwriting another. The publish job uses
CERN's pinned Auto DevOps EOS image, authenticates with Kerberos, and copies
files individually with the EOS client. It sets `EOS_MGM_URL` to
`root://eoscms.cern.ch` for this group area. Override `PUBLISH_EOS_BASE` when
starting a pipeline to publish under another writable EOS directory; also
override `EOS_MGM_URL` if changing EOS instances.

## Running the pipeline

Pipelines are created for GitHub pull requests when GitLab is connected using
**Run CI/CD for external repository**, for native GitLab merge requests, and
from **Build > Pipelines > Run pipeline**. Creating the pipeline starts all four
cache jobs immediately, and their dependent plotting jobs follow automatically.
Trigger `publish_plots` manually when the available plot set should be copied to
EOS; leaving it untriggered does not make the pipeline fail.

The cache jobs read CERN EOS through its internal XRootD endpoint using a
Kerberos ticket. They run in CERN's `al8-cms` image, create a Python 3.11 virtual
environment from the mounted LCG view, and install MenuTools plus the XRootD
Python bindings.

The inputs must contain the `Events` tree and the branches listed in
`configs/ci/pf_performance_caching.yaml`. The current configuration uses the
V50nano object definitions and records outputs under the `V50nano_170` label.

The cache jobs need two masked GitLab CI/CD variables using a CERN account that
can read the inputs: `AUTO_DEVOPS_CERNBOX_USER` (without `@CERN.CH`) and
`AUTO_DEVOPS_CERNBOX_PASS`. The plotting jobs do not use these credentials. The
account must also have write permission on `PUBLISH_EOS_BASE` for publication.

The Parquet caches and plot artifacts are retained for 14 days. The repository
ignores the local `cache` directory; it must remain ordinary job-local storage
rather than a link to a user-owned area.

## Equivalent local commands

The same processing can be run locally with Python 3.11 and suitable input
paths. Select only the samples that are available:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e . xrootd fsspec-xrootd

export JET_NANO_GLOB='/absolute/path/to/tt_menu_nano.root'
cache_objects configs/ci/pf_performance_caching.yaml --sample TT
object_performance configs/V50nano/object_performance/jets_matching.yaml --version V50nano_170
object_performance configs/V50nano/object_performance/jets_trigger.yaml --version V50nano_170
object_performance configs/V50nano/object_performance/jets_sc8_trigger.yaml --version V50nano_170
object_performance configs/V50nano/object_performance/met_ht_mht.yaml --version V50nano_170

export TAU_NANO_GLOB='/absolute/path/to/vbf_tau_menu_nano.root'
cache_objects configs/ci/pf_performance_caching.yaml --sample VBFHToTauTau
object_performance configs/V50nano/object_performance/tau_matching.yaml --version V50nano_170
object_performance configs/V50nano/object_performance/tau_trigger.yaml --version V50nano_170

export DY_NANO_GLOB='/absolute/path/to/dy_menu_nano.root'
cache_objects configs/ci/pf_performance_caching.yaml --sample DYLL_M50
python menu_tools/caching/merge_arrays.py --version V50nano_170 --sample DYLL_M50
object_performance configs/V50nano/object_performance/electron_matching.yaml --version V50nano_170
object_performance configs/V50nano/object_performance/electron_trigger.yaml --version V50nano_170
object_performance configs/V50nano/object_performance/muon_matching.yaml --version V50nano_170
object_performance configs/V50nano/object_performance/muon_trigger.yaml --version V50nano_170

export PHOTON_NANO_GLOB='/absolute/path/to/hgg_menu_nano.root'
cache_objects configs/ci/pf_performance_caching.yaml --sample Hgg
python menu_tools/caching/merge_arrays.py --version V50nano_170 --sample Hgg
object_performance configs/V50nano/object_performance/photons_matching.yaml --version V50nano_170
object_performance configs/V50nano/object_performance/photons_trigger.yaml --version V50nano_170
```

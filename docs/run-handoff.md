# MenuTools operator handoff

This runbook covers the current V50 menu-validation workflow on the
`gitlabCI` branch. It produces matching efficiencies, trigger turn-ons,
online-to-offline scalings, and per-object rate curves. It does not produce a
combined menu rate table.

Use GitLab CI when the input Nanos are on CERN EOS. Run directly on
`hm01.dice.priv` when the files exist only on that host, for example under
`/scratch`. GitLab Kubernetes runners cannot see files stored only on `hm01`.

## Inputs

| Variable | Expected sample | Products |
| --- | --- | --- |
| `JET_NANO_GLOB` | TTbar | jets, MET, HT, and MHT |
| `TAU_NANO_GLOB` | VBF H to tau tau | tau plots |
| `DY_NANO_GLOB` | DY to leptons | electron and muon plots |
| `PHOTON_NANO_GLOB` | H to gamma gamma | photon plots |
| `MINBIAS_NANO_GLOB` | unbiased MinBias | rate curves |

Each value may be one ROOT file or a glob. Set an unused variable to an empty
string. Without MinBias, efficiency and turn-on plots still run, but rate jobs
are skipped.

Inputs must contain an `Events` tree and the branches requested in
[`configs/ci/pf_performance_caching.yaml`](../configs/ci/pf_performance_caching.yaml).
Use Nanos from the same release, configuration, geometry, and pileup scenario
when interpreting their plots together.

## Route 1: GitLab CI with EOS inputs

Until this workflow is merged elsewhere, run the `gitlabCI` branch in the
GitLab mirror of `cms-l1-dpg/Phase2-L1MenuTools`:

1. Open **Build > Pipelines > New pipeline**.
2. Select `gitlabCI`.
3. Add the five input variables above. Set every unused input to an empty
   string so its public default is not processed.
4. Create the pipeline. Cache jobs start immediately; dependent jobs follow
   automatically.

Use an EOSCMS XRootD URL rather than assuming that `/eos` is mounted inside
the runner:

```text
root://eoscms.cern.ch//eos/cms/store/group/.../ttbar/*.root
```

A TTbar-only run sets:

```text
JET_NANO_GLOB=root://eoscms.cern.ch//eos/cms/store/group/.../ttbar/*.root
TAU_NANO_GLOB=
DY_NANO_GLOB=
PHOTON_NANO_GLOB=
MINBIAS_NANO_GLOB=
```

The project or parent GitLab group must provide masked
`AUTO_DEVOPS_CERNBOX_USER` and `AUTO_DEVOPS_CERNBOX_PASS` variables for a
CERN account that can read the input. The account also needs write permission
if the optional publish job is used.

Caches are written under `cache/V50nano_170`; plots and numerical output are
written under `outputs/V50nano_170/object_performance`. Missing optional
samples are skipped. A matched file that is unreadable, lacks required
branches, or fails during processing remains a visible failed job. Independent
sample groups continue, and artifacts are retained for 14 days.

Start the manual `publish_plots` job to retain the available output. Its
default destination is:

```text
/eos/cms/store/group/dpg_trigger/comm_trigger/L1Trigger/cmsl1dpg/MenuTools/<branch>/pipeline-<pipeline-id>/V50nano_170/
```

Set `PUBLISH_EOS_BASE` when creating the pipeline to select another writable
EOSCMS base directory.

## Route 2: run directly on hm01

For a fresh checkout:

```bash
ssh hm01.dice.priv
git clone git@github.com:cms-l1-dpg/Phase2-L1MenuTools.git
cd Phase2-L1MenuTools
git switch gitlabCI
scripts/setup_pyenv.sh
source setup.sh
```

`hm01` provides Python 3.11 and CVMFS. The setup script creates the
repository-local `pyenv` and installs MenuTools in editable mode. In later
shells, only `cd Phase2-L1MenuTools && source setup.sh` is needed.

For files held on `hm01`, use ordinary absolute paths or globs:

```bash
export JET_NANO_GLOB='/scratch/<user>/<production>/ttbar/*.root'
export TAU_NANO_GLOB=''
export DY_NANO_GLOB=''
export PHOTON_NANO_GLOB=''
export MINBIAS_NANO_GLOB=''

check_input_files "$JET_NANO_GLOB"
```

EOS can also be read from `hm01` with a
`root://eoscms.cern.ch//eos/cms/...` URL. Add the optional support and obtain
a Kerberos ticket first:

```bash
python -m pip install 'xrootd==6.2.1' 'fsspec-xrootd==0.2.4'
kinit <cern-username>@CERN.CH
```

### Cache the available samples

Run only commands for which an input was configured:

```bash
cache_objects configs/ci/pf_performance_caching.yaml --sample TT
cache_objects configs/ci/pf_performance_caching.yaml --sample VBFHToTauTau

cache_objects configs/ci/pf_performance_caching.yaml --sample Hgg
python menu_tools/caching/merge_arrays.py --version V50nano_170 --sample Hgg

cache_objects configs/ci/pf_performance_caching.yaml --sample DYLL_M50
python menu_tools/caching/merge_arrays.py --version V50nano_170 --sample DYLL_M50

cache_objects configs/ci/pf_performance_caching.yaml --sample MinBias
python menu_tools/caching/merge_arrays.py --version V50nano_170 --sample MinBias
```

### Produce matching and turn-on plots

```bash
# TTbar
object_performance configs/V50nano/object_performance/jets_matching.yaml --version V50nano_170
object_performance configs/V50nano/object_performance/jets_trigger.yaml --version V50nano_170
object_performance configs/V50nano/object_performance/jets_sc8_trigger.yaml --version V50nano_170
object_performance configs/V50nano/object_performance/met_ht_mht.yaml --version V50nano_170

# VBF H to tau tau
object_performance configs/V50nano/object_performance/tau_matching.yaml --version V50nano_170
object_performance configs/V50nano/object_performance/tau_trigger.yaml --version V50nano_170

# H to gamma gamma
object_performance configs/V50nano/object_performance/photons_matching.yaml --version V50nano_170
object_performance configs/V50nano/object_performance/photons_trigger.yaml --version V50nano_170

# DY
object_performance configs/V50nano/object_performance/electron_matching.yaml --version V50nano_170
object_performance configs/V50nano/object_performance/electron_trigger.yaml --version V50nano_170
object_performance configs/V50nano/object_performance/muon_matching.yaml --version V50nano_170
object_performance configs/V50nano/object_performance/muon_trigger.yaml --version V50nano_170
```

Run the photon turn-on before the electron turn-on when producing both locally.
Both can write an `L1EG` scaling; this order gives the electron-derived
scaling the same precedence used by CI.

### Produce rate curves

With a MinBias cache, run rates after the corresponding signal turn-ons so the
online-to-offline scaling files exist:

```bash
rate_plots configs/V50nano/rate_plots/jets.yaml --version V50nano_170
rate_plots configs/V50nano/rate_plots/jets_sc8.yaml --version V50nano_170
rate_plots configs/V50nano/rate_plots/met.yaml --version V50nano_170
rate_plots configs/V50nano/rate_plots/ht.yaml --version V50nano_170
rate_plots configs/V50nano/rate_plots/taus.yaml --version V50nano_170
rate_plots configs/V50nano/rate_plots/eg.yaml --version V50nano_170
rate_plots configs/V50nano/rate_plots/muons.yaml --version V50nano_170
```

The local route does not publish outputs automatically.

## Re-running with different inputs

`cache_objects` reuses an existing Parquet file without checking whether the
input glob changed. Before using the same checkout for another production, move
the old `cache/V50nano_170` and `outputs/V50nano_170` directories aside, or
use a fresh work directory. Record the input paths, Git commit, Nano production
identity, and output directory together as provenance.

For job dependencies, failure handling, and rate normalisation, see
[`docs/gitlab-ci.md`](gitlab-ci.md).

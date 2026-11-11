# GitLab CI PF object-performance workflow

The initial menu-validation pipeline separates Nano caching from plotting so
that several `object_performance` jobs can reuse the same selected columns.

The manual `cache_menu_objects` job reads the TT and VBF $H\to\tau\tau$ menu
Nanos, caches only the columns listed in
`configs/ci/pf_performance_caching.yaml`, and uploads `cache/V44nano` as an
artifact. It supports a single local or remote ROOT file and local or remote
filesystem globs.

After the cache succeeds, these jobs start automatically and download its
artifact:

- `jet_matching_efficiency`: standard and large-radius jet matching efficiency.
- `jet_trigger_turnons`: standard and large-radius jet trigger turn-ons.
- `event_sum_turnons`: PUPPI MET, HT, and MHT trigger turn-ons, with track-only
  sums retained as controls where the existing configuration includes them.
- `tau_matching_efficiency`: PUPPI and calorimeter tau matching efficiency.
- `tau_trigger_turnons`: PUPPI and calorimeter tau trigger turn-ons.

Each plotting job uploads its PNG, PDF, JSON, and plot-configuration outputs as
an artifact. Additional object-performance jobs can reuse the cache through the
same `needs` dependency when their required branches are added to the caching
configuration.

Pipelines are created for GitHub pull requests when GitLab is connected using
**Run CI/CD for external repository**, for native GitLab merge requests, and
from **Build > Pipelines > Run pipeline**. Start the manual
`cache_menu_objects` job; after it succeeds, all dependent plotting jobs start
automatically.

By default the cache job uses the public V44nano TT and VBF tau samples
configured in `.gitlab-ci.yml`. It reads them through CERN's internal EOS XRootD
endpoint using the job's Kerberos ticket. The job runs in CERN's `al8-cms`
image and creates a virtual environment using Python 3.11 from the mounted CERN
LCG view. It then isolates that environment from the LCG Python packages and
installs the versions pinned by MenuTools plus the XRootD Python bindings.

To process other compatible menu Nanos, start a pipeline with `JET_NANO_GLOB`
and `TAU_NANO_GLOB` set to remote ROOT URLs or filesystem globs, for example:

```text
root://eoscms.cern.ch//eos/cms/store/group/example/*.root
```

The inputs must contain the `Events` tree and the branches listed in
`configs/ci/pf_performance_caching.yaml`. The current configuration uses the
V44nano table names and object definitions.

The cache job needs two masked GitLab CI/CD variables, using a CERN account that
can read the inputs: `AUTO_DEVOPS_CERNBOX_USER` (without `@CERN.CH`) and
`AUTO_DEVOPS_CERNBOX_PASS`. These are the same variable names used by the
calibration CI. The plotting jobs do not use these credentials.

The Parquet cache and plot artifacts are retained for 14 days. The repository
ignores the local `cache` directory; it must remain ordinary job-local storage
rather than a link to a user-owned area.

The same commands can be run locally with Python 3.11 and suitable input paths:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e . xrootd fsspec-xrootd
export JET_NANO_GLOB='/absolute/path/to/tt_menu_nano.root'
export TAU_NANO_GLOB='/absolute/path/to/tau_menu_nano.root'
cache_objects configs/ci/pf_performance_caching.yaml
object_performance configs/V44nano/object_performance/jets_matching.yaml
object_performance configs/V44nano/object_performance/jets_trigger.yaml
object_performance configs/V44nano/object_performance/jets_sc8_trigger.yaml
object_performance configs/V44nano/object_performance/met_ht_mht.yaml
object_performance configs/V44nano/object_performance/tau_matching.yaml
object_performance configs/V44nano/object_performance/tau_trigger.yaml
```

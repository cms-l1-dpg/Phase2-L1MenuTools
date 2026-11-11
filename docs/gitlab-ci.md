# GitLab CI jet matching workflow

The initial menu-validation pipeline separates Nano caching from physics-object
plotting so that several `object_performance` jobs can reuse the same selected
columns.

The `cache_menu_objects` job:

1. Reads the selected TT menu Nano files.
2. Caches the generator and L1 jet branches listed in
   `configs/ci/jets_caching.yaml`.
3. Uploads `cache/V44nano` as an artifact for jobs in the next stage.

The dependent `jet_matching_efficiency` job downloads that artifact, produces
the barrel, endcap, forward and large-radius jet matching-efficiency plots, and
uploads the PNG, PDF, JSON and plot-configuration files as its own artifacts.
Future object-performance jobs can depend on `cache_menu_objects` in the same
way. The caching configuration must be extended when they require additional
Nano tables or branches.

Pipelines are created for GitHub pull requests when GitLab is connected using
**Run CI/CD for external repository**, for native GitLab merge requests, and
from **Build > Pipelines > Run pipeline**. Both jobs are manual. First start
`cache_menu_objects`; after it succeeds, start whichever object-performance
jobs are required.

By default the cache job uses the merged public V44nano TT sample configured
in `.gitlab-ci.yml`. It runs in CERN's `al8-cms` image, which exposes the
runner's EOS mount. The unprivileged job creates a virtual environment using
Python 3.11 from the mounted CERN LCG view, then installs MenuTools and its
dependencies there. To process another compatible menu Nano, start a pipeline
with `JET_NANO_GLOB` set to one mounted file or a filesystem glob, for example:

```text
/eos/cms/store/group/example/menu_nano.root
```

The input must contain the `Events` tree and the branches listed in
`configs/ci/jets_caching.yaml`. The current configuration uses the V44nano table
names and object definitions.

The Parquet cache artifact and final plot artifacts are retained for 14 days.
The repository ignores the local `cache` directory; it must remain ordinary
job-local storage rather than a link to a user-owned area.

The same commands can be run locally with Python 3.11:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
export JET_NANO_GLOB='/absolute/path/to/menu_nano.root'
cache_objects configs/ci/jets_caching.yaml
object_performance configs/V44nano/object_performance/jets_matching.yaml
```

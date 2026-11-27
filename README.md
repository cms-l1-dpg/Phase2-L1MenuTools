# Phase2-L1MenuTools

## Trigger efficiencies and rates

  This repository contains the python-based framework for the measurement of matching efficiencies,
  trigger turn-on curves, and scalings for the assessment of the physics performance of the CMS Phase-2 L1 Menu.

  For further instructions on how to run the tools, see the `docs`.
  Some documentation can also be found in the [wiki](https://github.com/cms-l1-dpg/Phase2-L1MenuTools/wiki).

## Setup

  These tools are expected to be used primarily on lxplus.
  To clone the repository run

  ```bash
  git clone git@github.com:cms-l1-dpg/Phase2-L1MenuTools.git
  ```

  The quickest way to set up the environment is

  ```bash
  scripts/setup_pyenv.sh
  source setup.sh
  ```

  which creates the venv `pyenv/` with Python 3.11, installs the tools into it,
  and makes it put a complete TeX Live (from cvmfs) on `PATH` when activated, as
  needed by `rate_table_tex` (the lxplus system TeX Live lacks some packages).
  Afterwards `source setup.sh` is all that is needed in a new shell.

  Alternatively, a standard venv with Python3.11 can be created on lxplus
  via `python3.11 -m venv <name_of_venv>` and all necessary
  dependencies installed via `pip install -e .`:

  ```bash
  python3.11 -m venv <name_of_venv>
  source <name_of_venv>/bin/activate
  pip install -e .
  ```

  **ATTENTION:** If you do not use the `-e` flag (editable), you will `pip install . --upgrade` whenever you pull changes.

  You can then execute the tools via

  ```python
  cache_objects <path_to_config>
  object_performance <path_to_config>
  rate_plots <path_to_config>
  rate_table <path_to_config>
  rate_table_tex <path_to_config>
  p2gt_compare --version <version> --menu <table_fname> --p2gt <P2GT menu>
  p2gt_scalings --version <version>
  ```

  `rate_table --truncated` rounds the scalings to two decimals, as the P2GT
  emulator menus do, so that both apply identical thresholds. Its outputs get a
  `_truncated` suffix, which `rate_table_tex` and `compare_menus` pick up with
  the same option.

  `p2gt_compare --version <version> --menu <table_fname> --p2gt <P2GT menu>`
  compares the `rate_table` results of a menu with the P2GT emulator decisions,
  which `cache_objects` caches from an `L1: "*_final"` entry in the MinBias
  section of the caching config (see the module docstring).

  `p2gt_scalings --version <version>` writes the scalings of a version in the format
  of the P2GT emulator menus; with `--cmssw <CMSSW_BASE>/src` straight into the menu
  folders, after checking that the menus find every scalings key they use.

## GitLab CI

The GitLab workflow caches selected objects from configurable menu Nanos and
produces V50 jet, event-sum, tau, electron, muon, and photon performance
plots. See
[`docs/gitlab-ci.md`](docs/gitlab-ci.md) for inputs, artifacts, publication, and
equivalent local commands.

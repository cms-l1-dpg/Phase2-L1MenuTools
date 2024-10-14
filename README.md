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

  A standard venv with Python3.11 can be created on lxplus
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
  ```

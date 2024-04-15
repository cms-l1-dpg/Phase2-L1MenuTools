# Phase2-L1MenuTools

## Trigger efficiencies and rates

  This repository contains the python-based framework for the measurement of matching efficiencies,
  trigger turn-on curves, and scalings for the assessment of the physics performance of the CMS Phase-2 L1 Menu.

  For further instructions on how to run the tools, see the `docs`.

## Setup

  A standard venv with Python3.11 can be created on lxplus
  via `python3.11 -m venv <name_of_venv>` and all necessary
  dependencies installed via `pip install .`:

  ```bash
  python3.11 -m venv pyenv
  source <name_of_venv>/bin/activate
  pip install .
  ```

  **ATTENTION:** Whenever you pull changes you need to `pip install . --upgrade`

  You can then execute the tools via

  ```python
  cache_objects <path_to_config>
  object_performance <path_to_config>
  rate_plots <path_to_config>
  rate_table <path_to_config>
  ```

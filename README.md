# Phase2-L1MenuTools

## Trigger efficiencies and rates

  This repository contains the python-based framework for the measurement of matching efficiencies, trigger turn-on curves, and scalings for the assessment of the physics performance of the CMS Phase-2 L1 Menu.

  The repository is organized as follows:

  * `objectPerformance`: tools for the measurement of the performance (matching efficiency, L1 turn-on efficiency curves, and online-to-offline scalings) of L1 objects. The definition of the L1 objects should follow the recommendations detailed [here](https://twiki.cern.ch/twiki/bin/view/CMS/PhaseIIL1TriggerMenuTools).

  * `rates`: tools for the measurement of trigger rates starting from the scalings derived with the tools in `objectPerformance`.

  Detailed instructions on how to run each step of the workflow are
  provided in each folder.

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
  cach_objects <path_to_config>
  object_performance <path_to_config>
  rate_plots <path_to_config>
  ```

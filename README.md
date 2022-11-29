# Phase2-L1MenuTools

## Trigger efficiencies and rates

  This repository contains the python-based framework for the measurement of matching efficiencies, trigger turn-on curves, and scalings for the assessment of the physics performance of the CMS Phase-2 L1 Menu.

  The repository is organized as follows:

  * `objectPerformance`: tools for the measurement of the performance (efficiency, turn-on, scaling) of L1 objects. The definition of the L1 objects should follow the recommendations detailed [here](https://twiki.cern.ch/twiki/bin/view/CMS/PhaseIIL1TriggerMenuTools).

  * `rates`: tools for the measurement of trigger rates starting from the scalings derived with the tools in `objectPerformance`.

  Detailed instructions on how to run each step of the workflow are
  provided in each folder.

## Setup of Python environment
  **Note:** The code should run without any setup on `lxplus`.

  In the event of failure of the
  central setup, the following steps are required to
  install a new Python environment.

### Install miniconda
  To install `miniconda` run the following commands:

    cd ~
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh

### Install the environment for the framework
  Specify the path to your `miniconda3` installation under `prefix`
  in `environment.yml` (working examples of `environment.yml` files
  are provided in the `objectPerformance` and `rates` folders) and run

    conda env create -f environment.yml

  This will create a new environment named `py310`.

  To execute the scripts in the repo you need to modify the [shebang](https://en.wikipedia.org/wiki/Shebang_%28Unix%29)
  (the very first line of the executable `.py` files which starts
  with `#!`) to point
  to your newly set up Python installation. To find the path run

    conda activate py310  
    which python

  and replace the current path in the shebang with the output.

  More details on how to set up a `conda` environment using a shared
  `.yml` file can be found
  [here](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#sharing-an-environment).


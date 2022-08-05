# Object Performance Tools

## Setup of Python environment
  The code has been tested on lxplus,
  but it should work on any machine that can access `/eos/`.

### Install miniconda
  To install `miniconda` run the following commands:

    wget https://repo.anaconda.com/miniconda/Miniconda3-py39_4.12.0-Linux-x86_64.sh
    sh Miniconda3-py39_4.12.0-Linux-x86_64.sh "${PATH}/miniconda3"

  Make sure you are installing the latest version by
  checking out the available installers [here](https://docs.conda.io/en/latest/miniconda.html#linux-installers).

### Install the environment for the framework
  The easiest way to set up the `conda` environment is to
  use the `environment.yml` file provided.
  Specify the path to your `miniconda3` installation in `prefix`
  and run:

    conda env create -f environment.yml

  This will create a new environment named `py310`.
  Before running the next steps, just activate the environment:

    conda activate py310  

## Caching the NTuple trees
  In order to run the below steps, the object
  trees from the L1NTuples need to be cached
  as akward arrays written to .parquet files.
  In order to do this, edit `cfg.yaml` specifying
  which trees and branches are to be loaded
  from which NTuple and run

  ```
  ./ntuple_loader.py
  ```

## Efficiency Plots
  To run the efficiency plots configure the plots
  you wish to make in a yaml file with the structure
  of e.g. `cfg_plots_dy.yaml` and then run

  ```
  ./plotter.py cfg_plots_dy.yaml
  ```

## Scalings
  Not implemented yet.

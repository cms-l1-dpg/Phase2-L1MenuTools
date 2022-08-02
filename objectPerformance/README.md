# Object Performance Tools

## Setup of Python environment
  In the final version of this code no
  setup will be required. Should the provided
  Python installation not work for some reason
  it can be installed locally from `environment.yml`.
  The documentation on how to do this can be found
  [here](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#sharing-an-environment).
  Most importantly you need to have `conda` or `miniconda`
  installed and then run

  ```
  conda env create -f environment.yml
  ```

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

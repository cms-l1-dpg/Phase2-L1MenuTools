# Object Performance Tools

  The code has been tested on lxplus,
  but should work on any machine that can access `/eos`.

## Caching the NTuple trees
  In order to run the below steps, the object
  trees from the L1NTuples need to be cached
  as awkward arrays written to .parquet files.
  In order to do this, edit `cfg.yaml` specifying
  which trees and branches are to be loaded
  from which NTuple and run

  ```
  ./cache_objects.py
  ```

## Efficiency and Scalings
  To produce matching efficiency and scaling plots,
  configure the plots you wish to make in a `.yaml` file
  with the structure of e.g. `cfg_plots_dy.yaml` and then run

  ```
    ./plotter.py --cfg_plots=cfg_plots_dy.yaml
  ```

  or

  ```
    ./plotter.py -c=cfg_plots_dy.yaml
  ```
  
  The outputs will be written to the `outputs` directory. The
  scalings are plottet automatically when a `scaling_pct` is
  configured in the plot config.

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
  in `environment.yml` and run

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

#!/afs/cern.ch/user/d/dhundhau/public/miniconda3/envs/py310/bin/python
import argparse
import yaml

from scaler import Scaler
from menu import MenuTable
from menu_config import MenuConfig

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "cfg",
        default="cfg_caching/V22.yaml",
        help=""
    )
    args = parser.parse_args()

    with open(args.cfg, 'r') as f:
        cfg = yaml.safe_load(f)

    path_to_scalings = "/eos/user/m/mbonanom/www/Postdoc/L1PhaseII/V29/scalings/"
    scaler = Scaler(path_to_scalings)
    scaler.collect_scalings
    scaler.scaling_dict

    for menu_title, menu_cfg in cfg.items():
        menu_config = MenuTable(menu_cfg)
        menu_config.make_table


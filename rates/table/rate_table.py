#!/afs/cern.ch/user/d/dhundhau/public/miniconda3/envs/py310/bin/python
import argparse
import yaml

from scaler import Scaler
from menu_table import MenuTable
from menu_config import MenuConfig

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "cfg",
        default="cfg/v29/v29_cfg.yml",
        help=""
    )
    args = parser.parse_args()

    with open(args.cfg, 'r') as f:
        cfg = yaml.safe_load(f)

    for menu_title, menu_cfg in cfg.items():
        scaler = Scaler(menu_cfg)
        scaler.collect_scalings
        scaler.dump_scalings

        menu_config = MenuTable(menu_cfg)
        table = menu_config.make_table()
        menu_config.dump_table(table)
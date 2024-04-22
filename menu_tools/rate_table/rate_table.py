import argparse
import yaml

from menu_tools.rate_table.menu_table import MenuTable


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config_file",
        help="Path to the menu config file, e.g. `configs/V29/rate_table/v29_cfg.yml`",
        default="configs/V38nano/rate_table/v38_cfg.yml",
    )
    args = parser.parse_args()

    with open(args.config_file, "r") as f:
        menu_config_dict = yaml.safe_load(f)

    menu_table = MenuTable(menu_config_dict)
    menu_table.make_table()
    menu_table.print_table()
    menu_table.save_table()
    menu_table.dump_masks()

    # menu_table.compute_tot_and_pure()

if __name__ == "__main__":
    main()

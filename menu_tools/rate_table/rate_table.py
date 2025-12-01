import argparse
import os
import yaml

from menu_tools.rate_table.menu_table import MenuTable


def _extract_version(path: str) -> str:
    parts = path.split(os.sep)
    try:
        idx = parts.index("configs")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    except ValueError:
        pass
    return "unknown_version"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config_file",
        help="Path to the menu config file, e.g. `configs/V29/rate_table/v29_cfg.yml`",
        default="configs/V38nano/rate_table/v38_cfg.yml",
    )
    parser.add_argument("--version", type=str, help="Override version for output/caching", default=None)
    args = parser.parse_args()

    with open(args.config_file, "r") as f:
        menu_config_dict = yaml.safe_load(f)

    config_version = _extract_version(args.config_file)

    menu_table = MenuTable(menu_config_dict, config_version=config_version, override_version=args.version)
    menu_table.make_table()
    menu_table.print_table()
    menu_table.save_table()
    menu_table.dump_masks()

    # menu_table.compute_tot_and_pure()


if __name__ == "__main__":
    main()

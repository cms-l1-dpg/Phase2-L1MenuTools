import argparse
import sys
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
    # ensure log printouts are flushed per line for easier monitoring when output is piped, e.g via tee
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config_file",
        help="Path to the menu config file, e.g. `configs/V29/rate_table/v29_cfg.yml`",
        default="configs/V38nano/rate_table/v38_cfg.yml",
    )
    parser.add_argument("--version", type=str, help="Override version for output/caching", default=None)
    parser.add_argument(
        "--scalings",
        type=str,
        help=(
            "Override version the online-to-offline scalings are loaded from. "
            "Takes precedence over --version for the scalings only; output "
            "filenames get a `_scalings_<version>` suffix."
        ),
        default=None,
    )
    parser.add_argument(
        "--signal",
        type=str,
        help=(
            "Override the sample from the config with a signal sample, to get "
            "per-seed signal efficiencies instead of rates. The rate column is "
            "dropped and output filenames get a `_<sample>` suffix."
        ),
        default=None,
    )
    args = parser.parse_args()

    with open(args.config_file, "r") as f:
        menu_config_dict = yaml.safe_load(f)

    config_version = _extract_version(args.config_file)

    menu_table = MenuTable(
        menu_config_dict,
        config_version=config_version,
        override_version=args.version,
        override_scalings_version=args.scalings,
        override_sample=args.signal,
    )
    menu_table.make_table()
    menu_table.print_table()
    menu_table.save_table()
    menu_table.dump_masks()

    # menu_table.compute_tot_and_pure()


if __name__ == "__main__":
    main()

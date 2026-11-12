import argparse

import pytest

from menu_tools.utils.versions import add_version_argument, get_versions, parse_args


def make_parser(several_configs: bool) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("cfg", nargs="+" if several_configs else None)
    add_version_argument(parser)
    parser.add_argument("--scalings")
    return parser


@pytest.mark.parametrize(
    "argv, several_configs, cfg, versions",
    [
        ("cfg.yml", False, "cfg.yml", [None]),
        ("cfg.yml --version A B", False, "cfg.yml", ["A", "B"]),
        ("--version A B cfg.yml", False, "cfg.yml", ["A", "B"]),
        ("a.yaml --version A b.yaml", True, ["a.yaml", "b.yaml"], ["A"]),
        ("--version A a.yaml b.yaml --scalings S", True, ["a.yaml", "b.yaml"], ["A"]),
        ("a.yaml --version=A b.yaml", True, ["a.yaml", "b.yaml"], ["A"]),
        ("a.yaml --scalings S b.yaml", True, ["a.yaml", "b.yaml"], [None]),
    ],
)
def test_config_files_anywhere(argv, several_configs, cfg, versions):
    parser = make_parser(several_configs)
    args = parse_args(parser, argv.split())
    assert args.cfg == cfg
    assert get_versions(parser, args) == versions


def test_options_after_versions_kept():
    args = parse_args(make_parser(False), "--version A cfg.yml --scalings S".split())
    assert args.scalings == "S"


def test_no_version_left_is_an_error():
    with pytest.raises(SystemExit):
        parse_args(make_parser(False), "--version cfg.yml".split())

"""`--version` handling shared by object_performance, rate_plots and rate_table.

`--version` takes one or more versions, and the command is run once per version, e.g.

    object_performance cfg1.yaml cfg2.yaml --version V50nano_170pre{6,5}{,_140PU}

(braces unquoted, so that bash expands them). The list ends at the next option (`--scalings`
etc.) or at the end of the command, so the config files have to come before `--version`.
"""
import argparse
import traceback
from typing import Callable, Optional


VERSION_HELP = (
    "Override version(s) for output/caching. Several versions run the command once per "
    "version, e.g. `--version V50nano_170pre{6,5}{,_140PU}` (braces unquoted). Everything "
    "after --version up to the next option is taken as a version, so put config files before it."
)


def add_version_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--version", type=str, nargs="+", default=None, help=VERSION_HELP)


def get_versions(parser: argparse.ArgumentParser, args: argparse.Namespace) -> list[Optional[str]]:
    """The versions to run, `[None]` (= the config's own version) if --version wasn't given."""
    if not args.version:
        return [None]
    configs = [v for v in args.version if v.endswith((".yaml", ".yml"))]
    if configs:
        parser.error(
            f"--version got config file(s) {configs}: put the config files before --version"
        )
    if any("{" in v or "}" in v for v in args.version):
        parser.error(
            f"--version got unexpanded braces in {args.version}: leave them unquoted so bash expands them"
        )
    return args.version


def run_per_version(versions: list[Optional[str]], run: Callable[[Optional[str]], None]) -> None:
    """Calls `run(version)` for each version.

    A single version runs exactly as before (an error ends the command with its traceback).
    With several, a failing version is reported and the rest still run; the command then
    exits non-zero listing the failures.
    """
    if len(versions) == 1:
        run(versions[0])
        return

    failed = []
    for i, version in enumerate(versions, 1):
        print(f"=== [{i}/{len(versions)}] version {version} ===")
        try:
            run(version)
        except Exception:
            traceback.print_exc()
            print(f"=== version {version} FAILED, continuing with the next one ===")
            failed.append(version)
    if failed:
        raise SystemExit(f"Failed for {len(failed)}/{len(versions)} versions: {' '.join(failed)}")
    print(f"=== done for all {len(versions)} versions ===")

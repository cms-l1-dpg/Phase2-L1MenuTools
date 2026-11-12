"""Resolve local or remote input paths used by the object cacher."""

import argparse
import glob
import os
import sys

import fsspec


REMOTE_PREFIXES = ("root://", "http://", "https://")


def resolve_input_files(input_path: str) -> list[str]:
    """Return files matching one local or fsspec-compatible input path."""
    input_path = os.path.expandvars(input_path).strip()
    if not input_path:
        return []

    if input_path.startswith(REMOTE_PREFIXES):
        filesystem, path = fsspec.core.url_to_fs(input_path)
        if glob.has_magic(path):
            return [
                filesystem.unstrip_protocol(match)
                for match in sorted(filesystem.glob(path))
            ]
        return [input_path] if filesystem.exists(path) else []

    return sorted(glob.glob(os.path.expanduser(input_path)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check whether a local or remote input path matches any files."
    )
    parser.add_argument("input_path", help="File path or filesystem glob to check.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    matches = resolve_input_files(args.input_path)
    if not matches:
        print(f"No input files match: {args.input_path}")
        return 3

    print(f"Matched {len(matches)} input file(s):")
    for match in matches:
        print(f"  {match}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

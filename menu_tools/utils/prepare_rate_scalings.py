"""Restore object-performance scaling artifacts for rate plots.

Object-performance jobs prefix scaling YAML files with the GitLab job name so
artifacts from independent samples do not overwrite one another. Rate plots use
canonical object:id:region.yaml names. This helper copies the selected job
artifacts back to those names.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


def restore_scalings(directory: Path, job_names: list[str]) -> list[Path]:
    """Restore prefixed YAML files; later jobs take precedence on collisions."""
    restored: list[Path] = []
    directory.mkdir(parents=True, exist_ok=True)

    for job_name in job_names:
        prefix = f"{job_name}_"
        sources = sorted(directory.glob(f"{prefix}*.yaml"))
        print(f"Restoring {len(sources)} scaling files from {job_name}")
        for source in sources:
            destination = directory / source.name.removeprefix(prefix)
            shutil.copy2(source, destination)
            restored.append(destination)

    return restored


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directory", type=Path, help="object-performance scaling directory"
    )
    parser.add_argument(
        "--from-job",
        action="append",
        default=[],
        dest="job_names",
        help="CI job prefix to restore; repeat in precedence order",
    )
    args = parser.parse_args()

    restore_scalings(args.directory, args.job_names)


if __name__ == "__main__":
    main()

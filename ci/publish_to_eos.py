#!/usr/bin/env python3
"""Copy a directory tree to EOS through the XRootD Python client."""

import argparse
from pathlib import Path, PurePosixPath


def require_success(status, action: str) -> None:
    if not status.ok:
        raise RuntimeError(f"{action} failed: {status}")


def ensure_directory(filesystem, remote_path: str, client) -> None:
    status, _ = filesystem.stat(remote_path)
    if status.ok:
        return

    status, _ = filesystem.mkdir(
        remote_path,
        flags=client.flags.MkDirFlags.MAKEPATH,
    )
    require_success(status, f"creating {remote_path}")


def publish(local_directory: Path, remote_directory: str, endpoint: str) -> None:
    from XRootD import client

    if not local_directory.is_dir():
        raise FileNotFoundError(f"Local directory does not exist: {local_directory}")

    remote_root = PurePosixPath("/") / remote_directory.lstrip("/")
    filesystem = client.FileSystem(endpoint)
    ensure_directory(filesystem, str(remote_root), client)

    files = sorted(path for path in local_directory.rglob("*") if path.is_file())
    if not files:
        raise RuntimeError(f"No files found below {local_directory}")

    created_directories = {remote_root}
    for local_path in files:
        relative_path = local_path.relative_to(local_directory)
        remote_path = remote_root / relative_path
        if remote_path.parent not in created_directories:
            ensure_directory(filesystem, str(remote_path.parent), client)
            created_directories.add(remote_path.parent)

        remote_url = f"{endpoint}/{remote_path}"
        status, _ = filesystem.copy(
            str(local_path.resolve()),
            remote_url,
            force=True,
        )
        require_success(status, f"copying {local_path} to {remote_url}")
        print(f"{local_path} -> {remote_url}")

    print(f"Published {len(files)} files to {endpoint}/{remote_root}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("local_directory", type=Path)
    parser.add_argument("remote_directory")
    parser.add_argument(
        "--endpoint",
        default="root://eosuser.cern.ch",
        help="XRootD endpoint used for the upload",
    )
    args = parser.parse_args()
    publish(args.local_directory, args.remote_directory, args.endpoint.rstrip("/"))


if __name__ == "__main__":
    main()

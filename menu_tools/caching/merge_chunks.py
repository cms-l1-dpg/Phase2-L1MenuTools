"""Merge the per-chunk parquet files of chunked caching into the standard cache files.

`cache_objects <cfg> --files-per-job N --job I` caches files [I*N, (I+1)*N) of the sorted
input list of each sample into
    <cache>/<version>/chunks/<version>_<sample>_<object>_chunkNNNNN.parquet
This script concatenates the chunks of each sample/object in chunk order (= sorted file
order, so all objects of a sample stay row-aligned) into
    <cache>/<version>/<version>_<sample>_<object>.parquet
It refuses to merge if a chunk is missing (unless --allow-missing), since a missing chunk
in one object but not another would break the alignment. Each chunk becomes one parquet
row group (streamed, so memory stays at about one chunk). The chunk files are left in
place; delete <cache>/<version>/chunks/ by hand after checking the merged files.

Usage:
    python3 menu_tools/caching/merge_chunks.py <cfg.yaml> --files-per-job N \
        [--samples MinBias] [--objects L1gmtTkMuon ...] [--allow-missing] [--dry-run]
"""

import argparse
import os
import sys

import awkward as ak
import yaml

from menu_tools.caching.cache_objects import (
    chunk_dir,
    chunk_suffix,
    n_chunks,
    sorted_ntuple_files,
)
from menu_tools.utils import constants


def merge_one(version, sample, obj, nchunks, allow_missing=False, dry_run=False):
    name = f"{version}_{sample}_{obj}"
    target = os.path.join(constants.CACHE_DIR, version, name + ".parquet")
    if os.path.exists(target):
        print(f"{target} exists, skipping")
        return True
    chunks = [
        os.path.join(chunk_dir(version), name + chunk_suffix(i) + ".parquet")
        for i in range(nchunks)
    ]
    missing = [i for i, c in enumerate(chunks) if not os.path.exists(c)]
    if missing:
        print(f"{name}: {len(missing)}/{nchunks} chunks missing: {missing[:20]}")
        if not allow_missing:
            return False
        chunks = [c for i, c in enumerate(chunks) if i not in missing]
    print(f"{name}: merging {len(chunks)} chunks -> {target}")
    if dry_run:
        return True

    n_events = 0

    def _iter():
        nonlocal n_events
        for c in chunks:
            arr = ak.from_parquet(c)
            n_events += len(arr)
            yield arr

    ak.to_parquet_row_groups(_iter(), target + ".tmp")
    os.replace(target + ".tmp", target)
    print(f"{name}: {n_events} events")
    return True


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("cfg", help="caching config used for the chunked caching")
    parser.add_argument("--files-per-job", type=int, required=True)
    parser.add_argument("--samples", nargs="+", default=None)
    parser.add_argument("--objects", nargs="+", default=None)
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--dry-run", "-d", action="store_true")
    args = parser.parse_args()

    with open(args.cfg) as f:
        cfg = yaml.safe_load(f)
    ok = True
    for version, samples in cfg.items():
        for sample, sample_cfg in samples.items():
            if args.samples and sample not in args.samples:
                continue
            nfiles = len(sorted_ntuple_files(sample_cfg["ntuple_path"]))
            nchunks = n_chunks(nfiles, args.files_per_job)
            print(f"{version} {sample}: {nfiles} files -> {nchunks} chunks")
            for tree, object_branches in sample_cfg["trees_branches"].items():
                for obj in object_branches:
                    if args.objects and obj not in args.objects:
                        continue
                    ok &= merge_one(
                        version, sample, obj, nchunks, args.allow_missing, args.dry_run
                    )
    if not ok:
        sys.exit("Some objects were not merged (missing chunks), see above")


if __name__ == "__main__":
    main()

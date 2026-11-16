"""Per-event (run, luminosityBlock, event) of a cached sample, row-aligned with its cache.

Reads the sorted input file list of the sample from the caching config (the order of
cache_objects / chunked caching) and writes
    <cache>/<version>/<version>_<sample>_EventID.parquet   (fields run, luminosityBlock, event)
Checks: no duplicate event IDs; if <version>_<sample>_L1.parquet exists, the number of rows
equals it. Used to map the p2nano v1 and v2 caches of the same events onto each other
(scripts/part/compare_v1_v2.py).

    python3 scripts/part/event_ids.py configs/V50nano/cache_objects/caching_170pre6_HLTv2.yaml \\
        --sample HHTo2B2Tau [--out <dir>]
"""

import argparse
import os
import sys

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import uproot
import yaml

from menu_tools.caching.cache_objects import sorted_ntuple_files
from menu_tools.utils import constants

BR = ["run", "luminosityBlock", "event"]


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("cfg")
    p.add_argument("--sample", required=True)
    p.add_argument("--out", default=None, help="output dir (default: the cache dir)")
    args = p.parse_args()
    with open(args.cfg) as f:
        cfg = yaml.safe_load(f)
    (version, samples), = cfg.items()
    files = sorted_ntuple_files(samples[args.sample]["ntuple_path"])
    print(f"{version} {args.sample}: {len(files)} files")
    cols = {b: [] for b in BR}
    for i, fn in enumerate(files):
        with uproot.open(fn) as f:
            a = f["Events"].arrays(BR, library="np")
        for b in BR:
            cols[b].append(a[b].astype(np.int64 if b == "event" else np.int32))
        if i % 200 == 0:
            print(f"  {i}/{len(files)}", flush=True)
    tab = pa.table({b: np.concatenate(v) for b, v in cols.items()})
    ids = np.stack([tab[b].to_numpy().astype(np.int64) for b in BR], 1)
    n_unique = len(np.unique(ids, axis=0))
    if n_unique != len(ids):
        sys.exit(f"{len(ids) - n_unique} duplicate event IDs")
    cache = os.path.join(constants.CACHE_DIR, version)
    l1 = os.path.join(cache, f"{version}_{args.sample}_L1.parquet")
    if os.path.exists(l1):
        n_l1 = pq.ParquetFile(l1).metadata.num_rows
        if n_l1 != len(ids):
            sys.exit(f"{len(ids)} event IDs but {n_l1} rows in {l1}")
        print(f"row count agrees with {l1}: {n_l1}")
    os.makedirs(args.out or cache, exist_ok=True)
    out = os.path.join(args.out or cache, f"{version}_{args.sample}_EventID.parquet")
    pq.write_table(tab, out + ".tmp")
    os.replace(out + ".tmp", out)
    print(f"wrote {out}: {len(ids)} events")


if __name__ == "__main__":
    main()

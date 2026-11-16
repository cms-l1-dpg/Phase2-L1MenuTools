"""Cross-check: p2nano v1 cache (V50nano_170pre6HLT) vs v2 cache (V50nano_170pre6HLTv2), event by event.

The v2 production reprocessed the same events; all v1 objects should be bit-identical. The events
are matched by (run, luminosityBlock, event): v1 IDs from the sorted v1 file lists
(<ids-dir>/ids_<HH|DY|MB>_v1.npy), v2 IDs from <v2>_<sample>_EventID.parquet
(scripts/part/event_ids.py). For each sample and object the per-event content of the listed
fields is compared (number of objects and every value); prints the number of events that differ.

    python3 scripts/part/compare_v1_v2.py --ids-dir <dir> [--samples HHTo2B2Tau DYLL_M50 MinBias]
"""

import argparse
import json
import os

import awkward as ak
import numpy as np

from menu_tools.utils import constants

V1, V2 = "V50nano_170pre6HLT", "V50nano_170pre6HLTv2"
IDK = {"HHTo2B2Tau": "HH", "DYLL_M50": "DY", "MinBias": "MB"}
OBJECTS = {
    "hltHpsPFTau": ["pt", "eta", "phi", "deepTauVSjet"],
    "hltAK4PuppiJet": ["pt", "eta", "phi", "DeepFlavour_prob_b", "DeepFlavour_prob_c"],
    "hltAK4PuppiJetCorr": ["pt", "eta"],
    "L1nnPuppiTau": ["pt", "eta", "phi"],
    "GenVisTau": ["pt", "eta", "status"],
    "GenJet": ["pt", "eta", "hadronFlavour"],
}
NO_MB = {"GenVisTau", "GenJet", "hltAK4PuppiJet", "hltAK4PuppiJetCorr"}


def key(ids):
    ids = ids.astype(np.int64)
    return (ids[:, 0] << 52) ^ (ids[:, 1] << 32) ^ ids[:, 2]


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--ids-dir", required=True)
    p.add_argument("--samples", nargs="+", default=list(IDK))
    p.add_argument("--out", default=None)
    args = p.parse_args()
    c1 = os.path.join(constants.CACHE_DIR, V1)
    c2 = os.path.join(constants.CACHE_DIR, V2)
    res = {}
    for s in args.samples:
        k1 = key(np.load(os.path.join(args.ids_dir, f"ids_{IDK[s]}_v1.npy")))
        e2 = ak.from_parquet(os.path.join(c2, f"{V2}_{s}_EventID.parquet"))
        k2 = key(np.stack([ak.to_numpy(e2[b]) for b in ("run", "luminosityBlock", "event")], 1))
        o1 = np.argsort(k1)
        pos = np.clip(np.searchsorted(k1[o1], k2), 0, len(k1) - 1)
        found = k1[o1][pos] == k2
        r1 = o1[pos][found]  # v1 row of each v2 row that exists in v1
        r2 = np.flatnonzero(found)
        print(f"{s}: v1 {len(k1)}, v2 {len(k2)} events, {found.sum()} common")
        res[s] = {"v1": int(len(k1)), "v2": int(len(k2)), "common": int(found.sum())}
        # v1 rows in increasing order for read_rows; keep the pairing
        srt = np.argsort(r1)
        r1s, r2s = r1[srt], r2[srt]
        o2 = np.argsort(r2s)
        recs = ["HLT", "L1"] + [o for o in OBJECTS if not (s == "MinBias" and o in NO_MB)]
        for obj in recs:
            f1 = os.path.join(c1, f"{V1}_{s}_{obj}.parquet")
            f2 = os.path.join(c2, f"{V2}_{s}_{obj}.parquet")
            if not (os.path.exists(f1) and os.path.exists(f2)):
                continue
            if obj in ("HLT", "L1"):
                a1 = ak.from_parquet(f1)
                a2 = ak.from_parquet(f2)
                flds = [f for f in a1.fields if f in a2.fields]
                diff = {}
                for f in flds:
                    d = int((ak.to_numpy(a1[f])[r1s] != ak.to_numpy(a2[f])[r2s]).sum())
                    if d:
                        diff[f] = d
                print(f"  {obj}: {len(flds)} bits, events differing per bit: {diff or 'none'}")
                res[s][obj] = diff
                continue
            cols = [f"{obj}_{c}" for c in OBJECTS[obj]]
            a1 = read_rows_cols(f1, r1s, cols)
            a2 = read_rows_cols(f2, np.sort(r2s), cols)[np.argsort(o2)]
            n1, n2 = ak.to_numpy(ak.num(a1[cols[0]])), ak.to_numpy(ak.num(a2[cols[0]]))
            same_n = n1 == n2
            bad = ~same_n
            for c in cols:
                eq = ak.to_numpy(ak.all(a1[c][same_n] == a2[c][same_n], axis=1))
                bad[np.flatnonzero(same_n)[~eq]] = True
            print(f"  {obj}: {bad.sum()} of {len(bad)} events differ ({(~same_n).sum()} in the object count)")
            res[s][obj] = int(bad.sum())
    if args.out:
        with open(args.out, "w") as f:
            json.dump(res, f, indent=1)


def read_rows_cols(fname, rows, cols):
    """read_rows with only some columns (rows sorted ascending)."""
    import pyarrow.parquet as pq

    md = pq.ParquetFile(fname).metadata
    start = np.cumsum([0] + [md.row_group(i).num_rows for i in range(md.num_row_groups)])
    parts = []
    for i in range(md.num_row_groups):
        sel = rows[(rows >= start[i]) & (rows < start[i + 1])]
        if len(sel):
            parts.append(ak.from_parquet(fname, columns=cols, row_groups=[i])[sel - start[i]])
    return ak.concatenate(parts) if len(parts) > 1 else parts[0]


if __name__ == "__main__":
    main()

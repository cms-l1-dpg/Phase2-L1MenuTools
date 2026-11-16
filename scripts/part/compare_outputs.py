"""Cross-check of the menu-tools outputs of two versions (e.g. v1 V50nano_170pre6HLT vs v2
V50nano_170pre6HLTv2): every curve present in both versions' json of the same plot is compared
bin by bin, pull = (y2 - y1) / sqrt(e1^2 + e2^2) (errors averaged up/down). For the same events
(HH) the curves must agree to << 1 sigma; for a larger superset (DY v2 = 5x v1) within statistics
(the two are correlated, so |pull| is an underestimate of the agreement, not of the difference).

    python3 scripts/part/compare_outputs.py <dir v1> <dir v2> --v1 V50nano_170pre6HLT \\
        --v2 V50nano_170pre6HLTv2 [--subdirs turnons path_efficiency] [--csv out.csv]
"""

import argparse
import glob
import json
import os

import numpy as np
import pandas as pd


def curves(d: dict) -> dict:
    """{curve key: (y, err)} of a turn-on / path-efficiency json."""
    out = {}
    for k, v in d.items():
        if not isinstance(v, dict):
            continue
        y = v.get("efficiency", v.get("y"))
        e = v.get("efficiency_err", None)
        if y is None:
            continue
        y = np.array(y, dtype=float)
        if e is None and "err_lo" in v:
            e = [v["err_lo"], v["err_hi"]]
        if e is None:
            continue
        e = np.array(e, dtype=float)
        err = e.mean(axis=0) if e.ndim == 2 else e
        if y.shape != err.shape:
            continue
        out[k] = (y, err)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("dir1")
    p.add_argument("dir2")
    p.add_argument("--v1", default="V50nano_170pre6HLT")
    p.add_argument("--v2", default="V50nano_170pre6HLTv2")
    p.add_argument("--subdirs", nargs="+", default=["turnons", "path_efficiency"])
    p.add_argument("--match", default="")
    p.add_argument("--csv", default=None)
    args = p.parse_args()
    rows = []
    for sub in args.subdirs:
        for f2 in sorted(glob.glob(os.path.join(args.dir2, sub, f"*{args.match}*_{args.v2}.json"))):
            name = os.path.basename(f2)[: -len(f"_{args.v2}.json")]
            f1 = os.path.join(args.dir1, sub, f"{name}_{args.v1}.json")
            if not os.path.exists(f1):
                continue
            with open(f1) as f:
                c1 = curves(json.load(f))
            with open(f2) as f:
                c2 = curves(json.load(f))
            for k in sorted(set(c1) & set(c2)):
                (y1, e1), (y2, e2) = c1[k], c2[k]
                if y1.shape != y2.shape:
                    continue
                s = np.sqrt(e1**2 + e2**2)
                ok = np.isfinite(y1) & np.isfinite(y2) & (s > 0)
                pull = (y2 - y1)[ok] / s[ok]
                rows.append(
                    {
                        "subdir": sub,
                        "plot": name,
                        "curve": k,
                        "bins": int(ok.sum()),
                        "max_abs_diff": float(np.max(np.abs(y2 - y1)[ok])) if ok.any() else np.nan,
                        "max_abs_pull": float(np.max(np.abs(pull))) if ok.any() else np.nan,
                        "chi2_ndf": float(np.mean(pull**2)) if ok.any() else np.nan,
                    }
                )
    df = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    if len(df):
        print(df.groupby("subdir")[["max_abs_diff", "max_abs_pull", "chi2_ndf"]].describe().T)
        print(df.sort_values("max_abs_pull", ascending=False).head(15).to_string(index=False))
    if args.csv:
        df.to_csv(args.csv, index=False, float_format="%.4g")


if __name__ == "__main__":
    main()

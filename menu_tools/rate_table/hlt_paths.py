"""Per HLT path: L1 seed, HLT and L1·HLT efficiencies (signal) or rates (minimum bias).

Reads the per-event bit records `HLT` (HLT_<path>) and `L1` (L1_p*_final, P2GT emulator)
from the cache and the path -> L1 seed mapping of
`configs/<version>/rate_table/hlt_paths.yml`:

    hlt_paths configs/V50nano/rate_table/hlt_paths.yml \\
        --version V50nano_dev170pre6HLT --sample DYLL_M50 TT MinBias

For each path and sample the CSV
`outputs/<version>/rate_tables/hlt_paths_<version>_<sample>.csv` holds the event counts
`n_l1` (OR of the path's L1 seeds), `n_hlt` (path fired), `n_l1_hlt` (both) and
`n_hlt_not_l1` (path fired without any of its seeds: 0 for a correct mapping of an
L1-seeded path, since the emulation runs the HLT on every event), the efficiencies with
68% Clopper-Pearson errors, and for minimum bias (`--rate`, default for samples named
`MinBias*`) the rates in kHz with 68% Garwood intervals.

Efficiencies are per event of the sample (no generator-level selection), as `rate_table
--signal`. The last row, `Total`, is the OR over paths of L1 (OR of all seeds used), HLT
and L1·HLT.

The mapping file: one entry per HLT path,

    HLT_IsoMu24_FromL1TkMuon:
      # OR of these bits; `ANY` = any L1_p*_final (L1 accept)
      l1_seeds: [L1_pSingleTkMuon22_final]
      confidence: high                        # optional, informational
"""
import argparse
import os
import sys
from typing import Optional

import awkward as ak
import numpy as np
import pandas as pd
import yaml

from menu_tools.rate_table.menu_table import garwood_interval, get_eff_err
from menu_tools.utils import constants

ANY_L1 = "ANY"


def load_bits(version: str, sample: str, record: str) -> ak.Array:
    fpath = os.path.join(
        constants.CACHE_DIR, version, f"{version}_{sample}_{record}.parquet"
    )
    return ak.from_parquet(fpath)


def l1_or(l1: ak.Array, seeds: list[str]) -> np.ndarray:
    """OR of the L1 bits `seeds` (`ANY`: all L1_p*_final bits) as a numpy bool array."""
    if ANY_L1 in seeds:
        seeds = [f for f in l1.fields if f.startswith("L1_p") and f.endswith("_final")]
    missing = [s for s in seeds if s not in l1.fields]
    if missing:
        raise KeyError(f"L1 bits {missing} not in the cached L1 record")
    out = np.zeros(len(l1), dtype=bool)
    for s in seeds:
        out |= ak.to_numpy(l1[s]).astype(bool)
    return out


def _counts_row(
    name: str, seeds: list[str], l1: np.ndarray, hlt: np.ndarray, as_rate: bool
) -> dict:
    ntot = len(hlt)
    n = {
        "l1": int(l1.sum()),
        "hlt": int(hlt.sum()),
        "l1_hlt": int((l1 & hlt).sum()),
    }
    row: dict = {
        "path": name,
        "l1_seeds": " OR ".join(seeds),
        "n_events": ntot,
        "n_l1": n["l1"],
        "n_hlt": n["hlt"],
        "n_l1_hlt": n["l1_hlt"],
        "n_hlt_not_l1": int((hlt & ~l1).sum()),
    }
    for key, npass in n.items():
        _, lo, hi = get_eff_err(npass, ntot)
        row[f"eff_{key}"] = npass / ntot
        row[f"eff_{key}_errLo"] = lo
        row[f"eff_{key}_errHi"] = hi
    if as_rate:
        norm = constants.RATE_NORM_FACTOR / ntot
        for key, npass in n.items():
            g_lo, g_hi = garwood_interval(npass)
            row[f"rate_{key}"] = npass * norm
            row[f"rate_{key}_lo68"] = g_lo * norm
            row[f"rate_{key}_hi68"] = g_hi * norm
    return row


def path_table(
    mapping: dict, hlt_bits: ak.Array, l1_bits: ak.Array, as_rate: bool
) -> pd.DataFrame:
    rows = []
    any_l1 = np.zeros(len(hlt_bits), dtype=bool)
    any_hlt = np.zeros(len(hlt_bits), dtype=bool)
    any_l1_hlt = np.zeros(len(hlt_bits), dtype=bool)
    all_seeds: set = set()
    for path, entry in mapping.items():
        if path not in hlt_bits.fields:
            print(f"WARNING: {path} not in the cached HLT record, skipped")
            continue
        seeds = list(entry.get("l1_seeds") or [])
        if not seeds:
            print(f"WARNING: {path} has no L1 seed in the mapping, skipped")
            continue
        hlt = ak.to_numpy(hlt_bits[path]).astype(bool)
        l1 = l1_or(l1_bits, seeds)
        rows.append(_counts_row(path, seeds, l1, hlt, as_rate))
        any_l1 |= l1
        any_hlt |= hlt
        any_l1_hlt |= l1 & hlt
        all_seeds.update(seeds)
    total = _counts_row("Total", sorted(all_seeds), any_l1, any_hlt, as_rate)
    total["n_l1_hlt"] = int(any_l1_hlt.sum())
    _, lo, hi = get_eff_err(total["n_l1_hlt"], len(any_hlt))
    total.update(
        {
            "eff_l1_hlt": total["n_l1_hlt"] / len(any_hlt),
            "eff_l1_hlt_errLo": lo,
            "eff_l1_hlt_errHi": hi,
            "n_hlt_not_l1": int((any_hlt & ~any_l1_hlt).sum()),
        }
    )
    if as_rate:
        norm = constants.RATE_NORM_FACTOR / len(any_hlt)
        g_lo, g_hi = garwood_interval(total["n_l1_hlt"])
        total["rate_l1_hlt"] = total["n_l1_hlt"] * norm
        total["rate_l1_hlt_lo68"] = g_lo * norm
        total["rate_l1_hlt_hi68"] = g_hi * norm
    rows.append(total)
    return pd.DataFrame(rows)


def _print(df: pd.DataFrame, as_rate: bool) -> None:
    show = pd.DataFrame({"path": df["path"].str.slice(0, 60)})
    for key in ("l1", "hlt", "l1_hlt"):
        show[f"n_{key}"] = df[f"n_{key}"]
        if as_rate:
            show[f"rate_{key} [kHz]"] = [
                f"{r:.3g} [{lo:.3g}, {hi:.3g}]"
                for r, lo, hi in zip(
                    df[f"rate_{key}"], df[f"rate_{key}_lo68"], df[f"rate_{key}_hi68"]
                )
            ]
        else:
            show[f"eff_{key} [%]"] = (100 * df[f"eff_{key}"]).round(2)
    show["n_hlt_not_l1"] = df["n_hlt_not_l1"]
    with pd.option_context(
        "display.max_rows", None, "display.width", 250, "display.max_columns", None
    ):
        print(show.to_string(index=False))


def run(
    mapping_file: str,
    version: str,
    sample: str,
    as_rate: Optional[bool],
    outdir: Optional[str],
) -> pd.DataFrame:
    with open(mapping_file) as f:
        mapping = yaml.safe_load(f)
    if as_rate is None:
        as_rate = sample.startswith("MinBias")
    hlt_bits = load_bits(version, sample, "HLT")
    l1_bits = load_bits(version, sample, "L1")
    df = path_table(mapping, hlt_bits, l1_bits, as_rate)
    print(
        f"=== {version} {sample}: {len(hlt_bits)} events, "
        + ("rates" if as_rate else "efficiencies")
        + " ==="
    )
    _print(df, as_rate)
    outdir = outdir or os.path.join("outputs", version, "rate_tables")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"hlt_paths_{version}_{sample}.csv")
    df.to_csv(out, index=False)
    print(f"Saved {out}")
    return df


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "mapping",
        help="HLT path -> L1 seeds yaml, e.g. configs/V50nano/rate_table/hlt_paths.yml",
    )
    parser.add_argument(
        "--version", required=True, help="Cache version, e.g. V50nano_170pre6HLT"
    )
    parser.add_argument(
        "--sample",
        nargs="+",
        required=True,
        help="Cached sample(s), e.g. DYLL_M50 TT MinBias",
    )
    rate = parser.add_mutually_exclusive_group()
    rate.add_argument(
        "--rate",
        dest="as_rate",
        action="store_true",
        default=None,
        help="Add rates (minimum bias normalisation); default for samples named "
        "MinBias*",
    )
    rate.add_argument("--no-rate", dest="as_rate", action="store_false")
    parser.add_argument(
        "--outdir", default=None, help="Default: outputs/<version>/rate_tables"
    )
    args = parser.parse_args()
    for sample in args.sample:
        run(args.mapping, args.version, sample, args.as_rate, args.outdir)


if __name__ == "__main__":
    main()

"""Compare the rate_table results of a menu with the P2GT emulator decisions.

Run after `rate_table`, naming the table and options as for `compare_menus`,
and the P2GT menu the ntuples were made with (cmsDriver `-s L1P2GT:<menu>`):

    p2gt_compare --version V50nano_170pre7 --menu v45_Step1p5Menu --p2gt step1p5_2026

The menu side is the masks parquet that `rate_table` wrote for that table,
outputs/<version>/rate_tables/<menu>_<version>[_scalings_<v>][_truncated]
[_<sample>]_masks.parquet, picked with the same --scalings, --truncated and
--signal. The P2GT side is the cache of the emulator decisions, i.e. the nano
branches `L1_<algo>_final`, made by `cache_objects` from an entry like

    MinBias:
      trees_branches:
        Events:
          L1: "*_final"

which writes `cache/<version>/<version>_MinBias_L1.parquet` from the same
ntuples, in the same order, as the objects `rate_table` used. Alternatively
`--gt-ntuples` reads the decisions straight from ntuples (e.g. a hadd file),
which must then hold the same events in the same order.

Seed `L1_X` is matched to the P2GT algorithm `pX`. The P2GT menus whose
algorithms keep their historical names (step1_2024, step1and2_2026) take a
map from p2gt_names/<map>.yml next to this module, or `--names`:

    L1_SingleTkMu: pSingleTkMuon22

Seeds without a P2GT algorithm (e.g. calo tau seeds) are listed and left out,
so totals and pure rates are computed over the seeds present on both sides.

Outputs, next to the rate_table outputs:
  <stem>_p2gt.csv               per seed: counts, rates, differences, events
                                passing only one side, pure rates
  <stem>_p2gt_rates.png/pdf     rates, difference, relative difference
  <stem>_p2gt_pure.png/pdf      the same for pure rates
  <stem>_p2gt_mismatch.png/pdf  events passing only the menu / only P2GT
with <stem> the name of the rate_table outputs, without `_masks.parquet`.
"""
import argparse
import glob
import os
import re
import sys
from typing import Optional

import awkward as ak
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import mplhep as hep  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from menu_tools.rate_table.menu_config import scalings_suffix  # noqa: E402
from menu_tools.utils import constants  # noqa: E402
from menu_tools.utils.versions import (  # noqa: E402
    add_version_argument,
    get_versions,
    run_per_version,
)

plt.style.use(hep.style.CMS)

GT_BRANCH = re.compile(r"^L1_(.+)_final$")
LABEL_MENU = "Menu"
LABEL_SIZE = 14
TICK_SIZE = 10
LABEL_GT = "P2GT"
COLORS = ["#1f77b4", "#ff7f0e"]

NAMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "p2gt_names")
# P2GT menu -> name map in NAMES_DIR; other menus name their algorithms p<seed>
NAME_MAPS = {"step1_2024": "step1_2024.yml", "step1and2_2026": "step1_2024.yml"}
P2GT_MENUS = ["step1_2024", "step1and2_2026", "step1p5_2026", "v0p0_2026"]


def output_stem(
    menu: str,
    version: str,
    scalings: Optional[str] = None,
    truncated: bool = False,
    signal: Optional[str] = None,
) -> str:
    """The file name stem rate_table uses for this table, version and options."""
    sample = f"_{signal}" if signal else ""
    return f"{menu}_{version}{scalings_suffix(scalings, truncated)}{sample}"


def names_path(p2gt_menu: Optional[str]) -> Optional[str]:
    """Name map of a P2GT menu, None for menus that name their algorithms p<seed>."""
    if p2gt_menu in NAME_MAPS:
        return os.path.join(NAMES_DIR, NAME_MAPS[p2gt_menu])
    return None


def normalise_algo(name: str) -> str:
    """P2GT algorithm name as in the nano branch `L1_<algo>_final`."""
    m = GT_BRANCH.match(name)
    return m.group(1) if m else name


def load_names(path: Optional[str]) -> dict[str, str]:
    if not path or not os.path.exists(path):
        return {}
    with open(path) as f:
        names = yaml.safe_load(f) or {}
    return {seed: normalise_algo(str(algo)) for seed, algo in names.items()}


def load_menu_masks(path: str) -> dict[str, np.ndarray]:
    arr = ak.from_parquet(path)
    return {f: ak.to_numpy(arr[f]).astype(bool) for f in arr.fields}


def gt_fields_to_masks(arr: ak.Array) -> dict[str, np.ndarray]:
    masks = {}
    for field in arr.fields:
        m = GT_BRANCH.match(field)
        if m:
            masks[m.group(1)] = ak.to_numpy(arr[field]).astype(bool)
    return masks


def load_gt_cache(path: str) -> dict[str, np.ndarray]:
    masks = gt_fields_to_masks(ak.from_parquet(path))
    if not masks:
        raise RuntimeError(f"No `L1_<algo>_final` fields in {path}")
    return masks


def load_gt_ntuples(pattern: str) -> dict[str, np.ndarray]:
    """Decisions read straight from ntuples, in sorted file order as cache_objects
    reads them."""
    import uproot

    fnames = sorted(glob.glob(pattern))
    if not fnames:
        raise FileNotFoundError(f"No ntuples match `{pattern}`")
    parts = []
    for fname in fnames:
        with uproot.open(fname) as f:
            parts.append(f["Events"].arrays(filter_name="L1_*_final"))
    masks = gt_fields_to_masks(ak.concatenate(parts))
    if not masks:
        raise RuntimeError(f"No `L1_<algo>_final` branches in `{pattern}`")
    return masks


def match_seeds(
    menu_seeds: list[str], gt_algos: list[str], names: dict[str, str]
) -> tuple[dict[str, str], list[str], list[str]]:
    """Menu seed -> P2GT algorithm, in menu order.

    Returns (matched, menu seeds without an algorithm, algorithms without a seed).
    """
    matched = {}
    missing = []
    for seed in menu_seeds:
        algo = names.get(seed) or "p" + seed.removeprefix("L1_")
        if algo in gt_algos:
            matched[seed] = algo
        else:
            missing.append(seed)
    used = set(matched.values())
    unmatched = [a for a in gt_algos if a not in used]
    return matched, missing, unmatched


def pure_counts(masks: np.ndarray) -> np.ndarray:
    """Events passing each seed (column) and no other seed of `masks`."""
    only_one = masks.sum(axis=1) == 1
    return (masks & only_one[:, None]).sum(axis=0)


def compare(
    menu: dict[str, np.ndarray], gt: dict[str, np.ndarray], matched: dict[str, str]
) -> pd.DataFrame:
    """Per-seed comparison over the matched seeds, plus a `Total` row (OR)."""
    seeds = list(matched)
    m: np.ndarray = np.stack([menu[s] for s in seeds], axis=1)
    g: np.ndarray = np.stack([gt[matched[s]] for s in seeds], axis=1)
    not_m, not_g = np.logical_not(m), np.logical_not(g)
    df = pd.DataFrame(
        {
            "p2gt_algo": [matched[s] for s in seeds],
            "npass_menu": m.sum(axis=0),
            "npass_p2gt": g.sum(axis=0),
            "menu_only": (m & not_g).sum(axis=0),
            "p2gt_only": (not_m & g).sum(axis=0),
            "npure_menu": pure_counts(m),
            "npure_p2gt": pure_counts(g),
        },
        index=pd.Index(seeds, name="seed"),
    )
    m_or, g_or = np.any(m, axis=1), np.any(g, axis=1)
    df.loc["Total"] = [
        "",
        np.sum(m_or),
        np.sum(g_or),
        np.sum(m_or & np.logical_not(g_or)),
        np.sum(np.logical_not(m_or) & g_or),
        np.nan,
        np.nan,
    ]
    return df


def add_rates(df: pd.DataFrame, n_events: int, signal: bool) -> pd.DataFrame:
    """Rates in kHz (efficiencies for a signal sample), differences as menu - P2GT."""
    norm = (1.0 if signal else constants.RATE_NORM_FACTOR) / n_events
    q = "eff" if signal else "rate"
    df = df.copy()
    for side in ("menu", "p2gt"):
        df[f"{q}_{side}"] = df[f"npass_{side}"].astype(float) * norm
        df[f"pure_{q}_{side}"] = df[f"npure_{side}"].astype(float) * norm
    for kind in ("", "pure_"):
        diff = df[f"{kind}{q}_menu"] - df[f"{kind}{q}_p2gt"]
        df[f"{kind}diff"] = diff
        with np.errstate(divide="ignore", invalid="ignore"):
            df[f"{kind}rel_diff"] = diff / df[f"{kind}{q}_p2gt"]
    df["mismatch"] = df["menu_only"] + df["p2gt_only"]
    return df


def fig_height(n_rows: int) -> float:
    return max(3.5, 1.6 + 0.3 * n_rows)


def style_axes(axs, xlabels) -> None:
    for ax, label in zip(axs, xlabels):
        ax.set_xlabel(label, fontsize=LABEL_SIZE)
        ax.tick_params(axis="x", labelsize=TICK_SIZE)
        ax.tick_params(axis="y", labelsize=TICK_SIZE)
        ax.grid()
        ax.set_ylabel("")


def three_panel(
    values: pd.DataFrame,
    diff: pd.Series,
    rel: pd.Series,
    xlabels: tuple[str, str, str],
    title: str,
):
    """Bars for menu and P2GT, then difference and relative difference."""
    fig, axs = plt.subplots(
        1,
        3,
        figsize=(14, fig_height(len(values))),
        sharey=True,
        gridspec_kw={"width_ratios": [3, 1, 1]},
    )
    values.plot(kind="barh", ax=axs[0], color=COLORS)
    axs[0].legend(loc="best", fontsize=12)
    diff.plot(kind="barh", ax=axs[1], color="grey", legend=False)
    rel.plot(kind="barh", ax=axs[2], color="grey", legend=False)
    style_axes(axs, xlabels)
    for ax in axs[1:]:
        lim = np.nanmax(np.abs(ax.get_xlim()))
        ax.set_xlim(-lim, lim)
        ax.axvline(0, color="black", lw=0.8)
    axs[0].set_title(title, fontsize=12, loc="left")
    fig.subplots_adjust(wspace=0.08)
    return fig


def save(fig, outdir: str, fname: str) -> None:
    for ext in ("png", "pdf"):
        path = os.path.join(outdir, f"{fname}.{ext}")
        fig.savefig(path, bbox_inches="tight", dpi=300)
        print(f"Saving plot at: {path}")
    plt.close(fig)


def order_rows(df: pd.DataFrame, sort: str, q: str, kind: str = "") -> pd.DataFrame:
    seeds = df.drop(index="Total")
    if sort == "menu":
        seeds = seeds.iloc[::-1]  # first seed at the top of a barh plot
    elif sort == "diff":
        seeds = seeds.sort_values(f"{kind}diff")
    elif sort == "rel":
        seeds = seeds.sort_values(f"{kind}rel_diff")
    elif sort == "rate":
        seeds = seeds.sort_values(f"{kind}{q}_menu")
    return seeds


def make_plots(
    df: pd.DataFrame, outdir: str, stem: str, title: str, sort: str, signal: bool
) -> None:
    q = "eff" if signal else "rate"
    unit = "Efficiency" if signal else "Rate [kHz]"
    for kind, tag, label in (("", "rates", unit), ("pure_", "pure", f"Pure {unit}")):
        rows = order_rows(df, sort, q, kind)
        values = rows[[f"{kind}{q}_menu", f"{kind}{q}_p2gt"]]
        values.columns = [LABEL_MENU, LABEL_GT]
        fig = three_panel(
            values,
            rows[f"{kind}diff"],
            rows[f"{kind}rel_diff"],
            (label, f"Diff: {LABEL_MENU} - {LABEL_GT}", "Rel. Diff."),
            title,
        )
        save(fig, outdir, f"{stem}_p2gt_{tag}")

    rows = df.drop(index="Total")
    if sort != "menu":
        rows = rows.assign(rel=rows["mismatch"] / rows["npass_menu"].replace(0, np.nan))
        rows = rows.sort_values("rel")
    else:
        rows = rows.iloc[::-1]
    counts = rows[["menu_only", "p2gt_only"]]
    counts.columns = [f"{LABEL_MENU} only", f"{LABEL_GT} only"]
    fig, axs = plt.subplots(
        1,
        2,
        figsize=(11, fig_height(len(rows))),
        sharey=True,
        gridspec_kw={"width_ratios": [3, 1]},
    )
    counts.plot(kind="barh", ax=axs[0], color=COLORS)
    axs[0].legend(loc="best", fontsize=12)
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = rows["mismatch"] / rows["npass_menu"]
    rel.plot(kind="barh", ax=axs[1], color="grey", legend=False)
    style_axes(axs, ("Events passing one side only", "Mismatch / menu npass"))
    axs[0].set_title(title, fontsize=12, loc="left")
    fig.subplots_adjust(wspace=0.08)
    save(fig, outdir, f"{stem}_p2gt_mismatch")


def print_table(df: pd.DataFrame, signal: bool) -> None:
    q = "eff" if signal else "rate"
    fmt = "{:10.4f}" if signal else "{:10.2f}"
    cols = [f"{q} menu", f"{q} P2GT", "diff", "menu only", "P2GT only"]
    head = f"{'seed':55s} " + " ".join(f"{c:>10s}" for c in cols)
    print(head)
    print("-" * len(head))
    for seed, r in df.iterrows():
        print(
            f"{seed:55s} {fmt.format(r[f'{q}_menu'])} {fmt.format(r[f'{q}_p2gt'])} "
            f"{fmt.format(r['diff'])} "
            f"{int(r['menu_only']):10d} {int(r['p2gt_only']):10d}"
        )


class CompareError(RuntimeError):
    """Missing or inconsistent inputs: ends this version with a message."""


def run_compare(args, version: str) -> None:
    stem = output_stem(args.menu, version, args.scalings, args.truncated, args.signal)
    table_dir = os.path.join("outputs", version, "rate_tables")
    outdir = args.outdir or table_dir
    sample = args.signal or "MinBias"
    masks_path = args.masks or os.path.join(table_dir, f"{stem}_masks.parquet")
    if not os.path.exists(masks_path):
        raise CompareError(
            f"No rate_table masks at {masks_path}: run rate_table first, "
            "with the same --scalings/--truncated/--signal"
        )
    menu = load_menu_masks(masks_path)

    if args.gt_ntuples:
        gt_source = args.gt_ntuples
        gt = load_gt_ntuples(args.gt_ntuples)
    else:
        gt_source = args.gt_cache or os.path.join(
            constants.CACHE_DIR, version, f"{version}_{sample}_L1.parquet"
        )
        if not os.path.exists(gt_source):
            raise CompareError(
                f'No P2GT decisions at {gt_source}: add `L1: "*_final"` to the '
                f"{sample} entry of the caching config and run cache_objects, "
                "or use --gt-ntuples"
            )
        gt = load_gt_cache(gt_source)
    print(f"Menu masks: {masks_path}\nP2GT decisions: {gt_source}")

    n_menu = len(next(iter(menu.values())))
    n_gt = len(next(iter(gt.values())))
    if n_menu != n_gt:
        raise CompareError(
            f"Event counts differ: {n_menu} in the menu masks, {n_gt} in the P2GT "
            "decisions. They must come from the same ntuples in the same order."
        )

    names_file = args.names or names_path(args.p2gt)
    names = load_names(names_file)
    if names:
        print(f"P2GT names from {names_file}")
    else:
        print("P2GT algorithms matched as L1_X -> pX")
    matched, missing, unmatched = match_seeds(list(menu), list(gt), names)
    excluded = [s for s in args.exclude if s in matched]
    for s in excluded:
        matched.pop(s)
    if missing:
        print(
            f"No P2GT algorithm for {len(missing)} seed(s), left out: "
            + ", ".join(missing)
        )
    if excluded:
        print(f"Excluded: {', '.join(excluded)}")
    if unmatched:
        print(f"P2GT algorithms without a menu seed: {', '.join(unmatched)}")
    if not matched:
        raise CompareError("No seed matched a P2GT algorithm: check --p2gt")

    signal = args.signal is not None
    df = add_rates(compare(menu, gt, matched), n_menu, signal)
    os.makedirs(outdir, exist_ok=True)
    csv_path = os.path.join(outdir, f"{stem}_p2gt.csv")
    df.to_csv(csv_path)
    print(f"Saved table to {csv_path}")
    print_table(df, signal)
    print(f"Total events: {n_menu}")

    if not args.no_plots:
        title = f"{args.menu}, {version}" + (f", P2GT {args.p2gt}" if args.p2gt else "")
        make_plots(df, outdir, stem, title, args.sort, signal)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)

    parser = argparse.ArgumentParser(
        description="Compare rate_table results with the P2GT emulator decisions."
    )
    add_version_argument(parser)
    parser.add_argument(
        "--menu",
        required=True,
        help="table name of the rate_table outputs (`table_fname` in the rate_table "
        "config), e.g. v45_Step1p5Menu",
    )
    parser.add_argument(
        "--p2gt",
        metavar="P2GT_MENU",
        help="P2GT menu of the ntuples (cmsDriver -s L1P2GT:<menu>), which picks the "
        f"seed -> algorithm names: {', '.join(P2GT_MENUS)}. Without it, and for "
        "other menus, seed L1_X is matched to algorithm pX",
    )
    parser.add_argument(
        "--scalings", help="same as for rate_table, to pick up its outputs"
    )
    parser.add_argument(
        "--truncated",
        action="store_true",
        help="same as for rate_table, to pick up its outputs",
    )
    parser.add_argument(
        "--signal", help="same as for rate_table, to pick up its outputs"
    )
    inp = parser.add_argument_group("inputs")
    inp.add_argument(
        "--masks", help="rate_table masks parquet, instead of the one from the options"
    )
    inp.add_argument(
        "--gt-cache",
        help="P2GT decisions cache "
        "(default: <cache>/<version>/<version>_<sample>_L1.parquet, <cache> = "
        "$MENU_TOOLS_CACHE or cache)",
    )
    inp.add_argument(
        "--gt-ntuples",
        help="read the P2GT decisions from these ntuples (glob) instead of the cache; "
        "they must hold the same events, in the same order, as the menu masks",
    )
    inp.add_argument(
        "--names",
        help="YAML map menu seed -> P2GT algorithm, instead of the one of --p2gt",
    )
    inp.add_argument(
        "--exclude", nargs="+", default=[], metavar="SEED", help="seeds to leave out"
    )
    out = parser.add_argument_group("output")
    out.add_argument(
        "-o", "--outdir", help="output directory (default: the rate_table one)"
    )
    out.add_argument(
        "--sort",
        choices=["diff", "rel", "rate", "menu"],
        default="diff",
        help="seed order in the plots (default: diff)",
    )
    out.add_argument("--no-plots", action="store_true", help="only write the CSV")
    args = parser.parse_args()

    if not args.version:
        parser.error("--version is required")
    if args.p2gt and args.p2gt not in P2GT_MENUS:
        print(f"WARNING: unknown P2GT menu {args.p2gt}, matching L1_X -> pX")
    try:
        run_per_version(
            get_versions(parser, args), lambda version: run_compare(args, str(version))
        )
    except CompareError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()

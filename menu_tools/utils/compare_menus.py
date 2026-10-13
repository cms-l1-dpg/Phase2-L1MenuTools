"""Compare rate (or signal efficiency) tables of up to three menu versions.

Reads the per-seed CSV tables written by `rate_table`. Only the CSVs are used,
not the per-event mask parquet files.

Conventions: v0 is the new version and v1 (and v2) the references, so for
each reference vN
    diff     = v0 - vN
    rel diff = (v0 - vN) / vN
With --uncertainties the statistical errors of the versions are combined in
quadrature, i.e. the tables are treated as statistically independent. That is
correct for independent samples (e.g. 140 vs 200 PU) but overestimates the
error when comparing versions run on the same events.
"""

import argparse
import os
import re
import warnings

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import pandas as pd
from matplotlib.container import BarContainer
from matplotlib.ticker import NullLocator

# Set up plotting style
plt.style.use(hep.style.CMS)
plt.rcParams["figure.facecolor"] = "white"
plt.rcParams["font.size"] = 14

TOTAL_ROW = "Total"
SEED_FONTSIZE = 11
# Dark grey error bars with small end caps
ERROR_KW = dict(ecolor="#404040", elinewidth=0.8, capsize=2.5, capthick=0.8)


class Quantity:
    """What is being compared: minbias rates or signal efficiencies."""

    def __init__(self, signal: bool):
        if signal:
            self.name, self.col, self.err_prefix = "eff", "eff", "eff"
            self.scale, self.unit, self.label = 100.0, "%", "Efficiency"
            self.fmt = "{:.2f}"
        else:
            self.name, self.col, self.err_prefix = "rate", "rate", "rate"
            self.scale, self.unit, self.label = 1.0, "kHz", "Rate"
            self.fmt = "{:.1f}"
        self.axis_label = f"{self.label} [{self.unit}]"

    def format(self, val: float, err: float = np.nan) -> str:
        if np.isnan(val):
            return "-"
        s = self.fmt.format(val)
        if not np.isnan(err):
            s += " ± " + self.fmt.format(err)
        return s


def get_df_new_csv(fname):
    """Load a rate-table CSV, selecting columns by header name so that
    extra columns (e.g. the rate/efficiency uncertainties) are harmless.
    Works for tables written both before and after the uncertainties."""
    df = pd.read_csv(fname)
    return df.rename(columns={"seed": "Seed", "npass": "counts", "efficiency": "eff"})

# def save_table_as_image(df, filename, output_dir):
#     """Save a dataframe as a table in PNG and PDF formats."""
#     if df.empty:
#         print(f"Skipping saving table {filename} as dataframe is empty")
#         return
#     # Drop rows with NaN values
#     df_clean = df.dropna()
#     if df_clean.empty:
#         print(f"Skipping saving table {filename} as dataframe is empty after dropping NaN")
#         return
#     fig, ax = plt.subplots(figsize=(12, len(df_clean) * 0.3))
#     ax.axis('tight')
#     ax.axis('off')
#     tbl = table(ax, df_clean, loc='center', cellLoc='center', colWidths=[0.2] * len(df_clean.columns))
#     tbl.auto_set_font_size(False)
#     tbl.set_fontsize(10)
#     tbl.scale(1.2, 1.2)
#     os.makedirs(output_dir, exist_ok=True)
#     for ext in ['png', 'pdf']:
#         filepath = os.path.join(output_dir, f"{filename}.{ext}")
#         plt.savefig(filepath, bbox_inches='tight', dpi=300)
#         print(f"Saving table at: {filepath}")
#     plt.close()

# Function to strip the prefix like Vxxnano_
# Hotfix: also drop "_VtxFindOff" so e.g. V49nano_AR25_VtxFindOff shows as AR25
def strip_prefix(s):
    s = re.sub(r"^V\d+nano_", "", s)
    return re.sub(r"_VtxFindOff$", "", s)


# Hotfix: when comparing <version> against <version>_140PU, label them by
# pileup instead, so e.g. V50nano_170pre5 / V50nano_170pre5_140PU show as
# 200PU / 140PU regardless of the order they are given in.
def version_label(version, all_versions):
    if version + "_140PU" in all_versions:
        return "200PU"
    if version.endswith("_140PU") and version.removesuffix("_140PU") in all_versions:
        return "140PU"
    return strip_prefix(version)


def fig_height(n_rows: int, n_versions: int) -> float:
    """Figure height scaling with the number of seeds, so small menus
    (e.g. step 2 only) are not stretched: ~0.3" per seed for two versions,
    plus a fixed allowance for axis labels."""
    per_row = 0.14 + 0.08 * n_versions
    return max(3.5, 1.6 + per_row * n_rows)


def barh(
    ax, val, lo=None, hi=None, colors=None, legend_labels=None, index_name="Trigger"
):
    """Grouped horizontal bars drawn with pandas, as before, with optional
    asymmetric error bars when `lo`/`hi` are given."""
    df = val.copy()
    if legend_labels:
        df.columns = legend_labels
    df.index.name = index_name
    df.columns.name = "version"
    xerr = None
    if lo is not None:
        # pandas wants asymmetric errors as (n_columns, 2, n_rows)
        xerr = np.stack([[lo[c].to_numpy(), hi[c].to_numpy()] for c in val.columns])
    df.plot(
        kind="barh",
        ax=ax,
        fontsize=SEED_FONTSIZE,
        color=colors,
        xerr=xerr,
        error_kw=ERROR_KW,
    )
    ax.grid()


def value_column(ax, bars_ax, val, err, labels, colors, qty):
    """Turn `ax` into a text column listing each version's value per seed,
    aligned with its bar in `bars_ax`. Keeps the y tick labels (seed names)."""
    containers = [c for c in bars_ax.containers if isinstance(c, BarContainer)]
    bar_height = containers[0].patches[0].get_height()
    ylim = bars_ax.get_ylim()
    ax_inch = bars_ax.get_position().height * bars_ax.figure.get_figheight()
    bar_inch = bar_height * ax_inch / (ylim[1] - ylim[0])
    fontsize = float(np.clip(0.8 * 72 * bar_inch, 5, 10))
    for j, (label, bars) in enumerate(zip(labels, containers)):
        errs = err[label] if err is not None else np.full(len(val), np.nan)
        for patch, v, e in zip(bars.patches, val[label], errs):
            ax.text(
                0.97,
                patch.get_y() + patch.get_height() / 2,
                qty.format(v, e),
                color=colors[j],
                fontsize=fontsize,
                ha="right",
                va="center",
                transform=ax.get_yaxis_transform(),
            )
    ax.set_xlim(0, 1)
    ax.set_title(qty.axis_label, fontsize=10, loc="right")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(
        which="both",
        bottom=False,
        top=False,
        labelbottom=False,
        left=False,
        right=False,
    )


def symmetric_limit(data, err=None):
    """Symmetric x range for a diff panel with error bars, set by the
    differences themselves rather than the error bars, so that the large
    relative errors of low-count seeds do not squash the rest (their bars are
    clipped instead).
    Error bars only widen it up to the 90th percentile of |diff| + error."""
    vals = np.abs(data.to_numpy(dtype=float))
    lim = 1.3 * np.nanmax(vals) if np.isfinite(vals).any() else 1.0
    if err is not None:
        reach = vals + err.to_numpy(dtype=float)
        if np.isfinite(reach).any():
            lim = max(lim, np.nanpercentile(reach, 90))
    lim = lim if lim > 0 else 1.0
    return -lim, lim


def make_axes(
    n_rows, n_versions, panel_ratios, width, show_values, with_unc, height_scale=1.0
):
    """Figure with optional value column on the left, then the data panels,
    all sharing the seed axis. Returns (fig, value_ax or None, data_axes)."""
    ratios = list(panel_ratios)
    if show_values:
        # Fixed physical width for the text column, whatever the panel layout
        value_width = 1.1 if with_unc else 0.6
        ratios = [value_width * sum(ratios) / width] + ratios
        width += value_width
    fig, axs = plt.subplots(
        1,
        len(ratios),
        figsize=(width, height_scale * fig_height(n_rows, n_versions)),
        sharey=True,
        gridspec_kw={"width_ratios": ratios},
        squeeze=False,
    )
    axs = list(axs[0])
    value_ax = axs.pop(0) if show_values else None
    return fig, value_ax, axs


def save(fig, output_dir, fname):
    for ext in ["png", "pdf"]:
        filepath = os.path.join(output_dir, f"{fname}.{ext}")
        fig.savefig(filepath, bbox_inches="tight", dpi=300)
        print(f"Saving plot at: {filepath}")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(
        description="Compare L1T Phase2 menu rates (or signal efficiencies) "
        "from two or three versions."
    )
    parser.add_argument(
        "--v0", required=True, help="New version name (e.g., V45nano_L1EGupdate1)"
    )
    parser.add_argument(
        "--v1",
        required=True,
        help="Reference version to compare against (e.g., V45nano_noL1EG)",
    )
    parser.add_argument("--v2", help="Optional second reference version")
    parser.add_argument(
        "--output-dir",
        default="comparisons",
        help="Output directory part (e.g., comparisons/bisecting)",
    )
    parser.add_argument(
        "--menu",
        default="v45_Step1Menu",
        help="Base menu name (default: v45_Step1Menu)",
    )
    parser.add_argument(
        "--menu-v0", default=None, help="Menu name for v0 (overrides --menu)"
    )
    parser.add_argument(
        "--menu-v1", default=None, help="Menu name for v1 (overrides --menu)"
    )
    parser.add_argument(
        "--menu-v2", default=None, help="Menu name for v2 (overrides --menu)"
    )
    parser.add_argument(
        "--csv-v0",
        default=None,
        help="Explicit CSV path for v0 (overrides the default path)",
    )
    parser.add_argument("--csv-v1", default=None, help="Explicit CSV path for v1")
    parser.add_argument("--csv-v2", default=None, help="Explicit CSV path for v2")
    parser.add_argument(
        "--signal",
        default=None,
        metavar="SAMPLE",
        help="Compare signal efficiencies instead of rates, reading the tables "
        "made with `rate_table --signal SAMPLE`",
    )
    parser.add_argument(
        "--uncertainties",
        action="store_true",
        help="Show statistical uncertainties (needs tables with error columns; "
        "versions are treated as independent)",
    )
    parser.add_argument(
        "--show-values",
        action="store_true",
        help="Add a column listing each seed's value left of the plots",
    )
    args = parser.parse_args()

    qty = Quantity(signal=args.signal is not None)
    sample_suffix = f"_{args.signal}" if args.signal else ""

    # Set menu names
    menu_v0 = args.menu_v0 if args.menu_v0 else args.menu
    menu_v1 = args.menu_v1 if args.menu_v1 else args.menu
    menu_v2 = args.menu_v2 if args.menu_v2 else args.menu

    # Collect all versions
    versions = [args.v0, args.v1]
    menus = [menu_v0, menu_v1]
    csv_overrides = [args.csv_v0, args.csv_v1]
    if args.v2:
        versions.append(args.v2)
        menus.append(menu_v2)
        csv_overrides.append(args.csv_v2)

    # Define labels
    labels = []
    for i, (version, menu) in enumerate(zip(versions, menus)):
        if len(set(versions)) == 1:  # All versions are the same
            labels.append(f"{version_label(version, versions)}_{menu}")
        elif len(set(menus)) == 1:  # All menus are the same
            labels.append(version_label(version, versions))
        else:  # Mixed case
            labels.append(f"{version_label(version, versions)}_{menu}")
    # Labels key the per-version dataframes, so they must stay unique: if
    # stripping makes two collide (e.g. V49nano_AR25 vs V49nano_AR25_VtxFindOff),
    # keep the full version names instead.
    if len(set(labels)) < len(labels):
        labels = [
            f"{v}_{m}" if len(set(menus)) > 1 or len(set(versions)) == 1 else v
            for v, m in zip(versions, menus)
        ]

    # Define input files
    base_path = "outputs"
    input_files = {}
    for label, version, menu, csv in zip(labels, versions, menus, csv_overrides):
        default = (
            f"{base_path}/{version}/rate_tables/{menu}_{version}{sample_suffix}.csv"
        )
        input_files[label] = csv if csv else default

    # Set up output directory
    parent_dir = f"{base_path}/{args.output_dir}"
    if not os.path.exists(parent_dir):
        raise FileNotFoundError(
            f"Parent directory not found, please confirm: {parent_dir}"
        )

    comparison_name = "vs".join(versions)
    output_dir = f"{base_path}/{args.output_dir}/{comparison_name}/rate_tables"
    os.makedirs(output_dir, exist_ok=True)

    # Check if input files exist
    for label, filepath in list(input_files.items()):
        if not os.path.exists(filepath):
            print(f"Warning: Input CSV file not found: {filepath}")
            if args.v2 and label == labels[-1]:
                print("Continuing without v2...")
                labels, versions, menus = labels[:-1], versions[:-1], menus[:-1]
                del input_files[label]
            else:
                raise FileNotFoundError(
                    f"Required input CSV file not found: {filepath}"
                )

    # Load dataframes, indexed by seed name (row order in the CSVs is irrelevant)
    dfs = {}
    for label, filepath in input_files.items():
        df = get_df_new_csv(filepath)
        df["Seed"] = df["Seed"].str.strip()
        if qty.col not in df.columns:
            raise KeyError(
                f"No '{qty.col}' column in {filepath}. "
                + ("Is this a signal table?" if args.signal is None else "")
            )
        dfs[label] = df.set_index("Seed")
        print(f"{label} length: {len(df)}")

    with_unc = args.uncertainties
    err_cols = [f"{qty.err_prefix}ErrLo", f"{qty.err_prefix}ErrHi"]
    if with_unc:
        missing = [
            lbl for lbl, df in dfs.items() if not set(err_cols) <= set(df.columns)
        ]
        if missing:
            warnings.warn(
                f"No uncertainty columns for {missing}; plotting without uncertainties"
            )
            with_unc = False

    def table(col):
        return pd.DataFrame({lbl: df[col] for lbl, df in dfs.items()}) * qty.scale

    val_all = table(qty.col)
    lo_all = table(err_cols[0]) if with_unc else None
    hi_all = table(err_cols[1]) if with_unc else None

    # Totals come from the "Total" row (the OR of all seeds)
    if TOTAL_ROW not in val_all.index:
        raise KeyError(f"No '{TOTAL_ROW}' row found in the input tables")
    total = val_all.loc[TOTAL_ROW]
    total_err = (
        ((lo_all.loc[TOTAL_ROW] + hi_all.loc[TOTAL_ROW]) / 2) if with_unc else None
    )

    def total_str(label):
        e = total_err[label] if with_unc else np.nan
        return f"{qty.format(total[label], e)} {qty.unit}"

    legend_labels = [f"{lbl} (Total: {total_str(lbl)})" for lbl in labels]

    # Per-seed tables (also drops the "Total" rows)
    seeds = [s for s in val_all.index if "L1_" in s]
    val = val_all.loc[seeds, labels]
    lo = lo_all.loc[seeds, labels] if with_unc else None
    hi = hi_all.loc[seeds, labels] if with_unc else None
    err = (lo + hi) / 2 if with_unc else None

    # Differences of the new version v0 w.r.t. each reference
    new = labels[0]
    refs = labels[1:]
    diff = pd.DataFrame({lbl: val[new] - val[lbl] for lbl in refs})
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = pd.DataFrame(
            {lbl: diff[lbl] / val[lbl].replace(0, np.nan) for lbl in refs}
        )
    diff_err = rel_err = None
    if with_unc:
        diff_err = pd.DataFrame({lbl: np.hypot(err[new], err[lbl]) for lbl in refs})
        # sigma of v0/vN - 1, written so it stays finite when v0 == 0
        rel_err = pd.DataFrame(
            {
                lbl: np.hypot(err[new], rel[lbl].add(1) * err[lbl])
                / val[lbl].replace(0, np.nan)
                for lbl in refs
            }
        )

    colors = [f"C{i}" for i in range(len(labels))]
    filename_base = "vs".join(
        f"{menu}_{version}" for menu, version in zip(menus, versions)
    )
    filename_base += sample_suffix
    n_ver = len(labels)

    # Plot: totals
    fig, ax = plt.subplots(figsize=(8, 1.5 + 0.5 * n_ver))
    y = np.arange(n_ver)[::-1]  # v0 on top
    ax.barh(
        y,
        total[labels].to_numpy(),
        color=colors,
        height=0.6,
        xerr=total_err[labels].to_numpy() if with_unc else None,
        error_kw=ERROR_KW,
    )
    for yi, lbl in zip(y, labels):
        x_end = total[lbl] + (total_err[lbl] if with_unc else 0)
        ax.text(x_end, yi, f"  {total_str(lbl)}", va="center", fontsize=12)
    ax.set_yticks(np.arange(n_ver), labels[::-1], fontsize=12)  # ascending ticks
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_xlim(0, total[labels].max() * 1.45)
    ax.set_xlabel(f"Total {qty.axis_label}")
    ax.grid(axis="x")
    save(fig, output_dir, f"{filename_base}_{qty.name}_total")

    # Plot: individual values (alphabetical), log scale for rates
    order = sorted(seeds)
    fig, value_ax, (ax,) = make_axes(
        len(seeds), n_ver, [1], 6, args.show_values, with_unc, height_scale=0.73
    )
    barh(
        ax,
        val.loc[order],
        lo.loc[order] if with_unc else None,
        hi.loc[order] if with_unc else None,
        colors,
        legend_labels,
        index_name="Seed",
    )
    ax.set_xlabel(qty.axis_label)
    if qty.name == "rate":
        ax.set_xscale("log")
    if value_ax is not None:
        value_column(
            value_ax,
            ax,
            val.loc[order],
            err.loc[order] if with_unc else None,
            labels,
            colors,
            qty,
        )
    save(fig, output_dir, f"{filename_base}_{qty.name}_individual")

    # Plots: values, diff and rel. diff, sorted by v0 value and by diff to v1
    for sort_name, key in [("byTotal", val[new]), ("", diff[refs[0]])]:
        order = key.sort_values().index
        fig, value_ax, axs = make_axes(
            len(seeds), n_ver, [3, 1, 1], 10, args.show_values, with_unc
        )
        barh(
            axs[0],
            val.loc[order],
            lo.loc[order] if with_unc else None,
            hi.loc[order] if with_unc else None,
            colors,
            legend_labels,
        )
        axs[0].set_xlabel(qty.axis_label)
        if value_ax is not None:
            value_column(
                value_ax,
                axs[0],
                val.loc[order],
                err.loc[order] if with_unc else None,
                labels,
                colors,
                qty,
            )

        for ax, data, data_err, xlabel in [
            (axs[1], diff, diff_err, f"Diff [{qty.unit}]"),
            (axs[2], rel, rel_err, "Rel. Diff"),
        ]:
            d = data.loc[order]
            e = data_err.loc[order] if with_unc else None
            barh(ax, d, e, e, colors[1:])
            ax.get_legend().remove()
            ax.set_xlabel(xlabel)
            if with_unc:
                ax.set_xlim(symmetric_limit(d, e))
        fig.subplots_adjust(wspace=0)
        suffix = f"_{sort_name}" if sort_name else ""
        save(fig, output_dir, f"{filename_base}_{qty.name}_diff_pull{suffix}")

    # Print summary statistics
    print("\n=== SUMMARY ===")
    print(f"Seeds compared: {len(seeds)}")
    for lbl in labels:
        print(f"{lbl} total {qty.label.lower()} (OR of all seeds): {total_str(lbl)}")
    for lbl in refs:
        d = total[new] - total[lbl]
        d_err = np.hypot(total_err[new], total_err[lbl]) if with_unc else np.nan
        msg = f"Total difference ({new} − {lbl}): {qty.format(d, d_err)} {qty.unit}"
        if with_unc:
            msg += " (error assumes independent samples)"
        print(msg)

    # # Save tables as images
    # # Unsorted df_rate
    # save_table_as_image(df_rate[[label1, label2]], f"{args.vNew}vs{args.vOld}_df_rate_unsorted", output_dir)
    # # Sorted df_rate
    # df_rate_sorted = df_rate.sort_values(by="Trigger", key=lambda x: abs(df_rate["diff"][x]), ascending=False)
    # save_table_as_image(df_rate_sorted[[label1, label2]], f"{args.vNew}vs{args.vOld}_df_rate_sorted", output_dir)
    # # Unsorted df_counts
    # save_table_as_image(df_counts[[label1, label2]], f"{args.vNew}vs{args.vOld}_menu_counts", output_dir)
    # # Sorted df_counts
    # df_counts_sorted = df_counts.sort_values(by='Trigger', key=lambda x: abs(df_rate["diff"][x]), ascending=False)
    # save_table_as_image(df_counts_sorted, f"{args.vNew}__menu_{sorted}", output_dir=output_dir)
    # # Unsorted df_rate with diff
    # save_table_as_image(df_rate[[label1, label2, "diff"]], f"{args.vNew}vs{args.vOld}_menu_diff", output_dir)
    # # Sorted df_rate with diff
    # save_table_as_image(df_rate_sorted[[label1, label2, "diff"]], f"{args.vNew}_rates_diff", output_dir)
    # # Unsorted df_counts with diff
    # save_table_as_image(df_counts[[label1, label2, "diff"]], f"{args.vNew}_counts_diff_unsorted", output_dir)
    # # Sorted df_counts with diff
    # save_table_as_image(df_counts_sorted[[label1, label2, "diff"]], f"{args.vNew}_counts_diff_sorted", output_dir)
    # # Unsorted df_rate with diff, pull, ratio
    # save_table_as_image(df_rate[[label1, label2, "diff", "pull", "ratio"]], f"{args.vNew}_rate_diff_pull_ratio", output_dir)
    # # Sorted df_rate with diff, pull, ratio
    # save_table_as_image(df_rate_sorted[[label1, label2, "diff", "pull", "ratio"]], f"{args.vNew}_rate_diff_pull_ratio_sorted", output_dir)

if __name__ == "__main__":
    main()

import argparse
import os
import sys
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import pandas as pd
from matplotlib.table import table

# Set up plotting style
plt.style.use(hep.style.CMS)
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams["font.size"] = 14

def get_df_new_csv(fname):
    """Load CSV file into a dataframe."""
    df = pd.read_csv(fname, names=["Seed", "counts", "eff", "rate"], skiprows=1)
    return df

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

def main():
    parser = argparse.ArgumentParser(description="Compare L1T Phase2 menu rates.")
    parser.add_argument("--vOld", default="V45nano_noL1EG", help="Old version name (e.g., V45nano_noL1EG)")
    parser.add_argument("--vNew", default="V45nano_L1EGupdate1", help="New version name (e.g., V45nano_L1EGupdate1)")
    parser.add_argument("--output-dir", default="comparisons", help="Output directory part (e.g., comparisons/bisecting)")
    parser.add_argument("--menu", default="v45_Step1Menu", help="Base menu name (default: v45_Step1Menu)")
    parser.add_argument("--menu-vOld", default=None, help="Menu name for vOld (overrides --menu)")
    parser.add_argument("--menu-vNew", default=None, help="Menu name for vNew (overrides --menu)")
    args = parser.parse_args()

    # Set menu names
    menu_vOld = args.menu_vOld if args.menu_vOld else args.menu
    menu_vNew = args.menu_vNew if args.menu_vNew else args.menu

    # Define input and output paths
    base_path = "outputs"
    input_files = {
        args.vOld: f"{base_path}/{args.vOld}/rate_tables/{menu_vOld}_{args.vOld}.csv",
        args.vNew: f"{base_path}/{args.vNew}/rate_tables/{menu_vNew}_{args.vNew}.csv",
    }
    output_dir = f"{base_path}/{args.output_dir}/{args.vNew}vs{args.vOld}/rate_tables"

    # Check if input files exist
    for version, filepath in input_files.items():
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Input CSV file not found: {filepath}")

    # Load dataframes
    dfs = {
        version: get_df_new_csv(filepath)
        for version, filepath in input_files.items()
    }

    # Add version column to dataframes
    for key, df in dfs.items():
        df["version"] = key
        print(f"{key} length: {len(df)}")

    # Concatenate dataframes
    df_all = pd.concat(dfs)
    df_all.Seed = df_all.Seed.str.strip()
    df_all["Trigger"] = df_all.Seed

    # Plot: Totals (Rates > 300 kHz)
    sel = df_all.rate > 300
    print("Rates > 300 kHz:")
    print(df_all[sel]["rate"])
    fig, ax = plt.subplots(figsize=(12, 4))
    df_all[sel].pivot(index='Seed', columns='version', values='rate').plot(kind='barh', ax=ax)
    ax.set_xlabel("Rate [kHz]")
    ax.grid()
    for ext in ['png', 'pdf']:
        filepath = os.path.join(output_dir, f"{args.vNew}vs{args.vOld}_rate_total.{ext}")
        plt.savefig(filepath, bbox_inches='tight', dpi=300)
        print(f"Saving plot at: {filepath}")
    plt.close()

    # Filter for L1_ triggers
    sel = df_all.Trigger.str.contains("L1_")
    df_all = df_all[sel]

    # Pivot tables
    df_rate = df_all.pivot(index='Trigger', columns='version', values='rate')
    df_counts = df_all.pivot(index='Trigger', columns='version', values='counts')

    # Define labels
    label1 = args.vNew
    label2 = args.vOld

    # Calculate differences and ratios
    df_rate["diff"] = df_rate[label1] - df_rate[label2]
    df_rate["pull"] = (df_rate[label1] / df_rate[label2]) - 1
    df_rate["ratio"] = df_rate[label1] / df_rate[label2]
    df_counts["diff"] = df_counts[label1] - df_counts[label2]

    # Plot: Individual Rates (Via Rates < 1200 kHz)
    sel = df_all.rate < 1200
    fig, ax = plt.subplots(figsize=(6, 11))
    df_all[sel].pivot(index='Seed', columns='version', values='rate').plot(kind='barh', ax=ax)
    ax.set_xlabel("Rate [kHz]")
    ax.grid()
    ax.set_xscale("log")
    for ext in ['png', 'pdf']:
        filepath = os.path.join(output_dir, f"{args.vNew}vs{args.vOld}_rate_individual.{ext}")
        plt.savefig(filepath, bbox_inches='tight', dpi=300)
        print(f"Saving plot at: {filepath}")
    plt.close()

    # Plot: Rates, Diff, and Pull
    fig, axs = plt.subplots(1, 3, figsize=(10, 15), sharey=True, gridspec_kw={'width_ratios': [3, 1, 1]})
    df_rate_sort = df_rate.sort_values("diff")
    df_rate_sort[[label1, label2]].plot(kind='barh', ax=axs[0], fontsize=11)
    axs[0].grid()
    axs[0].set_xlabel("Rate [kHz]")
    df_rate_sort[["diff"]].plot(kind='barh', ax=axs[1], legend=False, rot=45)
    axs[1].grid()
    axs[1].set_xlabel(f"Diff: {label1} - {label2} [kHz]")
    df_rate_sort[["pull"]].plot(kind='barh', ax=axs[2], legend=False, rot=45)
    axs[2].grid()
    axs[2].set_xlabel(f"Pull: {label1}/{label2} - 1 [%]")
    plt.subplots_adjust(wspace=0, hspace=0)
    for ext in ['png', 'pdf']:
        filepath = os.path.join(output_dir, f"{args.vNew}vs{args.vOld}_rate_diff_pull.{ext}")
        plt.savefig(filepath, bbox_inches='tight', dpi=300)
        print(f"Saving plot at: {filepath}")
    plt.close()

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

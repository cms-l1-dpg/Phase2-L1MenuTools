import argparse
import os, sys, re
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

# Function to strip the prefix like Vxxnano_
def strip_prefix(s):
    return re.sub(r"^V\d+nano_", "", s)


def main():
    parser = argparse.ArgumentParser(description="Compare L1T Phase2 menu rates from two or three versions.")
    parser.add_argument("--v0", required=True, help="Reference version name (e.g., V45nano_L1EGupdate1)")
    parser.add_argument("--v1", required=True, help="Second version to compare (e.g., V45nano_noL1EG)")
    parser.add_argument("--v2", help="Optional third version to compare")
    parser.add_argument("--output-dir", default="comparisons", help="Output directory part (e.g., comparisons/bisecting)")
    parser.add_argument("--menu", default="v45_Step1Menu", help="Base menu name (default: v45_Step1Menu)")
    parser.add_argument("--menu-v0", default=None, help="Menu name for v0 (overrides --menu)")
    parser.add_argument("--menu-v1", default=None, help="Menu name for v1 (overrides --menu)")
    parser.add_argument("--menu-v2", default=None, help="Menu name for v2 (overrides --menu)")
    args = parser.parse_args()

    # Set menu names
    menu_v0 = args.menu_v0 if args.menu_v0 else args.menu
    menu_v1 = args.menu_v1 if args.menu_v1 else args.menu
    menu_v2 = args.menu_v2 if args.menu_v2 else args.menu

    # Collect all versions
    versions = [args.v0, args.v1]
    menus = [menu_v0, menu_v1]
    if args.v2:
        versions.append(args.v2)
        menus.append(menu_v2)

    # Define labels
    labels = []
    for i, (version, menu) in enumerate(zip(versions, menus)):
        if len(set(versions)) == 1:  # All versions are the same
            labels.append(f"{strip_prefix(version)}_{menu}")
        elif len(set(menus)) == 1:  # All menus are the same
            labels.append(strip_prefix(version))
        else:  # Mixed case
            labels.append(f"{strip_prefix(version)}_{menu}")

    # Define input files
    base_path = "outputs"
    input_files = {}
    for label, version, menu in zip(labels, versions, menus):
        input_files[label] = f"{base_path}/{version}/rate_tables/{menu}_{version}.csv"

    # Set up output directory
    parent_dir = f"{base_path}/{args.output_dir}"
    if not os.path.exists(parent_dir):
        raise FileNotFoundError(f"Parent directory not found, please confirm: {parent_dir}")
    
    comparison_name = f"{args.v0}vs{args.v1}"
    if args.v2:
        comparison_name += f"vs{args.v2}"
    output_dir = f"{base_path}/{args.output_dir}/{comparison_name}/rate_tables"
    os.makedirs(output_dir, exist_ok=True)

    # Check if input files exist
    for version, filepath in input_files.items():
        if not os.path.exists(filepath):
            print(f"Warning: Input CSV file not found: {filepath}")
            if version in labels and args.v2 and version == labels[-1]:
                print("Continuing without v2...")
                # Remove v2 from processing
                labels = labels[:-1]
                versions = versions[:-1]
                menus = menus[:-1]
                input_files = {k: v for k, v in input_files.items() if k != version}
            else:
                raise FileNotFoundError(f"Required input CSV file not found: {filepath}")

    # Load dataframes
    dfs = {}
    for version, filepath in input_files.items():
        dfs[version] = get_df_new_csv(filepath)

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
    # fig, ax = plt.subplots(figsize=(12, 4))
    # df_all[sel].pivot(index='Seed', columns='version', values='rate').plot(kind='barh', ax=ax)
    # ax.set_xlabel("Rate [kHz]")
    # ax.grid()
    # for ext in ['png', 'pdf']:
    #     filepath = os.path.join(output_dir, f"{menu_vNew}_{args.vNew}vs{menu_vOld}_{args.vOld}_rate_total.{ext}")
    #     plt.savefig(filepath, bbox_inches='tight', dpi=300)
    #     print(f"Saving plot at: {filepath}")
    # plt.close()

    # Filter for L1_ triggers
    sel = df_all.Trigger.str.contains("L1_")
    df_all = df_all[sel]

    # Pivot tables
    df_rate = df_all.pivot(index='Trigger', columns='version', values='rate')
    df_counts = df_all.pivot(index='Trigger', columns='version', values='counts')

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
        filepath = os.path.join(output_dir, f"{menu_vNew}_{args.vNew}vs{menu_vOld}_{args.vOld}_rate_individual.{ext}")
        plt.savefig(filepath, bbox_inches='tight', dpi=300)
        print(f"Saving plot at: {filepath}")
    plt.close()

    # Plot: Rates, Diff, and Pull - sorted by total
    fig, axs = plt.subplots(1, 3, figsize=(10, 15), sharey=True, gridspec_kw={'width_ratios': [3, 1, 1]})
    df_rate_sort = df_rate.sort_values(label1)
    df_rate_sort[[label1, label2]].plot(kind='barh', ax=axs[0], fontsize=11)
    axs[0].grid()
    axs[0].set_xlabel("Rate [kHz]")
    df_rate_sort[["diff"]].plot(kind='barh', ax=axs[1], legend=False, rot=45)
    axs[1].grid()
    axs[1].set_xlabel(f"Diff [kHz]")
    df_rate_sort[["pull"]].plot(kind='barh', ax=axs[2], legend=False, rot=45)
    axs[2].grid()
    axs[2].set_xlabel(f"Pull")
    plt.subplots_adjust(wspace=0, hspace=0)
    for ext in ['png', 'pdf']:
        filepath = os.path.join(output_dir, f"{menu_vNew}_{args.vNew}vs{menu_vOld}_{args.vOld}_rate_diff_pull_byTotal.{ext}")
        plt.savefig(filepath, bbox_inches='tight', dpi=300)
        print(f"Saving plot at: {filepath}")
    plt.close()

    # Plot: Rates, Diff, and Pull - sorted by diff
    fig, axs = plt.subplots(1, 3, figsize=(10, 15), sharey=True, gridspec_kw={'width_ratios': [3, 1, 1]})
    df_rate_sort = df_rate.sort_values("diff")
    df_rate_sort[[label1, label2]].plot(kind='barh', ax=axs[0], fontsize=11)
    axs[0].grid()
    axs[0].set_xlabel("Rate [kHz]")
    df_rate_sort[["diff"]].plot(kind='barh', ax=axs[1], legend=False, rot=45)
    axs[1].grid()
    axs[1].set_xlabel(f"Diff [kHz]")
    df_rate_sort[["pull"]].plot(kind='barh', ax=axs[2], legend=False, rot=45)
    axs[2].grid()
    axs[2].set_xlabel(f"Pull")
    plt.subplots_adjust(wspace=0, hspace=0)
    for ext in ['png', 'pdf']:
        filepath = os.path.join(output_dir, f"{menu_vNew}_{args.vNew}vs{menu_vOld}_{args.vOld}_rate_diff_pull.{ext}")
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

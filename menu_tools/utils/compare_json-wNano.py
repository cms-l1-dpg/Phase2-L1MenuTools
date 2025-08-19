#!/usr/bin/env python3
import argparse
import os, sys, re
from glob import glob

import matplotlib.pyplot as plt
import mplhep as hep
plt.style.use(hep.style.CMS)
plt.rcParams['figure.facecolor'] = 'white'

import numpy as np
import pandas as pd
import yaml
import json

def load_json(fname):
    with open(fname) as f:
        plot = json.load(f)
        return plot

# Function to strip the prefix like Vxxnano_
def strip_prefix(s):
    return re.sub(r"^V\d+nano_", "", s)

def comp_nano_plots(nano_plot, menu_plot, v2_plot=None, sfxs=["v22", "v27"], ptype="turnon",
                   lss=["-", "--"], keys=None, markers=["o", "s"]):
    
    fig, axs = plt.subplots(2, 1, figsize=(10, 12),
                            sharex=True,
                            gridspec_kw={'height_ratios': [3, 1]})
    hep.cms.label(ax=axs[0], llabel="Phase-2 Simulation", rlabel="14 TeV")

    if keys is None: keys = nano_plot.keys()
                
    # clean keys - now check against all plots
    clean_keys = []
    only1_keys = []
    only2_keys = []
    only3_keys = []
    
    for key in keys:
        if key in ['xlabel', 'ylabel', 'watermark']: 
            continue
        
        in_nano = key in nano_plot.keys()
        in_menu = key in menu_plot.keys()
        in_v2 = v2_plot is not None and key in v2_plot.keys()
        
        if in_nano and in_menu and (v2_plot is None or in_v2):
            clean_keys.append(key)
        elif in_nano and not in_menu and not in_v2:
            only1_keys.append(key)
        elif not in_nano and in_menu and not in_v2:
            only2_keys.append(key)
        elif not in_nano and not in_menu and in_v2:
            only3_keys.append(key)
        else:
            # Handle partial matches - for now, skip with warning
            missing = []
            if not in_nano: missing.append("nano_plot")
            if not in_menu: missing.append("menu_plot")
            if v2_plot is not None and not in_v2: missing.append("v2_plot")
            if missing:
                print(f"Warning: {key} missing in {', '.join(missing)}. Skipping...")
        
    jTot = 0
    
    # Plot keys that exist in all relevant plots
    for j, key in enumerate(clean_keys):
        plots = [nano_plot[key], menu_plot[key]]
        if v2_plot is not None:
            plots.append(v2_plot[key])
            
        color = f"C{j}"
        jTot += 1
        
        for i, p1 in enumerate(plots):
            sfx = sfxs[i] if i < len(sfxs) else sfxs[-1]  # Use last sfx if not enough provided
            label = None
            if i == 0:
                label = f"{p1['label']}"

            # Determine line style and marker fill
            if i == 0:  # v0 - solid line, filled marker
                ls = "-"
                mfc = color
            elif i == 1:  # v1 - dashed line, empty marker
                ls = "--"
                mfc = "none"
            else:  # v2 - dotted line, empty marker
                ls = ":"
                mfc = "none"

            if ptype == "scalings":
                axs[0].plot(p1["xvals"], p1["yvals"], color=color, marker=markers[min(i, len(markers)-1)],
                            label=label, ls=ls, mfc=mfc)
            elif ptype == "rate":
                axs[0].plot(p1["x_values"], p1["y_values"], color=color, marker=markers[min(i, len(markers)-1)],
                            label=label, ls=ls, mfc=mfc)
            elif ptype == "turnon":
                p1["err_kwargs"]["marker"] = markers[min(i, len(markers)-1)]
                p1["err_kwargs"]["xerr"] = None

                axs[0].errorbar(p1["xbins"], p1["efficiency"], yerr=p1["efficiency_err"], 
                            label=label, ls=ls, color=color, mfc=mfc,
                            **(p1["err_kwargs"]))
        
        # Make ratios (only between v0 and v1 for now, as v0 is the reference)
        plots_for_ratio = [nano_plot[key], menu_plot[key]]
        if ptype == "scalings":
            d_p1 = dict(zip(plots_for_ratio[0]["xvals"], plots_for_ratio[0]["yvals"]))
            d_p2 = dict(zip(plots_for_ratio[1]["xvals"], plots_for_ratio[1]["yvals"]))
        elif ptype == "rate":
            d_p1 = dict(zip(plots_for_ratio[0]["x_values"], plots_for_ratio[0]["y_values"]))
            d_p2 = dict(zip(plots_for_ratio[1]["x_values"], plots_for_ratio[1]["y_values"]))
        elif ptype == "turnon":
            d_p1 = dict(zip(plots_for_ratio[0]["xbins"], plots_for_ratio[0]["efficiency"]))
            d_p2 = dict(zip(plots_for_ratio[1]["xbins"], plots_for_ratio[1]["efficiency"]))
            
        df_p1 = pd.Series(d_p1)
        df_p2 = pd.Series(d_p2)

        if (df_p1.sum() != 0) and (df_p2.sum() != 0):
            diff = (df_p1 - df_p2) 
            if ptype == "rate":
                diff /= df_p2
            label_ratio = p1["label"].split(",")[0]
            
            # diff.plot(ax=axs[1], color=color, label=label_ratio)
            diff.plot(ax=axs[1], color=color, linestyle="--", label=label_ratio)
            
            if ptype == "turnon":
                if len(plots_for_ratio[0]["efficiency_err"][0]) == len(plots_for_ratio[1]["efficiency_err"][0]):
                    y_err = np.hypot(plots_for_ratio[0]["efficiency_err"][0], plots_for_ratio[1]["efficiency_err"][0])
                    if len(diff) == len(y_err):
                        axs[1].fill_between(diff.index, diff.values - y_err, diff.values + y_err,
                                            alpha=0.3, color=color)
        
        # Add ratio for v2 if it exists
        if v2_plot is not None and key in v2_plot:
            if ptype == "scalings":
                d_p3 = dict(zip(v2_plot[key]["xvals"], v2_plot[key]["yvals"]))
            elif ptype == "rate":
                d_p3 = dict(zip(v2_plot[key]["x_values"], v2_plot[key]["y_values"]))
            elif ptype == "turnon":
                d_p3 = dict(zip(v2_plot[key]["xbins"], v2_plot[key]["efficiency"]))
                
            df_p3 = pd.Series(d_p3)
            
            if (df_p1.sum() != 0) and (df_p3.sum() != 0):
                diff_v2 = (df_p1 - df_p3)
                if ptype == "rate":
                    diff_v2 /= df_p3
                
                diff_v2.plot(ax=axs[1], color=color, linestyle=":", alpha=0.7)

    # Handle keys only in specific plots
    for j, key in enumerate(only1_keys):
        plots = [nano_plot[key]]
        color = f"C{jTot}"
        jTot += 1
        for i, p1 in enumerate(plots):
            label = f"{p1['label']}"

            if ptype == "scalings":
                axs[0].plot(p1["xvals"], p1["yvals"], color=color, marker=markers[0],
                            label=label, ls="-", mfc=color)
            elif ptype == "rate":
                axs[0].plot(p1["x_values"], p1["y_values"], color=color, marker=markers[0],
                            label=label, ls="-", mfc=color)
            elif ptype == "turnon":
                p1["err_kwargs"]["marker"] = markers[0]
                p1["err_kwargs"]["xerr"] = None
                axs[0].errorbar(p1["xbins"], p1["efficiency"], yerr=p1["efficiency_err"], 
                            label=label, ls="-", color=color, mfc=color,
                            **(p1["err_kwargs"]))

    for j, key in enumerate(only2_keys):
        plots = [menu_plot[key]]
        color = f"C{jTot}"
        jTot += 1
        for i, p1 in enumerate(plots):
            label = f"{strip_prefix(sfxs[1])}, {p1['label']}"

            if ptype == "scalings":
                axs[0].plot(p1["xvals"], p1["yvals"], color=color, marker=markers[1],
                            label=label, ls="--", mfc="none")
            elif ptype == "rate":
                axs[0].plot(p1["x_values"], p1["y_values"], color=color, marker=markers[1],
                            label=label, ls="--", mfc="none")
            elif ptype == "turnon":
                p1["err_kwargs"]["marker"] = markers[1]
                p1["err_kwargs"]["xerr"] = None
                axs[0].errorbar(p1["xbins"], p1["efficiency"], yerr=p1["efficiency_err"], 
                                label=label, ls="--", color=color, mfc="none",
                                **(p1["err_kwargs"]))

    for j, key in enumerate(only3_keys):
        plots = [v2_plot[key]]
        color = f"C{jTot}"
        jTot += 1
        for i, p1 in enumerate(plots):
            label = f"{strip_prefix(sfxs[2])}, {p1['label']}"

            if ptype == "scalings":
                axs[0].plot(p1["xvals"], p1["yvals"], color=color, marker=markers[1],
                            label=label, ls=":", mfc="none")
            elif ptype == "rate":
                axs[0].plot(p1["x_values"], p1["y_values"], color=color, marker=markers[1],
                            label=label, ls=":", mfc="none")
            elif ptype == "turnon":
                p1["err_kwargs"]["marker"] = markers[1]
                p1["err_kwargs"]["xerr"] = None
                axs[0].errorbar(p1["xbins"], p1["efficiency"], yerr=p1["efficiency_err"], 
                                label=label, ls=":", color=color, mfc="none",
                                **(p1["err_kwargs"]))

    # Add legend entries for version styles (without markers, at the end)
    if ptype == "turnon":
        axs[0].errorbar([], [], yerr=[], label=f"{strip_prefix(sfxs[1])}", ls="--", color="grey", mfc="none")
        if v2_plot is not None and len(sfxs) > 2:
            axs[0].errorbar([], [], yerr=[], label=f"{strip_prefix(sfxs[2])}", ls=":", color="grey", mfc="none")
    else:
        axs[0].plot([], [], color="grey", label=f"{strip_prefix(sfxs[1])}", ls="--")
        if v2_plot is not None and len(sfxs) > 2:
            axs[0].plot([], [], color="grey", label=f"{strip_prefix(sfxs[2])}", ls=":")

    # make axis stuff
    axs[0].legend(fontsize="x-small")
    axs[1].legend(fontsize="x-small")
    
    if ptype == "rate":
        axs[1].set_ylabel("Rel. Diff.", fontsize="small")
        axs[0].set_yscale("log")
        axs[1].set_xlabel(nano_plot[list(clean_keys)[0]]["xlabel"] if clean_keys else "")
        axs[0].set_ylabel("Rate [kHz]")
    else:
        axs[1].set_ylabel("Diff.", fontsize="small")
        
    if ptype == "scalings":
        axs[0].set_ylabel("95 % Location [GeV]")
        axs[1].set_xlabel("L1 threshold [GeV]")
    elif ptype == "turnon":
        axs[0].set_ylabel(nano_plot.get("ylabel", ""), fontsize="small")
        axs[1].set_xlabel(nano_plot.get("xlabel", ""))
        axs[1].set_ylim(-.1, .1)
        
    for ax in axs: ax.grid()
    plt.tight_layout()
    plt.subplots_adjust(wspace=0, hspace=0)

    return fig

def main():
    parser = argparse.ArgumentParser(description="Compare JSON plots from two or three versions")
    parser.add_argument("--v0", required=True, help="First version to compare (reference)")
    parser.add_argument("--v1", required=True, help="Second version to compare")
    parser.add_argument("--v2", help="Optional third version to compare")
    parser.add_argument("--base-path", default="/eos/user/r/roward/www/L1T/Phase2/menu/Validation/NewMenuTools",
                        help="Base path for JSON files")
    parser.add_argument("--output-dir", default="comparisons", help="Output directory for plots")
    
    args = parser.parse_args()
    
    v0 = args.v0
    v1 = args.v1
    v2 = args.v2
    
    v0_jsons = glob(f"{args.base_path}/{v0}/object_performance/*/*.json")
    
    for v0_json in v0_jsons:
        v1_json = v0_json.replace(v0, v1)
        if not os.path.exists(v1_json):
            print(f"{v1_json} does not exist")
            continue

        v2_json = None
        v2_plot = None
        if v2 is not None:
            v2_json = v0_json.replace(v0, v2)
            if not os.path.exists(v2_json):
                print(f"{v2_json} does not exist, skipping v2 for this plot")
            else:
                v2_plot = load_json(v2_json)

        print(os.path.basename(v0_json))
        print(os.path.basename(v1_json))
        if v2_json:
            print(os.path.basename(v2_json))
        
        if "Offline_JetExtendedRates" in v0_json:
            print(f"SKIPPING {v0_json}")
            continue
        
        plot1 = load_json(v0_json)
        plot2 = load_json(v1_json)
        
        if "turnon" in v0_json:
            ptype = "turnon"
        elif "scaling" in v0_json:
            ptype = "scalings"
        elif "rate" in v0_json:
            ptype = "rate"
        else:
            print("WARNING, unsupported plot type")
            continue
        
        sfxs = [v0, v1]
        if v2 is not None:
            sfxs.append(v2)
        
        f = comp_nano_plots(plot1, plot2, v2_plot, sfxs=sfxs, 
                       lss=["-", "--"],
                       markers=[".", "o"],
                       ptype=ptype)

        # Construct output filename
        comparison_name = f"{v0}vs{v1}"
        if v2 is not None:
            comparison_name += f"vs{v2}"
            
        outfname = v0_json.replace(v0, comparison_name).replace(".json", ".png").replace(f"{comparison_name}/", f"{args.output_dir}/{comparison_name}/")
        
        outdir = os.path.dirname(outfname)
        if not os.path.exists(outdir): 
            os.makedirs(outdir)
            
        print(f"Saving plot {outfname}")
        plt.savefig(outfname)

        # save pdf
        outfname_pdf = outfname.replace(".png", ".pdf")
        plt.savefig(outfname_pdf)
        
        plt.close()

if __name__ == "__main__":
    main()

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

def comp_nano_plots(nano_plot, menu_plot, sfxs=["v22", "v27"], ptype="turnon",
                   lss=["-", "--"], keys=None, markers=["o", "s"]):
    
    fig, axs = plt.subplots(2, 1, figsize=(10, 12),
                            sharex=True,
                            gridspec_kw={'height_ratios': [3, 1]})
    hep.cms.label(ax=axs[0], llabel="Phase-2 Simulation", rlabel="14 TeV")

    if keys is None: keys = nano_plot.keys()
                
    # clean keys
    clean_keys = []
    only1_keys = []
    only2_keys = []
    for key in keys:
        if key in ['xlabel', 'ylabel', 'watermark']: 
            continue
        if key not in nano_plot.keys():
            print(f"Warning: {key} not in plot 1 keys. Skipping...")
            only2_keys.append(key)
            continue
        if key not in menu_plot.keys():
            print(f"Warning: {key} not in plot 2 keys. Skipping...")
            only1_keys.append(key)
            continue
        clean_keys.append(key)
        
    jTot=0
    for j, key in enumerate(clean_keys):
        ## plot 1
        plots = [nano_plot[key], menu_plot[key]]
        color = f"C{j}"
        jTot+=1
        for i, p1 in enumerate(plots):
            sfx = sfxs[i]
            label = None
            if i == 0:
                label = f"{p1['label']}"
                # label = f"{strip_prefix(sfx)}, {p1['label']}"

            if ptype == "scalings":
                axs[0].plot(p1["xvals"], p1["yvals"], color=color, marker=markers[i],
                            label=label, ls=lss[i], mfc="none" if i == 1 else color)
            elif ptype == "rate":
                axs[0].plot(p1["x_values"], p1["y_values"], color=color, marker=markers[i],
                            label=label, ls=lss[i], mfc="none" if i == 1 else color)
            elif ptype == "turnon":
                p1["err_kwargs"]["marker"] = markers[i]
                p1["err_kwargs"]["xerr"] = None

                axs[0].errorbar(p1["xbins"], p1["efficiency"], yerr=p1["efficiency_err"], 
                            label=label, ls=lss[i], color=color, mfc="none" if i == 1 else color,
                            **(p1["err_kwargs"]))
        
        ## Make ratios
        if ptype == "scalings":
            d_p1 = dict(zip(plots[0]["xvals"], plots[0]["yvals"]))
            d_p2 = dict(zip(plots[1]["xvals"], plots[1]["yvals"]))
        elif ptype == "rate":
            d_p1 = dict(zip(plots[0]["x_values"], plots[0]["y_values"]))
            d_p2 = dict(zip(plots[1]["x_values"], plots[1]["y_values"]))
        elif ptype == "turnon":
            d_p1 = dict(zip(plots[0]["xbins"], plots[0]["efficiency"]))
            d_p2 = dict(zip(plots[1]["xbins"], plots[1]["efficiency"]))
            
        df_p1 = pd.Series(d_p1)
        df_p2 = pd.Series(d_p2)

        if (df_p1.sum() != 0) and (df_p2.sum() != 0):
            diff = (df_p1 - df_p2) 
            if ptype == "rate":
                diff /= df_p2
            label = p1["label"].split(",")[0]
            
            diff.plot(ax=axs[1], color=color, label=label)
            
            if ptype == "turnon":
                if len(plots[0]["efficiency_err"][0]) != len(plots[1]["efficiency_err"][0]): continue
                y_err = np.hypot(plots[0]["efficiency_err"][0], plots[1]["efficiency_err"][0])
                if len(diff) != len(y_err): continue
                axs[1].fill_between(diff.index, diff.values - y_err, diff.values + y_err,
                                    alpha=0.3, color=color)

    for j, key in enumerate(only1_keys):
        ## plot 1
        plots = [nano_plot[key]]
        color = f"C{jTot}"
        jTot+=1
        for i, p1 in enumerate(plots):
            sfx = sfxs[0]
            label = f"{p1['label']}"
            # label = f"{strip_prefix(sfx)}, {p1['label']}"

            if ptype == "scalings":
                axs[0].plot(p1["xvals"], p1["yvals"], color=color, marker=markers[0],
                            label=label, ls=lss[0], mfc=color)
            elif ptype == "rate":
                axs[0].plot(p1["x_values"], p1["y_values"], color=color, marker=markers[0],
                            label=label, ls=lss[0], mfc=color)
            elif ptype == "turnon":
                p1["err_kwargs"]["marker"] = markers[0]
                p1["err_kwargs"]["xerr"] = None

                axs[0].errorbar(p1["xbins"], p1["efficiency"], yerr=p1["efficiency_err"], 
                            label=label, ls=lss[0], color=color, mfc=color,
                            **(p1["err_kwargs"]))

    for j, key in enumerate(only2_keys):
        ## plot 1
        plots = [menu_plot[key]]
        color = f"C{jTot}"
        jTot+=1
        for i, p1 in enumerate(plots):
            sfx = sfxs[1]
            label = f"{strip_prefix(sfx)}, {p1['label']}"

            if ptype == "scalings":
                axs[0].plot(p1["xvals"], p1["yvals"], color=color, marker=markers[1],
                            label=label, ls=lss[1], mfc="none")
            elif ptype == "rate":
                axs[0].plot(p1["x_values"], p1["y_values"], color=color, marker=markers[1],
                            label=label, ls=lss[1], mfc="none")
            elif ptype == "turnon":
                p1["err_kwargs"]["marker"] = markers[1]
                p1["err_kwargs"]["xerr"] = None

                axs[0].errorbar(p1["xbins"], p1["efficiency"], yerr=p1["efficiency_err"], 
                                label=label, ls=lss[1], color=color, mfc="none",
                                **(p1["err_kwargs"]))

                
    # add old version label
    if ptype == "scalings":
        axs[0].plot([], [], color="grey", marker=markers[1], label=f"{strip_prefix(sfxs[1])}", ls=lss[1], mfc="none")
    elif ptype == "rate":
        axs[0].plot([], [], color="grey", marker=markers[1], label=f"{strip_prefix(sfxs[1])}", ls=lss[1], mfc="none")
    elif ptype == "turnon":
        axs[0].errorbar([], [], yerr=[], label=f"{strip_prefix(sfxs[1])}", ls=lss[1], color="grey", mfc="none")

    # make axis stuff
    axs[0].legend(fontsize="x-small")
    axs[1].legend(fontsize="x-small")
    
    if ptype == "rate":
        # axs[1].set_ylabel(f"({sfxs[0]}-{sfxs[1]})/{sfxs[1]}", fontsize="x-small")
        axs[1].set_ylabel(f"({strip_prefix(sfxs[0])}-{strip_prefix(sfxs[1])})/{strip_prefix(sfxs[1])}", fontsize="x-small")
        axs[0].set_yscale("log")
        axs[1].set_xlabel(nano_plot[key]["xlabel"])
        axs[0].set_ylabel("Rate [kHz]")
    else:
        # axs[1].set_ylabel(f"{sfxs[0]} - {sfxs[1]}", fontsize="x-small")
        axs[1].set_ylabel(f"{strip_prefix(sfxs[0])} - {strip_prefix(sfxs[1])}", fontsize="x-small")
        
    if ptype == "scalings":
        axs[0].set_ylabel("95 % Location [GeV]")
        axs[1].set_xlabel("L1 threshold [GeV]")
    elif ptype == "turnon":
        axs[0].set_ylabel(nano_plot["ylabel"], fontsize="small")
        axs[1].set_xlabel(nano_plot["xlabel"])
        axs[1].set_ylim(-.1, .1)
        
    for ax in axs: ax.grid()
    plt.tight_layout()
    plt.subplots_adjust(wspace=0, hspace=0)

    return fig

def main():
    parser = argparse.ArgumentParser(description="Compare JSON plots from two versions")
    parser.add_argument("--v0", required=True, help="First version to compare")
    parser.add_argument("--v1", required=True, help="Second version to compare")
    parser.add_argument("--base-path", default="outputs",
                        help="Base path for JSON files")
    parser.add_argument("--output-dir", default="comparisons", help="Output directory for plots")
    
    args = parser.parse_args()
    
    v0 = args.v0
    v1 = args.v1
    
    v0_jsons = glob(f"{args.base_path}/{v0}/object_performance/*/*.json")
    
    for v0_json in v0_jsons:
        v1_json = v0_json.replace(v0, v1)
        if not os.path.exists(v1_json):
            print(f"{v1_json} does not exist")
            continue

        print(os.path.basename(v0_json))
        print(os.path.basename(v1_json))
        
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
        
        f = comp_nano_plots(plot1, plot2, sfxs=[v0, v1], 
                       lss=["-", "--"],
                       markers=[".", "o"],
                       ptype=ptype)

        
        outfname = v0_json.replace(v0, f"{v0}vs{v1}").replace(".json", ".png").replace(f"{v0}vs{v1}/", f"{args.output_dir}/{v0}vs{v1}/")
        
        outdir = os.path.dirname(outfname)
        if not os.path.exists(outdir): os.makedirs(outdir)
            
        print(f"Saving plot {outfname}")
        plt.savefig(outfname)

        # save pdf
        outfname = outfname.replace(".png", ".pdf")
        plt.savefig(outfname)
        
        plt.close()

if __name__ == "__main__":
    main()

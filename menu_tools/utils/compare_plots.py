import os
import json
import numpy as np
import pandas as pd
from glob import glob
import matplotlib.pyplot as plt
import mplhep as hep

f = plt.figure()
plt.close()


plt.style.use(hep.style.CMS)
plt.rcParams["figure.facecolor"] = "white"


def load_json(fname):
    with open(fname) as f:
        plot = json.load(f)
        return plot


def remap_nano_key(key):
    if "StaMu" in key:
        key = key.replace("StaMu", "gmtMuon")

    #     print("before", key)

    if "L1puppiJetSC4sums:HT" in key:
        key = key.replace("L1puppiJetSC4sums:HT", "seededConePuppiHT:default")
    if "L1puppiJetSC4sums:MHT" in key:
        key = key.replace("L1puppiJetSC4sums:MHT", "seededConePuppiMHT:default")

    if "nnPuppiTau" in key:
        key = key.replace("nnPuppiTau", "nnTau")

    if "L1puppiHistoJetSums:HT" in key:
        key = key.replace("L1puppiHistoJetSums:HT", "phase1PuppiHT:default")
    if "L1puppiHistoJetSums:MHT" in key:
        key = key.replace("L1puppiHistoJetSums:MHT", "phase1PuppiMHT:default")

    if "L1TrackHT:HT" in key:
        key = key.replace("L1TrackHT:HT", "trackerHT:default")
    if "L1TrackHT:MHT" in key:
        key = key.replace("L1TrackHT:MHT", "trackerMHT:default")
    if "L1TrackMET" in key:
        key = key.replace("L1TrackMET", "trackerMET")
    if "L1TrackJet" in key:
        key = key.replace("L1TrackJet", "trackerJet")

    if "puppiJetHisto" in key:
        key = key.replace("puppiJetHisto", "phase1PuppiJet")
    if "puppiJetSC4" in key:
        key = key.replace("puppiJetSC4", "seededConePuppiJet")

    if "L1puppiExtJetSC4" in key:
        key = "seededConeExtendedPuppiJet"

    key = key.replace("L1", "")
    #     print("after", key)

    return key


def comp_plots(
    nano_plot,
    menu_plot,
    sfxs=["v22", "v27"],
    ptype="turnon",
    lss=["-", "--"],
    keys=None,
    markers=["o", "s"],
):
    fig, axs = plt.subplots(
        2, 1, figsize=(10, 12), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )
    hep.cms.label(ax=axs[0], llabel="Phase-2 Simulation", rlabel="14 TeV")

    if keys is None:
        keys = nano_plot.keys()
    # clean keys
    clean_keys = []
    for key in keys:
        if key in ["xlabel", "ylabel", "watermark"]:
            continue
        if key not in nano_plot.keys():
            print(f"Warning: {key} not in plot 1 keys. Skipping...")
            continue
        if remap_nano_key(key) not in menu_plot.keys():
            print(menu_plot.keys())
            print(f"Warning: {key} not in plot 2 keys. Skipping...")
            continue
        clean_keys.append(key)

    #     if ptype == "rate":
    #         xval_str = "x_values"
    #         yval_str = "y_values"
    #     else:
    #         xval_str = "xvals"
    #         yval_str = "yvals"

    for j, key in enumerate(clean_keys):
        ## plot 1
        plots = [nano_plot[key], menu_plot[remap_nano_key(key)]]
        color = f"C{j}"

        for i, p1 in enumerate(plots):
            sfx = sfxs[i]
            label = f"{sfx}, {p1['label']}"

            if ptype == "scalings":
                axs[0].plot(
                    p1["xvals"],
                    p1["yvals"],
                    color=color,
                    marker=markers[i],
                    label=label,
                    ls=lss[i],
                    mfc="none" if i == 1 else color,
                )
            elif ptype == "rate":
                axs[0].plot(
                    p1["x_values"],
                    p1["y_values"],
                    color=color,
                    marker=markers[i],
                    label=label,
                    ls=lss[i],
                    mfc="none" if i == 1 else color,
                )
            elif ptype == "turnon":
                p1["err_kwargs"]["marker"] = markers[i]
                p1["err_kwargs"]["xerr"] = None

                axs[0].errorbar(
                    p1["xbins"],
                    p1["efficiency"],
                    yerr=p1["efficiency_err"],
                    label=label,
                    ls=lss[i],
                    color=color,
                    mfc="none" if i == 1 else color,
                    **(p1["err_kwargs"]),
                )

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

            # add 100% eff line
        #             axs[0].axhline(1,ls = ":", alpha = 0.5, c = "k")

        df_p1 = pd.Series(d_p1)
        df_p2 = pd.Series(d_p2)

        #         ax = axs[1]

        if (df_p1.sum() != 0) and (df_p1.sum() != 0):
            diff = df_p1 - df_p2
            if ptype == "rate":
                diff /= df_p2
            label = p1["label"].split(",")[0]

            diff.plot(
                ax=axs[1], color=color, label=label
            )  # , marker = ".", color = color)
            # axs[1].errorbar(
            #     p1["xbins"],df_p1 - df_p2,
            #     yerr = np.hypot(plots[0]["efficiency_err"], plots[1]["efficiency_err"]),
            #     # label = label, marker = ".", color = color,
            #     label = label, ls = lss[i], color = color, mfc="none" if i == 1 else color,
            #     **(p1["err_kwargs"])
            #     )
            if ptype == "turnon":
                if len(plots[0]["efficiency_err"][0]) != len(
                    plots[1]["efficiency_err"][0]
                ):
                    continue
                y_err = np.hypot(
                    plots[0]["efficiency_err"][0], plots[1]["efficiency_err"][0]
                )
                if len(diff) != len(y_err):
                    continue
                axs[1].fill_between(
                    diff.index,
                    diff.values - y_err,
                    diff.values + y_err,
                    #                                 label = label,
                    alpha=0.3,
                    color=color,
                )

    # make axis stuff
    axs[0].legend(fontsize="x-small")
    axs[1].legend(fontsize="x-small")

    if ptype == "rate":
        axs[1].set_ylabel(f"({sfxs[0]}-{sfxs[1]})/{sfxs[1]}", fontsize="x-small")
        axs[0].set_yscale("log")
        axs[1].set_xlabel("Threshold [GeV]")
        axs[0].set_ylabel("Rate [kHz]")
    else:
        axs[1].set_ylabel(f"{sfxs[0]} - {sfxs[1]}", fontsize="x-small")

    if ptype == "scalings":
        axs[0].set_ylabel("95 % Location [GeV]")
        axs[1].set_xlabel("L1 threshold [GeV]")
    elif ptype == "turnon":
        axs[0].set_ylabel(nano_plot["ylabel"], fontsize="small")
        axs[1].set_xlabel(nano_plot["xlabel"])

        axs[1].set_ylim(-0.1, 0.1)

    for ax in axs:
        ax.grid()
    plt.tight_layout()
    plt.subplots_adjust(wspace=0, hspace=0)

    return fig


def main(v0, v1, v0_jsons):
    for v0_json in v0_jsons:
        v1_json = v0_json.replace(v0, v1)
        if not os.path.exists(v1_json):
            print(v1_json + " does not exist")
            continue
        #     continue

        #     print("1")
        plot1 = load_json(v0_json)
        #     print("2")
        plot2 = load_json(v1_json)

        print(os.path.basename(v0_json))
        print(os.path.basename(v1_json))

        if "turnon" in v0_json:
            ptype = "turnon"
        elif "scaling" in v0_json:
            ptype = "scalings"
        elif "rate" in v0_json:
            ptype = "rate"
        else:
            print("WARNING, unsupported plot type")
            continue

        comp_plots(
            plot1,
            plot2,
            sfxs=[v0, v1],
            lss=["-", "--"],
            #                    lss = ["",""],
            markers=[".", "o"],
            ptype=ptype,
        )

        # outfname = v0_json.replace(
        #     v0,"%svs%s"%(v0,v1)).replace(
        #         ".json",".png").replace("tools","tools/comparisons")

        outfname = (
            v0_json.replace(v0, "%svs%s" % (v0, v1))
            .replace(".json", ".png")
            .replace("%svs%s/" % (v0, v1), "comparisons/%svs%s/" % (v0, v1))
        )

        #     break

        outdir = os.path.dirname(outfname)
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        print("Saving plot %s" % outfname)
        plt.savefig(outfname)

        # save pdf
        outfname = outfname.replace(".png", ".pdf")
        plt.savefig(outfname)

        plt.close()
    #     break


### MAIN

v0 = "V33nano"
# v0 = "V29"
# v0 = "V32nano"
# v0 = "V31"

basedir = "/eos/user/a/alobanov/www/L1T/Phase2/menu/Validation/NewMenuTools"
v0_jsons = glob(
    # f"{basedir}/{v0}//s*/**.json")
    f"{basedir}/{v0}/object_performance/r*/*JetsBy*.json"
)

# v1 = "V29"
# v1 = "V32"
# v1 = "V32nano"
v1 = "V31"

print(f"Found {len(v0_jsons)} files")

main(v0, v1, v0_jsons)

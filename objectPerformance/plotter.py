#!/afs/cern.ch/user/d/dhundhau/miniconda3/envs/py310/bin/python
import argparse
from datetime import datetime
import glob
from itertools import product
import json
import time
import warnings

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import pandas as pd
from scipy.stats import beta
import yaml

from ntuple_loader import NTupleLoader
import utils


plt.style.use(hep.style.CMS)


class Skimmer():

    def __init__(self, cfg_plot, version, sample, threshold, region):
        self.cfg_plot = cfg_plot
        self.version = version
        self.sample = sample
        self.threshold = threshold
        self.region = region
        self.bin_width = cfg_plot["binning"]["step"]
        self.bins = np.array([i * self.bin_width for i in range(int(cfg_plot["binning"]["max"] / self.bin_width) + 1)])
        self.df = None
        self.hists = {}

    def _load_df_from_h5(self):
        """ Load dfs from h5 file with hased name of sample+config """
        fname = self.version + '_' + self.sample
        self.df = pd.read_hdf(f"tmp/{fname}.h5", key="l1")
        # print(self.df["genMetTrue"])
        # print(self.df["jetPt"])

    def _get_reference_cuts_mask(self, df, sel):
        if not self.cfg_plot["reference_cuts"]:
            return sel
        for branch, cut_cfg in self.cfg_plot["reference_cuts"].items():
            op = utils.str_to_op(cut_cfg["operator"])
            threshold = cut_cfg["threshold"]
            tmp_sel = op(self.df[branch], threshold)
            # df.loc[tmp_sel, branch] = 0
            sel = np.logical_and(sel, tmp_sel)
        return sel
 
    def _apply_ref_column_trafo(self, df):
        try:
            trafo = self.cfg_plot["inputs"]["reference_trafo"]
        except KeyError:
            # print("No Trafo made!")
            return df
        if trafo == "per_event_sum":
            return df.groupby(level=0).sum()

    def _get_ref_column(self):
        col_ref = self.cfg_plot["inputs"]["reference_key"]
        df_ref = self.df[[col_ref]]
        sel = self._get_reference_cuts_mask(df_ref, df_ref > -999)
        df_ref = df_ref[sel]
        df_ref = self._apply_ref_column_trafo(df_ref)
        return df_ref

    def _get_reco_column(self, obj_key, df_ref):
        df_reco = self.df[obj_key]
        sel = (df_reco > self.threshold)
        return df_ref[sel]

    def _skim_to_hists(self):
        df_ref = self._get_ref_column()
        # print(df_ref)
        self.hists["ref"] = np.histogram(df_ref, bins=self.bins)
        for obj_key in self.cfg_plot["inputs"]["object_keys_labels"]:
            df_reco = self._get_reco_column(obj_key, df_ref)
            # print(df_reco)
            self.hists[obj_key] = np.histogram(df_reco, bins=self.bins)

    def create_hists(self):
        self._load_df_from_h5()
        self._skim_to_hists()


class EfficiencyPlotter():

    def __init__(self, name, cfg, skimmer):
        self.plot_name = name
        self.cfg = cfg
        self.skimmer = skimmer

    def plot(self):
        print("Plotting ...")
        fig, ax = plt.subplots(figsize = (10,10))
        hep.cms.label(ax=ax, llabel="Phase-2 Simulation", com=14)
        gen_hist_ref = self.skimmer.hists["ref"]
        xbins = self.skimmer.bins[:-1] + self.skimmer.bin_width / 2

        xerr = np.ones_like(gen_hist_ref[0]) * self.skimmer.bin_width / 2
        err_kwargs = {"xerr": xerr, "capsize": 3, "marker": 'o', "markersize": 8}
        for obj_key, gen_hist_trig in self.skimmer.hists.items():
            if obj_key== "ref":
                continue
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                efficiency = gen_hist_trig[0] / gen_hist_ref[0]
            yerr = utils.clopper_pearson_err(gen_hist_trig[0], gen_hist_ref[0])
            label = self.cfg["inputs"]["object_keys_labels"][obj_key]
            ax.errorbar(xbins, efficiency, yerr=yerr, label=label, **err_kwargs)

        ax.axvline(self.skimmer.threshold, ls = ":", c = "k")
        ax.axhline(1, ls = ":", c = "k")
        ax.legend(loc="lower right", frameon=False)
        ax.set_xlabel(self.cfg["xlabel"])
        # ax.set_xlabel(self.cfg["xlabel"] + datetime.now().strftime("%H:%M:%S"))
        ylabel = self.cfg["ylabel"].replace("<threshold>", str(self.skimmer.threshold))
        ylabel = ylabel.replace("<region>", f"{', ' + self.skimmer.region if self.skimmer.region else ''}")
        ax.set_ylabel(ylabel)
        ax.set_xlim(self.cfg["binning"]["min"], self.cfg["binning"]["max"])
        ax.set_ylim(0, 1.1)
        ax.tick_params(direction="in")
        plt.savefig(f"plot_output/{self.plot_name}_{self.skimmer.threshold}.png")
        plt.savefig(f"/eos/user/d/dhundhau/www/L1_PhaseII/python_plots/{self.plot_name}_{self.skimmer.threshold}.png")
        plt.close()


class PlottingCentral():

    def __init__(self, cfg_plots_path):
        with open("cfg.yaml", 'r') as f:
            self.cfg = yaml.safe_load(f)
        with open(cfg_plots_path, 'r') as f:
            self.cfg_plots = yaml.safe_load(f)
        self.version = self.cfg_plots["global"]["version"]
        self.sample = self.cfg_plots["global"]["sample"]

    def _load_ntuples(self):
        loader = NTupleLoader(self.version, self.sample)
        loader.load()

    def run(self):
        for plot_name, cfg_plot in self.cfg_plots["plots"].items():
            self._load_ntuples()
            for region, threshold in product(cfg_plot["regions"], cfg_plot["thresholds"]):
                print(f">>> {plot_name} ({threshold} GeV {region}) <<<")
                # Skim loaded dataframe
                skimmer = Skimmer(cfg_plot, self.version, self.sample, threshold, region)
                skimmer.create_hists()
                # Plot
                plotter = EfficiencyPlotter(plot_name, cfg_plot, skimmer)
                plotter.plot()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cfg_plots",
        "-c",
        default="cfg_plots.yaml",
        help="Path of YAML file specifying the desired plots."
    )
    args = parser.parse_args()

    plotter = PlottingCentral(args.cfg_plots)
    plotter.run()


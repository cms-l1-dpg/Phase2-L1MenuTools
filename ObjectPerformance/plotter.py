#!/eos/user/d/dhundhau/miniconda3/envs/l1phase2/bin/python
import argparse
import glob
from itertools import product
import json
import time

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import pandas as pd
import uproot
import yaml

from ntuple_loader import NTupleLoader


plt.style.use(hep.style.CMS)


class Skimmer():
    
    def __init__(self, config, version, sample, threshold, region):
        self.config = config
        self.version = version
        self.sample = sample
        self.threshold = threshold
        self.region = region
        self.bin_width = config["binning"]["step"]
        self.bins = np.array([i * self.bin_width for i in range(int(config["binning"]["max"] / self.bin_width) + 1)])
        self.df = None
        self.hists = {}

    def _load_dfs_from_h5(self):
        """ Load dfs from h5 file with hased name of sample+config """
        fname = self.version + '_' + self.sample
        self.df = pd.read_hdf(f"tmp/{fname}.h5", key="l1")

    def _get_gen_df(self):
        col = self.config["inputs"]["reference_key"]
        sel_reg = self.df["genJetEta"] < 999
        if self.region == "barrel":
            sel_reg = self.df["genJetEta"] < 2.4
        df_gen = self.df[col]  # [sel_reg]
        return df_gen

    def _get_reco_df(self, obj_key):
        thr_sel = (self.df[obj_key] > self.threshold)
        eta_sel = self.df[obj_key.replace("Pt", "Eta")] < 999
        if self.region == "barrel":
            eta_sel = self.df[obj_key.replace("Pt", "Eta")] < 2.4
        sel = thr_sel & eta_sel
        return self.df.loc[sel, self.config["inputs"]["reference_key"]]

    def _skim_to_hists(self):
        df_gen = self._get_gen_df()
        self.hists["all"] = plt.hist(df_gen, bins=self.bins, log=True)

        # select threshold
        for obj_key in self.config["inputs"]["object_keys_labels"]:
            df_reco = self._get_reco_df(obj_key)
            self.hists[obj_key] = plt.hist(
                df_reco,
                bins=self.bins,
                log=True
            )

    def create_hists(self):
        self._load_dfs_from_h5()
        self._skim_to_hists()


class EfficiencyPlotter():

    def __init__(self, name, config, skimmer):
        self.plot_name = name
        self.config = config
        self.skimmer = skimmer

    def plot(self):
        print("Plotting ...")
        fig, ax = plt.subplots(figsize = (10,10))
        hep.cms.label(ax=ax, llabel="Phase-2 Simulation", com=14)
        gen_hist_all = self.skimmer.hists["all"]
        xbins = self.skimmer.bins[:-1] + self.skimmer.bin_width / 2

        xerr = np.ones_like(gen_hist_all[0]) * self.skimmer.bin_width / 2
        err_kwargs = {"xerr": xerr, "capsize": 3, "marker": 'o', "markersize": 8}
        for obj_key, gen_hist_trig in self.skimmer.hists.items():
            if obj_key== "all":
                continue
            label = self.config["inputs"]["object_keys_labels"][obj_key]
            efficiency = gen_hist_trig[0] / gen_hist_all[0]
            yerr = np.sqrt(gen_hist_all[0])  * gen_hist_trig[0] / gen_hist_all[0] ** 2
            yerr = np.stack([yerr, np.minimum(1 - efficiency, yerr)])
            ax.errorbar(xbins, efficiency, yerr=yerr, label=label, **err_kwargs)

        ax.axvline(self.skimmer.threshold, ls = ":", c = "k")
        ax.axhline(1, ls = ":", c = "k")
        ax.legend(loc="lower right", frameon=False)
        ax.set_xlabel(self.config["xlabel"])
        ylabel = self.config["ylabel"].replace("<threshold>", str(self.skimmer.threshold))
        ylabel = ylabel.replace("<region>", f", {self.skimmer.region}")
        ax.set_ylabel(ylabel)
        ax.set_xlim(self.config["binning"]["min"], self.config["binning"]["max"])
        ax.set_ylim(0, 1.1)
        ax.tick_params(direction="in")
        plt.savefig(f"plot_output/{self.plot_name}_{self.skimmer.threshold}.png")
        plt.savefig(f"/eos/user/d/dhundhau/www/L1_PhaseII/python_plots/{self.plot_name}_{self.skimmer.threshold}.png")
        plt.close()


class PlottingCentral():
    
    def __init__(self, cfg_plots_path):
        with open("config.yaml", 'r') as f:
            self.cfg = yaml.safe_load(f)
        with open(cfg_plots_path, 'r') as f:
            self.cfg_plots = yaml.safe_load(f)
        self.version = self.cfg_plots["global"]["version"]
        self.sample = self.cfg_plots["global"]["sample"]

    def _load_ntuples(self):
        loader = NTupleLoader(self.version, self.sample)
        loader.load()

    def run(self):
        for plot, cfg_plot in self.cfg_plots["plots"].items():
            self._load_ntuples()
            for region, threshold in product(cfg_plot["regions"], cfg_plot["thresholds"]):
                print(f">>> {plot} ({threshold} GeV {region}) <<<")
                # Skim loaded dataframe
                skimmer = Skimmer(cfg_plot, self.version, self.sample, threshold, region)
                skimmer.create_hists()
                # Plot
                plotter = EfficiencyPlotter(plot, cfg_plot, skimmer)
                plotter.plot()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("cfg_plots_path", help="Path of YAML file specifying the desired plots.")
    args = parser.parse_args()

    plotter = PlottingCentral(args.cfg_plots_path)
    plotter.run()


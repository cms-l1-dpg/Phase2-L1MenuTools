#!/eos/user/d/dhundhau/miniconda3/envs/l1phase2/bin/python
#/eos/user/d/dhundhau/miniconda3/bin/python
import glob
import json
import time

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import pandas as pd
import uproot
import yaml


plt.style.use(hep.style.CMS)


class NTupleLoader():
    
    def __init__(self, ntuple_path, config):
        self.ntuple_path = ntuple_path
        self.config = config
        self.df = None
    
    def _load_ntuples_into_df(self):
        fnames = glob.glob(self.ntuple_path + "L1NtuplePhaseII_Step1_*.root")[:]
        print(f"Loading objects from {len(fnames)} files...")
        gen_tree = "genTree/L1GenTree"
        reco_tree = "l1PhaseIITree/L1PhaseIITree"
        df = None

        t0 = time.time()
        for f_in in fnames:
            with uproot.open(f_in) as f:
                df_gen = f[gen_tree].arrays(
                    self.config["inputs"]["truth_key"],
                    library="pd"
                )
                if "jetPt" in (x := self.config["inputs"]["truth_key"]):
                    df_gen.loc[df_gen[x] < 30, x] = 0
                    df_gen = df_gen.groupby(level=0).sum()
                df_reco = f[reco_tree].arrays(
                    self.config["inputs"]["object_keys_labels"].keys(),
                    library="pd"
                )
            df_merged = pd.concat([df_gen, df_reco], axis=1)
            df = pd.concat([df, df_merged], axis=0)
        t1 = time.time()
        print(f"Loading of {len(fnames)} files took {round(t1 - t0, 1)}s")
        return df

    def _add_missing_columns(self):
        print("Required columns not cached. Loading ...")
        df = self._load_ntuples_into_df()
        duplicate_cols = list(set(df.columns) - set(self.df.columns))
        df.drop(duplicate_cols, axis=1)
        self.df = pd.concat([self.df, df], axis=1)
        print(self.df.columns)

    def _get_h5_fname(self):
        version = self.config["inputs"]["version"]
        sample = self.config["inputs"]["sample"]
        return version + '_' + sample

    def _save_df(self):
        self.df.to_hdf(f"tmp/{self._get_h5_fname()}.h5", key="l1")

    def _cache_has_columns(self):
        """
        Checks if the required columns
        are present in the cached h5 file.
        """
        required_keys = [self.config["inputs"]["truth_key"]]
        required_keys += list(self.config["inputs"]["object_keys_labels"].keys())
        return all([x in self.df.columns for x in required_keys])

    def _cache_file_exists(self):
        """
        Checks if there is h5 file in tmp
        with the name 'version_sample.h5'
        """
        try:
            self.df = pd.read_hdf(f"tmp/{self._get_h5_fname()}.h5", key="l1")
            return True
        except FileNotFoundError:
            return False

    def load(self):
        if not self._cache_file_exists():
            print("Cache file does not exist.")
            self.df = self._load_ntuples_into_df()
            self._save_df()
        if not self._cache_has_columns():
            print("Cache file does not have required columns")
            self._add_missing_columns()
            self._save_df()


class Skimmer():
    
    def __init__(self, config):
        self.config = config
        self.threshold = config["threshold"]
        self.bin_width = config["binning"]["step"]
        self.bins = np.array([i * self.bin_width for i in range(int(config["binning"]["max"] / self.bin_width) + 1)])
        self.df = None
        self.hists = {}

    def _load_dfs_from_h5(self):
        """ Load dfs from h5 file with hased name of sample+config """
        version = self.config["inputs"]["version"]
        sample = self.config["inputs"]["sample"]
        fname = version + '_' + sample
        self.df = pd.read_hdf(f"tmp/{fname}.h5", key="l1")

    def _skim_to_hists(self):
        self.hists["all"] = plt.hist(self.df[self.config["inputs"]["truth_key"]], bins=self.bins, log=True)

        # select threshold
        for obj_key in self.config["inputs"]["object_keys_labels"]:
            trig_sel = self.df[obj_key] > self.threshold
            self.hists[obj_key] = plt.hist(
                self.df.loc[trig_sel,
                self.config["inputs"]["truth_key"]],
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
        ax.set_ylabel(self.config["ylabel"])
        ax.set_xlim(self.config["binning"]["min"], self.config["binning"]["max"])
        ax.set_ylim(0, 1.1)
        ax.tick_params(direction="in")
        plt.savefig(f"plot_output/{self.plot_name}.png")
        plt.savefig(f"/eos/user/d/dhundhau/www/L1_PhaseII/python_plots/{self.plot_name}.png")
        plt.close()


class PlottingCentral():
    
    def __init__(self):
        self.conf = None
        self.plot_conf = None
        self._load_configs()

    def _load_configs(self):
        with open("config.yaml", 'r') as f:
            self.conf = yaml.safe_load(f)
        with open("plotting_config.yaml", 'r') as f:
            self.plot_conf = yaml.safe_load(f)

    def run(self):
        for plot, pconfig in self.plot_conf.items():
            print(f">>> {plot} <<<")
            # Get Config
            version = pconfig["inputs"]["version"]
            sample = pconfig["inputs"]["sample"]
            fpath = self.conf[version][sample]
            # Load L1 NTuple (if not cached)
            loader = NTupleLoader(fpath, pconfig)
            loader.load()
            # Skim loaded dataframe
            skimmer = Skimmer(pconfig)
            skimmer.create_hists()
            # Plot
            plotter = EfficiencyPlotter(plot, pconfig, skimmer)
            plotter.plot()


if __name__ == "__main__":
    plotter = PlottingCentral()
    plotter.run()


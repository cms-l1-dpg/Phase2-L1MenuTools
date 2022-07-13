#!/eos/user/d/dhundhau/miniconda3/envs/l1phase2/bin/python
#/eos/user/d/dhundhau/miniconda3/bin/python
import glob
import hashlib
import json

import matplotlib.pyplot as plt
import numpy as np
import uproot
import yaml


class NTupleSkimmer():
    
    def __init__(self, indir, config, skim_type="MET"):
        self.indir = indir
        self.config = config
        self.threshold = config["threshold"]
        self.skim_type = skim_type
        self.bin_width = config["binning"]["step"]
        self.bins = np.array([i * self.bin_width for i in range(int(config["binning"]["max"] / self.bin_width) + 1)])
        self.df_gen = None
        self.df_reco = None
        self.fhash = None
        self.gen_hists = {}

    def _set_hashname(self):
        h = hashlib.blake2s()
        h.update(str.encode(self.indir))
        h.update(str.encode(json.dumps(self.config)))
        self.fhash = h.hexdigest()

    def _load_ntuples_into_df(self):
        # gen
        print("Loading GEN objects ...")
        fnames = glob.glob(self.indir + "L1NtuplePhaseII_Step1_*.root")
        gen_files = {fname:"genTree/L1GenTree" for fname in fnames}
        self.df_gen = uproot.concatenate(
            gen_files,
            library="pd",
            filter_name=self.config["truth_key"]
        )

        # reco
        reco_filter_name = "/(" + '|'.join(self.config["object_keys"]) + ')/'
        print(f"Loading RECO objects with filter {reco_filter_name}...")
        reco_files = {fname: "l1PhaseIITree/L1PhaseIITree" for fname in fnames}
        self.df_reco = uproot.concatenate(
            reco_files,
            library="pd",
            filter_name=reco_filter_name
        )

    def _load_dfs_from_h5(self):
        """ TODO: Load dfs from h5 file with hased name of sample+config """
        pass  

    def _skim_data(self):
        self.gen_hists["all"] = plt.hist(self.df_gen[self.config["truth_key"]], bins=self.bins, log=True)

        # select threshold
        for obj_key in self.config["object_keys"]:
            trig_sel = self.df_reco[obj_key] > self.threshold
            self.gen_hists[obj_key] = plt.hist(
                self.df_gen.loc[trig_sel,
                self.config["truth_key"]],
                bins=self.bins,
                log=True
            )

    def _save_skimmed_dfs(self):
        self.df_reco.to_hdf(f"tmp/{self.fhash}_reco.h5", key="reco")
        self.df_gen.to_hdf(f"tmp/{self.fhash}_gen.h5", key="gen")

    def _is_cached(self):
        """ Should check if there are h5 files in tmp
        with the hash of this NTuple. """
        return False

    def load_skim_save(self, overwrite=True):
        self._set_hashname()
        if overwrite or not self._is_cached():
            self._load_ntuples_into_df()
            self._save_skimmed_dfs()
        else:
            self._load_dfs_from_h5()
        self._skim_data()


class EfficiencyPlotter():

    def __init__(self, name, config, skimmer):
        print("Initialising Plotter")
        self.plot_name = name
        self.config = config
        self.skimmer = skimmer

    def plot(self):
        fig, ax = plt.subplots(figsize = (10,10))
        gen_hist_all = self.skimmer.gen_hists["all"]
        xbins = self.skimmer.bins[:-1] + self.skimmer.bin_width / 2

        err_kwargs = {"capsize": 3, "marker": 'o', "markersize": 8}
        for label, gen_hist_trig in self.skimmer.gen_hists.items():
            if label == "all":
                continue
            ax.errorbar(xbins, gen_hist_trig[0] / gen_hist_all[0], label=label, **err_kwargs)

        ax.axvline(self.skimmer.threshold, ls = ":", c = "k")
        ax.axhline(1, ls = ":", c = "k")
        ax.legend(frameon=False)
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
            print(f"Working on {plot} ...")
            # Get Config
            version = pconfig["inputs"]["version"]
            sample = pconfig["inputs"]["sample"]
            fpath = self.conf[version][sample]
            # Process L1 NTuple
            skimmer = NTupleSkimmer(fpath, pconfig)
            skimmer.load_skim_save()
            # Plot
            plotter = EfficiencyPlotter(plot, pconfig, skimmer)
            plotter.plot()


if __name__ == "__main__":
    print("Starting up!")
    plotter = PlottingCentral()
    plotter.run()


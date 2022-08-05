#!/afs/cern.ch/user/d/dhundhau/public/miniconda3/envs/py310/bin/python
import argparse
from datetime import datetime
import glob
from itertools import product
import json
import sys
import time
import warnings

import awkward as ak
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
from scipy.stats import beta
import vector
import yaml

from plot_config import PlotConfig
import utils


vector.register_awkward()
plt.style.use(hep.style.CMS)


class EfficiencyHist():
    """
    Efficiency hist corresponds to one curve in
    a turn-on plot, i.e. on combination of test
    and reference object, at a certain threshold.
    """

    def __init__(self):
        self.threshold = None
        self.version = None
        self.hist_ref = None
        self.hist_test = None


class Skimmer():

    def __init__(self, cfg_plot, threshold):
        self.cfg_plot = PlotConfig(cfg_plot)
        self.threshold = threshold
        self.bin_width = cfg_plot["binning"]["step"]
        self.default_version = cfg_plot["default_version"]
        self.bins = np.array([i * self.bin_width for i in range(int(cfg_plot["binning"]["max"] / self.bin_width) + 1)])
        self.ak_arrays = {}
        self.hists = {}

    def _load_branches_from_parquet(self):
        """
        Load ak arrays from parquet files.
        """
        sample = self.cfg_plot.sample

        # Load reference object
        ref_obj = self.cfg_plot.reference_object
        version_ref = self.cfg_plot.version_ref_object
        ref_array = ak.from_parquet(f"tmp/{version_ref}_{sample}_{ref_obj}.parquet")
        ref_array = ak.zip({
            key.removeprefix(ref_obj).lower(): ref_array[key]
            for key in ref_array.fields
        })
        self.ak_arrays["ref"] = ak.with_name(ref_array, "Momentum4D")
        print(self.ak_arrays["ref"])

        # Load test objects
        for test_obj in self.cfg_plot.test_objects:
            version = self.cfg_plot.get_test_object_version(test_obj)
            ak_arr = ak.from_parquet(f"tmp/{version}_{sample}_{test_obj}.parquet")
            ak_arr = ak.zip({
                key.removeprefix(test_obj).lower(): ak_arr[key]
                for key in ak_arr.fields
            })
            self.ak_arrays[test_obj] = ak.with_name(ak_arr, "Momentum4D")

    def _match_test_to_ref(self):
        """
        Method for deltaR matching of test objects
        to reference objects.
        """
        for test_obj, obj_cfg in self.cfg_plot.test_objects.items():
            suffix = obj_cfg["suffix"].lower()
            ref_test = ak.cartesian(
                {"ref": self.ak_arrays["ref"],
                 "test": self.ak_arrays[test_obj],
                },
                nested=True
            )
            js, gs = ak.unzip(ref_test)
            dR = gs.deltaR(js)

            self.ak_arrays["ref"]["dR_value_" + test_obj] = ak.min(dR, axis = -1)
            best_dR = ak.argmin(dR, axis=-1, keepdims=True)
            self.ak_arrays["ref"]["dR_matched_" + test_obj] = ref_test[best_dR]["test"][suffix][:,:,0]

            # TODO: Implement dR matching with pT sorting
            # add dR as property of ref arrays
            # pass_dR = dR < self.cfg_plot.match_dR
            # pass_dR_lowest_pT = ak.argmin(ref_test["test"][suffix][pass_dR], axis=-1, keepdims=True)
            # self.ak_arrays["ref"]["dR_value_" + test_obj] = dR[pass_dR_lowest_pT]
            # store field (pt, ...) of dr matched object
            # self.ak_arrays["ref"]["dR_matched_" + test_obj] = ref_test[pass_dR_lowest_pT]["test"][suffix][:,:,0]

    def _flatten_array(self, ak_array):
        """
        Returns a flattend array if the ak array is nested.
        If the ak array is already flat, the function returns
        the original array.
        """
        try:
            return ak.flatten(ak_array)
        except ValueError:
            return ak_array

    def _apply_reference_trafo(self):
        """
        Transforms the reference branch, e.g.
        by summing over jetPt to get the HT
        reference object.
        """
        if not (trafo := self.cfg_plot.reference_trafo):
            return

        if trafo == "HT":
            self.ak_arrays["ref"]["pt"] = ak.sum(
                self.ak_arrays["ref"]["pt"],
                axis=-1
            )

        if trafo == "MHT":
            # TODO: To be implemented
            pass

    def _apply_reference_cuts(self):
        """
        Applies configured cuts on reference objects.
        Should be applied before any matching.
        """
        if not self.cfg_plot.reference_cuts:
            return
        
        for branch, cut_cfg in self.cfg_plot.reference_cuts.items():
            op = utils.str_to_op(cut_cfg["operator"])
            threshold = cut_cfg["threshold"]
            sel = op(abs(self.ak_arrays["ref"][branch]), threshold)
            self.ak_arrays["ref"] = self.ak_arrays["ref"][sel]

    def _apply_test_obj_cuts(self):
        """
        Applies configured cuts on all configured
        test objects.
        Should be applied before any matching.
        """
        for test_obj in self.cfg_plot.test_objects:
            cuts = self.cfg_plot.get_object_cuts(test_obj)
            if not cuts:
                continue
            for branch, cut_cfg in cuts.items():
                op = utils.str_to_op(cut_cfg["operator"])
                threshold = cut_cfg["threshold"]
                sel = op(abs(self.ak_arrays[test_obj][branch]), threshold)
                self.ak_arrays[test_obj] = self.ak_arrays[test_obj][sel]

    def _skim_to_hists(self):
        ref_field = self.cfg_plot.reference_field
        for test_obj, cfg in self.cfg_plot.test_objects.items():
            field = cfg["suffix"].lower()
            sel = self.ak_arrays[test_obj][field] > self.threshold
            ak_array = self._flatten_array(self.ak_arrays["ref"][sel][ref_field])
            self.hists[test_obj] = np.histogram(ak_array, bins=self.bins)

        self.hists["ref"] = np.histogram(
            self._flatten_array(self.ak_arrays["ref"][ref_field]),
            bins=self.bins
        )

    def _skim_to_hists_dR_matched(self):
        ref_field = self.cfg_plot.reference_field
        for test_obj, cfg in self.cfg_plot.test_objects.items():
            sel_threshold = self.ak_arrays["ref"]["dR_matched_" + test_obj] > self.threshold
            sel_dR = self.ak_arrays["ref"]["dR_value_" + test_obj] < self.cfg_plot.match_dR
            sel = sel_threshold & sel_dR

            ak_array = self.ak_arrays["ref"][sel]
            ak_array = self._flatten_array(ak_array[ref_field])
            self.hists[test_obj] = np.histogram(
                ak.to_numpy(ak_array, allow_missing=True),
                bins=self.bins
            )

        ref_flat_np = ak.to_numpy(
            self._flatten_array(
              self.ak_arrays["ref"][ref_field]
            )
        )
        self.hists["ref"] = np.histogram(
            ref_flat_np,
            bins=self.bins
        )

    def create_hists(self):
        self._load_branches_from_parquet()
        self._apply_reference_cuts()
        self._apply_reference_trafo()
        self._apply_test_obj_cuts()
        if not self.cfg_plot.match_dR:
            self._skim_to_hists()
        else:
            self._match_test_to_ref()
            self._skim_to_hists_dR_matched()


class EfficiencyPlotter():

    def __init__(self, name, cfg, skimmer):
        self.plot_name = name
        self.cfg = cfg
        self.skimmer = skimmer

    def _compute_efficiency(self, test_vals, ref_vals):
        eff = np.nan_to_num(test_vals / ref_vals, posinf=0)
        # assert all(0 <= i <= 1 for i in eff)
        return eff

    def _plot_efficiency_curve(self):
        """
        Efficiency / turn-on plots.
        """
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
                efficiency = self._compute_efficiency(gen_hist_trig[0], gen_hist_ref[0])
            yerr = utils.clopper_pearson_err(gen_hist_trig[0], gen_hist_ref[0])
            label = self.cfg["test_objects"][obj_key]["label"]
            ax.errorbar(xbins, efficiency, yerr=yerr, label=label, **err_kwargs)

        ax.axvline(self.skimmer.threshold, ls = ":", c = "k")
        ax.axhline(1, ls = ":", c = "k")
        ax.legend(loc="lower right", frameon=False)
        ax.set_xlabel(self.cfg["xlabel"])
        ax.set_xlabel(self.cfg["xlabel"] + datetime.now().strftime("%H:%M:%S"))
        ylabel = self.cfg["ylabel"].replace("<threshold>", str(self.skimmer.threshold))
        ax.set_ylabel(ylabel)
        ax.set_xlim(self.cfg["binning"]["min"], self.cfg["binning"]["max"])
        ax.set_ylim(0, 1.1)
        ax.tick_params(direction="in")
        fig.tight_layout()
        plt.savefig(f"plot_output/{self.plot_name}_{self.skimmer.threshold}.png")
        plt.savefig(f"/eos/user/d/dhundhau/www/L1_PhaseII/python_plots/{self.plot_name}_{self.skimmer.threshold}.png")
        plt.close()

    def _plot_raw_counts(self):
        """
        Raw counts of objects in bins
        of the efficiency plots.
        """
        fig, ax = plt.subplots(figsize = (10,10))
        hep.cms.label(ax=ax, llabel="Phase-2 Simulation", com=14)
        gen_hist_ref = self.skimmer.hists["ref"]
        xbins = self.skimmer.bins[:-1] + self.skimmer.bin_width / 2

        xerr = np.ones_like(gen_hist_ref[0]) * self.skimmer.bin_width / 2
        err_kwargs = {"xerr": xerr, "capsize": 3, "marker": 'o', "markersize": 8}

        for obj_key, gen_hist_trig in self.skimmer.hists.items():
            if obj_key== "ref":
                continue
            yerr = np.sqrt(gen_hist_trig[0])
            label = self.cfg["test_objects"][obj_key]["label"]
            ax.errorbar(xbins, gen_hist_trig[0], yerr=yerr, label=label, **err_kwargs)

        ax.axvline(self.skimmer.threshold, ls = ":", c = "k")
        ax.legend(loc="upper right", frameon=False)
        ax.set_xlabel(self.cfg["xlabel"])
        ax.set_xlabel(self.cfg["xlabel"] + datetime.now().strftime("%H:%M:%S"))
        ylabel = self.cfg["ylabel"].replace("<threshold>", str(self.skimmer.threshold))
        ax.set_ylabel(ylabel)
        ax.set_xlim(self.cfg["binning"]["min"], self.cfg["binning"]["max"])
        ax.tick_params(direction="in")
        fig.tight_layout()
        plt.savefig(f"plot_output/{self.plot_name}_{self.skimmer.threshold}.png")
        plt.savefig(f"/eos/user/d/dhundhau/www/L1_PhaseII/python_plots/raw_{self.plot_name}_{self.skimmer.threshold}.png")
        plt.close()

    def plot(self):
        print("Plotting ...")
        self._plot_efficiency_curve()
        self._plot_raw_counts()


class PlottingCentral():

    def __init__(self, cfg_plots_path):
        with open(cfg_plots_path, 'r') as f:
            self.cfg_plots = yaml.safe_load(f)

    def run(self):
        for plot_name, cfg_plot in self.cfg_plots.items():
            for threshold in cfg_plot["thresholds"]:
                print(f">>> {plot_name} ({threshold} GeV) <<<")
                skimmer = Skimmer(cfg_plot, threshold)
                skimmer.create_hists()

                plotter = EfficiencyPlotter(plot_name, cfg_plot, skimmer)
                plotter.plot()


class ScalingCentral(PlottingCentral):

    def __init__(self, cfg_plots_path):
        super().__init__(cfg_plots_path)
        with open("./cfg_scalings.yaml", 'r') as f:
            self.cfg_scalings = yaml.safe_load(f)

    def _get_scaling_thresholds(self, cfg):
        # TODO: Implement (sample, object) -> scaling threshold list mapping
        pass

    def run(self):
        for plot_name, cfg_plot in self.cfg_plots.items():
            for threshold in self._get_scaling_thresholds(cfg_plot):
                print(f">>> {plot_name} ({threshold} GeV) <<<")
                skimmer = Skimmer(cfg_plot, threshold)
                skimmer.create_hists()

                scalingClass = ScalingFitter(skimmer)
                sclaingClass.fit()

                plotter = ScalingsPlotter(scalingClass)
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

    # scalings = ScalingCentral()
    # scalings.run()


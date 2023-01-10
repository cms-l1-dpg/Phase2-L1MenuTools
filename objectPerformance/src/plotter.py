#!/afs/cern.ch/user/d/dhundhau/public/miniconda3/envs/py310/bin/python
import argparse
import os

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
from progress.bar import IncrementalBar
import yaml
import json

from turnon_collection import TurnOnCollection
from scaling_collection import ScalingCollection
import utils


plt.style.use(hep.style.CMS)


class Plotter():

    def _make_output_dirs(self, version: str):
        os.makedirs(f"outputs/{version}/turnons", exist_ok=True)
        os.makedirs(f"outputs/{version}/distributions", exist_ok=True)
        os.makedirs(f"outputs/{version}/scalings", exist_ok=True)

    def _create_new_plot(self):
        fig, ax = plt.subplots(figsize=(10, 10))
        hep.cms.label(ax=ax, llabel="Phase-2 Simulation", com=14)
        return fig, ax


class EfficiencyPlotter(Plotter):

    def __init__(self, name, cfg, turnon_collection):
        self.plot_name = name
        self.cfg = cfg
        self.turnon_collection = turnon_collection
        self.version = self.turnon_collection.version
        self.bin_width = turnon_collection.cfg_plot.bin_width

    def _style_plot(self, fig, ax, legend_loc="lower right"):
        ax.axvline(self.turnon_collection.threshold, ls=":", c="k")
        ax.axhline(1, ls=":", c="k")
        ax.legend(loc=legend_loc, frameon=False)
        ax.set_xlabel(rf"{self.cfg['xlabel']}")
        ylabel = self.cfg["ylabel"].replace(
            "<threshold>",
            str(self.turnon_collection.threshold)
        )
        ax.set_ylabel(rf"{ylabel}")
        ax.set_xlim(self.cfg["binning"]["min"], self.cfg["binning"]["max"])
        ax.set_ylim(0.0, 1)
        ax.tick_params(direction="in")
        watermark = f"{self.version}_{self.plot_name}_"\
                    f"{self.turnon_collection.threshold}"
        ax.text(0, -0.1, watermark,
                color="grey", alpha=0.2,
                fontsize=20,
                transform=ax.transAxes)
        fig.tight_layout()

    def _save_json(self, file_name):
        plot = {}

        xlabel = self.cfg["xlabel"]
        ylabel = self.cfg["ylabel"].replace(
            "<threshold>",
            str(self.turnon_collection.threshold)
        )
        watermark = f"{self.version}_{self.plot_name}_"\
                    f"{self.turnon_collection.threshold}"

        plot["xlabel"] = xlabel
        plot["ylabel"] = ylabel
        plot["watermark"] = watermark

        xbins = self.turnon_collection.bins
        xbins = 0.5 * (xbins[1:] + xbins[:-1])

        for obj_key, gen_hist_trig in self.turnon_collection.hists.items():
            if obj_key == "ref":
                continue

            _object = {}

            if "Iso" in self.cfg["xlabel"]:
                efficiency = self._get_iso_vs_eff_hist(gen_hist_trig[0])
                efficiency = efficiency.tolist()
                yerr = np.zeros(len(efficiency))
                xerr = yerr.tolist()
            else:
                eff, yerr = self.turnon_collection.get_efficiency(obj_key)
                efficiency = eff.tolist()
                xerr = self.turnon_collection.xerr(obj_key).tolist()

            label = self.cfg["test_objects"][obj_key]["label"]

            err_kwargs = {"xerr": xerr,
                          "capsize": 3, "marker": 'o', "markersize": 8}

            _object["label"] = label
            _object["efficiency"] = efficiency
            _object["efficiency_err"] = yerr.tolist()
            _object["xbins"] = xbins.tolist()
            _object["err_kwargs"] = err_kwargs

            plot[obj_key] = _object

        with open(f"{file_name}", "w") as outfile:
            outfile.write(json.dumps(plot, indent=4))

    def _get_iso_vs_eff_hist(self, test_hist):
        """
        Cumulative ratio of efficiency vs L1 Iso histogram.
        """

        l1_isolation_histogram = sum(test_hist)
        l1_cumulative_sum = np.cumsum(test_hist) / l1_isolation_histogram

        return l1_cumulative_sum

    @utils.ignore_warnings
    def _plot_efficiency_curve(self):
        """
        Efficiency / turn-on plots.
        """
        fig, ax = self._create_new_plot()
        xbins = self.turnon_collection.bins
        xbins = 0.5 * (xbins[1:] + xbins[:-1])

        for obj_key, gen_hist_trig in self.turnon_collection.hists.items():
            if obj_key == "ref":
                continue
            efficiency, yerr = self.turnon_collection.get_efficiency(obj_key)

            label = self.cfg["test_objects"][obj_key]["label"]

            err_kwargs = {"xerr": self.turnon_collection.xerr(obj_key),
                          "capsize": 3, "marker": 'o', "markersize": 8}
            ax.errorbar(xbins, efficiency, yerr=yerr, label=label,
                        **err_kwargs)

        self._style_plot(fig, ax)
        ax.set_ylim(0, 1.1)
        plt.savefig(f"outputs/{self.version}/turnons/{self.plot_name}_"
                    f"{self.turnon_collection.threshold}.png")
        self._save_json(f"outputs/{self.version}/turnons/{self.plot_name}_"
                        f"{self.turnon_collection.threshold}.json")
        plt.close()

    @utils.ignore_warnings
    def _plot_iso_vs_efficiency_curve(self):
        """
        Efficiency vs L1 Iso plots.
        """
        fig, ax = self._create_new_plot()
        xbins = self.turnon_collection.bins
        xbins = 0.5 * (xbins[1:] + xbins[:-1])

        for obj_key, gen_hist_trig in self.turnon_collection.hists.items():
            if obj_key == "ref":
                continue
            iso_vs_eff_hist = self._get_iso_vs_eff_hist(gen_hist_trig[0])

            # yerr = np.sqrt(iso_vs_eff_hist) # TODO: Possibly introduce errors
            label = self.cfg["test_objects"][obj_key]["label"]
            err_kwargs = {"capsize": 3, "marker": 'o', "markersize": 8}
            ax.errorbar(xbins, iso_vs_eff_hist, label=label, **err_kwargs)

        self._style_plot(fig, ax)
        plt.savefig(f"outputs/{self.version}/turnons/{self.plot_name}_"
                    f"{self.turnon_collection.threshold}.png")
        self._save_json(f"outputs/{self.version}/turnons/{self.plot_name}_"
                        f"{self.turnon_collection.threshold}.json")
        plt.close()

    def _plot_raw_counts(self):
        """
        Raw counts of objects in bins
        of the efficiency plots.
        """
        fig, ax = self._create_new_plot()
        xbins = self.turnon_collection.bins
        xbins = 0.5 * (xbins[1:] + xbins[:-1])

        for obj_key, ref_hist in self.turnon_collection.hists["ref"].items():
            err_kwargs = {"xerr": self.turnon_collection.xerr(obj_key),
                          "capsize": 1, "marker": 'o', "markersize": 2,
                          "linestyle": "None"}

            ref_hist = ax.step(xbins, ref_hist[0], where="mid")
            label = self.cfg["reference_object"]["label"]

        for obj_key, gen_hist_trig in self.turnon_collection.hists.items():
            if obj_key == "ref":
                continue
            yerr = np.sqrt(gen_hist_trig[0])
            label = self.cfg["test_objects"][obj_key]["label"]
            test_hist = ax.step(xbins, gen_hist_trig[0], where="mid")
            ax.errorbar(xbins, gen_hist_trig[0], yerr=yerr, label=label,
                        color=test_hist[0].get_color(), **err_kwargs)

        self._style_plot(fig, ax)
        plt.savefig(f"outputs/{self.version}/distributions/{self.plot_name}"
                    f"_{self.turnon_collection.threshold}_dist.png")
        plt.close()

    def plot(self):
        self._make_output_dirs(self.version)
        if "Iso" in self.cfg["xlabel"]:
            self._plot_iso_vs_efficiency_curve()
        else:
            self._plot_efficiency_curve()
            self._plot_raw_counts()


class EfficiencyCentral():
    """
    Class that orchestrates the plotting of
    """

    def __init__(self, cfg_plots_path):
        with open(cfg_plots_path, 'r') as f:
            self.cfg_plots = yaml.safe_load(f)

    def get_thresholds(self, cfg_plot: dict):
        """
        Function that returns the threholds for which
        efficiency plots are to be produced. If the
        thresholds are given in the config, these
        values are returned in a list. If the
        threshold configuration is missing, a single
        threshold of -999 is returned.
        """
        try:
            return cfg_plot["thresholds"]
        except KeyError:
            return [-999]

    def run(self):
        """
        This function iterates over all plots defined
        in the configuration file, creates a turnon_collection
        for it and passes it to the EfficiencyPlotter for
        plotting.
        """
        for plot_name, cfg_plot in self.cfg_plots.items():
            for threshold in self.get_thresholds(cfg_plot):
                print(f">>> Turn On {plot_name} ({threshold} GeV) <<<")
                turnon_collection = TurnOnCollection(cfg_plot, threshold)
                turnon_collection.create_hists()

                plotter = EfficiencyPlotter(plot_name, cfg_plot,
                                            turnon_collection)
                plotter.plot()


class ScalingPlotter(Plotter):

    def __init__(self, plot_name: str, cfg_plot: dict, scalings: dict,
                 scaling_pct: float, version: str, params: dict):
        self.plot_name = plot_name
        self.cfg_plot = cfg_plot
        self.scalings = scalings
        self.params = params
        self.version = version
        self.scaling_pct = scaling_pct

    def _params_to_func_str(self, obj):
        a = round(self.params[obj][0], 3)
        b = round(self.params[obj][1], 3)
        pm = '+' if b > 0 else '-'
        return f"y = {a} x {pm} {abs(b)}"

    def _set_plot_ranges(self, ax):
        xmax = 0
        ymax = 0
        for points in self.scalings.values():
            x_points = np.array(list(points.keys()) + [xmax])
            y_points = np.array(list(points.values()) + [ymax])
            xmax = np.max(x_points)
            ymax = np.max(y_points)
        ax.set_xlim(0, xmax)
        ax.set_ylim(0, ymax)

    def save_json(self):
        file_name = f"outputs/{self.version}/scalings/{self.plot_name}.json"
        plot = {}

        watermark = f"{self.version}_{self.plot_name}"
        plot["watermark"] = watermark

        for obj, points in self.scalings.items():
            _object = {}
            x_points = list(points.keys())
            y_points = list(points.values())

            label = (self.cfg_plot["test_objects"][obj]["label"]
                     + ", "
                     + self._params_to_func_str(obj))

            _object["xvals"] = x_points
            _object["yvals"] = y_points
            _object["label"] = label

            plot[obj] = _object

        with open(f"{file_name}", "w") as outfile:
            outfile.write(json.dumps(plot, indent=4))

    def plot(self):
        self._make_output_dirs(self.version)

        fig, ax = self._create_new_plot()
        for obj, points in self.scalings.items():
            x_points = np.array(list(points.keys()))
            y_points = np.array(list(points.values()))
            pts = ax.plot(x_points, y_points, 'o')

            label = (self.cfg_plot["test_objects"][obj]["label"]
                     + ", "
                     + self._params_to_func_str(obj))
            a, b = self.params[obj]
            x = np.linspace(0, 2500, 20)
            y = utils.scaling_func(x, a, b)
            ax.plot(x, y, color=pts[0].get_color(), label=label)

        ax.legend(loc="lower right")
        ax.set_xlabel("Threshold")
        ax.set_ylabel(f"{int(self.scaling_pct*100)}% Location")
        watermark = f"{self.version}_{self.plot_name}"
        ax.text(0, -0.1, watermark,
                color="grey", alpha=0.2,
                fontsize=20,
                transform=ax.transAxes)
        self._set_plot_ranges(ax)
        fig.tight_layout()

        plt.savefig(f"outputs/{self.version}/scalings/{self.plot_name}.png")
        plt.close()


class ScalingCentral():

    def __init__(self, cfg_plots_path):
        with open(cfg_plots_path, 'r') as f:
            self.cfg_plots = yaml.safe_load(f)
        with open("./cfg_plots/scaling_thresholds.yaml", 'r') as f:
            self.scaling_thresholds = yaml.safe_load(f)

    def _get_scaling_thresholds(self, cfg_plot, test_obj):
        if test_obj in self.scaling_thresholds:
            return self.scaling_thresholds[test_obj]
        if any("Muon" in x for x in cfg_plot["test_objects"]):
            return self.scaling_thresholds["Muon"]
        if any("Elec" in x or "Photon" in x for x in cfg_plot["test_objects"]):
            return self.scaling_thresholds["EG"]
        if any("HT" in x or "MET" in x for x in cfg_plot["test_objects"]):
            return self.scaling_thresholds["HT"]
        if any("Tau" in x for x in cfg_plot["test_objects"]):
            return self.scaling_thresholds["Tau"]
        if any("Jet" in x for x in cfg_plot["test_objects"]):
            return self.scaling_thresholds["Jet"]
        raise RuntimeError(
            "Failed to find thresholds in cfg_scaling_thresholds!"
        )

    def _rate_config_function(self, name: str, a: float, b: float):
        pm = '+' if b > 0 else ''
        f_string = (f"function :: {name}Scaling :: "
                    f"args:=(offline); lambda:={a}*offline{pm}{b}")
        return f_string

    def _write_scalings_to_file(self,
                                plot_name: str,
                                version: str,
                                params: dict):
        with open(f"outputs/{version}/scalings/{plot_name}.txt", 'w+') as f:
            f.write('')

        with open(f"outputs/{version}/scalings/{plot_name}.txt", 'a') as f:
            for obj, obj_params in params.items():
                a, b = obj_params
                f.write(self._rate_config_function(obj, a, b) + "\n")

    def run(self):
        for plot_name, cfg_plot in self.cfg_plots.items():
            if "scalings" not in cfg_plot:
                continue
            print(f">>> Scalings {plot_name} <<<")

            scalings = {x: {} for x in cfg_plot["test_objects"]}

            for test_obj in cfg_plot["test_objects"]:
                scal = {test_obj: {}}
                thds = self._get_scaling_thresholds(cfg_plot, test_obj)
                bar = IncrementalBar("Progress", max=len(thds))
                for threshold in thds:
                    bar.next()
                    turnon_collection = TurnOnCollection(cfg_plot, threshold)
                    turnon_collection.create_hists()
                    scaling_pct = turnon_collection.cfg_plot.scaling_pct
                    method = turnon_collection.cfg_plot.scaling_method
                    scaling_collect = ScalingCollection(cfg_plot,
                                                        method,
                                                        scaling_pct)
                    version = turnon_collection.version
                    scal = scaling_collect._compute_scalings(turnon_collection,
                                                             test_obj,
                                                             scal,
                                                             scaling_pct,
                                                             method)
                bar.finish()
                scalings[test_obj] = scal[test_obj]

            params = scaling_collect._fit_linear_functions(scalings)
            if params:
                plotter = ScalingPlotter(plot_name, cfg_plot, scalings,
                                         scaling_pct, version, params)
                plotter.plot()
                plotter.save_json()
                self._write_scalings_to_file(plot_name, version, params)

            params = scaling_collect._fit_linear_functions(scalings)
            if params:
                plotter = ScalingPlotter(plot_name, cfg_plot, scalings,
                                         scaling_pct, version, params)
                plotter.plot()
                plotter.save_json()
                self._write_scalings_to_file(plot_name, version, params)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "cfg_plots",
        default="cfg_plots/muons.yaml",
        help="Path of YAML file specifying the desired plots."
    )
    args = parser.parse_args()

    plotter = EfficiencyCentral(args.cfg_plots)
    plotter.run()

    scalings = ScalingCentral(args.cfg_plots)
    scalings.run()


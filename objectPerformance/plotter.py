#!/Users/danielhundhausen/opt/miniconda3/envs/py310/bin/python
#!/afs/cern.ch/user/d/dhundhau/public/miniconda3/envs/py310/bin/python
import argparse
from datetime import datetime
import os
import warnings

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
from progress.bar import IncrementalBar
from scipy.optimize import curve_fit
import yaml

from turnon_collection import TurnOnCollection
import utils


plt.style.use(hep.style.CMS)


class Plotter():

    def _new_plot(self):
        fig, ax = plt.subplots(figsize=(10, 10))
        hep.cms.label(ax=ax, llabel="Phase-2 Simulation", com=14)
        return fig, ax


class EfficiencyPlotter(Plotter):

    def __init__(self, name, cfg, turnon_collection):
        os.makedirs("outputs/turnons", exist_ok=True)
        os.makedirs("outputs/distributions", exist_ok=True)
        self.plot_name = name
        self.cfg = cfg
        self.turnon_collection = turnon_collection
        self.bin_width = turnon_collection.cfg_plot.bin_width

    def _style_plot(self, fig, ax, legend_loc="lower right"):
        ax.axvline(self.turnon_collection.threshold, ls=":", c="k")
        ax.axhline(1, ls=":", c="k")
        ax.legend(loc=legend_loc, frameon=False)
        ax.set_xlabel(self.cfg["xlabel"])
        ax.set_xlabel(self.cfg["xlabel"] + datetime.now().strftime("%H:%M:%S"))
        ylabel = self.cfg["ylabel"].replace("<threshold>", str(self.turnon_collection.threshold))
        ax.set_ylabel(ylabel)
        ax.set_xlim(self.cfg["binning"]["min"], self.cfg["binning"]["max"])
        ax.tick_params(direction="in")
        fig.tight_layout()

    def _plot_efficiency_curve(self):
        """
        Efficiency / turn-on plots.
        """
        fig, ax = self._new_plot()
        xbins = self.turnon_collection.bins[:-1] + self.bin_width / 2

        err_kwargs = {"xerr": self.turnon_collection.xerr,
                      "capsize": 3, "marker": 'o', "markersize": 8}

        for obj_key, gen_hist_trig in self.turnon_collection.hists.items():
            if obj_key == "ref":
                continue
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                efficiency, yerr = self.turnon_collection.get_efficiency(obj_key)

            label = self.cfg["test_objects"][obj_key]["label"]
            ax.errorbar(xbins, efficiency, yerr=yerr, label=label,
                        **err_kwargs)

        self._style_plot(fig, ax)
        ax.set_ylim(0, 1.1)
        plt.savefig(f"outputs/turnons/{self.plot_name}_{self.turnon_collection.threshold}.png")
        # plt.savefig(f"/eos/user/d/dhundhau/www/L1_PhaseII/python_plots/{self.plot_name}_{self.turnon_collection.threshold}.png")

    def _plot_raw_counts(self):
        """
        Raw counts of objects in bins
        of the efficiency plots.
        """
        fig, ax = self._new_plot()
        gen_hist_ref = self.turnon_collection.hists["ref"]
        xbins = self.turnon_collection.bins[:-1] + self.bin_width / 2

        err_kwargs = {"xerr": self.turnon_collection.xerr, "capsize": 1, "marker": 'o',
                      "markersize": 2, "linestyle": "None"}

        ref_hist = ax.step(xbins, gen_hist_ref[0], where="mid")
        label = self.cfg["reference_object"]["label"]
        ax.errorbar(xbins, gen_hist_ref[0], yerr=np.sqrt(gen_hist_ref[0]),
                    label=label, color=ref_hist[0].get_color(), **err_kwargs)

        for obj_key, gen_hist_trig in self.turnon_collection.hists.items():
            if obj_key == "ref":
                continue
            yerr = np.sqrt(gen_hist_trig[0])
            label = self.cfg["test_objects"][obj_key]["label"]
            test_hist = ax.step(xbins, gen_hist_trig[0], where="mid")
            ax.errorbar(xbins, gen_hist_trig[0], yerr=yerr, label=label,
                        color=test_hist[0].get_color(), **err_kwargs)

        self._style_plot(fig, ax)
        plt.savefig(f"outputs/distributions/{self.plot_name}"
                    f"_{self.turnon_collection.threshold}_dist.png")
        # plt.savefig(f"/eos/user/d/dhundhau/www/L1_PhaseII/python_plots/raw_{self.plot_name}_{threshold}.png")

    def plot(self):
        self._plot_efficiency_curve()
        self._plot_raw_counts()


class PlottingCentral():

    def __init__(self, cfg_plots_path):
        with open(cfg_plots_path, 'r') as f:
            self.cfg_plots = yaml.safe_load(f)

    def run(self):
        for plot_name, cfg_plot in self.cfg_plots.items():
            for threshold in cfg_plot["thresholds"]:
                print(f">>> Turn On {plot_name} ({threshold} GeV) <<<")
                turnon_collection = TurnOnCollection(cfg_plot, threshold)
                turnon_collection.create_hists()

                plotter = EfficiencyPlotter(plot_name, cfg_plot, turnon_collection)
                plotter.plot()


class ScalingPlotter(Plotter):

    def __init__(self, plot_name: str, cfg_plot: dict, scalings: dict, params: dict):
        os.makedirs("outputs/scalings", exist_ok=True)
        self.plot_name = plot_name
        self.cfg_plot = cfg_plot
        self.scalings = scalings
        self.params = params

    def _params_to_func_str(self, obj):
        a = round(self.params[obj][0], 3)
        b = round(self.params[obj][1], 3)
        pm = '+' if b > 0 else '-'
        return f"y = {a} x {pm} {abs(b)}"

    def plot(self, pct_point: float):
        fig, ax = self._new_plot()
        for obj, points in self.scalings.items():
            x_points = np.array(list(points.keys()))
            y_points = np.array(list(points.values()))
            pts = ax.plot(x_points, y_points, 'o')

            a, b = self.params[obj]
            label = (self.cfg_plot["test_objects"][obj]["label"]
                     + ", "
                     + self._params_to_func_str(obj))
            y_points = utils.scaling_func(x_points, a, b)
            ax.plot(x_points, y_points, color=pts[0].get_color(), label=label)

        ax.legend(loc="lower right")
        ax.set_xlabel("Threshold")
        ax.set_ylabel(f"{int(pct_point*100)}% Location")
        ax.set_xlim(0)
        ax.set_ylim(0)
        fig.tight_layout()

        plt.savefig(f"outputs/scalings/{self.plot_name}.png")


class ScalingCentral(PlottingCentral):

    def __init__(self, cfg_plots_path):
        super().__init__(cfg_plots_path)
        with open("./cfg_scaling_thresholds.yaml", 'r') as f:
            self.scaling_thresholds = yaml.safe_load(f)
            self.pct_point = 0.9

    def _get_scaling_thresholds(self, cfg_plot):
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
        raise RuntimeError("Failed to find thresholds in cfg_scaling_thresholds!")

    def _find_percentage_point(self, hist, bins):
        for i, eff in enumerate(hist[:-2]):
            is_point = (
                eff < self.pct_point
                and hist[i + 1] > self.pct_point
                and hist[i + 2] > self.pct_point
            )
            if is_point:
                return bins[i + 1]

    def _compute_scalings(self, turnon_collection, scalings):
        bins = turnon_collection.bins
        threshold = turnon_collection.threshold

        for obj in turnon_collection.hists:
            if obj == "ref":
                continue
            efficiency, _ = turnon_collection.get_efficiency(obj)
            percentage_point = self._find_percentage_point(efficiency, bins)
            if percentage_point:
                scalings[obj][threshold] = percentage_point

        return scalings

    def _fit_linear_functions(self, scalings):
        params = {}
        for obj, thresh_points in scalings.items():
            xdata = [th for th, val in thresh_points.items() if val]
            ydata = [thresh_points[x] for x in xdata]
            if not ydata:
                return None
            popt, pcov = curve_fit(utils.scaling_func, xdata, ydata)
            params[obj] = popt
        return params

    def _rate_config_function(self, name: str, a: float, b: float):
        pm = '+' if b > 0 else ''
        return f"function :: {name}Scaling :: args:=(offline); lambda:={a}*offline{pm}{b}"

    def _write_scalings_to_file(self, plot_name: str, params: dict):
        with open(f"outputs/scalings/{plot_name}.txt", 'w+') as f:
            f.write('')

        with open(f"outputs/scalings/{plot_name}.txt", 'a') as f:
            for obj, obj_params in params.items():
                a, b = obj_params
                f.write(self._rate_config_function(obj, a, b) + "\n")

    def run(self):
        for plot_name, cfg_plot in self.cfg_plots.items():
            print(f">>> Scalings {plot_name} <<<")
            thds = self._get_scaling_thresholds(cfg_plot)
            scalings = {x: {} for x in cfg_plot["test_objects"]}
            bar = IncrementalBar("Progress", max=len(thds))
            for threshold in thds:
                bar.next()
                turnon_collection = TurnOnCollection(cfg_plot, threshold)
                turnon_collection.create_hists()
                scalings = self._compute_scalings(turnon_collection, scalings)

            bar.finish()
            params = self._fit_linear_functions(scalings)
            if params:
                plotter = ScalingPlotter(plot_name, cfg_plot, scalings, params)
                plotter.plot(self.pct_point)
                self._write_scalings_to_file(plot_name, params)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cfg_plots",
        "-c",
        default="cfg_plots_dy.yaml",
        help="Path of YAML file specifying the desired plots."
    )
    parser.add_argument(
        "--scalings",
        "-s",
        action="store_true",
        help="Produce scaling plots."
    )
    args = parser.parse_args()

    plotter = PlottingCentral(args.cfg_plots)
    plotter.run()

    if args.scalings:
        scalings = ScalingCentral(args.cfg_plots)
        scalings.run()

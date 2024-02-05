import argparse
import json
import os
import yaml
from typing import Any

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
from tqdm import tqdm

from menu_tools.object_performance.turnon_collection import TurnOnCollection
from menu_tools.object_performance.config import PerformancePlotConfig
from menu_tools.object_performance.scaling_collection import ScalingCollection
from menu_tools.utils import utils
from menu_tools.utils.objects import Object


plt.style.use(hep.style.CMS)


class Plotter:
    outdir_base = "outputs/object_performance/"

    def _make_output_dirs(self, version: str) -> None:
        os.makedirs(f"{self.outdir_base}/{version}/turnons", exist_ok=True)
        os.makedirs(f"{self.outdir_base}/{version}/distributions", exist_ok=True)
        os.makedirs(f"{self.outdir_base}/{version}/scalings", exist_ok=True)

    def _create_new_plot(self) -> tuple[plt.Figure, plt.Axes]:
        fig, ax = plt.subplots(figsize=(10, 10))
        hep.cms.label(ax=ax, llabel="Phase-2 Simulation", com=14)
        return fig, ax


class EfficiencyPlotter(Plotter):
    def __init__(self, name, cfg, turnon_collection):
        self.plot_name = name
        self.cfg = PerformancePlotConfig(cfg, name)
        self.turnon_collection = turnon_collection
        self.version = self.turnon_collection.version
        self.threshold = self.turnon_collection.threshold
        self.bin_width = turnon_collection.cfg_plot.bin_width

    @property
    def _outdir_turnons(self) -> str:
        return os.path.join(self.outdir_base, self.version, "turnons")

    @property
    def _outdir_distributions(self) -> str:
        return os.path.join(self.outdir_base, self.version, "distributions")

    def _style_plot(self, fig, ax, legend_loc="lower right"):
        ax.axvline(self.threshold, ls=":", c="k")
        ax.axhline(1, ls=":", c="k")
        ax.legend(loc=legend_loc, frameon=False)
        ax.set_xlabel(rf"{self.cfg.xlabel}")
        ylabel = self.cfg.ylabel.replace("<threshold>", str(self.threshold))
        ax.set_ylabel(rf"{ylabel}")
        ax.set_xlim(self.cfg.bin_min, self.cfg.bin_max)
        ax.tick_params(direction="in")
        watermark = f"{self.version}_{self.plot_name}_" f"{self.threshold}"
        ax.text(
            0,
            -0.1,
            watermark,
            color="grey",
            alpha=0.2,
            fontsize=20,
            transform=ax.transAxes,
        )
        fig.tight_layout()

    def _save_json(self, file_name):
        plot = {}
        plot["xlabel"] = self.cfg.xlabel
        plot["ylabel"] = self.cfg.ylabel.replace("<threshold>", str(self.threshold))
        plot["watermark"] = f"{self.version}_{self.plot_name}_" f"{self.threshold}"

        for obj_key, gen_hist_trig in self.turnon_collection.hists.items():
            if obj_key == "ref":
                continue
            obj = Object(
                obj_key,
                version=self.version,
            )

            xbins = self.turnon_collection.bins
            xbins = 0.5 * (xbins[1:] + xbins[:-1])

            if self.cfg.iso_vs_eff_plot:
                efficiency = self._get_iso_vs_eff_hist(gen_hist_trig[0])
                yerr = np.zeros((2, len(efficiency)))
                xerr = np.zeros(len(efficiency))
            else:
                efficiency, yerr = self.turnon_collection.get_efficiency(obj_key)
                xerr = self.turnon_collection.xerr(obj_key)

            yerr = np.array(
                [yerr[0][~np.isnan(efficiency)], yerr[1][~np.isnan(efficiency)]]
            )
            xerr = xerr[np.isfinite(efficiency)]
            xbins = xbins[np.isfinite(efficiency)]
            efficiency = efficiency[np.isfinite(efficiency)]

            xerr = xerr.tolist()
            yerr = yerr.tolist()
            xbins = xbins.tolist()
            efficiency = efficiency.tolist()

            plot[obj_key] = {}
            plot[obj_key]["label"] = obj.plot_label
            plot[obj_key]["efficiency"] = efficiency
            plot[obj_key]["efficiency_err"] = yerr
            plot[obj_key]["xbins"] = xbins
            plot[obj_key]["err_kwargs"] = {
                "xerr": xerr,
                "capsize": 3,
                "marker": "o",
                "markersize": 8,
            }

        with open(f"{file_name}", "w") as outfile:
            outfile.write(json.dumps(plot, indent=4))

    def _get_iso_vs_eff_hist(self, test_hist):
        """
        Cumulative ratio of efficiency vs L1 Iso histogram.
        """

        l1_isolation_histogram = np.sum(test_hist)
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

            obj = Object(
                obj_key,
                version=self.version,
            )

            err_kwargs = {
                "xerr": self.turnon_collection.xerr(obj_key),
                "capsize": 3,
                "marker": "o",
                "markersize": 8,
            }
            ax.errorbar(
                xbins, efficiency, yerr=yerr, label=obj.plot_label, **err_kwargs
            )

        self._style_plot(fig, ax)
        ax.set_ylim(0, 1.1)

        # Save figure
        plot_fname = f"{self.plot_name}_{self.threshold}_{self.version}"
        plt.savefig(os.path.join(self._outdir_turnons, f"{plot_fname}.png"))
        plt.savefig(os.path.join(self._outdir_turnons, f"{plot_fname}.pdf"))
        self._save_json(os.path.join(self._outdir_turnons, f"{plot_fname}.json"))

        # Save config
        with open(os.path.join(self._outdir_turnons, f"{plot_fname}.yaml"), "w") as f:
            yaml.dump(
                {self.plot_name: self.cfg.config_dict}, f, default_flow_style=False
            )

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

            obj = Object(
                obj_key,
                version=self.version,
            )

            # yerr = np.sqrt(iso_vs_eff_hist) # TODO: Possibly introduce errors
            err_kwargs = {"capsize": 3, "marker": "o", "markersize": 8}
            ax.errorbar(xbins, iso_vs_eff_hist, label=obj.plot_label, **err_kwargs)

        self._style_plot(fig, ax)

        # Save figure
        plot_fname = f"{self.plot_name}_{self.threshold}_{self.version}"
        plt.savefig(os.path.join(self._outdir_turnons, f"{plot_fname}.png"))
        plt.savefig(os.path.join(self._outdir_turnons, f"{plot_fname}.pdf"))
        self._save_json(os.path.join(self._outdir_turnons, f"{plot_fname}.json"))

        # Save config
        with open(os.path.join(self._outdir_turnons, f"{plot_fname}.yaml"), "w") as f:
            yaml.dump(
                {self.plot_name: self.cfg.config_dict}, f, default_flow_style=False
            )

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
            err_kwargs = {
                "xerr": self.turnon_collection.xerr(obj_key),
                "capsize": 1,
                "marker": "o",
                "markersize": 2,
                "linestyle": "None",
            }

            ref_hist = ax.step(
                xbins,
                ref_hist[0],
                where="mid",
                label="ref: " + obj_key,
                ls="--",
                color="k",
            )

        for obj_key, gen_hist_trig in self.turnon_collection.hists.items():
            if obj_key == "ref":
                continue
            yerr = np.sqrt(gen_hist_trig[0])
            label = obj_key
            test_hist = ax.step(xbins, gen_hist_trig[0], where="mid")
            ax.errorbar(
                xbins,
                gen_hist_trig[0],
                yerr=yerr,
                label=label,
                color=test_hist[0].get_color(),
                **err_kwargs,
            )

        self._style_plot(fig, ax)
        # Save figure
        plot_fname = f"{self.plot_name}_{self.threshold}_dist_{self.version}"
        plt.savefig(os.path.join(self._outdir_distributions, f"{plot_fname}.png"))
        plt.savefig(os.path.join(self._outdir_distributions, f"{plot_fname}.pdf"))

        plt.close()

    def plot(self):
        self._make_output_dirs(self.version)
        if self.cfg.iso_vs_eff_plot:
            self._plot_iso_vs_efficiency_curve()
        else:
            self._plot_efficiency_curve()
            self._plot_raw_counts()


class EfficiencyCentral:
    """
    Class that orchestrates the plotting of
    """

    def __init__(self, cfg_plots_path):
        with open(cfg_plots_path, "r") as f:
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
                turnon_collection = TurnOnCollection(cfg_plot, threshold, plot_name)
                turnon_collection.create_hists()

                plotter = EfficiencyPlotter(plot_name, cfg_plot, turnon_collection)
                plotter.plot()


class ScalingPlotter(Plotter):
    def __init__(
        self,
        plot_name: str,
        cfg_plot: dict,
        scalings: dict,
        scaling_pct: float,
        version: str,
        params: dict[str, np.ndarray],
    ):
        self.plot_name = plot_name
        self.cfg_plot = cfg_plot
        self.scalings = scalings
        self.params = params
        self.version = version
        self.scaling_pct = scaling_pct

    def _params_to_func_str(self, obj_key: str):
        a = round(self.params[obj_key][0], 3)
        b = round(self.params[obj_key][1], 3)
        pm = "+" if b > 0 else "-"
        return f"y = {a} x {pm} {abs(b)}"

    def _save_json(self, fpath: str) -> None:
        plot: dict[str, Any] = {"watermark": f"{self.version}_{self.plot_name}"}

        for obj, points in self.scalings.items():
            _object = {}
            x_points = list(points.keys())
            y_points = list(points.values())

            label = obj + ", " + self._params_to_func_str(obj)

            _object["xvals"] = x_points
            _object["yvals"] = y_points
            _object["label"] = label

            plot[obj] = _object

        with open(fpath, "w") as outfile:
            outfile.write(json.dumps(plot, indent=4))

    def plot(self):
        self._make_output_dirs(self.version)

        fig, ax = self._create_new_plot()
        for obj_key, points in self.scalings.items():
            obj = Object(obj_key, self.version)
            x_points = np.array(list(points.keys()))
            y_points = np.array(list(points.values()))
            pts = ax.plot(x_points, y_points, "o")

            label = obj.plot_label + ", " + self._params_to_func_str(obj_key)
            a, b = self.params[obj_key]
            x = np.linspace(0, 2500, 20)
            y = utils.scaling_func(x, a, b)
            ax.plot(x, y, color=pts[0].get_color(), label=label)

        ax.legend(loc="lower right")
        ax.set_xlabel("L1 threshold [GeV]")
        ax.set_ylabel(f"{int(self.scaling_pct * 100)}% Location (gen, GeV)")
        watermark = f"{self.version}_{self.plot_name}"
        ax.text(
            0,
            -0.1,
            watermark,
            color="grey",
            alpha=0.2,
            fontsize=20,
            transform=ax.transAxes,
        )
        fig.tight_layout()
        ax.set_xlim(0, np.max(x_points))
        ax.set_ylim(0, np.max(y_points))

        plot_fname = os.path.join(
            self.outdir_base,
            self.version,
            "scalings",
            f"{self.plot_name}_{self.version}",
        )
        plt.savefig(f"{plot_fname}.png")
        plt.savefig(f"{plot_fname}.pdf")
        self._save_json(f"{plot_fname}.json")

        ## save config
        with open(f"{plot_fname}.yaml", "w") as outfile:
            yaml.dump(
                {self.plot_name: self.cfg_plot}, outfile, default_flow_style=False
            )

        plt.close()


class ScalingCentral:
    outdir = "outputs/object_performance/"

    def __init__(self, cfg_plots_path: str) -> None:
        with open(cfg_plots_path, "r") as f:
            self.cfg_plots = yaml.safe_load(f)
        with open("./configs/scaling_thresholds.yaml", "r") as f:
            self.scaling_thresholds = yaml.safe_load(f)

    def _get_scaling_thresholds(self, cfg_plot, test_obj) -> list[int]:
        if test_obj in self.scaling_thresholds:
            return self.scaling_thresholds[test_obj]
        if any("Muon" in x for x in cfg_plot["test_objects"]):
            return self.scaling_thresholds["Muon"]
        if any(
            any([y in x for x in cfg_plot["test_objects"]])
            for y in ["Ele", "EG", "Photon"]
        ):
            return self.scaling_thresholds["EG"]
        if any("MHT" in x for x in cfg_plot["test_objects"]):
            return self.scaling_thresholds["MHT"]
        if any("MET" in x for x in cfg_plot["test_objects"]):
            return self.scaling_thresholds["MET"]
        if any(("HT" in x) and ("MHT" not in x) for x in cfg_plot["test_objects"]):
            return self.scaling_thresholds["HT"]
        if any("Tau" in x for x in cfg_plot["test_objects"]):
            return self.scaling_thresholds["Tau"]
        if any("Jet" in x for x in cfg_plot["test_objects"]):
            return self.scaling_thresholds["Jet"]
        raise RuntimeError("Failed to find thresholds in cfg_scaling_thresholds!")

    def _write_scalings_to_file(self, obj: Object, params: np.ndarray) -> None:
        """Dumps the scaling parameters to a file.

        Writes the offset and slope params of the linear scaling function to
        a yaml file for usage in the offline rate computation.

        Retruns:
            None
        """
        fpath = os.path.join(
            "outputs",
            "object_performance",
            obj.version,
            "scalings",
        )
        os.makedirs(fpath, exist_ok=True)
        a, b = params
        with open(os.path.join(fpath, str(obj) + ".yaml"), "w") as f:
            yaml.dump({"slope": float(a), "offset": float(b)}, f)

    def run(self):
        for plot_name, cfg_plot in self.cfg_plots.items():
            plot_config = PerformancePlotConfig(cfg_plot, plot_name)
            if not plot_config.compute_scalings:
                continue
            print(f">>> Scalings {plot_name} <<<")

            scalings = {}
            scaling_function_params = {}

            pbar = tqdm(total=len(plot_config.test_object_instances), desc="Objects")
            for test_obj in plot_config.test_object_instances:
                pbar.write(str(test_obj))
                pbar.update(1)
                scalings[str(test_obj)] = {}
                thds = self._get_scaling_thresholds(cfg_plot, test_obj)
                for threshold in tqdm(thds, leave=False, desc="Thresholds"):
                    turnon_collection = TurnOnCollection(cfg_plot, threshold)
                    turnon_collection.create_hists()
                    scaling_pct = turnon_collection.cfg_plot.scaling_pct
                    method = turnon_collection.cfg_plot.scaling_method
                    scaling_collection = ScalingCollection(
                        cfg_plot, method, scaling_pct
                    )
                    scalings[str(test_obj)][
                        threshold
                    ] = scaling_collection._compute_scalings(
                        turnon_collection, test_obj, scaling_pct, method
                    )
                # Fit parameters of scaling function
                params = scaling_collection.fit_linear_function(scalings[str(test_obj)])
                scaling_function_params[str(test_obj)] = params
                # Write scalings for test_obj to file for usage in rate part
                self._write_scalings_to_file(test_obj, params)

            plotter = ScalingPlotter(
                plot_name,
                cfg_plot,
                scalings,
                scaling_pct,
                turnon_collection.version,
                scaling_function_params,
            )
            plotter.plot()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "cfg_plots",
        nargs="+",
        type=str,
        help="Path of YAML configuration file specifying the desired plots.",
    )
    args = parser.parse_args()

    for path_cfg_plot in args.cfg_plots:
        plotter = EfficiencyCentral(path_cfg_plot)
        plotter.run()

        scalings = ScalingCentral(path_cfg_plot)
        scalings.run()


if __name__ == "__main__":
    main()

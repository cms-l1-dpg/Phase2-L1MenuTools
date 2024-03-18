import argparse
import os
import json

import awkward as ak
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import yaml

from menu_tools.utils import constants
from menu_tools.utils import objects
from menu_tools.utils import scalings
from menu_tools.utils.objects import Object
from menu_tools.rate_plots.config import RatePlotConfig

plt.style.use(hep.style.CMS)


class RatePlotter:
    # Common plot properties
    _figsize = (10, 10)
    _llabel = "Phase-2 Simulation"
    _com = 14
    _outdir = "outputs/rate_plots/"

    def __init__(self, cfg, data, offline_pt: bool):
        self.cfg = cfg
        self.data = data
        self.offline_pt = offline_pt

        ## Overwrite outdir
        self._outdir = os.path.join(
            "outputs", self.cfg.version, "object_performance", "rates"
        )

    @property
    def _online_offline(self):
        if self.offline_pt:
            return "Offline"
        return "Online"

    def _style_plot(self, fig, ax0, ax1=None, legend_loc="upper right"):
        ax0.legend(loc=legend_loc, frameon=False)
        ax0.set_ylabel("Rate [kHz]")
        ax0.set_yscale("log")
        ax0.grid()
        ax0.tick_params(direction="in")
        if ax1:
            ax1.set_xlabel(rf"{self._online_offline} $p_T$ [GeV]")
            ax1.grid()
        else:
            ax0.set_xlabel(rf"{self._online_offline} $p_T$ [GeV]")
        fig.tight_layout()

    def _plot_single_version_rate_curves(self):
        """
        TODO: Write description!
        """
        version = self.cfg.version
        fig, ax = plt.subplots(figsize=self._figsize)
        hep.cms.label(ax=ax, llabel=self._llabel, com=self._com)

        plot_dict = {}

        for obj_specifier, obj_instances in self.cfg.test_object_instances.items():
            if obj_specifier not in self.data.keys():
                continue
            rate_values = self.data[obj_specifier][version]

            xvals = list(rate_values.keys())
            yvals = list(rate_values.values())
            label = f"{obj_instances[version].plot_label}"

            plot_dict[obj_specifier] = {
                "x_values": xvals,
                "y_values": yvals,
                "object": obj_instances[version].plot_label,
                "label": label,
                "version": version,
                "xlabel": rf"{self._online_offline} $p_T$ [GeV]",
            }

            ax.plot(
                xvals,
                yvals,
                marker="o",
                label=label,
            )

        self._style_plot(fig, ax)

        # Save plot
        fname = os.path.join(
            self._outdir,
            f"{version}_{self._online_offline}_{self.cfg.plot_name}",
        )
        print("Saving to ", fname)
        plt.savefig(fname + ".png")
        plt.savefig(fname + ".pdf")

        with open(fname + ".json", "w") as outfile:
            outfile.write(json.dumps(plot_dict, indent=4))

        # TODO: Add styling
        plt.close()

    def _plot_version_comparsion_rate_curves(self):
        """
        TODO: Write description!
        """
        v1, v2 = self.cfg.versions
        fig, axs = plt.subplots(
            2,
            1,
            figsize=self._figsize,
            sharex=True,
            gridspec_kw={"height_ratios": [3, 1]},
        )
        hep.cms.label(ax=axs[0], llabel=self._llabel, com=self._com)

        for obj_key, rate_values in self.data.items():
            xvalues = np.fromiter(rate_values[v1].keys(), dtype=float)
            v1_values = np.fromiter(rate_values[v1].values(), dtype=float)
            v2_values = np.fromiter(rate_values[v2].values(), dtype=float)
            p = axs[0].plot(
                xvalues,
                v1_values,
                marker="o",
                linestyle="solid",
                label=f"{obj_key} @ {v1}",
            )
            axs[0].plot(
                xvalues,
                v2_values,
                marker="o",
                linestyle="dashed",
                label=f"{obj_key} @ {v2}",
                color=p[0].get_color(),
            )
            axs[1].plot(
                xvalues,
                v1_values / v2_values,
                marker="o",
                linestyle="dotted",
                label=f"({obj_key} @ {v1}) / ({obj_key} @ {v2})",
            )
            axs[1].axhline(1, alpha=0.6, color="black")

        self._style_plot(fig, axs[0], axs[1])
        fname = os.path.join(
            self._outdir, f"{v1}-vs-{v2}_{self._online_offline}_{self.cfg.plot_name}"
        )
        plt.savefig(fname + ".png")
        plt.savefig(fname + ".pdf")

        plt.close()

    def plot(self):
        os.makedirs(self._outdir, exist_ok=True)
        if self.cfg.compare_versions:
            self._plot_version_comparsion_rate_curves()
        else:
            self._plot_single_version_rate_curves()

        # Dump plot conifg
        with open(os.path.join(self._outdir, f"{self.cfg.plot_name}.yaml"), "w") as f:
            yaml.dump(
                {self.cfg.plot_name: self.cfg.config_dict}, f, default_flow_style=False
            )


class RateComputer:
    def __init__(
        self,
        obj: Object,
        sample: str,
        version: str,
        apply_offline_conversion: bool,
    ):
        self.object = obj
        self.sample = sample
        self.version = version
        self.apply_offline_conversion = apply_offline_conversion
        self.arrays = self._load_cached_arrays()

    def _transform_key(self, raw_key: str) -> str:
        """Maps <obj_name><obj_field> to <obj_field>.

        Returns:
            key: string of with the l1 object name prefix removed, qual
            transformed to quality
        """
        ## nano
        if "_" in raw_key:
            key = raw_key.removeprefix(self.object.nano_obj_name).split("_")[-1]
        ## menu ntuples
        else:
            key = raw_key.removeprefix(self.object.nano_obj_name).lower()

        if "qual" in key:
            return "quality"
        return key

    def _load_cached_arrays(self):
        """
        Loads array for specified object/version combination
        from the cached parquet file.
        """
        fpath = os.path.join(
            "cache",
            self.version,
            f"{self.version}_{self.sample}_{self.object.nano_obj_name}.parquet",
        )
        arr = ak.from_parquet(fpath)

        # Remove object name prefix from array fields
        arr = ak.zip({self._transform_key(var): arr[var] for var in arr.fields})

        # Apply scalings if so configured
        if self.apply_offline_conversion:
            arr = scalings.add_offline_pt(arr, self.object)
        arr["pt"] = scalings.get_pt_branch(arr, str(self.object))

        return arr

    def compute_rate(self, thresholds: np.ndarray) -> dict:
        """Computes rate at threholds after application of all object cuts.

        threshold: pt threshold for which to compute rate

        Returns:
            rate: rate computed after all object cuts are applied
        """
        obj_mask = objects.compute_selection_mask_for_object_cuts(
            self.object, self.arrays
        )

        pt_field = "offline_pt" if self.apply_offline_conversion else "pt"

        if (max_pt_obj := self.arrays[obj_mask][pt_field]).ndim > 1:
            max_pt_obj = ak.max(max_pt_obj, axis=1)

        cumsum = np.cumsum(
            np.histogram(max_pt_obj, bins=[-1] + list(thresholds) + [1e5])[0]
        )
        rate = (cumsum[-1] - cumsum) / len(obj_mask) * constants.RATE_NORM_FACTOR

        return dict(zip(thresholds, rate))


class RatePlotCentral:
    """
    Class that orchestrates the creation of the rate plots
    (pt thresholds vs. rate).
    """

    def __init__(self, cfg_plots_path: str):
        with open(cfg_plots_path, "r") as f:
            self.cfg_plots = yaml.safe_load(f)

    def get_bins(self, plot_config: RatePlotConfig) -> np.ndarray:
        """
        Set bins according to configuration.
        """
        bin_width = plot_config.bin_width
        xmax = plot_config.bin_max + 1e-5
        xmin = plot_config.bin_min
        return np.arange(xmin, xmax, bin_width)

    def _compute_rates(
        self,
        plot_config: RatePlotConfig,
        obj_specifier: str,
        obj_instances: dict[str, Object],
        apply_offline_conversion: bool,
    ) -> dict:
        """
        This function orchestrates the computations of
        the rates at the different thresholds that are
        to be plotted. Instances of RateComputer are created
        and called for this purpose.
        """
        rate_data: dict[str, dict] = {}

        # Iterate over version(s)
        for version in plot_config.versions:
            rate_data[version] = {}
            rate_computer = RateComputer(
                obj_instances[version],
                plot_config.sample,
                version,
                apply_offline_conversion,
            )

            rate_data[version] = rate_computer.compute_rate(self.get_bins(plot_config))

        return rate_data

    def run(self, apply_offline_conversion: bool = False) -> None:
        """
        This function iterates over all plots defined
        in the configuration file, computes the rates
        at the configured thresholds and passes it to
        the RatePlotter for plotting.
        """
        # Iterate over plots
        for plot_name, cfg_plot in self.cfg_plots.items():
            print(
                "Plotting ",
                plot_name,
                " Offline" if apply_offline_conversion else " Online",
            )
            plot_config = RatePlotConfig(cfg_plot, plot_name)
            rate_plot_data = {}

            # Iterate over test objects in plot
            for (
                obj_specifier,
                obj_instances,
            ) in plot_config.test_object_instances.items():
                try:
                    rate_plot_data[obj_specifier] = self._compute_rates(
                        plot_config,
                        obj_specifier,
                        obj_instances,
                        apply_offline_conversion,
                    )
                    scalings_found = True
                except UserWarning:
                    # Continue without creating a plot if a warning was raised.
                    # This applies to no scalings being found for an object.
                    scalings_found = False
                    continue
            if not scalings_found:
                continue

            # Plot Rate vs. Threshold after all data has been aggregated
            plotter = RatePlotter(plot_config, rate_plot_data, apply_offline_conversion)
            plotter.plot()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "cfg_plots", help="Path of YAML file specifying the desired plots."
    )
    args = parser.parse_args()

    plotter = RatePlotCentral(args.cfg_plots)
    plotter.run(apply_offline_conversion=True)
    plotter.run()


if __name__ == "__main__":
    main()

"""Plots of the response / resolution computed by `ResolutionCollection`.

Run through `object_performance <config>`: every plot entry with a `resolution:` block
is handled here (and skipped by the efficiency plotter). Outputs go to
outputs/<version>/object_performance/resolution/:
  <plot>_<var>_vs_<vs>_<version>.{png,pdf,json}       median and resolution vs <vs>,
                                                      all test objects
  <plot>_<var>_vs_<vs>_dist_<version>.{png,pdf}       per-bin response distributions
                                                      (only for variables in
                                                      `response_binning`)
  <plot>_<version>.yaml                               copy of the plot config
"""
import json
import math
import os
from typing import Any, Optional

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import yaml

from menu_tools.object_performance.plotter import Plotter
from menu_tools.object_performance.resolution_collection import (
    RATIO_VARIABLES,
    ResolutionCollection,
    make_edges,
)
from menu_tools.utils import utils
from menu_tools.utils.objects import Object
from menu_tools.utils.plotting import add_watermark


# Event-level sums (MET, HT): the pT response is the ratio of the sums.
EVENT_LEVEL_PT_LABELS = (
    r"L1 / ref",
    r"Median L1 / ref",
    r"$\sigma_{eff}$(L1 / ref) / median",
)

RESPONSE_LABELS = {
    "pt": (
        r"$p_T^{L1} / p_T^{ref}$",
        r"Median $p_T^{L1} / p_T^{ref}$",
        r"$\sigma_{eff}(p_T^{L1} / p_T^{ref})$ / median",
    ),
    "eta": (
        r"$\eta^{L1} - \eta^{ref}$",
        r"Median $\Delta\eta$",
        r"$\sigma_{eff}(\Delta\eta)$",
    ),
    "phi": (
        r"$\phi^{L1} - \phi^{ref}$",
        r"Median $\Delta\phi$ (rad)",
        r"$\sigma_{eff}(\Delta\phi)$ (rad)",
    ),
}


def _nan_to_none(values):
    return [
        None if (v is None or (isinstance(v, float) and math.isnan(v))) else v
        for v in values
    ]


class ResolutionPlotter(Plotter):
    def __init__(
        self, plot_name: str, collection: ResolutionCollection, pu_value: int = 200
    ):
        self.plot_name = plot_name
        self.collection = collection
        self.cfg = collection.cfg_plot
        self.res_cfg = collection.res_cfg
        self.version = collection.version
        self.pu_value = pu_value

    @property
    def _outdir(self) -> str:
        return os.path.join("outputs", self.version, "object_performance", "resolution")

    def _response_labels(self, var: str) -> tuple[str, str, str]:
        if var == "pt" and self.collection.event_level:
            return EVENT_LEVEL_PT_LABELS
        return RESPONSE_LABELS[var]

    def _label(self, obj_key: str) -> str:
        return Object(obj_key, version=self.cfg.version_for_objects).plot_label

    def _vs_label(self, vs: str) -> str:
        if label := self.res_cfg.vs_label(vs):
            return label
        ref = self.cfg.reference_label
        if vs == "pt":
            if self.collection.event_level:
                return f"{ref} (GeV)"
            return rf"{ref} $p_T$ (GeV)"
        if vs == "eta":
            return rf"{ref} $\eta$"
        if vs == "abseta":
            return rf"{ref} $|\eta|$"
        if vs == "phi":
            return rf"{ref} $\phi$"
        return f"Pileup ({self.res_cfg.pu_variable})"

    def _fname(self, var: str, vs: str, suffix: str = "") -> str:
        return os.path.join(
            self._outdir, f"{self.plot_name}_{var}_vs_{vs}{suffix}_{self.version}"
        )

    def _save_json(self, var: str, vs: str, fname: str) -> None:
        out: dict[str, Any] = {
            "watermark": f"{self.version}_{self.plot_name}_{var}_vs_{vs}",
            "xlabel": self._vs_label(vs),
            "response": self._response_labels(var)[0],
            "resolution_definition": "half of the 16-84% interquantile range"
            + (" divided by the median" if var in RATIO_VARIABLES else ""),
            "pu_variable": self.res_cfg.pu_variable if vs == "pu" else None,
        }
        for obj_key, res in self.collection.results[var][vs].items():
            edges = np.asarray(res["edges"])
            entry = {
                "label": self._label(obj_key),
                "xbins": (0.5 * (edges[1:] + edges[:-1])).tolist(),
                "xerr": (0.5 * np.diff(edges)).tolist(),
                "edges": res["edges"],
            }
            for k in (
                "n",
                "median",
                "median_err",
                "q16",
                "q84",
                "resolution",
                "resolution_err",
                "mean",
                "std",
            ):
                entry[k] = _nan_to_none(
                    [float(v) if k != "n" else int(v) for v in res[k]]
                )
            out[obj_key] = entry
        with open(fname, "w") as f:
            f.write(json.dumps(out, indent=4))

    @utils.ignore_warnings
    def _plot_summary(self, var: str, vs: str) -> None:
        results = self.collection.results[var][vs]
        if not results:
            print(f"WARNING: no {var} response vs {vs} for {self.plot_name}")
            return
        fig, (ax_med, ax_res) = plt.subplots(
            2,
            1,
            figsize=(10, 12),
            sharex=True,
            gridspec_kw={"height_ratios": [1, 1], "hspace": 0.05},
        )
        hep.cms.label(
            ax=ax_med, llabel="Phase-2 Simulation", com=14, rlabel=f"{self.pu_value} PU"
        )
        edges = self.res_cfg.vs_edges(vs)
        x = 0.5 * (edges[1:] + edges[:-1])
        xerr = 0.5 * np.diff(edges)
        err_kwargs = {"capsize": 3, "marker": "o", "markersize": 7, "linestyle": "none"}
        for obj_key, res in results.items():
            label = self._label(obj_key)
            ax_med.errorbar(
                x,
                res["median"],
                yerr=res["median_err"],
                xerr=xerr,
                label=label,
                **err_kwargs,
            )
            ax_res.errorbar(
                x,
                res["resolution"],
                yerr=res["resolution_err"],
                xerr=xerr,
                **err_kwargs,
            )

        ax_med.axhline(1 if var in RATIO_VARIABLES else 0, ls=":", c="k")
        _, med_label, res_label = self._response_labels(var)
        ax_med.set_ylabel(med_label)
        ax_res.set_ylabel(res_label)
        ax_res.set_xlabel(self._vs_label(vs))
        ax_res.set_xlim(edges[0], edges[-1])
        ax_res.set_ylim(bottom=0)
        ax_med.legend(
            loc="best",
            frameon=False,
            fontsize=18,
            title=self.cfg.reference_label,
            title_fontsize=18,
        )
        for ax in (ax_med, ax_res):
            ax.tick_params(direction="in")
        fig.tight_layout()
        add_watermark(ax_res, f"{self.version}_{self.plot_name}_{var}_vs_{vs}")

        fname = self._fname(var, vs)
        plt.savefig(f"{fname}.png", bbox_inches="tight")
        plt.savefig(f"{fname}.pdf", bbox_inches="tight")
        self._save_json(var, vs, f"{fname}.json")
        plt.close(fig)

    @utils.ignore_warnings
    def _plot_distributions(self, var: str, vs: str) -> None:
        """Response distributions in all bins of `vs`, all test objects overlaid (unit
        area).
        """
        hist_edges = make_edges(self.res_cfg.response_binning[var])
        vs_edges = self.res_cfg.vs_edges(vs)
        nbins = len(vs_edges) - 1
        ncols = min(4, nbins)
        nrows = math.ceil(nbins / ncols)
        with plt.rc_context(
            {
                "font.size": 11,
                "axes.labelsize": 11,
                "xtick.labelsize": 9,
                "ytick.labelsize": 9,
                "legend.fontsize": 9,
            }
        ):
            fig, axes = plt.subplots(
                nrows, ncols, figsize=(4.2 * ncols, 3.4 * nrows), squeeze=False
            )
            for i_obj, obj_key in enumerate(self.collection.pairs):
                values = self.collection.response(obj_key, var)
                x = self.collection.vs_values(obj_key, vs)
                if values is None or x is None:
                    continue
                idx = np.digitize(x, vs_edges) - 1
                color = f"C{i_obj}"
                for i in range(nbins):
                    sel = values[idx == i]
                    ax = axes[i // ncols][i % ncols]
                    if len(sel) == 0:
                        continue
                    counts, _ = np.histogram(
                        np.clip(sel, hist_edges[0], hist_edges[-1]), bins=hist_edges
                    )
                    ax.stairs(
                        counts / max(len(sel), 1),
                        hist_edges,
                        color=color,
                        label=f"{self._label(obj_key)} ({len(sel)})",
                    )
            for i in range(nrows * ncols):
                ax = axes[i // ncols][i % ncols]
                if i >= nbins:
                    ax.set_visible(False)
                    continue
                ax.set_title(
                    f"{self._vs_label(vs)} in [{vs_edges[i]:g}, {vs_edges[i + 1]:g})",
                    fontsize=10,
                )
                ax.axvline(1 if var in RATIO_VARIABLES else 0, ls=":", c="k", lw=0.8)
                ax.set_xlabel(self._response_labels(var)[0])
                ax.set_ylabel("Fraction")
                ax.legend(loc="upper right", frameon=False, fontsize=7)
            fig.suptitle(
                f"CMS Phase-2 Simulation  -  {self.plot_name}, {self.version}  "
                f"({self.pu_value} PU)",
                fontsize=13,
                y=1.0,
            )
            fig.tight_layout()
            fname = self._fname(var, vs, "_dist")
            plt.savefig(f"{fname}.png", bbox_inches="tight")
            plt.savefig(f"{fname}.pdf", bbox_inches="tight")
            plt.close(fig)

    def plot(self) -> None:
        os.makedirs(self._outdir, exist_ok=True)
        for var in self.collection.results:
            for vs in self.collection.results[var]:
                self._plot_summary(var, vs)
                if var in self.res_cfg.response_binning:
                    self._plot_distributions(var, vs)
        with open(
            os.path.join(self._outdir, f"{self.plot_name}_{self.version}.yaml"), "w"
        ) as f:
            yaml.dump(
                {self.plot_name: self.cfg.config_dict}, f, default_flow_style=False
            )


class ResolutionCentral:
    """Runs all plot entries of a config file that contain a `resolution:` block."""

    def __init__(self, cfg_plots_path: str, override_version: Optional[str] = None):
        with open(cfg_plots_path, "r") as f:
            self.cfg_plots = yaml.safe_load(f)
        self.override_version = override_version
        self.config_version = self._extract_version(cfg_plots_path)

    @staticmethod
    def _extract_version(path: str) -> str:
        parts = os.path.normpath(path).split(os.sep)
        if "configs" in parts:
            idx = parts.index("configs")
            if idx + 1 < len(parts):
                return parts[idx + 1]
        return "unknown_version"

    def run(self) -> None:
        for plot_name, cfg_plot in self.cfg_plots.items():
            if not isinstance(cfg_plot, dict) or "resolution" not in cfg_plot:
                continue
            print(f">>> Resolution {plot_name} <<<")
            collection = ResolutionCollection(
                cfg_plot,
                plot_name,
                config_version=self.config_version,
                override_version=self.override_version,
            )
            collection.create()
            ResolutionPlotter(plot_name, collection).plot()
            version = collection.version
            print(
                "INFO: resolution plots in "
                f"outputs/{version}/object_performance/resolution"
            )

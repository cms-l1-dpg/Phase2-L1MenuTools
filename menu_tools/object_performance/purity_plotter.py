"""Plots of the purity / fake rate / multiplicity computed by `PurityCollection`.

Run through `object_performance <config>`: every plot entry with a `purity:` block is
handled here (and skipped by the efficiency plotter). Outputs go to
outputs/<version>/object_performance/purity/:
  <plot>_<quantity>_vs_<vs>[_thr<t>]_<version>.{png,pdf,json}
      all test objects overlaid
  <plot>_<version>.yaml
      copy of the plot config
"""
import json
import math
import os
from typing import Optional

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import yaml

from menu_tools.object_performance.plotter import Plotter
from menu_tools.object_performance.purity_collection import PurityCollection
from menu_tools.utils import utils
from menu_tools.utils.objects import Object, trigger_level
from menu_tools.utils.plotting import add_watermark


def _clean(values):
    out = []
    for v in values:
        if v is None:
            out.append(None)
            continue
        v = float(v)
        out.append(None if math.isnan(v) else v)
    return out


def _fmt_thr(t: float) -> str:
    return f"{t:g}".replace(".", "p")


class PurityPlotter(Plotter):
    def __init__(
        self, plot_name: str, collection: PurityCollection, pu_value: int = 200
    ):
        self.plot_name = plot_name
        self.collection = collection
        self.cfg = collection.cfg_plot
        self.pur_cfg = collection.pur_cfg
        self.version = collection.version
        self.pu_value = pu_value
        self.lvl = trigger_level(self.cfg.test_objects.keys())

    @property
    def _outdir(self) -> str:
        return os.path.join("outputs", self.version, "object_performance", "purity")

    def _label(self, obj_key: str) -> str:
        label = Object(obj_key, version=self.cfg.version_for_objects).plot_label
        rng = obj_key.split(":")[2] if obj_key.count(":") >= 2 else "inclusive"
        return label if rng == "inclusive" else f"{label} ({rng})"

    # ---- labels --------------------------------------------------------------------

    def _ylabel(self, quantity: str) -> str:
        lvl, rate = self.lvl, self.pur_cfg.rate
        unit = " [kHz]" if rate else ""
        lead = "leading " if self.pur_cfg.leading_only else ""
        if quantity == "purity":
            return f"Purity of {lead}{lvl} objects"
        if quantity == "fake_fraction":
            return f"Fake fraction of {lead}{lvl} objects (1 - purity)"
        if quantity == "unmatched_per_event":
            return f"Unmatched {lead}{lvl} objects / event"
        if quantity == "objects_per_event":
            return (
                f"Leading {lvl} objects / event" if lead else f"{lvl} objects / event"
            )
        if quantity == "unmatched_density":
            return f"Unmatched {lead}{lvl} objects / event / bin"
        if quantity == "density":
            return f"{lvl} objects / event / bin"
        if quantity == "event_fraction":
            what = (
                f"unmatched {lvl} obj."
                if self.pur_cfg.mode == "fake_rate"
                else f"{lvl} obj."
            )
            return (
                f"Rate (events with $\\geq$1 {what})"
                if rate
                else f"Events with $\\geq$1 {what}"
            ) + unit
        raise ValueError(quantity)

    def _xlabel(self, vs: str) -> str:
        if label := self.pur_cfg.vs_label(vs):
            return label
        lvl = self.lvl
        return {
            "pt": rf"{lvl} object $p_T$ (GeV)",
            "eta": rf"{lvl} object $\eta$",
            "abseta": rf"{lvl} object $|\eta|$",
            "phi": rf"{lvl} object $\phi$",
            "pu": f"Pileup ({self.pur_cfg.pu_variable})",
            "threshold": rf"{lvl} $p_T$ threshold (GeV)",
        }[vs]

    def _definition(self, quantity: str) -> str:
        lvl = self.lvl
        gen = self.pur_cfg.gen_label if self.pur_cfg.reference_gen else ""
        drs = sorted({o["dr"] for o in self.collection.objects.values()})
        dr = "/".join(f"{d:g}" for d in drs)
        match = rf"matched: $\Delta R$({lvl}, {gen}) < {dr}"
        if quantity == "purity":
            return f"Purity = N(matched {lvl}) / N({lvl}); {match}"
        if quantity == "fake_fraction":
            return f"Fake fraction = N(unmatched {lvl}) / N({lvl}); {match}"
        if quantity in ("unmatched_per_event", "unmatched_density"):
            return f"Unmatched: no {gen} within $\\Delta R$ < {dr}"
        if quantity == "event_fraction" and self.pur_cfg.mode == "fake_rate":
            scale = r" $\times$ 31038 kHz" if self.pur_cfg.rate else ""
            return (
                f"Fraction of events with $\\geq$1 unmatched {lvl} object{scale}; "
                f"no {gen} within $\\Delta R$ < {dr}"
            )
        if quantity == "event_fraction":
            scale = r" $\times$ 31038 kHz" if self.pur_cfg.rate else ""
            return (
                f"Fraction of events with $\\geq$1 {lvl} object above "
                f"threshold{scale} (no gen matching)"
            )
        return f"All {lvl} objects after ID / $\\eta$ cuts (no gen matching)"

    def _context(self, plot: dict) -> str:
        parts = [self.cfg.sample]
        if plot["threshold"] is not None:
            parts.append(rf"$p_T \geq$ {plot['threshold']:g} GeV")
        if self.pur_cfg.leading_only:
            parts.append("leading object only")
        return ", ".join(parts)

    def _fname(self, plot: dict) -> str:
        thr = (
            f"_thr{_fmt_thr(plot['threshold'])}"
            if plot["threshold"] is not None
            else ""
        )
        return os.path.join(
            self._outdir,
            f"{self.plot_name}_{plot['quantity']}_vs_{plot['vs']}{thr}_{self.version}",
        )

    # ---- output --------------------------------------------------------------------

    def _save_json(self, plot: dict, fname: str) -> None:
        edges = np.asarray(plot["edges"], dtype=float)
        is_scan = plot["vs"] == "threshold"
        out = {
            "watermark": os.path.basename(fname),
            "sample": self.cfg.sample,
            "mode": self.pur_cfg.mode,
            "quantity": plot["quantity"],
            "definition": self._definition(plot["quantity"]),
            "xlabel": self._xlabel(plot["vs"]),
            "ylabel": self._ylabel(plot["quantity"]),
            "threshold": plot["threshold"],
            "leading_only": self.pur_cfg.leading_only,
            "rate_kHz": self.pur_cfg.rate and plot["quantity"] == "event_fraction",
            "n_events": self.collection.n_events,
            "pu_variable": self.pur_cfg.pu_variable if plot["vs"] == "pu" else None,
            "pileup_source": self.collection.pileup_source
            if plot["vs"] == "pu"
            else None,
        }
        for key, s in plot["series"].items():
            entry = {
                "label": self._label(key),
                "match_dR": self.collection.objects[key]["dr"],
            }
            if is_scan:
                entry["thresholds"] = edges.tolist()
            else:
                entry["edges"] = edges.tolist()
                entry["xbins"] = (0.5 * (edges[1:] + edges[:-1])).tolist()
            for k in ("y", "err_lo", "err_hi"):
                entry[k] = _clean(s[k])
            entry["num"] = [int(v) for v in s["num"]]
            entry["den"] = [int(v) for v in s["den"]]
            for k in ("integral", "integral_n", "fit"):
                if k in s:
                    entry[k] = s[k]
            out[key] = entry
        with open(fname, "w") as f:
            json.dump(out, f, indent=4)

    @utils.ignore_warnings
    def _plot_one(self, plot: dict) -> None:
        if not plot["series"]:
            return
        quantity, vs = plot["quantity"], plot["vs"]
        fig, ax = plt.subplots(figsize=(10, 10))
        hep.cms.label(
            ax=ax, llabel="Phase-2 Simulation", com=14, rlabel=f"{self.pu_value} PU"
        )
        edges = np.asarray(plot["edges"], dtype=float)
        if vs == "threshold":
            x, xerr = edges, None
            kwargs = {
                "capsize": 3,
                "marker": "o",
                "markersize": 6,
                "linestyle": "-",
                "linewidth": 1,
            }
        else:
            x, xerr = 0.5 * (edges[1:] + edges[:-1]), 0.5 * np.diff(edges)
            kwargs = {"capsize": 3, "marker": "o", "markersize": 7, "linestyle": "none"}
        for key, s in plot["series"].items():
            label = self._label(key)
            if "integral" in s and s["integral"] is not None and vs == "pt":
                label += f" (all: {s['integral']:.2f})"
            if s.get("fit"):
                label += f" (slope {s['fit']['slope']:.2g}/PU)"
            y = np.asarray(s["y"], dtype=float)
            ax.errorbar(
                x, y, yerr=[s["err_lo"], s["err_hi"]], xerr=xerr, label=label, **kwargs
            )
            if s.get("fit") and vs == "pu":
                xx = np.array([edges[0], edges[-1]])
                ax.plot(
                    xx,
                    s["fit"]["intercept"] + s["fit"]["slope"] * xx,
                    ls=":",
                    c=ax.lines[-1].get_color(),
                    lw=1,
                )

        ax.set_xlabel(self._xlabel(vs))
        ax.set_ylabel(self._ylabel(quantity))
        ax.set_xlim(
            edges[0] - (0.02 * (edges[-1] - edges[0]) if vs == "threshold" else 0),
            edges[-1],
        )
        if quantity in ("purity", "fake_fraction"):
            ax.set_ylim(0, 1.35)
            ax.axhline(1, ls=":", c="k", lw=0.8)
        else:
            y = np.concatenate(
                [np.asarray(s["y"], float) for s in plot["series"].values()]
            )
            y_hi = y + np.concatenate(
                [np.asarray(s["err_hi"], float) for s in plot["series"].values()]
            )
            y, y_hi = y[np.isfinite(y) & (y > 0)], y_hi[np.isfinite(y_hi) & (y_hi > 0)]
            if len(y) and vs == "threshold":
                # threshold scans span orders of magnitude
                ax.set_yscale("log")
                ax.set_ylim(y.min() / 3, y_hi.max() * 30)
            elif len(y_hi):
                ax.set_ylim(0, y_hi.max() * 1.45)
        # The definition takes the top line of the axes, the legend goes below it.
        ax.legend(
            loc="upper right",
            bbox_to_anchor=(1, 0.95),
            frameon=False,
            fontsize=16,
            title=self._context(plot),
            title_fontsize=16,
        )
        ax.text(
            0.02,
            0.98,
            self._definition(quantity),
            transform=ax.transAxes,
            fontsize=11,
            va="top",
            wrap=True,
        )
        ax.tick_params(direction="in")
        fig.tight_layout()
        fname = self._fname(plot)
        add_watermark(ax, os.path.basename(fname))
        plt.savefig(f"{fname}.png", bbox_inches="tight")
        plt.savefig(f"{fname}.pdf", bbox_inches="tight")
        self._save_json(plot, f"{fname}.json")
        plt.close(fig)

    def plot(self) -> None:
        os.makedirs(self._outdir, exist_ok=True)
        for plot in self.collection.plots:
            self._plot_one(plot)
        with open(
            os.path.join(self._outdir, f"{self.plot_name}_{self.version}.yaml"), "w"
        ) as f:
            yaml.dump(
                {self.plot_name: self.cfg.config_dict}, f, default_flow_style=False
            )


class PurityCentral:
    """Runs all plot entries of a config file that contain a `purity:` block."""

    def __init__(self, cfg_plots_path: str, override_version: Optional[str] = None):
        with open(cfg_plots_path, "r") as f:
            self.cfg_plots = yaml.safe_load(f)
        self.override_version = override_version
        parts = os.path.normpath(cfg_plots_path).split(os.sep)
        idx = parts.index("configs") if "configs" in parts else -1
        self.config_version = (
            parts[idx + 1] if 0 <= idx < len(parts) - 1 else "unknown_version"
        )

    def run(self) -> None:
        for plot_name, cfg_plot in self.cfg_plots.items():
            if not isinstance(cfg_plot, dict) or "purity" not in cfg_plot:
                continue
            print(
                f">>> Purity {plot_name} ({cfg_plot['purity'].get('mode', 'purity')}) "
                "<<<"
            )
            collection = PurityCollection(
                cfg_plot,
                plot_name,
                config_version=self.config_version,
                override_version=self.override_version,
            )
            try:
                collection.create()
            except FileNotFoundError as err:
                # e.g. a MinBias entry run on a version without minimum bias: skip,
                # don't stop the file
                print(f"WARNING: skipping {plot_name} on {collection.version}: {err}")
                continue
            PurityPlotter(plot_name, collection).plot()
            print(
                "INFO: purity plots in "
                f"outputs/{collection.version}/object_performance/purity"
            )

"""Plots of the b-tagging efficiencies / mis-id rates computed by `BTagCollection`.

Run through `object_performance <config>`: every plot entry with a `btag:` block is
handled here (and skipped by the efficiency plotter). Outputs go to
outputs/<version>/object_performance/btag/:
  <plot>_<flavour>_vs_<vs>_<version>.{png,pdf,json}    efficiency / mis-id rate per
                                                       flavour, all objects and WPs
  <plot>_roc_<against>_pt<lo>to<hi>_<version>.{png,pdf,json}   ROC curves, WPs marked
  <plot>_summary_<version>.{json,txt}                  rates in pt bins / eta regions
  <plot>_<version>.yaml                                copy of the plot config
"""
import json
import math
import os
from typing import Any, Optional

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import yaml

from menu_tools.object_performance.btag_collection import BTagCollection
from menu_tools.utils import utils
from menu_tools.utils.objects import Object, trigger_level
from menu_tools.utils.plotting import add_watermark

FLAVOUR_LABEL = {
    "b": "b jets",
    "c": "c jets",
    "light": "light jets",
    "pu": "pileup jets",
}
# One colour map per test object; the working points of an object are shades of it.
CMAPS = ["Blues", "Oranges", "Greens", "Purples", "Reds", "Greys"]
MARKERS = ["o", "s", "^", "v", "D", "P"]
LINESTYLES = ["-", "--", ":", "-."]


def _clean(values) -> list[Optional[float]]:
    out: list[Optional[float]] = []
    for v in values:
        v = float(v)
        out.append(None if math.isnan(v) or math.isinf(v) else v)
    return out


class BTagPlotter:
    def __init__(self, plot_name: str, collection: BTagCollection, pu_value: int = 200):
        self.plot_name = plot_name
        self.collection = collection
        self.cfg = collection.cfg_plot
        self.btag_cfg = collection.btag_cfg
        self.version = collection.version
        self.pu_value = pu_value
        self.objects = list(collection.jets)
        self.lvl = trigger_level(self.objects)

    @property
    def _outdir(self) -> str:
        return os.path.join("outputs", self.version, "object_performance", "btag")

    # ---- labels and styles ---------------------------------------------------------

    def _obj_label(self, key: str) -> str:
        return Object(key, version=self.collection.obj_version).plot_label

    def _wp_label(self, key: str, wp_key: str) -> str:
        return self.collection.wp_labels[key][wp_key]

    def _colour(self, key: str, i: int = 0, n: int = 1) -> Any:
        cmap = plt.get_cmap(CMAPS[self.objects.index(key) % len(CMAPS)])
        # darkest shade for the first curve
        return cmap(0.9 - 0.45 * i / max(n - 1, 1))

    def _flavour_ylabel(self, flavour: str) -> str:
        if flavour == "b":
            return "b-tagging efficiency"
        return f"Mis-identification rate ({FLAVOUR_LABEL[flavour]})"

    def _xlabel(self, vs: str) -> str:
        if label := self.btag_cfg.vs_label(vs):
            return label
        return {
            "pt": "Reco jet $p_T$ (GeV)",
            "genpt": "Gen jet $p_T$ (GeV)",
            "eta": r"Reco jet $\eta$",
            "abseta": r"Reco jet $|\eta|$",
            "pu": f"Pileup ({self.btag_cfg.pu_variable})",
        }[vs]

    def _definition(self) -> str:
        cfg = self.btag_cfg
        drs = sorted({j["dr"] for j in self.collection.jets.values()})
        dr = "/".join(f"{d:g}" for d in drs)
        gen = cfg.reference_gen.get("label", cfg.reference_gen["object"])
        return (
            "N(tagged) / N(reco jets of the flavour), conditional on the reco jet; "
            f"flavour: {gen} {cfg.flavour_field} within $\\Delta R$ < {dr}; "
            f"pileup: no {gen} within $\\Delta R$ < {cfg.pu_dR:g}"
        )

    def _context(self, min_pt: Optional[float], pt_bin=None) -> str:
        parts = [self.cfg.sample, rf"$|\eta|$ < {self.btag_cfg.max_abs_eta:g}"]
        if pt_bin is not None:
            lo, hi = pt_bin
            parts.append(
                rf"$p_T$ > {lo:g} GeV"
                if hi is None
                else rf"{lo:g} < $p_T$ < {hi:g} GeV"
            )
        elif min_pt is not None:
            parts.append(rf"$p_T \geq$ {min_pt:g} GeV")
        return ", ".join(parts)

    def _axes(self):
        fig, ax = plt.subplots(figsize=(10, 10))
        hep.cms.label(
            ax=ax, llabel="Phase-2 Simulation", com=14, rlabel=f"{self.pu_value} PU"
        )
        return fig, ax

    def _save(self, fig, ax, fname: str, out: dict) -> None:
        ax.text(
            0.02,
            0.98,
            self._definition(),
            transform=ax.transAxes,
            fontsize=10,
            va="top",
            wrap=True,
        )
        ax.tick_params(direction="in")
        fig.tight_layout()
        add_watermark(ax, os.path.basename(fname))
        plt.savefig(f"{fname}.png", bbox_inches="tight")
        plt.savefig(f"{fname}.pdf", bbox_inches="tight")
        plt.close(fig)
        with open(f"{fname}.json", "w") as f:
            json.dump(out, f, indent=4)

    # ---- efficiency vs x -----------------------------------------------------------

    @utils.ignore_warnings
    def _plot_eff(self, plot: dict) -> None:
        if not plot["series"]:
            return
        flavour, vs = plot["flavour"], plot["vs"]
        edges = np.asarray(plot["edges"], dtype=float)
        x, xerr = 0.5 * (edges[1:] + edges[:-1]), 0.5 * np.diff(edges)
        fname = os.path.join(
            self._outdir, f"{self.plot_name}_{flavour}_vs_{vs}_{self.version}"
        )
        fig, ax = self._axes()
        out: dict[str, Any] = {
            "watermark": os.path.basename(fname),
            "sample": self.cfg.sample,
            "flavour": flavour,
            "vs": vs,
            "definition": self._definition(),
            "xlabel": self._xlabel(vs),
            "ylabel": self._flavour_ylabel(flavour),
            "min_pt": plot["min_pt"],
            "max_abs_eta": self.btag_cfg.max_abs_eta,
            "n_events": self.collection.n_events,
            "pileup_source": self.collection.pileup_source if vs == "pu" else None,
        }
        for key in self.objects:
            wps = [k for (o, k) in plot["series"] if o == key]
            for i, wp_key in enumerate(wps):
                s = plot["series"][(key, wp_key)]
                label = self._wp_label(key, wp_key)
                ax.errorbar(
                    x,
                    s["y"],
                    yerr=[s["err_lo"], s["err_hi"]],
                    xerr=xerr,
                    label=label,
                    color=self._colour(key, i, len(wps)),
                    marker=MARKERS[i % len(MARKERS)],
                    markersize=7,
                    capsize=3,
                    linestyle="none",
                )
                out[f"{key}|{wp_key}"] = {
                    "object": key,
                    "working_point": wp_key,
                    "label": label,
                    "edges": edges.tolist(),
                    "xbins": x.tolist(),
                    "y": _clean(s["y"]),
                    "err_lo": _clean(s["err_lo"]),
                    "err_hi": _clean(s["err_hi"]),
                    "num": [int(v) for v in s["num"]],
                    "den": [int(v) for v in s["den"]],
                }
        ax.set_xlabel(self._xlabel(vs))
        ax.set_ylabel(self._flavour_ylabel(flavour))
        ax.set_xlim(edges[0], edges[-1])
        ys = [np.asarray(s["y"], float) for s in plot["series"].values()]
        y = np.concatenate(ys) if ys else np.zeros(0)
        y = y[np.isfinite(y) & (y > 0)]
        # room above the curves for the definition text and the legend
        room = 0.08 + 0.04 * (len(plot["series"]) + 1)
        if flavour == "b" or not len(y):
            ax.set_ylim(0, 1.05 / (1 - room))
            ax.axhline(1, ls=":", c="k", lw=0.8)
        else:
            ax.set_yscale("log")
            lo, hi = max(y.min() / 3, 1e-5), min(y.max() * 1.5, 1.5)
            ax.set_ylim(lo, hi * (hi / lo) ** (room / (1 - room)))
        ax.legend(
            loc="upper right",
            bbox_to_anchor=(1, 0.93),
            frameon=False,
            fontsize=13,
            title=self._context(plot["min_pt"]),
            title_fontsize=15,
        )
        self._save(fig, ax, fname, out)

    # ---- ROC -----------------------------------------------------------------------

    @utils.ignore_warnings
    def _plot_roc(self, roc: dict) -> None:
        against, pt_bin = roc["against"], roc["pt_bin"]
        fname = os.path.join(
            self._outdir,
            f"{self.plot_name}_roc_{against}_{self.collection.bin_label(pt_bin)}"
            f"_{self.version}",
        )
        fig, ax = self._axes()
        out: dict[str, Any] = {
            "watermark": os.path.basename(fname),
            "sample": self.cfg.sample,
            "against": against,
            "pt_bin": list(pt_bin),
            "eta_region": list(roc["eta_region"]) if roc["eta_region"] else None,
            "definition": self._definition(),
            "curves": {},
            "working_points": {},
            "target_misid": [],
        }
        ymin = 1.0
        for key in self.objects:
            names = [n for (o, n) in roc["curves"] if o == key]
            for i, name in enumerate(names):
                c = roc["curves"][(key, name)]
                label = self._obj_label(key) + (f" ({name})" if name else "")
                ok = np.isfinite(c["eff_b"]) & np.isfinite(c["misid"])
                ax.plot(
                    c["eff_b"][ok],
                    c["misid"][ok],
                    color=self._colour(key),
                    ls=LINESTYLES[i % len(LINESTYLES)],
                    lw=2,
                    label=f"{label}: {c['n_b']} b, {c['n_x']} {against}",
                )
                pos = c["misid"][ok]
                if np.any(pos > 0):
                    ymin = min(ymin, pos[pos > 0].min())
                out["curves"][f"{key}|{name}"] = {
                    "object": key,
                    "discriminant": name or None,
                    "expression": self.btag_cfg.discriminants[key][name],
                    "label": label,
                    "n_b": c["n_b"],
                    "n_misid": c["n_x"],
                    "threshold": _clean(c["threshold"]),
                    "eff_b": _clean(c["eff_b"]),
                    "misid": _clean(c["misid"]),
                }
            wps = [k for (o, k) in roc["wps"] if o == key]
            for i, wp_key in enumerate(wps):
                w = roc["wps"][(key, wp_key)]
                label = self._wp_label(key, wp_key)
                ax.errorbar(
                    [w["eff_b"]],
                    [w["misid"]],
                    xerr=np.array([w["eff_b_err"]]).T,
                    yerr=np.array([w["misid_err"]]).T,
                    color=self._colour(key, i, len(wps)),
                    marker=MARKERS[i % len(MARKERS)],
                    markersize=10,
                    markeredgecolor="k",
                    linestyle="none",
                    label=f"WP: {label}",
                )
                out["working_points"][f"{key}|{wp_key}"] = {"label": label, **w}
        for (key, name, target), t in roc["targets"].items():
            out["target_misid"].append(
                {"object": key, "discriminant": name or None, "target": target, **t}
            )
        ax.set_xlabel("b-tagging efficiency")
        ax.set_ylabel(f"Mis-identification rate ({FLAVOUR_LABEL[against]})")
        ax.set_xlim(0, 1)
        ax.set_yscale("log")
        ax.set_ylim(max(ymin / 2, 1e-4), 50)
        ax.grid(True, which="major", ls=":", lw=0.5)
        ax.legend(
            loc="upper left",
            bbox_to_anchor=(0, 0.93),
            frameon=False,
            fontsize=12,
            title=self._context(None, pt_bin),
            title_fontsize=14,
        )
        self._save(fig, ax, fname, out)

    # ---- summary -------------------------------------------------------------------

    def _summary_text(self) -> str:
        lines = [
            f"{self.plot_name} ({self.cfg.sample}, {self.version}): "
            "tagged fraction per truth category, conditional on the reco jet",
            self._definition().replace("$\\Delta R$", "dR"),
            "",
        ]
        head = f"{'object':<40} {'working point':<38} {'eta':<10} {'pt bin':<10}"
        lines.append(head + "".join(f" {f:>26}" for f in self.btag_cfg.flavours))
        rows: dict[tuple, dict[str, dict]] = {}
        for r in self.collection.summary:
            k = (r["object"], r["wp"], r["eta_region"], tuple(r["pt_bin"]))
            rows.setdefault(k, {})[r["flavour"]] = r
        for (obj, wp, region, (lo, hi)), by_f in rows.items():
            pt = f"{lo:g}-{'inf' if hi is None else f'{hi:g}'}"
            line = f"{obj:<40} {wp:<38} {region:<10} {pt:<10}"
            for f in self.btag_cfg.flavours:
                row = by_f.get(f)
                if row is None or row["den"] == 0:
                    line += f" {'-':>26}"
                    continue
                err = 0.5 * (row["err_lo"] + row["err_hi"])
                cell = f"{row['eff']:.4f} +- {err:.4f} ({row['den']})"
                line += f" {cell:>26}"
            lines.append(line)
        lines += ["", "jets per category:"]
        for obj, counts in self.collection.category_counts().items():
            lines.append(f"  {obj}: {counts}")
        return "\n".join(lines) + "\n"

    def _save_summary(self) -> None:
        base = os.path.join(self._outdir, f"{self.plot_name}_summary_{self.version}")
        out = {
            "sample": self.cfg.sample,
            "definition": self._definition(),
            "n_events": self.collection.n_events,
            "category_counts": self.collection.category_counts(),
            "rows": self.collection.summary,
            "target_misid": [
                {
                    "object": key,
                    "discriminant": name or None,
                    "against": roc["against"],
                    "pt_bin": list(roc["pt_bin"]),
                    "target": target,
                    **t,
                }
                for roc in self.collection.rocs
                for (key, name, target), t in roc["targets"].items()
            ],
        }
        with open(f"{base}.json", "w") as f:
            json.dump(out, f, indent=4)
        text = self._summary_text()
        with open(f"{base}.txt", "w") as f:
            f.write(text)
        print(text)

    def plot(self) -> None:
        os.makedirs(self._outdir, exist_ok=True)
        for plot in self.collection.eff_plots:
            self._plot_eff(plot)
        for roc in self.collection.rocs:
            self._plot_roc(roc)
        self._save_summary()
        cfg_out = os.path.join(self._outdir, f"{self.plot_name}_{self.version}.yaml")
        with open(cfg_out, "w") as f:
            yaml.dump(
                {self.plot_name: self.cfg.config_dict}, f, default_flow_style=False
            )


class BTagCentral:
    """Runs all plot entries of a config file that contain a `btag:` block."""

    def __init__(self, cfg_plots_path: str, override_version: Optional[str] = None):
        with open(cfg_plots_path, "r") as f:
            self.cfg_plots = yaml.safe_load(f)
        self.override_version = override_version
        parts = os.path.normpath(cfg_plots_path).split(os.sep)
        idx = parts.index("configs") if "configs" in parts else -1
        has_version = 0 <= idx < len(parts) - 1
        self.config_version = parts[idx + 1] if has_version else "unknown_version"

    def run(self) -> None:
        for plot_name, cfg_plot in self.cfg_plots.items():
            if not isinstance(cfg_plot, dict) or "btag" not in cfg_plot:
                continue
            print(f">>> b-tag {plot_name} <<<")
            collection = BTagCollection(
                cfg_plot,
                plot_name,
                config_version=self.config_version,
                override_version=self.override_version,
            )
            try:
                collection.create()
            except FileNotFoundError as err:
                print(f"WARNING: skipping {plot_name} on {collection.version}: {err}")
                continue
            BTagPlotter(plot_name, collection).plot()
            print(
                f"INFO: b-tag plots in outputs/{collection.version}"
                "/object_performance/btag"
            )

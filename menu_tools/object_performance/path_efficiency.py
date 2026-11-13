"""Efficiencies of L1 seeds and HLT paths (trigger bits) vs a reference (gen) quantity.

Plot entries with a top-level `path_efficiency:` block are handled here (and skipped by
the turn-on / scaling plotters). Example:

    IsoMu24PathEff:
      sample: DYLL_M50
      version: V50nano
      reference_object:                      # as in the turn-on configs
        object: GenPart
        x_arg: pt
        label: "Gen muon"
        cuts:
          object:
            ["abs({pdgId}) == 13", "(({statusFlags}>>7)&1) == 1", "abs({eta}) < 2.4"]
        # rank: 2              # x of the 2nd-highest-pT reference object (default 1)
      path_efficiency:
        L1: [L1_pSingleTkMuon22_final]       # OR of the listed L1 seeds
        HLT: [HLT_IsoMu24_FromL1TkMuon]      # OR of the listed HLT paths
        curves: [L1, HLT, L1_and_HLT]  # also: HLT_given_L1 (denominator: L1 fired)
        # labels: {L1: "...", ...}           # optional legend labels
        # optional: integrated efficiency for x >= plateau_min
        # plateau_min: 30
      binning: {min: 0, max: 100, step: 2}   # or {edges: [...]}
      xlabel: "Gen muon $p_T$ (GeV)"
      ylabel: "Efficiency"

The reference selection is the one of `TurnOnCollection` (object cuts, then the leading
object, then event cuts on it; `trafo: HT/MHT` and MET references are event-level). The
efficiency is per event: denominator = events with a reference object in the bin,
numerator = those in which the OR of the listed bits fired. No matching between the
trigger objects and the reference.

The bits are read directly from the cached per-event records
`<version>_<sample>_L1.parquet` (L1_* fields) and `<version>_<sample>_HLT.parquet`
(HLT_* fields).

Outputs:
outputs/<version>/object_performance/path_efficiency/<plot>_<version>.{png,pdf,json,yaml}

Several groups of bits (e.g. two HLT paths with the same L1 seed) in one plot: replace
`L1` / `HLT` / `labels` by a `paths:` map, group name -> {L1, HLT, curves, labels}
(`curves` defaults to the top-level one). The curves are then keyed `<group>:<curve>`
in the JSON:

      path_efficiency:
        paths:
          DeepTau:
            L1: [L1_pDoublePuppiTau52_52_final]
            HLT: [HLT_DoubleMediumDeepTauPFTauHPS35_eta2p1]
            curves: [L1, L1_and_HLT]
            labels: {L1: "L1 seed", L1_and_HLT: "DeepTau path"}
          ParT:
            L1: [L1_pDoublePuppiTau52_52_final]
            HLT: [HLT_DoubleMediumPFPuppiParTTauh30_eta2p1]
            curves: [L1_and_HLT]

Other options:
  * `reference_object.min_objects: n`: only events with at least n reference objects
    (after the object cuts), e.g. the leading tau pT of di-tau events.
  * `reference_object.x_arg: "abs(eta)"`: the absolute value of a reference field.
  * `path_efficiency.event_x: Pileup_nTrueInt`: x is the per-event branch
    `<object>_<field>` (from `<version>_<sample>_<object>.parquet`) of the events
    with a reference object (e.g. efficiency vs pileup); the reference selection is
    unchanged.
  * `split_by` (split.py): the same curves per event category, from the split field of
    the reference object at `rank`, or with `split_by.objects: n` from the combination
    of the categories of the n leading reference objects (e.g. the decay-mode pair of
    the two leading taus). Outputs `<plot><tag>_<category or curve>_<version>.*` and
    `<plot><tag>_fractions_<version>.json`.
"""
import json
import os
import re
from typing import Any, Optional

import awkward as ak
import matplotlib.pyplot as plt
import numpy as np
import yaml

from menu_tools.object_performance.plotter import Plotter
from menu_tools.object_performance.resolution_collection import make_edges
from menu_tools.object_performance.split import (
    OTHER,
    SplitConfig,
    assign_events,
    event_categories,
    integrated_efficiency,
    safe_name,
)
from menu_tools.object_performance.turnon_collection import (
    ArrayLoader,
    TurnOnCollection,
)
from menu_tools.utils import constants
from menu_tools.utils import utils
from menu_tools.utils.plotting import add_watermark
from menu_tools.utils.sample_labels import legend_title


CURVES = ("L1", "HLT", "L1_and_HLT", "HLT_given_L1")
DEFAULT_LABELS = {"L1_and_HLT": "L1 and HLT", "HLT_given_L1": "HLT | L1 fired"}
# Distinct markers, L1_and_HLT open, so that coinciding curves (e.g. HLT = L1_and_HLT
# when the HLT bit already contains its L1 seed) stay visible.
MARKERS: dict[str, dict[str, Any]] = {
    "L1": {"marker": "o"},
    "HLT": {"marker": "s"},
    "L1_and_HLT": {"marker": "^", "markersize": 12, "markerfacecolor": "none"},
    "HLT_given_L1": {"marker": "v"},
}
# Markers of the 2nd, 3rd, ... group of a `paths:` map (fill style kept per curve type)
GROUP_MARKERS = ("D", "P", "X", "*", "h", "<", ">")
ABS_RE = re.compile(r"^abs\((\w+)\)$")


def _bit_file(bit: str) -> str:
    """Name of the cached record holding a bit: `L1` for L1_* seeds, `HLT` for HLT_*
    paths.
    """
    for prefix in ("L1", "HLT"):
        if bit.startswith(prefix + "_"):
            return prefix
    raise ValueError(f"Trigger bit '{bit}' must start with 'L1_' or 'HLT_'")


def _parse_group(
    entry: dict[str, Any], default_curves: Optional[list], where: str
) -> dict[str, Any]:
    """{bits: {L1, HLT}, curves, labels} of one group of bits, validated."""
    bits = {level: list(entry.get(level) or []) for level in ("L1", "HLT")}
    curves = list(
        entry.get("curves")
        or default_curves
        or [lvl for lvl in ("L1", "HLT") if bits[lvl]]
    )
    for curve in curves:
        if curve not in CURVES:
            raise ValueError(f"{where}: unknown curve '{curve}' (known: {CURVES})")
        needed = ("L1", "HLT") if curve in ("L1_and_HLT", "HLT_given_L1") else (curve,)
        for level in needed:
            if not bits[level]:
                raise ValueError(
                    f"{where}: curve '{curve}' needs a non-empty '{level}' list"
                )
    return {"bits": bits, "curves": curves, "labels": dict(entry.get("labels") or {})}


class PathEfficiencyCollection(TurnOnCollection):
    """Per-event efficiency of OR-ed trigger bits vs the reference object's x_arg."""

    def __init__(
        self,
        cfg_plot: dict,
        plot_name: Optional[str] = None,
        config_version: Optional[str] = None,
        override_version: Optional[str] = None,
    ):
        super().__init__(
            cfg_plot,
            -999,
            plot_name,
            config_version=config_version,
            override_version=override_version,
        )
        self.pe_cfg: dict[str, Any] = cfg_plot["path_efficiency"]
        # group name -> {bits, curves, labels}; "" for the single-group syntax
        self.groups: dict[str, dict[str, Any]] = {}
        if "paths" in self.pe_cfg:
            clash = [k for k in ("L1", "HLT", "labels") if k in self.pe_cfg]
            if clash:
                raise ValueError(f"{plot_name}: `paths` replaces {clash}")
            paths = self.pe_cfg["paths"]
            if not isinstance(paths, dict) or not paths:
                raise ValueError(f"{plot_name}: `paths` must be a non-empty mapping")
            for name, entry in paths.items():
                name = str(name)
                if not name or ":" in name or not isinstance(entry, dict):
                    raise ValueError(
                        f"{plot_name}: path group '{name}' needs a name without ':' "
                        "and a mapping {L1, HLT, curves, labels}"
                    )
                self.groups[name] = _parse_group(
                    entry, self.pe_cfg.get("curves"), f"{plot_name} [{name}]"
                )
        else:
            self.groups[""] = _parse_group(
                self.pe_cfg, self.pe_cfg.get("curves"), str(plot_name)
            )
        # curve key -> (group, curve type); key = curve type for the single group
        self.curve_types: dict[str, tuple[str, str]] = {}
        for group, spec in self.groups.items():
            for curve in spec["curves"]:
                key = f"{group}:{curve}" if group else curve
                self.curve_types[key] = (group, curve)
        self.curves: list[str] = list(self.curve_types)
        ref_cfg = cfg_plot["reference_object"]
        rank = ref_cfg.get("rank", 1)
        if int(rank) < 1:
            raise ValueError(f"{plot_name}: reference_object rank must be >= 1")
        self.ref_rank = int(rank)
        self.min_objects = int(ref_cfg.get("min_objects", 1))
        self.split: Optional[SplitConfig] = self.cfg_plot.split_by
        # reference x per event (nan: no reference object)
        self.x: Optional[np.ndarray] = None
        # group -> "L1"/"HLT" -> per-event OR of the bits
        self.fired: dict[str, dict[str, np.ndarray]] = {}
        # reference objects after the object cuts, pT-ordered (None: event-level ref.)
        self._ref_objects: Optional[ak.Array] = None
        # `split_by`: event category per event, histograms per category
        self.category: Optional[np.ndarray] = None
        self.split_hists: dict[str, dict[str, Any]] = {}

    @property
    def bit_groups(self) -> dict[str, Any]:
        """The bits ({L1, HLT}; per group name for a `paths:` map)."""
        if "" in self.groups:
            return self.groups[""]["bits"]
        return {g: spec["bits"] for g, spec in self.groups.items()}

    @property
    def bins(self) -> np.ndarray:
        return make_edges(self.cfg_plot.config_dict["binning"])

    def label(self, key: str) -> str:
        group, curve = self.curve_types[key]
        labels = self.groups[group]["labels"]
        if curve in labels:
            return labels[curve]
        if curve in DEFAULT_LABELS:
            text = DEFAULT_LABELS[curve]
        else:
            names = [
                b.removeprefix(curve + "_").removesuffix("_final")
                for b in self.groups[group]["bits"][curve]
            ]
            text = f"{curve}: " + " OR ".join(names)
        return f"{group}, {text}" if group else text

    def marker(self, key: str) -> dict[str, Any]:
        group, curve = self.curve_types[key]
        style = dict(MARKERS[curve])
        i = list(self.groups).index(group)
        if i > 0:
            style["marker"] = GROUP_MARKERS[(i - 1) % len(GROUP_MARKERS)]
        return style

    # --- reference: the TurnOnCollection selection, without test objects --------------

    def _reduce_to_per_event(self):
        """No test objects to reduce."""

    def _select_highest_pt_ref_object(self):
        """Keeps the `rank`-th highest-pT reference object.

        Rank 1 = leading, as in turn-ons.

        Events with fewer reference objects keep none. All reference objects (after the
        object cuts, pT-ordered) are kept in `_ref_objects` (`min_objects`, `split_by`).
        """
        order = ak.argsort(self.ak_arrays["ref"]["pt"], axis=-1, ascending=False)
        self._ref_objects = self.ak_arrays["ref"][order]
        if self.ref_rank == 1:
            return super()._select_highest_pt_ref_object()
        self.ak_arrays["ref"] = self.ak_arrays["ref"][
            order[:, self.ref_rank - 1 : self.ref_rank]
        ]

    def _reference_x(self) -> np.ndarray:
        field = self.cfg_plot.reference_trafo or self.cfg_plot.reference_field
        take_abs = False
        if (m := ABS_RE.match(field)) is not None:
            field, take_abs = m.group(1), True
        x = self.ak_arrays["ref"][field]
        if x.ndim > 1:
            x = ak.firsts(x, axis=-1)
            while x.ndim > 1:
                x = ak.firsts(x, axis=-1)
        x = ak.to_numpy(ak.fill_none(x, np.nan)).astype(float)
        return np.abs(x) if take_abs else x

    def _apply_min_objects(self) -> None:
        if self.min_objects <= 1:
            return
        if self._ref_objects is None:
            raise ValueError("min_objects needs a reference object collection")
        assert self.x is not None
        n = ak.to_numpy(ak.num(self._ref_objects, axis=1))
        self.x[n < self.min_objects] = np.nan

    def _apply_event_x(self) -> None:
        """x = the per-event branch `event_x` for the events with a reference."""
        branch = self.pe_cfg.get("event_x")
        if not branch:
            return
        assert self.x is not None
        obj = str(branch).split("_")[0]
        cfg = self.cfg_plot
        fname = (
            f"{constants.CACHE_DIR}/{cfg.version}/{cfg.version}_{cfg.sample}_{obj}"
            ".parquet"
        )
        arr = ak.from_parquet(fname, columns=[branch])
        if branch not in arr.fields:
            raise KeyError(f"{branch} not in {fname}")
        vals = ak.to_numpy(ak.fill_none(arr[branch], np.nan)).astype(float)
        if vals.ndim != 1 or len(vals) != len(self.x):
            raise ValueError(
                f"event_x {branch} must be one value per event ({len(self.x)} events)"
            )
        self.x = np.where(np.isfinite(self.x), vals, np.nan)

    def _assign_categories(self) -> None:
        split = self.split
        if split is None:
            return
        if self._ref_objects is None:
            raise ValueError("split_by needs a reference object collection")
        if split.field not in self._ref_objects.fields:
            raise KeyError(
                f"split_by: reference {self.cfg_plot.reference_object} has no field "
                f"`{split.field}` (fields: {self._ref_objects.fields})"
            )
        if split.objects is None:  # the reference object at `rank` (the x object)
            values = self.ak_arrays["ref"][split.field]
            self.category = assign_events(split, values, 1)
        else:
            values = self._ref_objects[split.field]
            self.category = assign_events(split, values, split.objects)

    # --- trigger bits -----------------------------------------------------------------

    def _load_bits(self) -> None:
        cfg = self.cfg_plot
        by_file: dict[str, list[str]] = {}
        for spec in self.groups.values():
            for bits in spec["bits"].values():
                for bit in bits:
                    fields = by_file.setdefault(_bit_file(bit), [])
                    if bit not in fields:
                        fields.append(bit)
        values: dict[str, np.ndarray] = {}
        for fname_obj, fields in by_file.items():
            fname = (
                f"{constants.CACHE_DIR}/{cfg.version}/{cfg.version}_"
                f"{cfg.sample}_{fname_obj}.parquet"
            )
            arr = ak.from_parquet(fname, columns=fields)
            missing = [b for b in fields if b not in arr.fields]
            if missing:
                raise KeyError(f"{missing} not in {fname}")
            for bit in fields:
                values[bit] = ak.to_numpy(ak.fill_none(arr[bit], False)).astype(bool)
        for group, spec in self.groups.items():
            self.fired[group] = {}
            for level, bits in spec["bits"].items():
                if not bits:
                    continue
                fired = values[bits[0]].copy()
                for bit in bits[1:]:
                    fired |= values[bit]
                self.fired[group][level] = fired

    # --- histograms -------------------------------------------------------------------

    def _pass_and_den(
        self, key: str, mask: Optional[np.ndarray] = None
    ) -> tuple[np.ndarray, np.ndarray]:
        assert self.x is not None
        group, curve = self.curve_types[key]
        fired = self.fired[group]
        den = np.isfinite(self.x)
        if mask is not None:
            den = den & mask
        if curve == "L1_and_HLT":
            return fired["L1"] & fired["HLT"], den
        if curve == "HLT_given_L1":
            return fired["HLT"], den & fired["L1"]
        return fired[curve], den

    def category_mask(self, category: str) -> np.ndarray:
        assert self.category is not None
        return self.category == category

    def _fill(self, hists: dict[str, Any], mask: Optional[np.ndarray] = None) -> None:
        assert self.x is not None
        hists.setdefault("ref", {})
        for key in self.curves:
            passed, den = self._pass_and_den(key, mask)
            hists["ref"][key] = np.histogram(self.x[den], bins=self.bins)
            hists[key] = np.histogram(self.x[den & passed], bins=self.bins)

    def _skim(self) -> None:
        self._fill(self.hists)
        if self.split is not None:
            self.split_hists = {}
            for cat in event_categories(self.split):
                self.split_hists[cat] = {"ref": {}}
                self._fill(self.split_hists[cat], self.category_mask(cat))

    def plateau(
        self, key: str, mask: Optional[np.ndarray] = None
    ) -> Optional[dict[str, Any]]:
        """Integrated efficiency for x >= plateau_min (None if not configured)."""
        xmin = self.pe_cfg.get("plateau_min")
        if xmin is None:
            return None
        passed, den = self._pass_and_den(key, mask)
        assert self.x is not None
        sel = den & (self.x >= float(xmin))
        n, k = int(sel.sum()), int((sel & passed).sum())
        out: dict[str, Any] = {"x_min": float(xmin), "n_pass": k, "n_total": n}
        if n == 0:  # e.g. an empty category
            return {**out, "efficiency": None, "efficiency_err": [None, None]}
        err = utils.clopper_pearson_err([k], [n])
        return {
            **out,
            "efficiency": k / n,
            "efficiency_err": [float(err[0][0]), float(err[1][0])],
        }

    def create_hists(self) -> None:
        loader = ArrayLoader(self, self.cfg_plot)
        loader._load_ref_branches()
        self._apply_reference_cuts()
        self._apply_reference_trafo()
        self.x = self._reference_x()
        self._apply_min_objects()
        self._apply_event_x()
        self._assign_categories()
        self._load_bits()
        for group, fired_group in self.fired.items():
            for level, fired in fired_group.items():
                if len(fired) != len(self.x):
                    raise ValueError(
                        f"{level} bits have {len(fired)} events, the reference "
                        f"{len(self.x)}: "
                        "the caches are not event-aligned"
                    )
        self._skim()


class PathEfficiencyPlotter(Plotter):
    def __init__(
        self, plot_name: str, collection: PathEfficiencyCollection, pu_value: int = 200
    ):
        self.plot_name = plot_name
        self.collection = collection
        self.cfg = collection.cfg_plot
        self.version = collection.version
        self.pu_value = pu_value

    @property
    def _outdir(self) -> str:
        return os.path.join(
            "outputs", self.version, "object_performance", "path_efficiency"
        )

    def _curve_data(
        self,
        key: str,
        hists: Optional[dict[str, Any]] = None,
        label: Optional[str] = None,
        style: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        hists = self.collection.hists if hists is None else hists
        edges = self.collection.bins
        eff, err = self.collection.get_efficiency(key, hists)
        ok = np.isfinite(eff)
        x = 0.5 * (edges[1:] + edges[:-1])
        xerr = 0.5 * np.diff(edges)
        return {
            "label": self.collection.label(key) if label is None else label,
            "xbins": x[ok].tolist(),
            "efficiency": eff[ok].tolist(),
            "efficiency_err": [err[0][ok].tolist(), err[1][ok].tolist()],
            "n_pass": hists[key][0][ok].tolist(),
            "n_total": hists["ref"][key][0][ok].tolist(),
            "err_kwargs": {
                "xerr": xerr[ok].tolist(),
                "capsize": 3,
                "markersize": 8,
                **(self.collection.marker(key) if style is None else style),
            },
        }

    def _header(self) -> dict[str, Any]:
        return {
            "xlabel": self.cfg.xlabel,
            "ylabel": self.cfg.ylabel,
            "watermark": f"{self.version}_{self.plot_name}",
            "reference": self.cfg.reference_label,
            "bits": self.collection.bit_groups,
        }

    def _draw(
        self, curves: list[dict[str, Any]], title: str, suffix: str, out: dict
    ) -> None:
        """One plot of the curve data `curves`, saved as <plot><suffix>_<version>;
        legend title: the sample label and `title`."""
        # the legend spans the top of the plot: wider title lines than the default
        title = legend_title(self.cfg.sample_label, title, width=50) or ""
        fig, ax = self._create_new_plot()
        for data in curves:
            ax.errorbar(
                data["xbins"],
                data["efficiency"],
                yerr=data["efficiency_err"],
                label=data["label"],
                linestyle="none",
                **data["err_kwargs"],
            )

        ax.axhline(1, ls=":", c="k")
        # Legend above the plateau: turn-ons fill the lower right, so leave headroom
        # instead.
        ax.legend(
            loc="upper left",
            frameon=False,
            title=title,
            fontsize=16,
            title_fontsize=18,
        )
        ax.set_xlabel(rf"{self.cfg.xlabel}")
        ax.set_ylabel(rf"{self.cfg.ylabel}")
        edges = self.collection.bins
        ax.set_xlim(edges[0], edges[-1])
        n_title = title.count("\n") + 1
        ax.set_ylim(0, 1.15 + 0.07 * (len(curves) + n_title))
        ax.tick_params(direction="in")
        fig.tight_layout()
        add_watermark(ax, f"{self.version}_{self.plot_name} ({self.pu_value})")

        fname = os.path.join(self._outdir, f"{self.plot_name}{suffix}_{self.version}")
        plt.savefig(f"{fname}.png")
        plt.savefig(f"{fname}.pdf", bbox_inches="tight")
        plt.close(fig)
        with open(f"{fname}.json", "w") as f:
            f.write(json.dumps(out, indent=4))

    @utils.ignore_warnings
    def plot(self) -> dict[str, Any]:
        os.makedirs(self._outdir, exist_ok=True)
        out = self._header()
        curves = []
        for key in self.collection.curves:
            data = self._curve_data(key)
            if (plateau := self.collection.plateau(key)) is not None:
                data["plateau"] = plateau
            out[key] = data
            curves.append(data)
        self._draw(curves, self.cfg.reference_label, "", out)
        fname = os.path.join(self._outdir, f"{self.plot_name}_{self.version}")
        with open(f"{fname}.yaml", "w") as f:
            yaml.dump(
                {self.plot_name: self.cfg.config_dict}, f, default_flow_style=False
            )
        if self.collection.split is not None:
            out["split"] = self._plot_split()
        return out

    # --- split_by ---------------------------------------------------------------------

    def _plot_split(self) -> dict[str, Any]:
        """Plots per category (`per_category`) or per curve (`per_object`) and the
        category table `<plot><tag>_fractions_<version>.json` (returned)."""
        coll = self.collection
        split = coll.split
        assert split is not None
        if split.layout == "per_category":
            for cat, hists in coll.split_hists.items():
                mask = coll.category_mask(cat)
                out = {**self._header(), "category": cat}
                curves = []
                for key in coll.curves:
                    data = self._curve_data(key, hists)
                    if (plateau := coll.plateau(key, mask)) is not None:
                        data["plateau"] = plateau
                    out[key] = data
                    curves.append(data)
                title = f"{self.cfg.reference_label}\n{cat}"
                self._draw(curves, title, f"{split.tag}_{safe_name(cat)}", out)
        else:
            for key in coll.curves:
                n_all = coll.hists["ref"][key][0].sum()
                out = {**self._header(), "curve": key}
                style = {"marker": "o"}
                data = self._curve_data(key, label="All", style={**style, "color": "k"})
                if (plateau := coll.plateau(key)) is not None:
                    data["plateau"] = plateau
                out["inclusive"] = data
                curves = [data]
                for i, (cat, hists) in enumerate(coll.split_hists.items()):
                    frac = hists["ref"][key][0].sum() / n_all if n_all else 0.0
                    data = self._curve_data(
                        key, hists, f"{cat} ({frac:.0%})", {**style, "color": f"C{i}"}
                    )
                    if (
                        plateau := coll.plateau(key, coll.category_mask(cat))
                    ) is not None:
                        data["plateau"] = plateau
                    out[cat] = data
                    curves.append(data)
                self._draw(
                    curves, coll.label(key), f"{split.tag}_{safe_name(key)}", out
                )

        fractions = self._split_fractions()
        fname = os.path.join(
            self._outdir, f"{self.plot_name}{split.tag}_fractions_{self.version}"
        )
        with open(f"{fname}.json", "w") as f:
            f.write(json.dumps(fractions, indent=4))
        return fractions

    def _split_fractions(self) -> dict[str, Any]:
        """Event categories (all events with a reference x) and, per curve and
        category, the denominator, its fraction, the efficiency integrated over
        `summary_range` (default: the binning) and the plateau (`plateau_min`)."""
        coll = self.collection
        split = coll.split
        assert split is not None and coll.category is not None and coll.x is not None
        bins = coll.bins
        has_x = np.isfinite(coll.x)
        n_ref = int(has_x.sum())
        cats = list(coll.split_hists) + [OTHER]
        reference: dict[str, Any] = {"n": n_ref, "categories": {}}
        for cat in cats:
            k = int((has_x & coll.category_mask(cat)).sum())
            reference["categories"][cat] = {
                "n": k,
                "fraction": k / n_ref if n_ref else None,
            }
        out: dict[str, Any] = {
            **self._header(),
            "field": split.field,
            "categories": split.categories,
            "objects": split.objects,
            "summary_range": list(split.summary_range or (bins[0], bins[-1])),
            "reference": reference,
            "curves": {},
        }
        for key in coll.curves:
            entry: dict[str, Any] = {"label": coll.label(key)}
            groups: list[tuple[str, dict[str, Any], Optional[np.ndarray]]] = [
                ("inclusive", coll.hists, None)
            ]
            groups += [
                (cat, hists, coll.category_mask(cat))
                for cat, hists in coll.split_hists.items()
            ]
            groups.append((OTHER, {}, coll.category_mask(OTHER)))
            for name, hists, mask in groups:
                if name == OTHER:
                    passed, den = coll._pass_and_den(key, mask)
                    hists = {"ref": {key: np.histogram(coll.x[den], bins=bins)}}
                    hists[key] = np.histogram(coll.x[den & passed], bins=bins)
                entry[name] = integrated_efficiency(
                    hists[key][0], hists["ref"][key][0], bins, split.summary_range
                )
                if (plateau := coll.plateau(key, mask)) is not None:
                    entry[name]["plateau"] = plateau
            n_den = entry["inclusive"]["n_den"]
            for name, _, _ in groups:
                entry[name]["fraction"] = (
                    entry[name]["n_den"] / n_den if n_den else None
                )
            out["curves"][key] = entry
        return out


class PathEfficiencyCentral:
    """Runs all plot entries of a config file that contain a
    `path_efficiency:` block.
    """

    def __init__(self, cfg_plots_path: str, override_version: Optional[str] = None):
        with open(cfg_plots_path, "r") as f:
            self.cfg_plots = yaml.safe_load(f)
        self.override_version = override_version
        parts = os.path.normpath(cfg_plots_path).split(os.sep)
        idx = parts.index("configs") if "configs" in parts else -1
        self.config_version = (
            parts[idx + 1] if 0 <= idx < len(parts) - 1 else "unknown_version"
        )

    @staticmethod
    def _print_plateau(name: str, p: dict[str, Any]) -> None:
        if not p["n_total"]:
            return
        print(
            f"  {name:13s} x >= {p['x_min']:g}: {p['efficiency']:.3f} "
            f"+{p['efficiency_err'][1]:.3f} -{p['efficiency_err'][0]:.3f} "
            f"({p['n_pass']}/{p['n_total']})"
        )

    def run(self) -> None:
        for plot_name, cfg_plot in self.cfg_plots.items():
            if not isinstance(cfg_plot, dict) or "path_efficiency" not in cfg_plot:
                continue
            print(f">>> Path efficiency {plot_name} <<<")
            collection = PathEfficiencyCollection(
                cfg_plot,
                plot_name,
                config_version=self.config_version,
                override_version=self.override_version,
            )
            collection.create_hists()
            out = PathEfficiencyPlotter(plot_name, collection).plot()
            for key in collection.curves:
                if (p := out[key].get("plateau")) is not None:
                    self._print_plateau(key, p)
            for key, entry in out.get("split", {}).get("curves", {}).items():
                for cat in list(collection.split_hists) + [OTHER]:
                    if (p := entry[cat].get("plateau")) is not None:
                        self._print_plateau(f"{key} [{cat}]", p)
            print(
                "INFO: path efficiencies in "
                f"outputs/{collection.version}/object_performance/path_efficiency"
            )

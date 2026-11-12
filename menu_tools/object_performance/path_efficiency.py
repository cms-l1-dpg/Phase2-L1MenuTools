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
"""
import json
import os
from typing import Any, Optional

import awkward as ak
import matplotlib.pyplot as plt
import numpy as np
import yaml

from menu_tools.object_performance.plotter import Plotter
from menu_tools.object_performance.resolution_collection import make_edges
from menu_tools.object_performance.turnon_collection import (
    ArrayLoader,
    TurnOnCollection,
)
from menu_tools.utils import constants
from menu_tools.utils import utils
from menu_tools.utils.plotting import add_watermark


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


def _bit_file(bit: str) -> str:
    """Name of the cached record holding a bit: `L1` for L1_* seeds, `HLT` for HLT_*
    paths.
    """
    for prefix in ("L1", "HLT"):
        if bit.startswith(prefix + "_"):
            return prefix
    raise ValueError(f"Trigger bit '{bit}' must start with 'L1_' or 'HLT_'")


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
        self.bit_groups: dict[str, list[str]] = {
            level: list(self.pe_cfg.get(level) or []) for level in ("L1", "HLT")
        }
        self.curves: list[str] = list(
            self.pe_cfg.get("curves")
            or [lvl for lvl in ("L1", "HLT") if self.bit_groups[lvl]]
        )
        for curve in self.curves:
            if curve not in CURVES:
                raise ValueError(
                    f"{plot_name}: unknown curve '{curve}' (known: {CURVES})"
                )
            needed = (
                ("L1", "HLT") if curve in ("L1_and_HLT", "HLT_given_L1") else (curve,)
            )
            for level in needed:
                if not self.bit_groups[level]:
                    raise ValueError(
                        f"{plot_name}: curve '{curve}' needs a non-empty '{level}' list"
                    )
        rank = cfg_plot["reference_object"].get("rank", 1)
        if int(rank) < 1:
            raise ValueError(f"{plot_name}: reference_object rank must be >= 1")
        self.ref_rank = int(rank)
        # reference x per event (nan: no reference object)
        self.x: Optional[np.ndarray] = None
        self.fired: dict[str, np.ndarray] = {}  # "L1"/"HLT" -> per-event OR of the bits

    @property
    def bins(self) -> np.ndarray:
        return make_edges(self.cfg_plot.config_dict["binning"])

    def label(self, curve: str) -> str:
        labels = self.pe_cfg.get("labels") or {}
        if curve in labels:
            return labels[curve]
        if curve in DEFAULT_LABELS:
            return DEFAULT_LABELS[curve]
        names = [
            b.removeprefix(curve + "_").removesuffix("_final")
            for b in self.bit_groups[curve]
        ]
        return f"{curve}: " + " OR ".join(names)

    # --- reference: the TurnOnCollection selection, without test objects --------------

    def _reduce_to_per_event(self):
        """No test objects to reduce."""

    def _select_highest_pt_ref_object(self):
        """Keeps the `rank`-th highest-pT reference object.

        Rank 1 = leading, as in turn-ons.

        Events with fewer reference objects keep none.
        """
        if self.ref_rank == 1:
            return super()._select_highest_pt_ref_object()
        order = ak.argsort(self.ak_arrays["ref"]["pt"], axis=-1, ascending=False)
        self.ak_arrays["ref"] = self.ak_arrays["ref"][
            order[:, self.ref_rank - 1 : self.ref_rank]
        ]

    def _reference_x(self) -> np.ndarray:
        field = self.cfg_plot.reference_trafo or self.cfg_plot.reference_field
        x = self.ak_arrays["ref"][field]
        if x.ndim > 1:
            x = ak.firsts(x, axis=-1)
            while x.ndim > 1:
                x = ak.firsts(x, axis=-1)
        return ak.to_numpy(ak.fill_none(x, np.nan)).astype(float)

    # --- trigger bits -----------------------------------------------------------------

    def _load_bits(self) -> None:
        cfg = self.cfg_plot
        for level, bits in self.bit_groups.items():
            if not bits:
                continue
            by_file: dict[str, list[str]] = {}
            for bit in bits:
                by_file.setdefault(_bit_file(bit), []).append(bit)
            fired: Optional[np.ndarray] = None
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
                    vals = ak.to_numpy(ak.fill_none(arr[bit], False)).astype(bool)
                    fired = vals if fired is None else fired | vals
            assert fired is not None
            self.fired[level] = fired

    # --- histograms -------------------------------------------------------------------

    def _pass_and_den(self, curve: str) -> tuple[np.ndarray, np.ndarray]:
        assert self.x is not None
        has_ref = np.isfinite(self.x)
        if curve == "L1_and_HLT":
            return self.fired["L1"] & self.fired["HLT"], has_ref
        if curve == "HLT_given_L1":
            return self.fired["HLT"], has_ref & self.fired["L1"]
        return self.fired[curve], has_ref

    def _skim(self) -> None:
        for curve in self.curves:
            passed, den = self._pass_and_den(curve)
            self.hists["ref"][curve] = np.histogram(self.x[den], bins=self.bins)
            self.hists[curve] = np.histogram(self.x[den & passed], bins=self.bins)

    def plateau(self, curve: str) -> Optional[dict[str, Any]]:
        """Integrated efficiency for x >= plateau_min (None if not configured)."""
        xmin = self.pe_cfg.get("plateau_min")
        if xmin is None:
            return None
        passed, den = self._pass_and_den(curve)
        assert self.x is not None
        sel = den & (self.x >= float(xmin))
        n, k = int(sel.sum()), int((sel & passed).sum())
        err = utils.clopper_pearson_err([k], [n])
        return {
            "x_min": float(xmin),
            "n_pass": k,
            "n_total": n,
            "efficiency": k / n if n else float("nan"),
            "efficiency_err": [float(err[0][0]), float(err[1][0])],
        }

    def create_hists(self) -> None:
        loader = ArrayLoader(self, self.cfg_plot)
        loader._load_ref_branches()
        self._apply_reference_cuts()
        self._apply_reference_trafo()
        self.x = self._reference_x()
        self._load_bits()
        for level, fired in self.fired.items():
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

    def _curve_data(self, curve: str) -> dict[str, Any]:
        edges = self.collection.bins
        eff, err = self.collection.get_efficiency(curve)
        ok = np.isfinite(eff)
        x = 0.5 * (edges[1:] + edges[:-1])
        xerr = 0.5 * np.diff(edges)
        return {
            "label": self.collection.label(curve),
            "xbins": x[ok].tolist(),
            "efficiency": eff[ok].tolist(),
            "efficiency_err": [err[0][ok].tolist(), err[1][ok].tolist()],
            "n_pass": self.collection.hists[curve][0][ok].tolist(),
            "n_total": self.collection.hists["ref"][curve][0][ok].tolist(),
            "err_kwargs": {
                "xerr": xerr[ok].tolist(),
                "capsize": 3,
                "markersize": 8,
                **MARKERS[curve],
            },
        }

    @utils.ignore_warnings
    def plot(self) -> dict[str, Any]:
        os.makedirs(self._outdir, exist_ok=True)
        fig, ax = self._create_new_plot()
        out: dict[str, Any] = {
            "xlabel": self.cfg.xlabel,
            "ylabel": self.cfg.ylabel,
            "watermark": f"{self.version}_{self.plot_name}",
            "reference": self.cfg.reference_label,
            "bits": self.collection.bit_groups,
        }
        for curve in self.collection.curves:
            data = self._curve_data(curve)
            if (plateau := self.collection.plateau(curve)) is not None:
                data["plateau"] = plateau
            out[curve] = data
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
            title=self.cfg.reference_label,
            fontsize=16,
            title_fontsize=18,
        )
        ax.set_xlabel(rf"{self.cfg.xlabel}")
        ax.set_ylabel(rf"{self.cfg.ylabel}")
        edges = self.collection.bins
        ax.set_xlim(edges[0], edges[-1])
        ax.set_ylim(0, 1.15 + 0.07 * (len(self.collection.curves) + 1))
        ax.tick_params(direction="in")
        fig.tight_layout()
        add_watermark(ax, f"{self.version}_{self.plot_name} ({self.pu_value})")

        fname = os.path.join(self._outdir, f"{self.plot_name}_{self.version}")
        plt.savefig(f"{fname}.png")
        plt.savefig(f"{fname}.pdf", bbox_inches="tight")
        plt.close(fig)
        with open(f"{fname}.json", "w") as f:
            f.write(json.dumps(out, indent=4))
        with open(f"{fname}.yaml", "w") as f:
            yaml.dump(
                {self.plot_name: self.cfg.config_dict}, f, default_flow_style=False
            )
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
            for curve in collection.curves:
                if (p := out[curve].get("plateau")) is not None:
                    print(
                        f"  {curve:13s} x >= {p['x_min']:g}: {p['efficiency']:.3f} "
                        f"+{p['efficiency_err'][1]:.3f} -{p['efficiency_err'][0]:.3f} "
                        f"({p['n_pass']}/{p['n_total']})"
                    )
            print(
                "INFO: path efficiencies in "
                f"outputs/{collection.version}/object_performance/path_efficiency"
            )

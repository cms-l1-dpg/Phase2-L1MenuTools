"""Purity, fake rate and multiplicity of trigger (L1 or HLT) objects.

Unlike the matching efficiencies (gen object -> trigger object), the loop runs over the
trigger objects: *all* test objects of each event that pass the object ID / eta cuts
(optionally only the leading one), and each is flagged `matched` if any selected gen
object lies within `match_dR` (the test object's `match_dR`, or the `purity.match_dR`
override). The matching is not exclusive: two trigger objects can match the same gen
object.

Modes (`purity.mode`), quantity and binning:
  purity        object-level purity  N(matched) / N(all)                vs pt/eta/pu
  fake_rate     fake fraction        N(unmatched) / N(all) = 1 - purity vs pt/eta/pu
                unmatched objects per event (mean) above threshold
                                                                    vs threshold/pu
                events with >= 1 unmatched object above threshold (fraction,
                in kHz if `rate`)                                   vs threshold/pu
                unmatched objects per event per bin (dN/dx)         vs pt/eta
  multiplicity  as fake_rate, but with all objects and no gen matching (for minimum
                bias, whose gen record is pruned): mean multiplicity, rate of events
                with >= 1 object above threshold (kHz), dN/dx per event.

Thresholds are on the online pT field `pt` of the test object, `pt >= threshold` as in
the rate plots (no offline scalings).
"""
import os
import re
from typing import Any, Optional, Sequence

import awkward as ak
import numpy as np
import numpy.typing as npt

from menu_tools.object_performance.resolution_collection import make_edges
from menu_tools.object_performance.turnon_collection import (
    ArrayLoader,
    TurnOnCollection,
)
from menu_tools.utils import constants, utils
from menu_tools.utils.objects import (
    CUT_FIELD_RE,
    Object,
    compute_selection_mask_for_object_cuts,
)

MODES = ("purity", "fake_rate", "multiplicity")
# Object-level binning variables (of the trigger object) and event-level ones.
OBJECT_VS = ("pt", "eta", "abseta", "phi")
EVENT_VS = ("pu", "threshold")
VS_VARIABLES = OBJECT_VS + EVENT_VS

DEFAULT_VS = {
    "purity": {"pt": {"min": 0, "max": 100, "step": 5}},
    "fake_rate": {
        "pt": {"min": 0, "max": 100, "step": 5},
        "threshold": {"min": 0, "max": 100, "step": 5},
    },
    "multiplicity": {"threshold": {"min": 0, "max": 100, "step": 5}},
}

# Events are processed in slices of this size for the trigger x gen pairing.
CHUNK = 200_000


def delta_phi(a, b):
    return (a - b + np.pi) % (2 * np.pi) - np.pi


def match_any(trig: ak.Array, gen: ak.Array, dr: float, chunk: int = CHUNK) -> ak.Array:
    """Per trigger object: True if any gen object of the same event is within `dr`.

    trig, gen: jagged records with `eta` and `phi`, one row per event (same length).
    Returns a jagged boolean array with the structure of `trig`.
    """
    out = []
    for start in range(0, len(trig), chunk):
        t = trig[start : start + chunk]
        g = gen[start : start + chunk]
        pairs = ak.cartesian(
            {"t": t[["eta", "phi"]], "g": g[["eta", "phi"]]}, nested=True
        )
        deta = pairs.t.eta - pairs.g.eta
        dphi = delta_phi(pairs.t.phi, pairs.g.phi)
        out.append(ak.any(deta * deta + dphi * dphi < dr * dr, axis=2))
    if not out:
        return ak.Array([])
    return ak.concatenate(out, axis=0) if len(out) > 1 else out[0]


def ratio_with_cp(
    num: npt.ArrayLike, den: npt.ArrayLike
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """num/den with Clopper-Pearson 68% errors (NaN where den == 0)."""
    num = np.asarray(num, dtype=float)
    den = np.asarray(den, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        y = np.where(den > 0, num / den, np.nan)
    err = utils.clopper_pearson_err(num, den)
    err = np.where(den > 0, err, np.nan)
    return y, err[0], err[1]


def mean_with_error(values: np.ndarray) -> tuple[float, float]:
    """Mean and its standard error (NaN for an empty sample)."""
    n = len(values)
    if n == 0:
        return np.nan, np.nan
    if n == 1:
        return float(values[0]), np.nan
    return float(np.mean(values)), float(np.std(values, ddof=1) / np.sqrt(n))


def linear_fit(x, y, yerr) -> Optional[dict[str, float]]:
    """Weighted straight-line fit y = a + b x; None with fewer than 2 usable points."""
    x, y, yerr = (np.asarray(v, dtype=float) for v in (x, y, yerr))
    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(yerr) & (yerr > 0)
    if ok.sum() < 2:
        return None
    w = 1 / yerr[ok] ** 2
    (b, a), cov = np.polyfit(x[ok], y[ok], 1, w=np.sqrt(w), cov="unscaled")
    return {
        "intercept": float(a),
        "slope": float(b),
        "slope_err": float(np.sqrt(cov[0, 0])),
    }


class PurityConfig:
    """The `purity:` block of a plot config.

    purity:
      mode: purity                 # purity | fake_rate | multiplicity
      # gen objects to match to (not for multiplicity); a list is an OR
      reference_gen:
        # parquet name, or an object key with id (e.g. "GenPart:electron")
        object: GenPart
        cuts: ["abs({pdgId}) == 11", "(({statusFlags}>>0)&1) == 1"]
        label: "gen e"
      match_dR: 0.15               # optional, default: the test object's match_dR
      vs:
        pt: {min: 0, max: 100, step: 5}       # trigger-object pT
        eta: {min: -3, max: 3, step: 0.2}     # trigger-object eta (abseta: |eta|, phi)
        pu: {edges: [140, 180, 200, 220, 260]} # pileup of the event (Pileup parquet)
        threshold: {min: 0, max: 100, step: 5} # threshold scan (event-level quantities)
      thresholds: [0, 20]          # pT thresholds for the vs eta/phi/pu plots
                                   # (default [0])
      leading_only: false          # only the leading (highest-pT) test object of
                                   # each event
      rate: false                  # event fractions in kHz (default: true for
                                   # MinBias samples)
      pu_variable: nPU
      pileup_version: null         # cache version holding the Pileup parquet
                                   # (default: the version, then <version>PU)
    """

    def __init__(self, cfg: Optional[dict], sample: str) -> None:
        cfg = cfg or {}
        self.mode: str = cfg.get("mode", "purity")
        if self.mode not in MODES:
            raise ValueError(f"purity: unknown mode `{self.mode}`, use one of {MODES}")
        gen = cfg.get("reference_gen")
        if self.mode != "multiplicity":
            if not gen:
                raise KeyError(f"purity: mode `{self.mode}` needs `reference_gen`")
            self.reference_gen: list[dict] = gen if isinstance(gen, list) else [gen]
            for spec in self.reference_gen:
                if "object" not in spec:
                    raise KeyError(
                        "purity: each `reference_gen` entry needs an `object`"
                    )
        else:
            self.reference_gen = []
        self.match_dR: Optional[float] = cfg.get("match_dR")
        vs = cfg.get("vs") or DEFAULT_VS[self.mode]
        for name in vs:
            if name not in VS_VARIABLES:
                raise ValueError(
                    f"purity: unknown `vs` variable `{name}`, use one of {VS_VARIABLES}"
                )
        self.vs: dict[str, Any] = dict(vs)
        self.thresholds: list[float] = [float(t) for t in cfg.get("thresholds", [0])]
        self.leading_only: bool = bool(cfg.get("leading_only", False))
        self.rate: bool = bool(cfg.get("rate", "minbias" in sample.lower()))
        self.pu_variable: str = cfg.get("pu_variable", "nPU").removeprefix("Pileup_")
        self.pileup_version: Optional[str] = cfg.get("pileup_version")

    @property
    def gen_label(self) -> str:
        labels = [s.get("label", s["object"]) for s in self.reference_gen]
        return " or ".join(labels)

    def vs_edges(self, name: str) -> np.ndarray:
        return make_edges(self.vs[name])

    def vs_label(self, name: str) -> Optional[str]:
        spec = self.vs[name]
        return spec.get("label") if isinstance(spec, dict) else None


class PurityCollection(TurnOnCollection):
    """Trigger objects of each test object, their gen-match flag, and the derived
    quantities.

    After `create()`:
      objects[obj_key]: flat numpy arrays pt, eta, phi, matched (None in multiplicity
                        mode), event (event index), dr (matching cone)
      n_events, pileup (per event, or None)
      plots: list of dicts, one per output plot (see `_add_plot`)
    """

    def __init__(
        self,
        cfg_plot: dict,
        plot_name: Optional[str] = None,
        config_version: Optional[str] = None,
        override_version: Optional[str] = None,
    ):
        super().__init__(
            cfg_plot,
            threshold=-999,
            plot_name=plot_name,
            config_version=config_version,
            override_version=override_version,
        )
        self.pur_cfg = PurityConfig(
            self.cfg_plot.config_dict.get("purity"), self.cfg_plot.sample
        )
        self.objects: dict[str, dict[str, Any]] = {}
        self.n_events: int = 0
        self.pileup: Optional[np.ndarray] = None
        self.pileup_source: Optional[str] = None
        self.gen: Optional[ak.Array] = None
        self.plots: list[dict] = []

    @property
    def matching(self) -> bool:
        return self.pur_cfg.mode != "multiplicity"

    # ---- loading -------------------------------------------------------------------

    @staticmethod
    def _cut_fields(cuts) -> set[str]:
        """Field names used in a list of cut strings (or a dict of such lists)."""
        if isinstance(cuts, dict):
            cuts = [c for v in cuts.values() for c in v]
        return {f for c in cuts or [] for f in re.findall(CUT_FIELD_RE, c)}

    def _load_parquet(self, name: str, fields: set[str]) -> ak.Array:
        """Only the needed columns of <version>_<sample>_<name>.parquet.

        As a record array with the field names of `ArrayLoader` (prefix stripped).
        """
        v = self.cfg_plot.version
        fname = f"{constants.CACHE_DIR}/{v}/{v}_{self.cfg_plot.sample}_{name}.parquet"
        if not os.path.exists(fname):
            raise FileNotFoundError(fname)
        loader = ArrayLoader(self, self.cfg_plot)
        cols = [
            c
            for c in ak.metadata_from_parquet(fname)["form"].fields
            if loader._transform_key(c, name) in fields
        ]
        try:
            arr = ak.from_parquet(fname, columns=cols)
        except Exception:
            # Caches written as one awkward record column cannot be pruned by pyarrow
            # ("only part of an extension's storage type"): read everything, keep the
            # fields.
            arr = ak.from_parquet(fname)[cols]
        return ak.zip({loader._transform_key(k, name): arr[k] for k in cols})

    def _load_arrays(self) -> None:
        for test_obj, _ in self.test_objects:
            fields = {"pt", "eta", "phi"} | self._cut_fields(test_obj.cuts)
            self.ak_arrays[str(test_obj)] = self._load_parquet(
                test_obj.nano_obj_name, fields
            )

    def _load_gen(self) -> None:
        """Selected gen objects of all `reference_gen` entries (eta, phi, pt),
        concatenated per event.
        """
        parts = []
        for spec in self.pur_cfg.reference_gen:
            key = spec["object"]
            name = key.split(":")[0]
            fields = {"pt", "eta", "phi"} | self._cut_fields(spec.get("cuts", []))
            if ":" in key:
                fields |= self._cut_fields(
                    Object(key, self.cfg_plot.version_for_objects).cuts
                )
            arr = self._load_parquet(name, fields)
            if ":" in key:
                # Object key with id: the cuts of the object definition
                obj = Object(key, self.cfg_plot.version_for_objects)
                arr = arr[compute_selection_mask_for_object_cuts(obj, arr)]
            for cut in spec.get("cuts", []):
                arr = arr[eval(re.sub(CUT_FIELD_RE, r"arr['\1']", cut))]
            parts.append(ak.zip({f: arr[f] for f in ("pt", "eta", "phi")}))
        self.gen = parts[0] if len(parts) == 1 else ak.concatenate(parts, axis=1)

    def _pileup_file(self) -> Optional[str]:
        version, sample = self.cfg_plot.version, self.cfg_plot.sample
        candidates = (
            [self.pur_cfg.pileup_version]
            if self.pur_cfg.pileup_version
            else [version, version + "PU"]
        )
        for v in candidates:
            fname = f"{constants.CACHE_DIR}/{v}/{v}_{sample}_Pileup.parquet"
            if os.path.exists(fname):
                return fname
        return None

    def _load_pileup(self, n_events: int) -> None:
        fname = self._pileup_file()
        if fname is None:
            print(
                f"WARNING: no Pileup parquet for {self.cfg_plot.version} / "
                f"{self.cfg_plot.sample}: skipping the pileup binning"
            )
            return
        arr = ak.from_parquet(fname)
        field = next(
            (
                f
                for f in arr.fields
                if f.removeprefix("Pileup_") == self.pur_cfg.pu_variable
            ),
            None,
        )
        if field is None:
            raise KeyError(
                f"{fname} has no field `{self.pur_cfg.pu_variable}` (fields: "
                f"{arr.fields})"
            )
        pileup = ak.to_numpy(arr[field]).astype(float)
        if len(pileup) != n_events:
            raise ValueError(
                f"{fname} has {len(pileup)} events, the test objects {n_events}: not "
                "row-aligned"
            )
        self.pileup = pileup
        self.pileup_source = fname

    # ---- per-object flags ----------------------------------------------------------

    def _build_objects(self) -> None:
        lengths = {len(self.ak_arrays[str(o)]) for o, _ in self.test_objects}
        if len(lengths) != 1:
            raise ValueError(
                f"test objects of {self.cfg_plot.plot_name} have different event "
                f"counts {lengths}"
            )
        self.n_events = lengths.pop()
        if self.gen is not None and len(self.gen) != self.n_events:
            raise ValueError(
                f"gen objects have {len(self.gen)} events, the test objects "
                f"{self.n_events}"
            )
        for test_obj, _ in self.test_objects:
            key = str(test_obj)
            arr = self.ak_arrays[key]
            if arr.ndim < 2:
                raise ValueError(
                    f"{key}: purity needs a jagged object collection, not a per-event "
                    "quantity"
                )
            arr = ak.zip({f: arr[f] for f in ("pt", "eta", "phi")})
            if self.pur_cfg.leading_only:
                arr = arr[ak.argmax(arr.pt, axis=1, keepdims=True)]
                arr = arr[~ak.is_none(arr, axis=1)]
            dr = float(
                self.pur_cfg.match_dR
                if self.pur_cfg.match_dR is not None
                else test_obj.match_dR
            )
            matched = match_any(arr, self.gen, dr) if self.matching else None
            event = ak.broadcast_arrays(ak.local_index(arr, axis=0), arr.pt)[0]
            flat = lambda a: ak.to_numpy(ak.flatten(a, axis=None))  # noqa: E731
            self.objects[key] = {
                "pt": flat(arr.pt).astype(float),
                "eta": flat(arr.eta).astype(float),
                "phi": flat(arr.phi).astype(float),
                "event": flat(event).astype(np.int64),
                "matched": flat(matched).astype(bool) if matched is not None else None,
                "dr": dr,
            }
            del self.ak_arrays[key]

    # ---- quantities ----------------------------------------------------------------

    def _x(self, obj: dict, vs: str) -> np.ndarray:
        if vs == "abseta":
            return np.abs(obj["eta"])
        if vs == "pu":
            return self.pileup[obj["event"]]
        return obj[vs]

    def _add_plot(
        self,
        quantity: str,
        vs: str,
        threshold: Optional[float],
        series: dict,
        extra=None,
    ) -> None:
        edges = self.pur_cfg.vs_edges(vs)
        plot = {
            "quantity": quantity,
            "vs": vs,
            "threshold": threshold,
            "edges": edges,
            "series": series,
        }
        plot.update(extra or {})
        self.plots.append(plot)

    def _object_ratio(self, quantity: str, vs: str, threshold: Optional[float]) -> None:
        """purity / fake fraction of the trigger objects in bins of `vs`."""
        edges = self.pur_cfg.vs_edges(vs)
        series = {}
        for key, obj in self.objects.items():
            sel = (
                obj["pt"] >= threshold
                if threshold is not None
                else np.ones(len(obj["pt"]), bool)
            )
            x = self._x(obj, vs)[sel]
            m = obj["matched"][sel]
            if quantity == "fake_fraction":
                m = ~m
            den = np.histogram(x, bins=edges)[0]
            num = np.histogram(x[m], bins=edges)[0]
            y, lo, hi = ratio_with_cp(num, den)
            total = ratio_with_cp([m.sum()], [len(m)])
            series[key] = {
                "y": y,
                "err_lo": lo,
                "err_hi": hi,
                "num": num,
                "den": den,
                "integral": float(total[0][0]) if len(m) else None,
                "integral_n": int(len(m)),
            }
        self._add_plot(quantity, vs, threshold, series)

    def _object_density(
        self, quantity: str, vs: str, threshold: Optional[float]
    ) -> None:
        """(Unmatched) objects per event in bins of an object variable,
        Poisson errors.
        """
        edges = self.pur_cfg.vs_edges(vs)
        series = {}
        for key, obj in self.objects.items():
            sel = (
                obj["pt"] >= threshold
                if threshold is not None
                else np.ones(len(obj["pt"]), bool)
            )
            if quantity == "unmatched_density":
                sel &= ~obj["matched"]
            counts = np.histogram(self._x(obj, vs)[sel], bins=edges)[0]
            y = counts / self.n_events
            err = np.sqrt(counts) / self.n_events
            series[key] = {
                "y": y,
                "err_lo": err,
                "err_hi": err,
                "num": counts,
                "den": np.full(len(counts), self.n_events),
            }
        self._add_plot(quantity, vs, threshold, series)

    def _per_event_counts(self, obj: dict, threshold: float) -> np.ndarray:
        sel = obj["pt"] >= threshold
        if self.matching:
            sel &= ~obj["matched"]
        return np.bincount(obj["event"][sel], minlength=self.n_events)

    def _event_quantity(self, counts: np.ndarray, quantity: str, ev_sel=None) -> tuple:
        """mean count per event, or fraction of events with >= 1 (CP; x rate factor)."""
        if ev_sel is not None:
            counts = counts[ev_sel]
        if quantity.endswith("per_event"):
            m, e = mean_with_error(counts)
            return m, e, e, int(counts.sum()), len(counts)
        n_pass = int((counts > 0).sum())
        y, lo, hi = ratio_with_cp([n_pass], [len(counts)])
        scale = constants.RATE_NORM_FACTOR if self.pur_cfg.rate else 1.0
        return y[0] * scale, lo[0] * scale, hi[0] * scale, n_pass, len(counts)

    def _event_vs_threshold(self, quantity: str) -> None:
        thresholds = self.pur_cfg.vs_edges("threshold")
        series = {}
        for key, obj in self.objects.items():
            cols = [
                self._event_quantity(self._per_event_counts(obj, t), quantity)
                for t in thresholds
            ]
            y, lo, hi, num, den = (np.asarray(c) for c in zip(*cols))
            series[key] = {"y": y, "err_lo": lo, "err_hi": hi, "num": num, "den": den}
        self._add_plot(quantity, "threshold", None, series)

    def _event_vs_pu(self, quantity: str, threshold: float) -> None:
        edges = self.pur_cfg.vs_edges("pu")
        assert self.pileup is not None
        ibin = np.digitize(self.pileup, edges) - 1
        centres = 0.5 * (edges[1:] + edges[:-1])
        series = {}
        for key, obj in self.objects.items():
            counts = self._per_event_counts(obj, threshold)
            cols = [
                self._event_quantity(counts, quantity, ibin == i)
                for i in range(len(edges) - 1)
            ]
            y, lo, hi, num, den = (np.asarray(c, dtype=float) for c in zip(*cols))
            fit = linear_fit(centres, y, 0.5 * (lo + hi))
            series[key] = {
                "y": y,
                "err_lo": lo,
                "err_hi": hi,
                "num": num,
                "den": den,
                "fit": fit,
            }
        self._add_plot(quantity, "pu", threshold, series)

    def _compute(self) -> None:
        mode = self.pur_cfg.mode
        vs_all = list(self.pur_cfg.vs)
        if "pu" in vs_all and self.pileup is None:
            vs_all.remove("pu")
        thresholds = self.pur_cfg.thresholds
        ratio_q: Optional[str]
        density_q: Optional[str]
        event_q: tuple[str, ...]
        if mode == "multiplicity":
            ratio_q, density_q, event_q = (
                None,
                "density",
                ("objects_per_event", "event_fraction"),
            )
        else:
            ratio_q = "purity" if mode == "purity" else "fake_fraction"
            density_q = "unmatched_density" if mode == "fake_rate" else None
            event_q = (
                ("unmatched_per_event", "event_fraction") if mode == "fake_rate" else ()
            )

        for vs in vs_all:
            if vs in OBJECT_VS:
                # vs pt: no threshold (the binning shows the pT dependence);
                # others: per threshold
                thrs: Sequence[Optional[float]] = thresholds
                if vs == "pt":
                    thrs = [None]
                for t in thrs:
                    if ratio_q:
                        self._object_ratio(ratio_q, vs, t)
                    if density_q and vs != "pt":
                        self._object_density(density_q, vs, t)
            elif vs == "pu":
                for t in thresholds:
                    if ratio_q:
                        self._object_ratio(ratio_q, vs, t)
                    for q in event_q:
                        self._event_vs_pu(q, t)
            elif vs == "threshold":
                for q in event_q:
                    self._event_vs_threshold(q)

    def create(self) -> None:
        self._load_arrays()
        self._apply_test_obj_cuts()
        if self.matching:
            self._load_gen()
        self._build_objects()
        self.gen = None
        self.ak_arrays = {}
        if "pu" in self.pur_cfg.vs:
            self._load_pileup(self.n_events)
        self._compute()

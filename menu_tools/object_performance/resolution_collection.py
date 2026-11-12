"""pT / eta / phi response and resolution of test objects with respect to a reference.

The reference selection, the test-object cuts and the dR matching are those of
`TurnOnCollection` (highest-pT test object within `match_dR` of the leading
reference object). Instead of efficiencies, the matched pairs give
  * pT response   test_pt / ref_pt  (or test_x_arg / ref value for event-level sums),
  * eta response  test_eta - ref_eta,
  * phi response  test_phi - ref_phi, wrapped to [-pi, pi),
binned in reference pT, reference eta and pileup.

Per bin: the median, the effective resolution (half of the 16-84% interquantile
range; normalised by the median for the pT response), the counts, and
distribution-free (order-statistics) uncertainties on the quantiles.

Event-level quantities (MET, HT, MHT: `match_test_to_ref: False`) are compared event by
event without matching, one value per event.
"""
import os
from typing import Any, Optional

import awkward as ak
import numpy as np

from menu_tools.object_performance.turnon_collection import (
    ArrayLoader,
    TurnOnCollection,
)
from menu_tools.utils import constants


# Quantities that are a ratio test/ref (resolution normalised by the median) vs. a
# difference.
RATIO_VARIABLES = ("pt",)
DIFF_VARIABLES = ("eta", "phi")
# Variables the response can be binned in ("vs"); "pu" is event-level from the Pileup
# parquet.
VS_VARIABLES = ("pt", "eta", "abseta", "phi", "pu")


def wrap_dphi(dphi):
    """Wraps an angle difference to [-pi, pi)."""
    return (np.asarray(dphi) + np.pi) % (2 * np.pi) - np.pi


def make_edges(spec: Any) -> np.ndarray:
    """Bin edges from `{min, max, step}` or `{edges: [...]}`.

    Or a plain list of edges.
    """
    if isinstance(spec, (list, tuple)):
        return np.asarray(spec, dtype=float)
    if "edges" in spec:
        return np.asarray(spec["edges"], dtype=float)
    return np.arange(float(spec["min"]), float(spec["max"]) + 1e-5, float(spec["step"]))


def quantile_with_error(sorted_x: np.ndarray, p: float) -> tuple[float, float]:
    """Quantile `p` of the sorted sample and its uncertainty.

    The uncertainty is distribution-free: the rank of the p-quantile fluctuates by
    sqrt(n p (1-p)) (binomial), so the error is half the distance between the order
    statistics one standard deviation in rank below and above.
    """
    n = len(sorted_x)
    q = float(np.quantile(sorted_x, p))
    k = p * (n - 1)
    s = np.sqrt(n * p * (1 - p))
    lo = sorted_x[int(max(0, np.floor(k - s)))]
    hi = sorted_x[int(min(n - 1, np.ceil(k + s)))]
    return q, 0.5 * float(hi - lo)


def summarize_response(values: np.ndarray, kind: str) -> dict[str, float]:
    """Median, 16/84% quantiles and effective resolution of one bin.

    kind: "ratio" (resolution = half 16-84% range / median) or "diff" (absolute).
    The resolution error adds the 16% and 84% quantile errors in quadrature, which
    neglects their (positive) correlation and therefore slightly overestimates it.
    """
    x = np.sort(np.asarray(values, dtype=float))
    med, med_err = quantile_with_error(x, 0.5)
    q16, q16_err = quantile_with_error(x, 0.16)
    q84, q84_err = quantile_with_error(x, 0.84)
    width = 0.5 * (q84 - q16)
    width_err = 0.5 * np.hypot(q16_err, q84_err)
    if kind == "ratio":
        res = width / med if med != 0 else np.nan
        res_err = (
            abs(res) * np.hypot(width_err / width, med_err / med)
            if (med != 0 and width > 0)
            else np.nan
        )
    else:
        res, res_err = width, width_err
    return {
        "n": int(len(x)),
        "median": med,
        "median_err": med_err,
        "q16": q16,
        "q84": q84,
        "resolution": float(res),
        "resolution_err": float(res_err),
        "mean": float(np.mean(x)),
        "std": float(np.std(x)),
    }


def binned_response(
    x: np.ndarray,
    values: np.ndarray,
    edges: np.ndarray,
    kind: str,
    min_entries: int = 20,
) -> dict[str, list]:
    """`summarize_response` in bins of `x`.

    Bins with fewer than `min_entries` give NaN.
    """
    x = np.asarray(x, dtype=float)
    values = np.asarray(values, dtype=float)
    keys = [
        "n",
        "median",
        "median_err",
        "q16",
        "q84",
        "resolution",
        "resolution_err",
        "mean",
        "std",
    ]
    out: dict[str, list] = {k: [] for k in keys}
    idx = np.digitize(x, edges) - 1
    for i in range(len(edges) - 1):
        vals = values[idx == i]
        if len(vals) >= max(min_entries, 1):
            summary = summarize_response(vals, kind)
        else:
            summary = {k: np.nan for k in keys}
            summary["n"] = int(len(vals))
        for k in keys:
            out[k].append(summary[k])
    out["edges"] = list(map(float, edges))
    return out


class ResolutionConfig:
    """The `resolution:` block of a plot config.

    resolution:
      # responses to compute (default: all; event-level: pt, phi)
      variables: [pt, eta, phi]
      # binning variables (default: pt with the top-level `binning`)
      vs:
        pt: {min: 0, max: 100, step: 10}  # reference pT (or event-level reference)
        eta: {min: -2.4, max: 2.4, step: 0.2}   # reference eta (abseta: |eta|)
        pu: {edges: [150, 180, 190, 200, 210, 220, 260]}  # pileup, see pu_variable
      # optional: per-bin response distributions for these
      response_binning:
        pt: {min: 0, max: 2, step: 0.04}
      pu_variable: nPU                    # field of the Pileup parquet (nTrueInt, nPU)
      min_entries: 20                     # bins with fewer pairs are not reported
      min_ref: 0                          # event-level only: reference value > min_ref
    Each `vs` entry may carry a `label` (x axis label).
    """

    def __init__(self, cfg: Optional[dict], top_level: dict, event_level: bool) -> None:
        cfg = cfg or {}
        self._cfg = cfg
        default_vars = ["pt", "phi"] if event_level else ["pt", "eta", "phi"]
        self.variables: list[str] = [
            v.lower() for v in cfg.get("variables", default_vars)
        ]
        for var in self.variables:
            if var not in RATIO_VARIABLES + DIFF_VARIABLES:
                raise ValueError(f"Unknown resolution variable `{var}`")
        vs = cfg.get("vs")
        if not vs:
            if "binning" not in top_level:
                raise KeyError("resolution: give `vs` or a top-level `binning`")
            vs = {"pt": top_level["binning"]}
        for name in vs:
            if name not in VS_VARIABLES:
                raise ValueError(
                    f"Unknown resolution `vs` variable `{name}`, use one of "
                    f"{VS_VARIABLES}"
                )
        self.vs: dict[str, dict] = dict(vs)
        self.response_binning: dict[str, Any] = cfg.get("response_binning", {}) or {}
        self.pu_variable: str = cfg.get("pu_variable", "nPU")
        self.min_entries: int = int(cfg.get("min_entries", 20))
        # Event-level only: lower cut on the reference value (e.g. gen MET), since the
        # pT response diverges for a reference near 0. Matched objects use the reference
        # cuts.
        self.min_ref: float = float(cfg.get("min_ref", 0))

    def vs_edges(self, name: str) -> np.ndarray:
        return make_edges(self.vs[name])

    def vs_label(self, name: str) -> Optional[str]:
        spec = self.vs[name]
        return spec.get("label") if isinstance(spec, dict) else None


class ResolutionCollection(TurnOnCollection):
    """Matched (or event-level) test/reference pairs and their binned response.

    After `create()`:
      pairs[obj_key]: dict of flat numpy arrays ref_pt, ref_eta, ref_phi, test_pt,
                      test_eta, test_phi (missing ones absent) and pu (if requested)
      results[variable][vs][obj_key]: output of `binned_response`
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
        self.event_level = not self.cfg_plot.matching
        self.res_cfg = ResolutionConfig(
            self.cfg_plot.config_dict.get("resolution"),
            self.cfg_plot.config_dict,
            self.event_level,
        )
        self.keep_matched_records = True
        self.matched_records: dict[str, dict] = {}
        self.pairs: dict[str, dict[str, np.ndarray]] = {}
        self.results: dict[str, dict[str, dict[str, dict]]] = {}
        self.pileup: Optional[np.ndarray] = None

    # ---- loading -------------------------------------------------------------------

    def _load_pileup(self) -> None:
        """Event-level pileup from the `Pileup` parquet of the same version and sample.

        It is row-aligned with the object parquets of that sample (one row per event).
        """
        fname = (
            f"{constants.CACHE_DIR}/{self.cfg_plot.version}/"
            f"{self.cfg_plot.version}_{self.cfg_plot.sample}_Pileup.parquet"
        )
        if not os.path.exists(fname):
            print(f"WARNING: no {fname}: skipping the pileup binning")
            del self.res_cfg.vs["pu"]
            return
        loader = ArrayLoader(self, self.cfg_plot)
        pileup = loader._load_array_from_parquet("Pileup")
        field = self.res_cfg.pu_variable.removeprefix("Pileup_")
        if field not in pileup.fields:
            raise KeyError(
                f"Pileup parquet has no field `{field}` (fields: {pileup.fields})"
            )
        self.pileup = pileup_values = ak.to_numpy(pileup[field]).astype(float)
        n_ref = len(self.ak_arrays["ref"])
        if len(pileup_values) != n_ref:
            raise ValueError(
                f"Pileup parquet has {len(pileup_values)} events, the reference "
                f"{n_ref}: "
                "not aligned"
            )

    # ---- pairs ---------------------------------------------------------------------

    @staticmethod
    def _flat(arr) -> np.ndarray:
        return ak.to_numpy(ak.flatten(arr, axis=None)).astype(float)

    def _matched_pairs(self) -> None:
        for test_obj, _ in self.test_objects:
            rec = self.matched_records[str(test_obj)]
            ref, test = rec["ref"], rec["test"]
            ok = ~ak.is_none(test, axis=1)
            ok = ak.fill_none(ok & ~ak.is_none(ref, axis=1), False)
            pairs = {}
            for field in ("pt", "eta", "phi"):
                if field in ref.fields:
                    pairs[f"ref_{field}"] = self._flat(ref[field][ok])
                if field in test.fields:
                    pairs[f"test_{field}"] = self._flat(test[field][ok])
            if self.pileup is not None:
                pu = ak.broadcast_arrays(ak.Array(self.pileup), ok)[0]
                pairs["pu"] = self._flat(pu[ok])
            self.pairs[str(test_obj)] = pairs

    @staticmethod
    def _per_event(arr, reducer):
        """One value per event: flat arrays as they are, jagged ones reduced (None if
        empty).
        """
        if arr.ndim > 1:
            arr = reducer(arr)
        return ak.to_numpy(ak.fill_none(arr, np.nan)).astype(float)

    def _event_level_pairs(self) -> None:
        ref_arr = self.ak_arrays["ref"]
        ref_field = self.cfg_plot.reference_trafo or self.cfg_plot.reference_field
        ref_val = self._per_event(ref_arr[ref_field], lambda a: ak.max(a, axis=1))
        ref_phi = None
        if "phi" in ref_arr.fields and not self.cfg_plot.reference_trafo:
            ref_phi = self._per_event(ref_arr["phi"], lambda a: ak.firsts(a, axis=1))
        n_ev = len(ref_val)
        for test_obj, x_arg in self.test_objects:
            test_arr = self.ak_arrays[str(test_obj)]
            if len(test_arr) != n_ev:
                raise ValueError(
                    f"{test_obj}: {len(test_arr)} events vs {n_ev} in the reference; "
                    "event-level resolution needs one row per event (no object cuts on "
                    "flat arrays)"
                )
            # Jagged sums (e.g. one entry per sumType after the object cuts): highest
            # value.
            test_val = self._per_event(test_arr[x_arg], lambda a: ak.max(a, axis=1))
            ok = (
                np.isfinite(ref_val)
                & np.isfinite(test_val)
                & (ref_val > self.res_cfg.min_ref)
            )
            pairs = {"ref_pt": ref_val[ok], "test_pt": test_val[ok]}
            if ref_phi is not None and "phi" in test_arr.fields:
                test_phi = self._per_event(
                    test_arr["phi"], lambda a: ak.firsts(a, axis=1)
                )
                ok_phi = ok & np.isfinite(ref_phi) & np.isfinite(test_phi)
                # keep arrays of equal length: phi NaN where unavailable
                pairs["ref_phi"] = np.where(ok_phi, ref_phi, np.nan)[ok]
                pairs["test_phi"] = np.where(ok_phi, test_phi, np.nan)[ok]
            if self.pileup is not None:
                pairs["pu"] = self.pileup[ok]
            self.pairs[str(test_obj)] = pairs

    # ---- response ------------------------------------------------------------------

    def response(self, obj_key: str, variable: str) -> Optional[np.ndarray]:
        """Response values of `variable` for the pairs of `obj_key` (None if
        unavailable).
        """
        p = self.pairs[obj_key]
        if not {f"ref_{variable}", f"test_{variable}"} <= p.keys():
            return None
        if variable == "pt":
            with np.errstate(divide="ignore", invalid="ignore"):
                return p["test_pt"] / p["ref_pt"]
        if variable == "phi":
            return wrap_dphi(p["test_phi"] - p["ref_phi"])
        return p[f"test_{variable}"] - p[f"ref_{variable}"]

    def vs_values(self, obj_key: str, vs: str) -> Optional[np.ndarray]:
        p = self.pairs[obj_key]
        if vs == "pu":
            return p.get("pu")
        if vs == "abseta":
            return np.abs(p["ref_eta"]) if "ref_eta" in p else None
        return p.get(f"ref_{vs}")

    def _compute_results(self) -> None:
        for var in self.res_cfg.variables:
            kind = "ratio" if var in RATIO_VARIABLES else "diff"
            self.results[var] = {}
            for vs in self.res_cfg.vs:
                self.results[var][vs] = {}
                for obj_key in self.pairs:
                    values = self.response(obj_key, var)
                    x = self.vs_values(obj_key, vs)
                    if values is None or x is None:
                        continue
                    ok = np.isfinite(values) & np.isfinite(x)
                    self.results[var][vs][obj_key] = binned_response(
                        x[ok],
                        values[ok],
                        self.res_cfg.vs_edges(vs),
                        kind,
                        self.res_cfg.min_entries,
                    )

    def create(self) -> None:
        self._load_arrays()
        if "pu" in self.res_cfg.vs:
            self._load_pileup()
        self._apply_cuts()
        if self.event_level:
            self._event_level_pairs()
        else:
            self._match_test_to_ref()
            self._matched_pairs()
        # The raw arrays are no longer needed.
        self.ak_arrays = {}
        self.matched_records = {}
        self.numerators = {"ref": {}, "test": {}}
        self._compute_results()

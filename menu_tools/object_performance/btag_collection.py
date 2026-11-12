"""b-tagging efficiency and mis-identification rates of trigger (L1 or HLT) jets.

The loop runs over the reco (trigger) jets: all jets of each event that pass the object
ID cuts and |eta| < `max_abs_eta`. Each jet gets a truth category from the gen jets:

  b / c / light   the closest GenJet within `match_dR` has hadronFlavour 5 / 4 / 0
  pu              no GenJet within `pu_dR` (pileup jet: GenJets are clustered from the
                  hard-scatter particles only)

Jets with a GenJet between `match_dR` and `pu_dR` (but none within `match_dR`) are not
used. A jet is *tagged* at a working point if it passes the cuts of the working-point ID
(an id of the same object, e.g. `L1puppiJetSC4NG:bTagLight10`). All rates are
conditional on the reco jet existing (and on its truth category): tagging efficiency of
b jets and mis-identification rates of c, light and pileup jets, N(tagged) / N(jets),
with Clopper-Pearson 68% intervals.

Outputs (see `BTagCollection.create`):
  efficiency curves per flavour vs reco pt, gen pt, eta, |eta| and pileup;
  ROC curves (b efficiency vs c / light / pileup mis-id) from the continuous
  discriminant in bins of reco pt, with the working points marked;
  a summary table of all rates in pt bins and eta regions.
"""
import os
import re
from typing import Any, Optional, Union

import awkward as ak
import numpy as np

from menu_tools.object_performance.purity_collection import delta_phi, ratio_with_cp
from menu_tools.object_performance.resolution_collection import make_edges
from menu_tools.object_performance.turnon_collection import (
    ArrayLoader,
    TurnOnCollection,
)
from menu_tools.utils import constants
from menu_tools.utils.objects import (
    CUT_FIELD_RE,
    Object,
    compute_selection_mask_for_object_cuts,
)

FLAVOURS = ("b", "c", "light", "pu")
# Category codes of the jets: hadronFlavour for matched jets, and two special values.
HADRON_FLAVOUR = {"b": 5, "c": 4, "light": 0}
PU_CODE = -1
AMBIGUOUS_CODE = -2
FLAVOUR_CODE = {**HADRON_FLAVOUR, "pu": PU_CODE}

VS_VARIABLES = ("pt", "genpt", "eta", "abseta", "pu")
DEFAULT_VS = {"pt": {"edges": [20, 30, 40, 50, 60, 80, 100, 150, 200, 300, 500]}}
DEFAULT_GEN = {"object": "GenJet", "label": "GenJet", "cuts": ["{pt} > 10"]}

# Events are processed in slices of this size for the reco x gen pairing.
CHUNK = 200_000


def closest_match(
    reco: ak.Array, gen: ak.Array, chunk: int = CHUNK
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per reco jet: distance to the closest gen jet, its flavour and its pt.

    reco, gen: jagged records (one row per event, same length); reco with eta, phi;
    gen with eta, phi, pt, flavour. Returns flat numpy arrays (reco-jet order): dR (inf
    if the event has no gen jet), flavour (-99 if none) and gen pt (NaN if none).
    """
    drs, flavs, pts = [], [], []
    for start in range(0, len(reco), chunk):
        r = reco[start : start + chunk]
        g = gen[start : start + chunk]
        pairs = ak.cartesian({"r": r[["eta", "phi"]], "g": g}, nested=True)
        deta = pairs.r.eta - pairs.g.eta
        dphi = delta_phi(pairs.r.phi, pairs.g.phi)
        dr2 = deta * deta + dphi * dphi
        imin = ak.argmin(dr2, axis=2, keepdims=True)
        # fill_none before flattening: flatten(axis=None) would drop the missing values
        dmin = ak.fill_none(ak.firsts(dr2[imin], axis=2), np.inf)
        drs.append(np.sqrt(ak.to_numpy(ak.flatten(dmin, axis=1)).astype(float)))
        fl = ak.fill_none(ak.firsts(pairs.g.flavour[imin], axis=2), -99)
        flavs.append(ak.to_numpy(ak.flatten(fl, axis=1)).astype(np.int64))
        gp = ak.fill_none(ak.firsts(pairs.g.pt[imin], axis=2), np.nan)
        pts.append(ak.to_numpy(ak.flatten(gp, axis=1)).astype(float))
    if not drs:
        return np.zeros(0), np.zeros(0, np.int64), np.zeros(0)
    return np.concatenate(drs), np.concatenate(flavs), np.concatenate(pts)


def jet_category(
    dr: np.ndarray, flavour: np.ndarray, match_dR: float, pu_dR: float
) -> np.ndarray:
    """Truth category code per jet: hadronFlavour (5, 4, 0) if the closest gen jet is
    within `match_dR`, PU_CODE if no gen jet is within `pu_dR`, else AMBIGUOUS_CODE.
    Other hadronFlavour values (none in nano) also count as ambiguous."""
    cat = np.full(len(dr), AMBIGUOUS_CODE, dtype=np.int64)
    matched = dr < match_dR
    known = np.isin(flavour, list(HADRON_FLAVOUR.values()))
    cat[matched & known] = flavour[matched & known]
    cat[dr >= pu_dR] = PU_CODE
    return cat


def rate_above(scores: np.ndarray, thresholds: np.ndarray) -> np.ndarray:
    """Fraction of `scores` strictly above each threshold (NaN for no scores)."""
    if len(scores) == 0:
        return np.full(len(thresholds), np.nan)
    s = np.sort(scores)
    return 1.0 - np.searchsorted(s, thresholds, side="right") / len(s)


def roc_thresholds(scores: np.ndarray, n_max: int = 400) -> np.ndarray:
    """Discriminant thresholds for a ROC curve: all distinct values (quantized scores,
    e.g. the L1 ones) or `n_max` quantiles, plus one value below the minimum (all jets
    tagged).
    """
    if len(scores) == 0:
        return np.zeros(0)
    uniq = np.unique(scores)
    if len(uniq) > n_max:
        uniq = np.unique(np.quantile(scores, np.linspace(0, 1, n_max + 1)))
    return np.concatenate([[uniq[0] - 1.0], uniq])


def threshold_for_target(
    scores: np.ndarray, target: float
) -> Optional[tuple[float, float]]:
    """Smallest threshold t among the score values with fraction(score > t) <= target,
    and that fraction. None for no scores."""
    if len(scores) == 0:
        return None
    thr = roc_thresholds(scores, n_max=100_000)
    rate = rate_above(scores, thr)
    ok = np.nonzero(rate <= target)[0]
    i = ok[0] if len(ok) else len(thr) - 1
    return float(thr[i]), float(rate[i])


def _bin_label(lo: float, hi: Optional[float]) -> str:
    return f"pt{lo:g}to{'Inf' if hi is None else f'{hi:g}'}"


class BTagConfig:
    """The `btag:` block of a plot config.

    btag:
      discriminants:                   # per test object: expression, or {name: expr}
        L1puppiJetSC4NG:default: "{bTagScore}"
        hltAK4PuppiJetCorr:default: {probb: "{DeepFlavour_prob_b}"}
      working_points:                  # per test object: ids of the same object, whose
        L1puppiJetSC4NG:default: [bTagLight10, bTagLight1]  # cuts define the tag
      reference_gen:                   # gen jets (default: GenJet with pt > 10)
        object: GenJet
        cuts: ["{pt} > 10"]
      flavour_field: hadronFlavour
      match_dR: 0.2                    # flavour matching (default: object's match_dR)
      pu_dR: 0.4                       # no gen jet within pu_dR: pileup jet
      max_abs_eta: 2.4                 # reco-jet |eta| cut
      min_pt: 30                       # reco-jet pt cut of the vs eta / pu plots
      flavours: [b, c, light, pu]
      vs:                              # pt: reco-jet pt; genpt: matched gen-jet pt
        pt: {edges: [20, 30, 50, 100, 200]}
        eta: {min: -2.4, max: 2.4, step: 0.2}
        pu: {edges: [140, 180, 200, 220, 260]}
      roc:
        pt_bins: [[30, 100], [100, null]]   # reco-jet pt bins (null: no upper edge)
        against: [light, c, pu]
        eta_region: [0, 2.4]           # optional |eta| range of the ROC jets
        target_misid: {light: [0.1, 0.01]}  # thresholds at these mis-id rates (json)
      summary:
        pt_bins: [[30, 100], [100, null]]
        eta_regions: {inclusive: [0, 2.4], barrel: [0, 1.5]}
      pu_variable: nPU
      pileup_version: null
    """

    def __init__(self, cfg: Optional[dict], test_keys: dict[str, str]) -> None:
        """test_keys: config key of each test object -> normalized key (str(Object))."""
        cfg = cfg or {}
        self.reference_gen: dict = dict(cfg.get("reference_gen") or DEFAULT_GEN)
        if "object" not in self.reference_gen:
            raise KeyError("btag: `reference_gen` needs an `object`")
        self.flavour_field: str = cfg.get("flavour_field", "hadronFlavour")
        self.match_dR: Optional[float] = cfg.get("match_dR")
        self.pu_dR: float = float(cfg.get("pu_dR", 0.4))
        self.max_abs_eta: float = float(cfg.get("max_abs_eta", 2.4))
        self.min_pt: float = float(cfg.get("min_pt", 30))
        self.flavours: list[str] = list(cfg.get("flavours", FLAVOURS))
        for f in self.flavours:
            if f not in FLAVOURS:
                raise ValueError(f"btag: unknown flavour `{f}`, use one of {FLAVOURS}")
        vs = cfg.get("vs") or DEFAULT_VS
        for name in vs:
            if name not in VS_VARIABLES:
                raise ValueError(
                    f"btag: unknown `vs` variable `{name}`, use one of {VS_VARIABLES}"
                )
        self.vs: dict[str, Any] = dict(vs)
        self.pu_variable: str = cfg.get("pu_variable", "nPU").removeprefix("Pileup_")
        self.pileup_version: Optional[str] = cfg.get("pileup_version")

        # Per-object settings, keyed by the normalized test-object key
        by_norm = {v: k for k, v in test_keys.items()}

        def per_object(block: Optional[dict], what: str) -> dict:
            out = {}
            for key, val in (block or {}).items():
                norm = test_keys.get(key, key)
                if norm not in by_norm:
                    raise KeyError(f"btag: `{what}` for `{key}`, not a test object")
                out[norm] = val
            return out

        discs = per_object(cfg.get("discriminants"), "discriminants")
        self.discriminants: dict[str, dict[str, str]] = {}
        for norm in by_norm:
            if norm not in discs:
                raise KeyError(f"btag: no `discriminants` entry for {by_norm[norm]}")
            d = discs[norm]
            self.discriminants[norm] = dict(d) if isinstance(d, dict) else {"": d}
        wps = per_object(cfg.get("working_points"), "working_points")
        self.working_points: dict[str, list[str]] = {
            norm: list(wps.get(norm, [])) for norm in by_norm
        }

        roc = cfg.get("roc") or {}
        self.roc_pt_bins: list[tuple[float, Optional[float]]] = [
            (float(lo), None if hi is None else float(hi))
            for lo, hi in roc.get("pt_bins", [[30, 100], [100, None]])
        ]
        self.roc_against: list[str] = list(roc.get("against", ["light", "c", "pu"]))
        for f in self.roc_against:
            if f not in FLAVOURS or f == "b":
                raise ValueError(
                    f"btag: roc `against` must be c / light / pu, not `{f}`"
                )
        region = roc.get("eta_region")
        self.roc_eta_region: Optional[tuple[float, float]] = (
            (float(region[0]), float(region[1])) if region else None
        )
        self.target_misid: dict[str, list[float]] = {
            f: [float(t) for t in ts]
            for f, ts in (roc.get("target_misid") or {}).items()
        }
        summ = cfg.get("summary") or {}
        self.summary_pt_bins: list[tuple[float, Optional[float]]] = [
            (float(lo), None if hi is None else float(hi))
            for lo, hi in summ.get("pt_bins", self.roc_pt_bins)
        ]
        regions = summ.get("eta_regions") or {"inclusive": [0, self.max_abs_eta]}
        self.summary_eta_regions: dict[str, tuple[float, float]] = {
            k: (float(v[0]), float(v[1])) for k, v in regions.items()
        }

    def vs_edges(self, name: str) -> np.ndarray:
        return make_edges(self.vs[name])

    def vs_label(self, name: str) -> Optional[str]:
        spec = self.vs[name]
        return spec.get("label") if isinstance(spec, dict) else None


class BTagCollection(TurnOnCollection):
    """Reco jets of each test object with their truth category, discriminants and tags.

    After `create()`:
      jets[obj]: flat numpy arrays pt, eta, event, category, genpt, dr (matching cone),
                 disc[name], tag[wp_key]
      wp_labels[obj][wp_key]: legend label of each working point
      n_events, pileup (per event, or None)
      eff_plots: list of {"flavour", "vs", "edges", "min_pt", "series"}, series keyed by
                 (object, working point)
      rocs: list of {"against", "pt_bin", "eta_region", "curves", "wps", "targets"}
      summary: list of rows {object, wp, flavour, pt_bin, eta_region, eff, err_lo,
               err_hi, num, den}
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
        test_keys = {key: str(obj) for key, obj in self._config_objects().items()}
        self.btag_cfg = BTagConfig(self.cfg_plot.config_dict.get("btag"), test_keys)
        self.jets: dict[str, dict[str, Any]] = {}
        self.wp_labels: dict[str, dict[str, str]] = {}
        self.n_events: int = 0
        self.pileup: Optional[np.ndarray] = None
        self.pileup_source: Optional[str] = None
        self.eff_plots: list[dict] = []
        self.rocs: list[dict] = []
        self.summary: list[dict] = []

    # ---- objects -------------------------------------------------------------------

    @property
    def obj_version(self) -> str:
        if self._override_version and self._config_version:
            return self._config_version
        return self.version

    def _config_objects(self) -> dict[str, Object]:
        return {
            key: Object(key, self.obj_version) for key in self.cfg_plot.test_objects
        }

    def wp_objects(self, test_obj: Object) -> dict[str, Object]:
        """Working-point objects of a test object: `<object>:<id>` -> Object."""
        out = {}
        for wp in self.btag_cfg.working_points[str(test_obj)]:
            key = wp if ":" in wp else f"{test_obj.nano_obj_name}:{wp}"
            obj = Object(key, self.obj_version)
            if obj.nano_obj_name != test_obj.nano_obj_name:
                raise ValueError(
                    f"btag: working point {key} is not an id of "
                    f"{test_obj.nano_obj_name}"
                )
            out[f"{obj.nano_obj_name}:{obj.obj_id_name}"] = obj
        return out

    # ---- loading -------------------------------------------------------------------

    @staticmethod
    def _cut_fields(cuts: Union[None, list[str], dict[str, list[str]]]) -> set[str]:
        """Field names used in a list of cut strings (or a dict of such lists)."""
        if isinstance(cuts, dict):
            cuts = [c for v in cuts.values() for c in v]
        return {f for c in cuts or [] for f in re.findall(CUT_FIELD_RE, c)}

    def _load_parquet(self, name: str, fields: set[str]) -> ak.Array:
        """The needed columns of <version>_<sample>_<name>.parquet, as a record array
        with the field names of `ArrayLoader` (prefix stripped)."""
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
        missing = fields - {loader._transform_key(c, name) for c in cols}
        if missing:
            raise KeyError(f"{fname} has no field(s) {sorted(missing)}")
        try:
            arr = ak.from_parquet(fname, columns=cols)
        except Exception:
            # Caches written as one awkward record column cannot be pruned by pyarrow.
            arr = ak.from_parquet(fname)[cols]
        return ak.zip({loader._transform_key(k, name): arr[k] for k in cols})

    def _load_gen(self) -> ak.Array:
        spec = self.btag_cfg.reference_gen
        flav = self.btag_cfg.flavour_field
        cuts = spec.get("cuts", [])
        fields = {"pt", "eta", "phi", flav} | self._cut_fields(cuts)
        arr = self._load_parquet(spec["object"], fields)
        for cut in cuts:
            arr = arr[eval(re.sub(CUT_FIELD_RE, r"arr['\1']", cut))]
        return ak.zip(
            {
                "pt": arr["pt"],
                "eta": arr["eta"],
                "phi": arr["phi"],
                "flavour": ak.values_astype(arr[flav], np.int64),
            }
        )

    def _pileup_file(self) -> Optional[str]:
        version, sample = self.cfg_plot.version, self.cfg_plot.sample
        pv = self.btag_cfg.pileup_version
        for v in [pv] if pv else [version, version + "PU"]:
            fname = f"{constants.CACHE_DIR}/{v}/{v}_{sample}_Pileup.parquet"
            if os.path.exists(fname):
                return fname
        return None

    def _load_pileup(self) -> None:
        fname = self._pileup_file()
        if fname is None:
            print(
                f"WARNING: no Pileup parquet for {self.cfg_plot.version} / "
                f"{self.cfg_plot.sample}: skipping the pileup binning"
            )
            return
        arr = ak.from_parquet(fname)
        var = self.btag_cfg.pu_variable
        field = next((f for f in arr.fields if f.removeprefix("Pileup_") == var), None)
        if field is None:
            raise KeyError(f"{fname} has no field `{var}` (fields: {arr.fields})")
        pileup = ak.to_numpy(arr[field]).astype(float)
        if len(pileup) != self.n_events:
            raise ValueError(
                f"{fname} has {len(pileup)} events, the jets {self.n_events}: "
                "not row-aligned"
            )
        self.pileup = pileup
        self.pileup_source = fname

    # ---- per-jet arrays ------------------------------------------------------------

    @staticmethod
    def _eval_expr(expr: str, arr: ak.Array) -> ak.Array:
        return eval(re.sub(CUT_FIELD_RE, r"arr['\1']", expr))

    def _build_jets(self, gen: ak.Array) -> None:
        cfg = self.btag_cfg
        for test_obj in self._config_objects().values():
            key = str(test_obj)
            wps = self.wp_objects(test_obj)
            fields = {"pt", "eta", "phi"} | self._cut_fields(test_obj.cuts)
            for expr in cfg.discriminants[key].values():
                fields |= self._cut_fields([expr])
            for wp in wps.values():
                fields |= self._cut_fields(wp.cuts)
            arr = self._load_parquet(test_obj.nano_obj_name, fields)
            if self.n_events and len(arr) != self.n_events:
                raise ValueError(
                    f"{key} has {len(arr)} events, the other objects {self.n_events}"
                )
            self.n_events = len(arr)
            if len(gen) != self.n_events:
                raise ValueError(
                    f"gen jets have {len(gen)} events, {key} {self.n_events}"
                )
            sel = compute_selection_mask_for_object_cuts(test_obj, arr)
            arr = arr[sel & (abs(arr["eta"]) < cfg.max_abs_eta)]

            flat = lambda a: ak.to_numpy(ak.flatten(a, axis=None))  # noqa: E731
            dr_match = float(
                cfg.match_dR if cfg.match_dR is not None else test_obj.match_dR
            )
            dr, flav, genpt = closest_match(arr, gen)
            category = jet_category(dr, flav, dr_match, cfg.pu_dR)
            event = ak.broadcast_arrays(ak.local_index(arr, axis=0), arr["pt"])[0]
            jets: dict[str, Any] = {
                "pt": flat(arr["pt"]).astype(float),
                "eta": flat(arr["eta"]).astype(float),
                "event": flat(event).astype(np.int64),
                "category": category,
                "genpt": np.where(dr < dr_match, genpt, np.nan),
                "dr": dr_match,
                "disc": {
                    name: flat(self._eval_expr(expr, arr)).astype(float)
                    for name, expr in cfg.discriminants[key].items()
                },
                "tag": {
                    wp_key: flat(
                        compute_selection_mask_for_object_cuts(wp, arr)
                    ).astype(bool)
                    for wp_key, wp in wps.items()
                },
            }
            self.jets[key] = jets
            self.wp_labels[key] = {wp_key: wp.plot_label for wp_key, wp in wps.items()}

    # ---- quantities ----------------------------------------------------------------

    def _x(self, jets: dict, vs: str) -> np.ndarray:
        if vs == "abseta":
            return np.abs(jets["eta"])
        if vs == "pu":
            assert self.pileup is not None
            return self.pileup[jets["event"]]
        return jets[vs]

    def _eff_plot(self, flavour: str, vs: str) -> None:
        edges = self.btag_cfg.vs_edges(vs)
        min_pt = None if vs in ("pt", "genpt") else self.btag_cfg.min_pt
        series = {}
        for key, jets in self.jets.items():
            sel = jets["category"] == FLAVOUR_CODE[flavour]
            if min_pt is not None:
                sel &= jets["pt"] >= min_pt
            x = self._x(jets, vs)[sel]
            den = np.histogram(x, bins=edges)[0]
            for wp_key, tag in jets["tag"].items():
                num = np.histogram(x[tag[sel]], bins=edges)[0]
                y, lo, hi = ratio_with_cp(num, den)
                series[(key, wp_key)] = {
                    "y": y,
                    "err_lo": lo,
                    "err_hi": hi,
                    "num": num,
                    "den": den,
                }
        self.eff_plots.append(
            {
                "flavour": flavour,
                "vs": vs,
                "edges": edges,
                "min_pt": min_pt,
                "series": series,
            }
        )

    @staticmethod
    def _in_bin(
        jets: dict, pt_bin: tuple[float, Optional[float]], region: Optional[tuple]
    ) -> np.ndarray:
        lo, hi = pt_bin
        sel = jets["pt"] >= lo
        if hi is not None:
            sel &= jets["pt"] < hi
        if region is not None:
            ae = np.abs(jets["eta"])
            sel &= (ae >= region[0]) & (ae < region[1])
        return sel

    def _roc(self, against: str, pt_bin: tuple[float, Optional[float]]) -> None:
        region = self.btag_cfg.roc_eta_region
        curves, wps, targets = {}, {}, {}
        for key, jets in self.jets.items():
            sel = self._in_bin(jets, pt_bin, region)
            is_b = sel & (jets["category"] == FLAVOUR_CODE["b"])
            is_x = sel & (jets["category"] == FLAVOUR_CODE[against])
            for name, disc in jets["disc"].items():
                sb, sx = disc[is_b], disc[is_x]
                thr = roc_thresholds(np.concatenate([sb, sx]))
                eff_b, mis = rate_above(sb, thr), rate_above(sx, thr)
                curves[(key, name)] = {
                    "threshold": thr,
                    "eff_b": eff_b,
                    "misid": mis,
                    "n_b": int(is_b.sum()),
                    "n_x": int(is_x.sum()),
                }
                for t in self.btag_cfg.target_misid.get(against, []):
                    found = threshold_for_target(sx, t)
                    if found is None:
                        continue
                    t_cut, rate = found
                    targets[(key, name, t)] = {
                        "threshold": t_cut,
                        "misid": rate,
                        "eff_b": float(rate_above(sb, np.array([t_cut]))[0]),
                    }
            for wp_key, tag in jets["tag"].items():
                eb = ratio_with_cp(np.array([tag[is_b].sum()]), np.array([is_b.sum()]))
                ex = ratio_with_cp(np.array([tag[is_x].sum()]), np.array([is_x.sum()]))
                wps[(key, wp_key)] = {
                    "eff_b": float(eb[0][0]),
                    "eff_b_err": [float(eb[1][0]), float(eb[2][0])],
                    "misid": float(ex[0][0]),
                    "misid_err": [float(ex[1][0]), float(ex[2][0])],
                }
        self.rocs.append(
            {
                "against": against,
                "pt_bin": pt_bin,
                "eta_region": region,
                "curves": curves,
                "wps": wps,
                "targets": targets,
            }
        )

    def _summary(self) -> None:
        cfg = self.btag_cfg
        for key, jets in self.jets.items():
            for region_name, region in cfg.summary_eta_regions.items():
                for pt_bin in cfg.summary_pt_bins:
                    sel = self._in_bin(jets, pt_bin, region)
                    for flavour in cfg.flavours:
                        is_f = sel & (jets["category"] == FLAVOUR_CODE[flavour])
                        for wp_key, tag in jets["tag"].items():
                            n_pass, n = int(tag[is_f].sum()), int(is_f.sum())
                            y, lo, hi = ratio_with_cp(np.array([n_pass]), np.array([n]))
                            self.summary.append(
                                {
                                    "object": key,
                                    "wp": wp_key,
                                    "flavour": flavour,
                                    "pt_bin": [pt_bin[0], pt_bin[1]],
                                    "eta_region": region_name,
                                    "eta_range": list(region),
                                    "eff": float(y[0]),
                                    "err_lo": float(lo[0]),
                                    "err_hi": float(hi[0]),
                                    "num": n_pass,
                                    "den": n,
                                }
                            )

    def category_counts(self) -> dict[str, dict[str, int]]:
        """Number of jets per truth category (and ambiguous) of each object."""
        names = {**FLAVOUR_CODE, "ambiguous": AMBIGUOUS_CODE}
        return {
            key: {n: int((j["category"] == c).sum()) for n, c in names.items()}
            for key, j in self.jets.items()
        }

    def create(self) -> None:
        gen = self._load_gen()
        self._build_jets(gen)
        del gen
        vs_all = list(self.btag_cfg.vs)
        if "pu" in vs_all:
            self._load_pileup()
            if self.pileup is None:
                vs_all.remove("pu")
        for flavour in self.btag_cfg.flavours:
            for vs in vs_all:
                if vs == "genpt" and flavour == "pu":
                    continue  # pileup jets have no gen jet
                self._eff_plot(flavour, vs)
        for against in self.btag_cfg.roc_against:
            for pt_bin in self.btag_cfg.roc_pt_bins:
                self._roc(against, pt_bin)
        self._summary()

    @staticmethod
    def bin_label(pt_bin: tuple[float, Optional[float]]) -> str:
        return _bin_label(*pt_bin)

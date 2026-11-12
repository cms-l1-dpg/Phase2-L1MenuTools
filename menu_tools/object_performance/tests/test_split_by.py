"""
Synthetic tests of `split_by` (efficiencies and resolutions split by categories of a
reference field, e.g. the generator tau decay mode `status` of GenVisTau): known category
fractions and per-category efficiencies / responses must be reproduced, and nothing must
change without `split_by`.

Run from the repository root (object definitions are read from configs/V50nano/objects).
"""
import awkward as ak
import numpy as np
import pytest
import vector

from menu_tools.object_performance.plotter import EfficiencyPlotter
from menu_tools.object_performance.resolution_collection import ResolutionCollection
from menu_tools.object_performance.split import SplitConfig, safe_name
from menu_tools.object_performance.turnon_collection import (
    L1SEED_KEY,
    L1SEED_SUFFIX,
    TurnOnCollection,
)

vector.register_awkward()

THR = 24
SPLIT = {
    "field": "status",
    "name": "DM",
    "categories": {
        "1-prong": [0],
        "1-prong + $\\pi^0$s": [1, 2],
        "3-prong": [10],
        "3-prong + $\\pi^0$": [11],
    },
}
# Per decay mode: number of reference taus, and how many of them have a matched test
# object with pT 40 (passes THR) / pT 10 (matched, fails THR) / an L1 seed object.
#           status: (n, n_pass, n_fail, n_l1)
LAYOUT = {
    0: (200, 200, 0, 100),
    1: (300, 150, 50, 300),
    2: (100, 0, 0, 0),
    10: (150, 0, 150, 150),
    11: (100, 50, 0, 50),
    15: (150, 150, 0, 150),  # "other": inclusive curve only
}
N_EV = sum(v[0] for v in LAYOUT.values())


def _vec(pt, eta, phi, **extra):
    fields = {"pt": pt, "eta": eta, "phi": phi, "mass": [[0.0] * len(x) for x in pt]}
    fields.update(extra)
    return ak.with_name(ak.zip(fields), "Momentum4D")


def _events():
    """One reference tau (pT 50) per event; test / L1 objects at its position."""
    status, hlt_pt, l1_pt = [], [], []
    for st, (n, n_pass, n_fail, n_l1) in LAYOUT.items():
        for i in range(n):
            status.append(st)
            hlt_pt.append(
                [40.0] if i < n_pass else [10.0] if i < n_pass + n_fail else []
            )
            l1_pt.append([30.0] if i < n_l1 else [])
    eta = [0.001 * (i % 1000) for i in range(N_EV)]
    phi = [0.0] * N_EV
    ref = _vec(
        [[50.0]] * N_EV,
        [[e] for e in eta],
        [[p] for p in phi],
        status=[[s] for s in status],
    )

    def objs(pts):
        return _vec(
            pts,
            [[eta[i]] * len(p) for i, p in enumerate(pts)],
            [[phi[i]] * len(p) for i, p in enumerate(pts)],
        )

    return ref, objs(hlt_pt), objs(l1_pt)


def _cfg(split=SPLIT, l1_seed=None, matching_and_threshold=True, layout=None):
    cfg = {
        "sample": "synthetic",
        "version": "V50nano",
        "match_test_to_ref": True,
        "matching_and_threshold": matching_and_threshold,
        "reference_object": {"object": "GenVisTau", "x_arg": "pt", "label": "Gen"},
        "test_objects": {"hltMuon:default": "pt"},
        "thresholds": [THR],
        "binning": {"min": 0, "max": 100, "step": 25},
        "xlabel": "x",
        "ylabel": "y",
    }
    if split is not None:
        cfg["split_by"] = dict(split, **({"layout": layout} if layout else {}))
    if l1_seed is not None:
        cfg["l1_seed"] = l1_seed
    return cfg


def _collection(threshold=THR, **kw):
    coll = TurnOnCollection(_cfg(**kw), threshold=threshold, plot_name="synthetic")
    ref, hlt, l1 = _events()
    coll.ak_arrays["ref"] = ref
    key = str(coll.test_objects[0][0])
    coll.ak_arrays[key] = hlt
    for i, (obj, _, _) in enumerate(coll.l1_seed_objects):
        coll.ak_arrays[coll._l1_seed_key(i, obj)] = l1
    coll._check_split()
    if coll.cfg_plot.l1_seed is not None:
        coll._match_l1_seed_to_ref()
    coll._match_test_to_ref()
    coll.set_threshold(threshold)
    return coll, key


def _counts(hists, key):
    """(numerator, denominator); all reference objects are in the [50, 75) bin."""
    num, den = hists[key][0], hists["ref"][key][0]
    assert num.sum() == num[2] and den.sum() == den[2]
    return int(num[2]), int(den[2])


def _expected(statuses, col):
    return sum(LAYOUT[s][col] for s in statuses)


def test_split_config():
    cfg = SplitConfig(SPLIT)
    assert cfg.layout == "per_object" and cfg.name == "DM"
    names = cfg.assign(np.array([0, 1, 2, 10, 11, 15]))
    assert list(names) == [
        "1-prong",
        "1-prong + $\\pi^0$s",
        "1-prong + $\\pi^0$s",
        "3-prong",
        "3-prong + $\\pi^0$",
        "other",
    ]
    assert SplitConfig({"field": "x", "categories": {"a": 1}}).name == "by_x"
    with pytest.raises(ValueError, match="share"):
        SplitConfig({"field": "x", "categories": {"a": [1], "b": [1, 2]}})
    with pytest.raises(ValueError, match="reserved"):
        SplitConfig({"field": "x", "categories": {"other": [1]}})
    with pytest.raises(ValueError, match="layout"):
        SplitConfig({"field": "x", "categories": {"a": [1]}, "layout": "grid"})
    assert safe_name("1-prong + $\\pi^0$s") == "1-prong_pi0s"
    assert safe_name("hltHpsPFTau:default+L1seed") == "hltHpsPFTau-default_L1seed"


@pytest.mark.parametrize("matching_and_threshold", [True, False])
def test_split_trigger_efficiency(matching_and_threshold):
    coll, key = _collection(matching_and_threshold=matching_and_threshold)
    cats = SplitConfig(SPLIT).categories
    total_num = total_den = 0
    for cat, statuses in cats.items():
        num, den = _counts(coll.split_hists[cat], key)
        assert num == _expected(statuses, 1)
        if matching_and_threshold:  # all reference taus of the category
            assert den == _expected(statuses, 0)
        else:  # matched reference taus only
            assert den == _expected(statuses, 1) + _expected(statuses, 2)
        total_num += num
        total_den += den
    # the inclusive curve is unchanged and contains "other" (status 15) as well
    num, den = _counts(coll.hists, key)
    assert num == total_num + LAYOUT[15][1]
    assert den == total_den + (
        LAYOUT[15][0] if matching_and_threshold else LAYOUT[15][1] + LAYOUT[15][2]
    )


def test_split_matching_efficiency():
    coll, key = _collection(threshold=-999)
    eff, _ = coll.get_efficiency(key, coll.split_hists["3-prong"])
    assert eff[2] == pytest.approx(1.0)  # all 3-prongs matched (to pT 10 objects)
    eff, _ = coll.get_efficiency(key, coll.split_hists["1-prong + $\\pi^0$s"])
    assert eff[2] == pytest.approx(200 / 400)


def test_split_l1_seed():
    seed = {"object": "L1gmtTkMuon:VLoose", "threshold": 20}
    coll, key = _collection(l1_seed=seed)
    hists = coll.split_hists["1-prong"]
    assert _counts(hists, L1SEED_KEY) == (100, 200)
    assert _counts(hists, key + L1SEED_SUFFIX) == (100, 200)
    hists = coll.split_hists["3-prong"]
    assert _counts(hists, L1SEED_KEY) == (150, 150)
    assert _counts(hists, key + L1SEED_SUFFIX) == (0, 150)
    hists = coll.split_hists["1-prong + $\\pi^0$s"]
    assert _counts(hists, key + L1SEED_SUFFIX) == (150, 400)


def test_split_fractions_and_plots():
    coll, key = _collection()
    plotter = EfficiencyPlotter("synthetic", None, coll)
    table = plotter._split_fractions()
    ref = table["reference"]
    assert ref["n"] == N_EV
    assert ref["categories"]["1-prong + $\\pi^0$s"]["n"] == 400
    assert ref["categories"]["other"]["fraction"] == pytest.approx(150 / N_EV)
    curve = table["curves"][key]
    assert curve["inclusive"]["n_den"] == N_EV
    assert curve["3-prong + $\\pi^0$"]["efficiency"] == pytest.approx(0.5)
    assert curve["3-prong + $\\pi^0$"]["fraction"] == pytest.approx(100 / N_EV)
    assert curve["other"]["n_den"] == 150
    # per_object: one plot per curve, inclusive + one curve per category
    plots = plotter._split_plots()
    assert [p[0] for p in plots] == [safe_name(key)]
    assert [c[0] for c in plots[0][2]] == ["inclusive"] + list(SPLIT["categories"])
    # per_category: one plot per category, all curves
    coll, key = _collection(layout="per_category")
    plots = EfficiencyPlotter("synthetic", None, coll)._split_plots()
    assert len(plots) == 4 and all(len(p[2]) == 1 for p in plots)


def test_without_split_unchanged():
    coll, key = _collection(split=None)
    assert coll.split_hists == {}
    coll_split, _ = _collection()
    np.testing.assert_array_equal(coll.hists[key][0], coll_split.hists[key][0])
    np.testing.assert_array_equal(
        coll.hists["ref"][key][0], coll_split.hists["ref"][key][0]
    )


def test_split_missing_field():
    coll = TurnOnCollection(_cfg(split={**SPLIT, "field": "nope"}), threshold=THR)
    coll.ak_arrays["ref"] = _events()[0]
    with pytest.raises(KeyError, match="nope"):
        coll._check_split()


def test_split_resolution(monkeypatch):
    """Per decay mode a different pT scale: the split medians recover it."""
    scales = {0: 0.9, 1: 1.0, 2: 1.1, 10: 1.2, 11: 1.3, 15: 2.0}
    rng = np.random.default_rng(4)
    n = 6000
    status = rng.choice(list(scales), n)
    ref_pt = rng.uniform(20, 100, n)
    test_pt = ref_pt * np.array([scales[s] for s in status])
    eta = rng.uniform(-2, 2, n)
    phi = rng.uniform(-3, 3, n)
    ref = _vec(
        ref_pt[:, None].tolist(),
        eta[:, None].tolist(),
        phi[:, None].tolist(),
        status=status[:, None].tolist(),
    )
    test = _vec(test_pt[:, None].tolist(), eta[:, None].tolist(), phi[:, None].tolist())
    cfg = _cfg()
    del cfg["matching_and_threshold"], cfg["thresholds"]
    cfg["resolution"] = {"variables": ["pt"], "vs": {"pt": {"edges": [20, 60, 100]}}}
    coll = ResolutionCollection(cfg, "synthetic")
    key = str(coll.test_objects[0][0])

    def fake_load(self=coll):
        coll.ak_arrays["ref"] = ref
        coll.ak_arrays[key] = test

    monkeypatch.setattr(coll, "_load_arrays", fake_load)
    coll.create()
    for cat, statuses in SPLIT["categories"].items():
        res = coll.split_results[cat]["pt"]["pt"][key]
        if len(statuses) == 1:
            np.testing.assert_allclose(res["median"], scales[statuses[0]], atol=1e-6)
        assert sum(res["n"]) == int(np.isin(status, statuses).sum())
    # inclusive unchanged, includes "other"
    assert sum(coll.results["pt"]["pt"][key]["n"]) == n

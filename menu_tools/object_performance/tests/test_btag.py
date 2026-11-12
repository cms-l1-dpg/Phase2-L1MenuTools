"""
b-tag efficiency / mis-id on a synthetic cache with known flavour and tag fractions
(parquet files in tmp_path, constants.CACHE_DIR monkeypatched).

Per event k (N_EVENTS a multiple of 20): one gen b, c and light jet, each with a reco
jet at dR = 0.05; one pileup reco jet far from all gen jets; one reco jet at dR = 0.3
from a gen jet (ambiguous: neither matched nor pileup); one forward b jet at |eta| = 3
(outside the |eta| < 2.4 acceptance). Scores (L1puppiJetSC4NG bTagScore): 0.5 passes
both working points used (bjetnn: > 0.15, bTagLight10: > 0.29), 0.2 only bjetnn, 0 none:
  b:     0.5 if k%10 < 5, 0.2 if k%10 in (5, 6), else 0   -> eff 0.7 / 0.5
  c:     0.5 if k%10 < 3                                   -> 0.3 / 0.3
  light: 0.5 if k%10 < 1                                   -> 0.1 / 0.1
  pu:    0.2 if k%20 < 1                                   -> 0.05 / 0

Run from the repository root (object definitions are read from configs/V50nano/objects).
"""
import json
import os

import awkward as ak
import numpy as np
import pytest

from menu_tools.object_performance.btag_collection import (
    AMBIGUOUS_CODE,
    PU_CODE,
    BTagCollection,
    closest_match,
    jet_category,
    rate_above,
    roc_thresholds,
    threshold_for_target,
)
from menu_tools.utils import constants

N_EVENTS = 2000
VERSION = "V50nano"
SAMPLE = "synthetic"
OBJ = "L1puppiJetSC4NG:default"
KEY = "L1puppiJetSC4NG:default:inclusive"
WP_LOOSE = "L1puppiJetSC4NG:bjetnn"
WP_TIGHT = "L1puppiJetSC4NG:bTagLight10"
EXPECTED = {  # flavour: (eff bjetnn, eff bTagLight10)
    "b": (0.7, 0.5),
    "c": (0.3, 0.3),
    "light": (0.1, 0.1),
    "pu": (0.05, 0.0),
}


def _make_events(seed=3):
    rng = np.random.default_rng(seed)
    gen = {"pt": [], "eta": [], "phi": [], "hadronFlavour": []}
    reco = {"pt": [], "eta": [], "phi": [], "bTagScore": []}
    for k in range(N_EVENTS):
        m10, m20 = k % 10, k % 20
        s_b = 0.5 if m10 < 5 else (0.2 if m10 < 7 else 0.0)
        s_c = 0.5 if m10 < 3 else 0.0
        s_l = 0.5 if m10 < 1 else 0.0
        s_pu = 0.2 if m20 < 1 else 0.0
        phi = rng.uniform(-np.pi, np.pi)
        # gen: b, c, light at phi, phi + 1.5, phi + 3; forward b; another light jet
        g_eta = [0.5, -0.5, 1.0, 3.0, -1.0]
        g_phi = [phi, phi + 1.5, phi + 3.0, phi, phi - 1.5]
        g_phi = [(p + np.pi) % (2 * np.pi) - np.pi for p in g_phi]
        gen["pt"].append(list(rng.uniform(20, 200, 5)))
        gen["eta"].append(g_eta)
        gen["phi"].append(g_phi)
        gen["hadronFlavour"].append([5, 4, 0, 5, 0])
        # reco: b, c, light matched (dR 0.05), pileup (dR > 1 from all gen jets),
        # ambiguous (dR 0.3 from the last gen light jet), forward b
        r_eta = [0.5 + 0.05, -0.5 + 0.05, 1.0 + 0.05, -2.2, -1.0 + 0.3, 3.0]
        r_phi = [g_phi[0], g_phi[1], g_phi[2], g_phi[4] + np.pi, g_phi[4], g_phi[3]]
        r_phi = [(p + np.pi) % (2 * np.pi) - np.pi for p in r_phi]
        reco["pt"].append(list(rng.uniform(30, 200, 6)))
        reco["eta"].append(r_eta)
        reco["phi"].append(r_phi)
        reco["bTagScore"].append([s_b, s_c, s_l, s_pu, 0.5, 0.5])
    pu = rng.integers(150, 250, N_EVENTS).astype(float)
    return gen, reco, pu


def _write(path, prefix, fields):
    arr = ak.zip(
        {f"{prefix}_{k}": ak.Array(v) for k, v in fields.items()}, depth_limit=1
    )
    ak.to_parquet(arr, str(path))


@pytest.fixture(scope="module")
def events():
    return _make_events()


@pytest.fixture
def cache(tmp_path, monkeypatch, events):
    gen, reco, pu = events
    d = tmp_path / VERSION
    d.mkdir()
    _write(d / f"{VERSION}_{SAMPLE}_GenJet.parquet", "GenJet", gen)
    _write(d / f"{VERSION}_{SAMPLE}_L1puppiJetSC4NG.parquet", "L1puppiJetSC4NG", reco)
    ak.to_parquet(
        ak.zip({"Pileup_nPU": pu, "Pileup_nTrueInt": np.full(N_EVENTS, 200.0)}),
        str(d / f"{VERSION}_{SAMPLE}_Pileup.parquet"),
    )
    monkeypatch.setattr(constants, "CACHE_DIR", str(tmp_path))
    return tmp_path


def _cfg(**extra):
    btag = {
        "discriminants": {OBJ: "{bTagScore}"},
        "working_points": {OBJ: ["bjetnn", "bTagLight10"]},
        "match_dR": 0.2,
        "pu_dR": 0.4,
        "vs": {
            "pt": {"edges": [30, 100, 200]},
            "genpt": {"edges": [20, 100, 200]},
            "abseta": {"edges": [0, 1.5, 2.4]},
            "pu": {"edges": [150, 200, 250]},
        },
        "roc": {
            "pt_bins": [[30, None]],
            "against": ["light", "c", "pu"],
            "target_misid": {"light": [0.1]},
        },
        "summary": {"pt_bins": [[30, None]], "eta_regions": {"inclusive": [0, 2.4]}},
    }
    btag.update(extra)
    return {
        "sample": SAMPLE,
        "version": VERSION,
        "test_objects": {OBJ: "pt"},
        "btag": btag,
    }


def _eff_plot(coll, flavour, vs):
    hits = [p for p in coll.eff_plots if p["flavour"] == flavour and p["vs"] == vs]
    assert len(hits) == 1
    return hits[0]


# ---- helpers -----------------------------------------------------------------------


def test_closest_match():
    reco = ak.Array(
        [
            [{"eta": 0.0, "phi": 3.1}, {"eta": 1.0, "phi": 0.0}],
            [{"eta": 0.0, "phi": 0.0}],
            [],
        ]
    )
    gen = ak.Array(
        [
            [
                {"eta": 0.0, "phi": -3.1, "pt": 50.0, "flavour": 5},
                {"eta": 1.0, "phi": 0.3, "pt": 20.0, "flavour": 0},
            ],
            [],
            [{"eta": 0.0, "phi": 0.0, "pt": 10.0, "flavour": 4}],
        ]
    )
    dr, flav, pt = closest_match(reco, gen, chunk=1)
    # dphi wraps around: (3.1, -3.1) are 0.083 apart; the event without gen jets: inf
    assert dr[0] == pytest.approx(2 * np.pi - 6.2)
    assert dr[1] == pytest.approx(0.3)
    assert np.isinf(dr[2])
    assert flav.tolist() == [5, 0, -99]
    assert pt[:2].tolist() == [50.0, 20.0] and np.isnan(pt[2])


def test_jet_category():
    dr = np.array([0.1, 0.1, 0.1, 0.3, 0.5, np.inf, 0.1])
    flav = np.array([5, 4, 0, 5, 5, -99, 21])
    cat = jet_category(dr, flav, match_dR=0.2, pu_dR=0.4)
    amb = AMBIGUOUS_CODE
    assert cat.tolist() == [5, 4, 0, amb, PU_CODE, PU_CODE, amb]


def test_rate_above_and_targets():
    s = np.array([0.0, 0.0, 0.2, 0.5, 0.5])
    assert rate_above(s, np.array([-1.0, 0.0, 0.2, 0.5])).tolist() == [1, 0.6, 0.4, 0]
    assert np.isnan(rate_above(np.zeros(0), np.array([0.0]))[0])
    assert roc_thresholds(s).tolist() == [-1.0, 0.0, 0.2, 0.5]
    # smallest threshold with rate <= target
    assert threshold_for_target(s, 0.5) == (0.2, pytest.approx(0.4))
    assert threshold_for_target(s, 0.0) == (0.5, 0.0)
    assert threshold_for_target(np.zeros(0), 0.1) is None


def test_config_errors(cache):
    with pytest.raises(KeyError):
        BTagCollection(_cfg(discriminants={}))
    with pytest.raises(ValueError):
        BTagCollection(_cfg(flavours=["b", "top"]))
    with pytest.raises(ValueError):
        BTagCollection(_cfg(vs={"mass": {"edges": [0, 1]}}))
    with pytest.raises(ValueError):
        BTagCollection(_cfg(roc={"against": ["b"]}))
    coll = BTagCollection(_cfg(working_points={OBJ: ["hltAK4PuppiJetCorr:default"]}))
    with pytest.raises(ValueError):
        coll.create()


# ---- collection --------------------------------------------------------------------


def test_categories(cache):
    coll = BTagCollection(_cfg())
    coll.create()
    n = N_EVENTS
    # forward jet removed by |eta| < 2.4; one ambiguous jet per event
    counts = coll.category_counts()[KEY]
    assert counts == {"b": n, "c": n, "light": n, "pu": n, "ambiguous": n}
    assert coll.n_events == n
    jets = coll.jets[KEY]
    assert np.all(np.isnan(jets["genpt"][jets["category"] == PU_CODE]))
    assert np.all(np.isfinite(jets["genpt"][jets["category"] >= 0]))


def test_summary_fractions(cache):
    coll = BTagCollection(_cfg())
    coll.create()
    rows = {(r["wp"], r["flavour"]): r for r in coll.summary}
    assert len(rows) == 2 * 4
    for flavour, (eff_loose, eff_tight) in EXPECTED.items():
        assert rows[(WP_LOOSE, flavour)]["den"] == N_EVENTS
        assert rows[(WP_LOOSE, flavour)]["eff"] == pytest.approx(eff_loose)
        assert rows[(WP_TIGHT, flavour)]["eff"] == pytest.approx(eff_tight)
        r = rows[(WP_TIGHT, flavour)]
        assert r["err_lo"] >= 0 and r["err_hi"] > 0


def test_efficiency_curves(cache):
    coll = BTagCollection(_cfg())
    coll.create()
    # vs pt: all flavours, the fractions hold in every bin within the statistical error
    for flavour, (eff_loose, _) in EXPECTED.items():
        s = _eff_plot(coll, flavour, "pt")["series"][(KEY, WP_LOOSE)]
        assert s["den"].sum() == N_EVENTS
        assert s["num"].sum() == pytest.approx(eff_loose * N_EVENTS)
        err = 0.5 * (s["err_lo"] + s["err_hi"])
        assert np.all(np.abs(s["y"] - eff_loose) < 5 * err + 1e-9)
    # no gen pt for pileup jets
    assert not [
        p for p in coll.eff_plots if p["flavour"] == "pu" and p["vs"] == "genpt"
    ]
    s = _eff_plot(coll, "b", "genpt")["series"][(KEY, WP_TIGHT)]
    assert s["num"].sum() == pytest.approx(0.5 * N_EVENTS)
    # vs |eta|: the b jet at |eta| = 0.55 in the first bin only, with min_pt 30
    p = _eff_plot(coll, "b", "abseta")
    assert p["min_pt"] == 30
    assert p["series"][(KEY, WP_LOOSE)]["den"].tolist() == [N_EVENTS, 0]
    # vs pileup (row-aligned Pileup parquet)
    s = _eff_plot(coll, "light", "pu")["series"][(KEY, WP_LOOSE)]
    assert s["den"].sum() == N_EVENTS
    assert coll.pileup_source is not None


def test_roc(cache):
    coll = BTagCollection(_cfg())
    coll.create()
    roc = {r["against"]: r for r in coll.rocs}
    assert set(roc) == {"light", "c", "pu"}
    c = roc["light"]["curves"][(KEY, "")]
    pts = set(zip(np.round(c["eff_b"], 6), np.round(c["misid"], 6)))
    # thresholds -1, 0, 0.2, 0.5: all, > 0, > 0.2, > 0.5
    assert {(1.0, 1.0), (0.7, 0.1), (0.5, 0.1), (0.0, 0.0)} <= pts
    wp = roc["light"]["wps"][(KEY, WP_LOOSE)]
    assert wp["eff_b"] == pytest.approx(0.7) and wp["misid"] == pytest.approx(0.1)
    assert roc["pu"]["wps"][(KEY, WP_TIGHT)]["misid"] == 0
    # light target 10%: smallest threshold with mis-id <= 0.1 is 0 (score > 0)
    t = roc["light"]["targets"][(KEY, "", 0.1)]
    assert t["threshold"] == 0.0
    assert t["misid"] == pytest.approx(0.1) and t["eff_b"] == pytest.approx(0.7)


def test_plotter_outputs(cache, tmp_path, monkeypatch):
    from menu_tools.object_performance.btag_plotter import BTagPlotter

    configs = os.path.join(os.path.dirname(__file__), "..", "..", "..", "configs")
    coll = BTagCollection(_cfg(), "synthetic_plot")
    coll.create()
    out = tmp_path / "run"
    out.mkdir()
    monkeypatch.chdir(out)
    os.symlink(os.path.abspath(configs), "configs")
    BTagPlotter("synthetic_plot", coll).plot()
    d = out / "outputs" / VERSION / "object_performance" / "btag"
    names = sorted(os.listdir(d))
    assert f"synthetic_plot_b_vs_pt_{VERSION}.png" in names
    assert f"synthetic_plot_roc_light_pt30toInf_{VERSION}.pdf" in names
    assert f"synthetic_plot_summary_{VERSION}.txt" in names
    with open(d / f"synthetic_plot_light_vs_pt_{VERSION}.json") as f:
        js = json.load(f)
    entry = js[f"{KEY}|{WP_LOOSE}"]
    assert sum(entry["den"]) == N_EVENTS
    with open(d / f"synthetic_plot_roc_light_pt30toInf_{VERSION}.json") as f:
        js = json.load(f)
    assert js["working_points"][f"{KEY}|{WP_LOOSE}"]["misid"] == pytest.approx(0.1)
    assert js["target_misid"][0]["threshold"] == 0.0

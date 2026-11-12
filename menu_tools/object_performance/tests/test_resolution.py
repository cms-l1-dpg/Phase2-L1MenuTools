"""
Resolution / response: synthetic pairs with a known 10% pT scale shift and known Gaussian
widths must give back the expected median and effective resolution.

Run from the repository root (object definitions are read from configs/V50nano/objects).
"""
import awkward as ak
import numpy as np
import pytest
import vector

from menu_tools.object_performance.resolution_collection import (
    ResolutionCollection,
    binned_response,
    summarize_response,
    wrap_dphi,
)

vector.register_awkward()

SCALE = 1.10
SIGMA_PT = 0.05  # relative
SIGMA_ETA = 0.01
SIGMA_PHI = 0.02
N_EVENTS = 40_000


def test_summarize_gaussian():
    rng = np.random.default_rng(1)
    vals = rng.normal(SCALE, SCALE * SIGMA_PT, 200_000)
    s = summarize_response(vals, "ratio")
    assert s["median"] == pytest.approx(SCALE, abs=1e-3)
    assert s["resolution"] == pytest.approx(SIGMA_PT, rel=0.02)
    # quoted uncertainty is in the right ballpark of the asymptotic one
    expected_med_err = np.sqrt(np.pi / 2) * SCALE * SIGMA_PT / np.sqrt(len(vals))
    assert s["median_err"] == pytest.approx(expected_med_err, rel=0.3)

    d = summarize_response(rng.normal(0.0, SIGMA_ETA, 200_000), "diff")
    assert d["median"] == pytest.approx(0.0, abs=1e-4)
    assert d["resolution"] == pytest.approx(SIGMA_ETA, rel=0.02)


def test_binned_min_entries():
    x = np.array([0.5] * 5 + [1.5] * 50)
    v = np.ones_like(x)
    out = binned_response(x, v, np.array([0, 1, 2]), "ratio", min_entries=10)
    assert np.isnan(out["median"][0]) and out["n"][0] == 5
    assert out["median"][1] == 1 and out["n"][1] == 50


def test_wrap_dphi():
    assert wrap_dphi(2 * np.pi - 0.1) == pytest.approx(-0.1)
    assert wrap_dphi(-2 * np.pi + 0.1) == pytest.approx(0.1)


def _synthetic_matched_arrays():
    rng = np.random.default_rng(2)
    ref_pt = rng.uniform(10, 100, N_EVENTS)
    ref_eta = rng.uniform(-2.0, 2.0, N_EVENTS)
    ref_phi = rng.uniform(-np.pi, np.pi, N_EVENTS)
    test_pt = SCALE * ref_pt * (1 + rng.normal(0, SIGMA_PT, N_EVENTS))
    test_eta = ref_eta + rng.normal(0, SIGMA_ETA, N_EVENTS)
    test_phi = wrap_dphi(ref_phi + rng.normal(0, SIGMA_PHI, N_EVENTS))
    # A lower-pT reference object (never the leading one) and, per event, a second, harder
    # test object far away (dR > 0.6) that must not be matched.
    ref = ak.zip(
        {
            "pt": np.stack([ref_pt, ref_pt * 0.1], axis=1),
            "eta": np.stack([ref_eta, -ref_eta], axis=1),
            "phi": np.stack([ref_phi, wrap_dphi(ref_phi + 1.5)], axis=1),
            "mass": np.zeros((N_EVENTS, 2)),
        }
    )
    test = ak.zip(
        {
            "pt": np.stack([test_pt, 5 * test_pt], axis=1),
            "eta": np.stack([test_eta, test_eta], axis=1),
            "phi": np.stack([test_phi, wrap_dphi(test_phi + np.pi)], axis=1),
            "mass": np.zeros((N_EVENTS, 2)),
        }
    )
    # Drop the test objects in 10% of the events: unmatched references.
    keep = rng.uniform(size=N_EVENTS) > 0.1
    ref, test = ak.from_regular(ref, axis=1), ak.from_regular(test, axis=1)
    test = test[ak.local_index(test, axis=1) < ak.Array(np.where(keep, 2, 0))]
    pu = rng.integers(160, 240, N_EVENTS).astype(float)
    return (
        ak.with_name(ref, "Momentum4D"),
        ak.with_name(test, "Momentum4D"),
        pu,
        keep,
    )


CFG = {
    "sample": "synthetic",
    "version": "V50nano",
    "match_test_to_ref": True,
    "reference_object": {"object": "GenPart", "x_arg": "pt", "label": "Gen Muons"},
    "test_objects": {"L1gmtMuon:dR0p6": "pt"},
    "resolution": {
        "variables": ["pt", "eta", "phi"],
        "vs": {"pt": {"edges": [10, 40, 70, 100]}, "pu": {"min": 160, "max": 240, "step": 40}},
        "min_entries": 50,
    },
}


def test_matched_resolution(monkeypatch):
    ref, test, pu, keep = _synthetic_matched_arrays()
    coll = ResolutionCollection(CFG, "synthetic")
    obj_key = str(coll.test_objects[0][0])

    def fake_load(self=coll):
        coll.ak_arrays["ref"] = ref
        coll.ak_arrays[obj_key] = test

    def fake_pileup(self=coll):
        coll.pileup = pu

    monkeypatch.setattr(coll, "_load_arrays", fake_load)
    monkeypatch.setattr(coll, "_load_pileup", fake_pileup)
    coll.create()

    pairs = coll.pairs[obj_key]
    assert len(pairs["ref_pt"]) == keep.sum()  # only the leading ref, only matched ones

    for vs in ("pt", "pu"):
        res_pt = coll.results["pt"][vs][obj_key]
        np.testing.assert_allclose(res_pt["median"], SCALE, atol=3e-3)
        np.testing.assert_allclose(res_pt["resolution"], SIGMA_PT, rtol=0.05)
        res_eta = coll.results["eta"][vs][obj_key]
        np.testing.assert_allclose(res_eta["median"], 0, atol=5e-4)
        np.testing.assert_allclose(res_eta["resolution"], SIGMA_ETA, rtol=0.05)
        res_phi = coll.results["phi"][vs][obj_key]
        np.testing.assert_allclose(res_phi["median"], 0, atol=1e-3)
        np.testing.assert_allclose(res_phi["resolution"], SIGMA_PHI, rtol=0.05)
        assert sum(res_pt["n"]) == keep.sum()


def test_event_level_resolution(monkeypatch):
    rng = np.random.default_rng(3)
    gen = rng.uniform(50, 300, N_EVENTS)
    gen_phi = rng.uniform(-np.pi, np.pi, N_EVENTS)
    l1 = SCALE * gen * (1 + rng.normal(0, SIGMA_PT, N_EVENTS))
    l1_phi = wrap_dphi(gen_phi + rng.normal(0, SIGMA_PHI, N_EVENTS))
    cfg = {
        "sample": "synthetic",
        "version": "V50nano",
        "reference_object": {"object": "GenMET", "x_arg": "pt", "label": "Gen MET"},
        "test_objects": {"L1puppiMET:default": "pt"},
        "resolution": {"vs": {"pt": {"edges": [50, 150, 300]}}},
    }
    coll = ResolutionCollection(cfg, "synthetic_met")
    obj_key = str(coll.test_objects[0][0])

    def fake_load(self=coll):
        coll.ak_arrays["ref"] = ak.zip({"pt": gen, "phi": gen_phi})
        coll.ak_arrays[obj_key] = ak.zip({"pt": l1, "phi": l1_phi})

    monkeypatch.setattr(coll, "_load_arrays", fake_load)
    coll.create()
    assert coll.res_cfg.variables == ["pt", "phi"]
    res = coll.results["pt"]["pt"][obj_key]
    np.testing.assert_allclose(res["median"], SCALE, atol=3e-3)
    np.testing.assert_allclose(res["resolution"], SIGMA_PT, rtol=0.05)
    res_phi = coll.results["phi"]["pt"][obj_key]
    np.testing.assert_allclose(res_phi["resolution"], SIGMA_PHI, rtol=0.05)

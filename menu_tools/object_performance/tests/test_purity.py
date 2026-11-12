"""
Purity / fake rate / multiplicity on a synthetic cache with a known number of matched and fake
trigger objects per event (parquet files in tmp_path, constants.CACHE_DIR monkeypatched).

Run from the repository root (object definitions are read from configs/V50nano/objects).
"""
import awkward as ak
import numpy as np
import pytest

from menu_tools.object_performance.purity_collection import (
    PurityCollection,
    PurityConfig,
    match_any,
    ratio_with_cp,
)
from menu_tools.utils import constants

N_EVENTS = 20_000
VERSION = "V50nano"
SAMPLE = "synthetic"
TEST_OBJ = "L1gmtMuon:dR0p6"  # no cuts, match_dR 0.6


def _make_events(seed=1):
    """Per event: 1-2 gen muons at eta ~ -1.5, one trigger muon next to each (matched), plus
    0-3 fake trigger muons at eta ~ +1.5 (dR > 2 from any gen muon). A gen pion next to the
    fakes must not be matched (pdgId cut)."""
    rng = np.random.default_rng(seed)
    n_gen = rng.integers(1, 3, N_EVENTS)
    n_fake = rng.integers(0, 4, N_EVENTS)
    pu = rng.integers(150, 250, N_EVENTS).astype(float)
    gen_eta, gen_phi, gen_pt, gen_pdg = [], [], [], []
    trg_eta, trg_phi, trg_pt, is_fake = [], [], [], []
    for i in range(N_EVENTS):
        ge = rng.uniform(-1.8, -1.2, n_gen[i])
        gp = rng.uniform(-np.pi, np.pi, n_gen[i])
        gen_eta.append(list(ge) + [1.5])
        gen_phi.append(list(gp) + [0.0])
        gen_pt.append(list(rng.uniform(5, 50, n_gen[i])) + [10.0])
        gen_pdg.append([13] * n_gen[i] + [211])
        fe = rng.uniform(1.3, 1.7, n_fake[i])
        fp = rng.uniform(-0.3, 0.3, n_fake[i])
        trg_eta.append(list(ge + 0.05) + list(fe))
        trg_phi.append(list(gp - 0.05) + list(fp))
        trg_pt.append(
            list(rng.uniform(20, 60, n_gen[i])) + list(rng.uniform(2, 30, n_fake[i]))
        )
        is_fake.append([False] * n_gen[i] + [True] * n_fake[i])
    gen = {"pt": gen_pt, "eta": gen_eta, "phi": gen_phi, "pdgId": gen_pdg}
    trg = {"pt": trg_pt, "eta": trg_eta, "phi": trg_phi}
    return gen, trg, ak.Array(is_fake), pu


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
    gen, trg, _, pu = events
    d = tmp_path / VERSION
    d.mkdir()
    _write(d / f"{VERSION}_{SAMPLE}_GenPart.parquet", "GenPart", gen)
    _write(d / f"{VERSION}_{SAMPLE}_L1gmtMuon.parquet", "L1gmtMuon", trg)
    # Pileup in the separate <version>PU cache (as V50nano_170X1026PU): found by the fallback
    dpu = tmp_path / f"{VERSION}PU"
    dpu.mkdir()
    ak.to_parquet(
        ak.zip({"Pileup_nPU": pu, "Pileup_nTrueInt": np.full(N_EVENTS, 200.0)}),
        str(dpu / f"{VERSION}PU_{SAMPLE}_Pileup.parquet"),
    )
    monkeypatch.setattr(constants, "CACHE_DIR", str(tmp_path))
    return tmp_path


def _cfg(mode, **extra):
    purity = {
        "mode": mode,
        "vs": {
            "pt": {"edges": [0, 10, 20, 40, 60]},
            "eta": {"min": -2, "max": 2, "step": 0.5},
            "pu": {"edges": [150, 200, 250]},
            "threshold": {"edges": [0, 10, 25]},
        },
        "thresholds": [0, 10],
    }
    if mode != "multiplicity":
        purity["reference_gen"] = {
            "object": "GenPart",
            "cuts": ["abs({pdgId}) == 13"],
            "label": "gen mu",
        }
    purity.update(extra)
    return {
        "sample": SAMPLE,
        "version": VERSION,
        "test_objects": {TEST_OBJ: "pt"},
        "purity": purity,
    }


def _plot(coll, quantity, vs, threshold=None):
    hits = [
        p
        for p in coll.plots
        if p["quantity"] == quantity and p["vs"] == vs and p["threshold"] == threshold
    ]
    assert len(hits) == 1, (
        quantity,
        vs,
        threshold,
        [(p["quantity"], p["vs"], p["threshold"]) for p in coll.plots],
    )
    return next(iter(hits[0]["series"].values()))


def test_match_any():
    trig = ak.Array([[{"eta": 0.0, "phi": 3.1}, {"eta": 1.0, "phi": 0.0}], []])
    gen = ak.Array([[{"eta": 0.0, "phi": -3.1}], [{"eta": 0.0, "phi": 0.0}]])
    # dphi wraps around: (3.1, -3.1) are 0.083 apart
    assert match_any(trig, gen, 0.1, chunk=1).tolist() == [[True, False], []]


def test_ratio_with_cp():
    y, lo, hi = ratio_with_cp([0, 5, 10], [0, 10, 10])
    assert np.isnan(y[0]) and y[1] == 0.5 and y[2] == 1.0
    assert lo[1] > 0 and hi[1] > 0 and hi[2] == pytest.approx(0, abs=1e-12)


def test_config_errors():
    with pytest.raises(ValueError):
        PurityConfig({"mode": "bogus"}, "x")
    with pytest.raises(KeyError):
        PurityConfig({"mode": "purity"}, "x")
    with pytest.raises(ValueError):
        PurityConfig({"mode": "multiplicity", "vs": {"foo": {}}}, "x")
    assert PurityConfig({"mode": "multiplicity"}, "MinBias").rate
    assert not PurityConfig({"mode": "multiplicity"}, "TT").rate


def test_purity(cache, events):
    _, trg, is_fake, pu = events
    coll = PurityCollection(_cfg("purity"), "synthetic_purity")
    coll.create()
    assert coll.n_events == N_EVENTS
    assert coll.pileup_source.endswith(f"{VERSION}PU_{SAMPLE}_Pileup.parquet")

    pt = ak.to_numpy(ak.flatten(ak.Array(trg["pt"])))
    fake = ak.to_numpy(ak.flatten(is_fake))
    obj = next(iter(coll.objects.values()))
    np.testing.assert_array_equal(obj["matched"], ~fake)

    s = _plot(coll, "purity", "pt")
    edges = np.array([0, 10, 20, 40, 60])
    den = np.histogram(pt, edges)[0]
    num = np.histogram(pt[~fake], edges)[0]
    np.testing.assert_array_equal(s["den"], den)
    np.testing.assert_array_equal(s["num"], num)
    np.testing.assert_allclose(s["y"], num / den)
    assert s["integral"] == pytest.approx((~fake).mean())

    # vs pu with threshold 10: objects with pt >= 10 in events of each pu bin
    s = _plot(coll, "purity", "pu", 10.0)
    ev = ak.to_numpy(
        ak.flatten(ak.broadcast_arrays(ak.local_index(is_fake, axis=0), is_fake)[0])
    )
    sel = pt >= 10
    pu_obj = pu[ev]
    for i, (a, b) in enumerate([(150, 200), (200, 250)]):
        in_bin = sel & (pu_obj >= a) & (pu_obj < b)
        assert s["den"][i] == in_bin.sum()
        assert s["num"][i] == (in_bin & ~fake).sum()


def test_purity_leading_only(cache, events):
    _, trg, is_fake, _ = events
    coll = PurityCollection(_cfg("purity", leading_only=True), "synthetic_leading")
    coll.create()
    obj = next(iter(coll.objects.values()))
    assert len(obj["pt"]) == N_EVENTS  # every event has >= 1 trigger object
    pts = ak.Array(trg["pt"])
    lead_fake = ak.to_numpy(ak.firsts(is_fake[ak.argmax(pts, axis=1, keepdims=True)]))
    np.testing.assert_array_equal(obj["matched"], ~lead_fake)
    np.testing.assert_allclose(obj["pt"], ak.to_numpy(ak.max(pts, axis=1)))


def test_fake_rate(cache, events):
    _, trg, is_fake, pu = events
    coll = PurityCollection(_cfg("fake_rate"), "synthetic_fake")
    coll.create()
    pts = ak.Array(trg["pt"])
    for i_thr, thr in enumerate([0, 10, 25]):
        n_unm = ak.to_numpy(ak.sum(is_fake & (pts >= thr), axis=1))
        s = _plot(coll, "unmatched_per_event", "threshold")
        assert s["y"][i_thr] == pytest.approx(n_unm.mean())
        assert s["err_lo"][i_thr] == pytest.approx(
            n_unm.std(ddof=1) / np.sqrt(N_EVENTS)
        )
        s = _plot(coll, "event_fraction", "threshold")
        assert s["y"][i_thr] == pytest.approx((n_unm > 0).mean())  # not MinBias: no kHz
    s = _plot(coll, "fake_fraction", "pt")
    assert not any(p["quantity"] == "purity" for p in coll.plots)
    pt = ak.to_numpy(ak.flatten(pts))
    fake = ak.to_numpy(ak.flatten(is_fake))
    edges = np.array([0, 10, 20, 40, 60])
    np.testing.assert_allclose(
        s["y"], np.histogram(pt[fake], edges)[0] / np.histogram(pt, edges)[0]
    )
    # unmatched per event vs pu (threshold 0): the fakes are pileup-independent here: flat, slope ~ 0
    s = _plot(coll, "unmatched_per_event", "pu", 0.0)
    assert (
        s["fit"] is not None
        and abs(s["fit"]["slope"]) < 5 * s["fit"]["slope_err"] + 1e-3
    )
    # dN/deta of unmatched objects: all fakes sit at eta in [1.3, 1.7] -> bin [1.0, 1.5) and [1.5, 2.0)
    s = _plot(coll, "unmatched_density", "eta", 0.0)
    assert sum(s["num"]) == fake.sum()
    assert s["num"][0] == 0


def test_multiplicity_minbias_rate(cache, events, monkeypatch):
    _, trg, _, _ = events
    cfg = _cfg("multiplicity", rate=True)
    coll = PurityCollection(cfg, "synthetic_mult")
    coll.create()
    pts = ak.Array(trg["pt"])
    s_mult = _plot(coll, "objects_per_event", "threshold")
    s_rate = _plot(coll, "event_fraction", "threshold")
    for i_thr, thr in enumerate([0, 10, 25]):
        n = ak.to_numpy(ak.sum(pts >= thr, axis=1))
        assert s_mult["y"][i_thr] == pytest.approx(n.mean())
        assert s_rate["y"][i_thr] == pytest.approx(
            (n > 0).mean() * constants.RATE_NORM_FACTOR
        )
    assert all(o["matched"] is None for o in coll.objects.values())


def test_plotter_outputs(cache, tmp_path, monkeypatch):
    import os

    from menu_tools.object_performance.purity_plotter import PurityPlotter

    coll = PurityCollection(_cfg("fake_rate"), "synthetic_plot")
    coll.create()
    out = tmp_path / "out"
    out.mkdir()
    monkeypatch.chdir(out)
    # object labels are read from configs/<version>/objects relative to the working directory
    os.symlink(
        os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "configs")
        ),
        "configs",
    )
    PurityPlotter("synthetic_plot", coll).plot()
    d = out / "outputs" / VERSION / "object_performance" / "purity"
    assert (d / f"synthetic_plot_fake_fraction_vs_pt_{VERSION}.png").exists()
    assert (d / f"synthetic_plot_event_fraction_vs_threshold_{VERSION}.json").exists()
    assert (
        d / f"synthetic_plot_unmatched_per_event_vs_pu_thr10_{VERSION}.pdf"
    ).exists()
    assert (d / f"synthetic_plot_{VERSION}.yaml").exists()

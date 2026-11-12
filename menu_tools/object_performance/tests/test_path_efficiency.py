"""
Path efficiencies (L1 seeds / HLT paths vs a gen reference) on a synthetic cache:
reference selection, OR of the bits, the four curve types, rank-2 reference, MET reference.
"""
import json

import awkward as ak
import numpy as np
import pytest

from menu_tools.object_performance.path_efficiency import (
    PathEfficiencyCollection,
    PathEfficiencyPlotter,
)
from menu_tools.utils import constants

VERSION = "Vsynth"
SAMPLE = "synthetic"
HARD = 1 << 7  # statusFlags isHardProcess

# Per event: gen particles (pt, eta, pdgId), seeds A/B, path.
#  ev0: muons 40, 30          L1 A    HLT 1
#  ev1: muon 45               L1 B    HLT 0
#  ev2: muons 35, 12 + e 100  L1 -    HLT 1   (HLT without L1: tests that the curves are independent)
#  ev3: electron 60 only      L1 A    HLT 1   (no reference muon: not in any denominator)
#  ev4: muon 42 at |eta| 3    L1 A    HLT 1   (fails the eta cut)
#  ev5: muon 5                L1 -    HLT 0
GEN = [
    [(40, 0.1, 13), (30, -0.5, -13)],
    [(45, 1.0, 13)],
    [(35, 0.2, 13), (12, 2.0, -13), (100, 0.0, 11)],
    [(60, 0.3, 11)],
    [(42, 3.0, 13)],
    [(5, 0.0, 13)],
]
SEED_A = [True, False, False, True, True, False]
SEED_B = [False, True, False, False, False, False]
PATH = [True, False, True, True, True, False]
GENMET = [10.0, 30.0, 60.0, 80.0, 20.0, 70.0]


def _write_cache(tmp_path):
    d = tmp_path / VERSION
    d.mkdir()
    prefix = f"{VERSION}_{SAMPLE}"
    gen = ak.Array(
        {
            "GenPart_pt": [[float(p[0]) for p in ev] for ev in GEN],
            "GenPart_eta": [[float(p[1]) for p in ev] for ev in GEN],
            "GenPart_phi": [[0.0 for _ in ev] for ev in GEN],
            "GenPart_mass": [[0.0 for _ in ev] for ev in GEN],
            "GenPart_pdgId": [[p[2] for p in ev] for ev in GEN],
            "GenPart_statusFlags": [[HARD for _ in ev] for ev in GEN],
        }
    )
    ak.to_parquet(gen, d / f"{prefix}_GenPart.parquet")
    ak.to_parquet(
        ak.Array({"GenMET_pt": GENMET, "GenMET_phi": [0.0] * len(GENMET)}),
        d / f"{prefix}_GenMET.parquet",
    )
    ak.to_parquet(
        ak.Array({"L1_pSeedA_final": SEED_A, "L1_pSeedB_final": SEED_B}),
        d / f"{prefix}_L1.parquet",
    )
    ak.to_parquet(
        ak.Array({"HLT_Path": PATH, "HLT_Other": [False] * len(PATH)}),
        d / f"{prefix}_HLT.parquet",
    )


@pytest.fixture
def cache(tmp_path, monkeypatch):
    _write_cache(tmp_path)
    monkeypatch.setattr(constants, "CACHE_DIR", str(tmp_path))
    return tmp_path


def _cfg(rank=1, obj="GenPart", curves=("L1", "HLT", "L1_and_HLT", "HLT_given_L1")):
    ref = {"object": obj, "x_arg": "pt", "label": "Gen"}
    if obj == "GenPart":
        ref["cuts"] = {
            "object": [
                "abs({pdgId}) == 13",
                "(({statusFlags}>>7)&1) == 1",
                "abs({eta}) < 2.4",
            ]
        }
    if rank != 1:
        ref["rank"] = rank
    return {
        "sample": SAMPLE,
        "version": VERSION,
        "reference_object": ref,
        "path_efficiency": {
            "L1": ["L1_pSeedA_final", "L1_pSeedB_final"],
            "HLT": ["HLT_Path"],
            "curves": list(curves),
            "plateau_min": 25,
        },
        "binning": {"edges": [0, 25, 50, 100]},
        "xlabel": "x",
        "ylabel": "Efficiency",
    }


def _counts(coll, curve):
    return coll.hists[curve][0].tolist(), coll.hists["ref"][curve][0].tolist()


def test_leading_reference(cache):
    coll = PathEfficiencyCollection(_cfg(), "test")
    coll.create_hists()
    # reference x: leading selected muon; ev3 (no muon) and ev4 (eta) have none
    np.testing.assert_array_equal(coll.x, [40, 45, 35, np.nan, np.nan, 5])
    # bin [25, 50): ev0, ev1, ev2; bin [0, 25): ev5
    assert _counts(coll, "L1") == ([0, 2, 0], [1, 3, 0])  # ev0 (A) OR ev1 (B)
    assert _counts(coll, "HLT") == ([0, 2, 0], [1, 3, 0])  # ev0, ev2
    assert _counts(coll, "L1_and_HLT") == ([0, 1, 0], [1, 3, 0])  # ev0
    assert _counts(coll, "HLT_given_L1") == ([0, 1, 0], [0, 2, 0])  # ev0 of ev0, ev1
    eff, err = coll.get_efficiency("L1_and_HLT")
    assert eff[0] == 0 and eff[1] == pytest.approx(1 / 3) and np.isnan(eff[2])
    assert err.shape == (2, 3)
    p = coll.plateau("HLT_given_L1")
    assert (p["n_pass"], p["n_total"]) == (1, 2)


def test_subleading_reference(cache):
    coll = PathEfficiencyCollection(_cfg(rank=2), "test")
    coll.create_hists()
    # 2nd-highest-pT muon: ev0 30, ev2 12 (the 100 GeV electron is not a muon)
    np.testing.assert_array_equal(coll.x, [30, np.nan, 12, np.nan, np.nan, np.nan])
    assert _counts(coll, "L1") == ([0, 1, 0], [1, 1, 0])
    assert _counts(coll, "HLT") == ([1, 1, 0], [1, 1, 0])
    assert _counts(coll, "L1_and_HLT") == ([0, 1, 0], [1, 1, 0])


def test_met_reference_and_outputs(cache, tmp_path, monkeypatch):
    coll = PathEfficiencyCollection(
        _cfg(obj="GenMET", curves=("L1", "L1_and_HLT")), "metTest"
    )
    coll.create_hists()
    np.testing.assert_array_equal(coll.x, GENMET)
    # [0,25): ev0 (A), ev4 (A) -> 2/2; [25,50): ev1 (B) -> 1/1; [50,100): ev2, ev3 (A), ev5 -> 1/3
    assert _counts(coll, "L1") == ([2, 1, 1], [2, 1, 3])
    assert _counts(coll, "L1_and_HLT") == ([2, 0, 1], [2, 1, 3])

    monkeypatch.chdir(tmp_path)
    out = PathEfficiencyPlotter("metTest", coll).plot()
    outdir = tmp_path / "outputs" / VERSION / "object_performance" / "path_efficiency"
    for ext in ("png", "pdf", "json", "yaml"):
        assert (outdir / f"metTest_{VERSION}.{ext}").exists()
    saved = json.loads((outdir / f"metTest_{VERSION}.json").read_text())
    assert saved["L1"]["efficiency"] == pytest.approx([1.0, 1.0, 1 / 3])
    assert saved["L1_and_HLT"]["n_pass"] == [2, 0, 1]
    assert out["L1"]["plateau"]["n_total"] == 4


def test_bad_config(cache):
    cfg = _cfg(curves=("L1", "Nonsense"))
    with pytest.raises(ValueError):
        PathEfficiencyCollection(cfg, "bad")
    cfg = _cfg()
    cfg["path_efficiency"]["HLT"] = []
    with pytest.raises(ValueError):
        PathEfficiencyCollection(cfg, "bad")

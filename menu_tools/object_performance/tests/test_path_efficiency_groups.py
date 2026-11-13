"""
Path efficiencies on a synthetic di-tau cache: several path groups in one plot
(`paths:`), `split_by` with per-event categories (decay-mode pair of the two leading
taus, `objects: 2`), `min_objects`, `x_arg: abs(...)` and `event_x`.
"""
import json

import awkward as ak
import numpy as np
import pytest

from menu_tools.object_performance.path_efficiency import (
    PathEfficiencyCollection,
    PathEfficiencyPlotter,
)
from menu_tools.object_performance.split import (
    OTHER,
    SplitConfig,
    assign_events,
    event_categories,
)
from menu_tools.utils import constants

VERSION = "Vsynth"
SAMPLE = "ditau"
P11, P13, P33 = "1-prong + 1-prong", "1-prong + 3-prong", "3-prong + 3-prong"

# Per event: visible taus (pt, eta, decay mode), all in |eta| < 2.1 except one in ev5.
#  ev0: 50 (0), 40 (1) at eta -1.5       1p+1p   L1 1  A 1  B 1   nPU 190
#  ev1: 60 (10), 30 (1)                  1p+3p   L1 1  A 0  B 1   nPU 210
#  ev2: 70 (11), 45 (10), 20 (0)         3p+3p   L1 0  A 0  B 0   nPU 205
#  ev3: 80 (15), 35 (0)                  other   L1 1  A 1  B 0   nPU 180
#  ev4: 55 (0) only                      < 2     L1 1  A 1  B 0   nPU 200
#  ev5: 65 (0) at |eta| 2.5, 42 (2)      < 2     L1 1  A 0  B 1   nPU 220
TAUS = [
    [(50, 0.1, 0), (40, -1.5, 1)],
    [(60, 0.2, 10), (30, 0.5, 1)],
    [(70, 0.3, 11), (45, 1.0, 10), (20, 0.0, 0)],
    [(80, 0.0, 15), (35, 0.4, 0)],
    [(55, 0.0, 0)],
    [(65, 2.5, 0), (42, 0.3, 2)],
]
SEED = [True, True, False, True, True, True]
PATH_A = [True, False, False, True, True, False]
PATH_B = [True, True, False, False, False, True]
NPU = [190.0, 210.0, 205.0, 180.0, 200.0, 220.0]
DM_CATS = {"1-prong": [0, 1, 2], "3-prong": [10, 11]}


@pytest.fixture
def cache(tmp_path, monkeypatch):
    d = tmp_path / VERSION
    d.mkdir()
    prefix = f"{VERSION}_{SAMPLE}"
    taus = {
        "GenVisTau_pt": [[float(t[0]) for t in ev] for ev in TAUS],
        "GenVisTau_eta": [[float(t[1]) for t in ev] for ev in TAUS],
        "GenVisTau_phi": [[0.0 for _ in ev] for ev in TAUS],
        "GenVisTau_mass": [[0.0 for _ in ev] for ev in TAUS],
        "GenVisTau_status": [[t[2] for t in ev] for ev in TAUS],
    }
    ak.to_parquet(ak.Array(taus), d / f"{prefix}_GenVisTau.parquet")
    ak.to_parquet(ak.Array({"L1_pSeed_final": SEED}), d / f"{prefix}_L1.parquet")
    ak.to_parquet(
        ak.Array({"HLT_PathA": PATH_A, "HLT_PathB": PATH_B}),
        d / f"{prefix}_HLT.parquet",
    )
    ak.to_parquet(
        ak.Array({"Pileup_nPU": NPU, "Pileup_nTrueInt": [200.0] * len(NPU)}),
        d / f"{prefix}_Pileup.parquet",
    )
    monkeypatch.setattr(constants, "CACHE_DIR", str(tmp_path))
    return tmp_path


def _cfg(rank=2, x_arg="pt", split=None, **ref_extra):
    cfg = {
        "sample": SAMPLE,
        "version": VERSION,
        "reference_object": {
            "object": "GenVisTau",
            "x_arg": x_arg,
            "label": "Gen taus",
            "rank": rank,
            "cuts": {"object": ["abs({eta}) < 2.1"]},
            **ref_extra,
        },
        "path_efficiency": {
            "paths": {
                "A": {
                    "L1": ["L1_pSeed_final"],
                    "HLT": ["HLT_PathA"],
                    "curves": ["L1", "L1_and_HLT"],
                    "labels": {"L1_and_HLT": "path A"},
                },
                "B": {"L1": ["L1_pSeed_final"], "HLT": ["HLT_PathB"]},
            },
            "curves": ["L1_and_HLT"],  # default of the groups without `curves`
            "plateau_min": 0,
        },
        "binning": {"edges": [0, 100]},
        "xlabel": "x",
        "ylabel": "Efficiency",
    }
    if split is not None:
        cfg["split_by"] = split
    return cfg


def _counts(hists, key):
    return int(hists[key][0].sum()), int(hists["ref"][key][0].sum())


def test_path_groups(cache):
    coll = PathEfficiencyCollection(_cfg(), "groups")
    assert coll.curves == ["A:L1", "A:L1_and_HLT", "B:L1_and_HLT"]
    coll.create_hists()
    np.testing.assert_array_equal(coll.x, [40, 30, 45, 35, np.nan, np.nan])
    # denominator ev0-ev3; seed: ev0, ev1, ev3; A: ev0, ev3; B: ev0, ev1
    assert _counts(coll.hists, "A:L1") == (3, 4)
    assert _counts(coll.hists, "A:L1_and_HLT") == (2, 4)
    assert _counts(coll.hists, "B:L1_and_HLT") == (2, 4)
    assert coll.label("A:L1_and_HLT") == "path A"
    assert coll.label("B:L1_and_HLT") == "B, L1 and HLT"
    assert coll.bit_groups == {
        "A": {"L1": ["L1_pSeed_final"], "HLT": ["HLT_PathA"]},
        "B": {"L1": ["L1_pSeed_final"], "HLT": ["HLT_PathB"]},
    }


def test_split_by_decay_mode_pair(cache, tmp_path, monkeypatch, legend_titles):
    split = {
        "field": "status",
        "objects": 2,
        "categories": DM_CATS,
        "name": "DMpair",
        "layout": "per_category",
    }
    coll = PathEfficiencyCollection(_cfg(split=split), "ditau")
    coll.create_hists()
    assert coll.category is not None
    assert coll.category.tolist() == [P11, P13, P33, OTHER, OTHER, OTHER]
    assert list(coll.split_hists) == [P11, P13, P33]
    assert _counts(coll.split_hists[P11], "A:L1_and_HLT") == (1, 1)  # ev0
    assert _counts(coll.split_hists[P13], "A:L1_and_HLT") == (0, 1)  # ev1
    assert _counts(coll.split_hists[P13], "B:L1_and_HLT") == (1, 1)
    assert _counts(coll.split_hists[P33], "A:L1") == (0, 1)  # ev2
    p = coll.plateau("B:L1_and_HLT", coll.category_mask(P13))
    assert (p["n_pass"], p["n_total"]) == (1, 1)

    monkeypatch.chdir(tmp_path)
    out = PathEfficiencyPlotter("ditau", coll).plot()
    outdir = tmp_path / "outputs" / VERSION / "object_performance" / "path_efficiency"
    for suffix in ("", "_DMpair_1-prong_1-prong", "_DMpair_3-prong_3-prong"):
        for ext in ("png", "pdf", "json"):
            assert (outdir / f"ditau{suffix}_{VERSION}.{ext}").exists()
    saved = json.loads(
        (outdir / f"ditau_DMpair_1-prong_3-prong_{VERSION}.json").read_text()
    )
    assert saved["category"] == P13
    assert saved["B:L1_and_HLT"]["n_pass"] == [1]
    frac = json.loads((outdir / f"ditau_DMpair_fractions_{VERSION}.json").read_text())
    assert frac == out["split"]
    assert frac["reference"]["n"] == 4
    assert frac["reference"]["categories"][P11]["n"] == 1
    assert frac["reference"]["categories"][OTHER]["n"] == 1  # ev3 (DM 15)
    entry = frac["curves"]["A:L1"]
    assert (entry["inclusive"]["n_num"], entry["inclusive"]["n_den"]) == (3, 4)
    assert (entry[OTHER]["n_num"], entry[OTHER]["n_den"]) == (1, 1)  # ev3
    assert entry[P11]["fraction"] == pytest.approx(0.25)
    assert entry[P33]["plateau"]["n_total"] == 1
    # legend title: the sample (raw key: no label) above the reference label, and the
    # category; the JSON does not change
    assert legend_titles[f"ditau_{VERSION}"] == [f"{SAMPLE} — Gen taus"]
    assert legend_titles[f"ditau_DMpair_1-prong_3-prong_{VERSION}"] == [
        f"{SAMPLE}\nGen taus\n{P13}"
    ]
    before = (outdir / f"ditau_{VERSION}.json").read_text()
    coll.cfg_plot.config_dict["sample_label"] = False
    PathEfficiencyPlotter("ditau", coll).plot()
    assert legend_titles[f"ditau_{VERSION}"] == ["Gen taus"]
    assert (outdir / f"ditau_{VERSION}.json").read_text() == before


def test_split_by_rank_object_per_object_layout(cache, tmp_path, monkeypatch):
    # no `objects`: category of the reference object at `rank` (the subleading tau)
    split = {"field": "status", "categories": DM_CATS, "name": "DM"}
    coll = PathEfficiencyCollection(_cfg(split=split), "subl")
    coll.create_hists()
    assert coll.category is not None
    assert coll.category[:4].tolist() == ["1-prong", "1-prong", "3-prong", "1-prong"]
    assert _counts(coll.split_hists["1-prong"], "A:L1") == (3, 3)  # ev0, ev1, ev3
    monkeypatch.chdir(tmp_path)
    out = PathEfficiencyPlotter("subl", coll).plot()
    # no subleading tau in "other": empty plateau
    empty = out["split"]["curves"]["A:L1"][OTHER]["plateau"]
    assert empty["n_total"] == 0 and empty["efficiency"] is None
    outdir = tmp_path / "outputs" / VERSION / "object_performance" / "path_efficiency"
    saved = json.loads((outdir / f"subl_DM_A-L1_and_HLT_{VERSION}.json").read_text())
    assert saved["curve"] == "A:L1_and_HLT"
    assert saved["inclusive"]["n_total"] == [4]
    assert saved["3-prong"]["n_pass"] == [0]


def test_min_objects_abs_x_and_event_x(cache):
    coll = PathEfficiencyCollection(_cfg(rank=1), "lead")
    coll.create_hists()
    np.testing.assert_array_equal(coll.x, [50, 60, 70, 80, 55, 42])
    coll = PathEfficiencyCollection(_cfg(rank=1, min_objects=2), "lead2")
    coll.create_hists()
    np.testing.assert_array_equal(coll.x, [50, 60, 70, 80, np.nan, np.nan])
    coll = PathEfficiencyCollection(_cfg(x_arg="abs(eta)"), "eta")
    coll.create_hists()
    np.testing.assert_allclose(coll.x, [1.5, 0.5, 1.0, 0.4, np.nan, np.nan])
    cfg = _cfg()
    cfg["path_efficiency"]["event_x"] = "Pileup_nPU"
    coll = PathEfficiencyCollection(cfg, "npu")
    coll.create_hists()
    np.testing.assert_array_equal(coll.x, [190, 210, 205, 180, np.nan, np.nan])


def test_assign_events():
    split = SplitConfig({"field": "s", "categories": DM_CATS, "objects": 2})
    assert event_categories(split) == [P11, P13, P33]
    values = ak.Array([[10, 0], [0, 2], [11, 10, 0], [0], [], [0, 15], [15, 0, 0]])
    assert assign_events(split, values, 2).tolist() == [
        P13,
        P11,
        P33,
        OTHER,
        OTHER,
        OTHER,
        OTHER,
    ]
    assert assign_events(split, values, 1).tolist() == [
        "3-prong",
        "1-prong",
        "3-prong",
        "1-prong",
        OTHER,
        "1-prong",
        OTHER,
    ]


def test_bad_configs(cache):
    cfg = _cfg()
    cfg["path_efficiency"]["L1"] = ["L1_pSeed_final"]  # `paths` replaces L1/HLT
    with pytest.raises(ValueError):
        PathEfficiencyCollection(cfg, "bad")
    cfg = _cfg()
    cfg["path_efficiency"]["paths"]["B"]["curves"] = ["HLT_given_L1"]
    cfg["path_efficiency"]["paths"]["B"]["L1"] = []
    with pytest.raises(ValueError):
        PathEfficiencyCollection(cfg, "bad")
    with pytest.raises(ValueError):
        SplitConfig({"field": "s", "categories": DM_CATS, "objects": 0})

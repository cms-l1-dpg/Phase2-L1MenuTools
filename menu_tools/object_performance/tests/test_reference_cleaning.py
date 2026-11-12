"""
Cross-object cleaning of the reference (`reference_cleaning`) on a synthetic cache:
config parsing, the selection of the cleaning objects (read per row group), the dR
veto, and the effect on a matching efficiency and on a gen HT reference.
"""
import awkward as ak
import numpy as np
import pytest

from menu_tools.object_performance.config import PerformancePlotConfig
from menu_tools.object_performance.reference_cleaning import (
    clean_reference,
    load_cleaning_objects,
    near_mask,
    parse_reference_cleaning,
)
from menu_tools.object_performance.turnon_collection import TurnOnCollection
from menu_tools.utils import constants

VERSION = "V50nano"  # object definitions (L1puppiJetSC4) from configs/V50nano/objects
SAMPLE = "synthetic"
PROMPT = 1  # statusFlags isPrompt
TAUDECAY = 1 << 5  # isDirectPromptTauDecayProduct

PROMPT_LEPTONS = {
    "object": "GenPart",
    "cuts": [
        "{status} == 1",
        "(abs({pdgId}) == 11) | (abs({pdgId}) == 13)",
        "({statusFlags} & 33) > 0",
        "{pt} > 10",
    ],
    "dR": 0.4,
}

# Per event: gen jets (pt, eta, phi); gen particles (pt, eta, phi, pdgId, status, flags);
# L1 jets (pt, eta, phi).
#  ev0: jet 100 at (0, 0) = prompt muon (no L1 jet); jet 50 at (0, 2) with an L1 jet
#  ev1: jet 80 at (0.5, 1) with a non-prompt muon (b decay) inside: kept; L1 jet
#  ev2: jet 60 at (1, -1) = electron from a prompt tau decay (L1 jet); jet 30 far away
#  ev3: jet 40 at (0, 0) near a prompt muon of 5 GeV (below the pT cut): kept, no L1 jet
#  ev4: jet 70 at (0, 0) near a prompt photon (not a lepton): kept, L1 jet
#  ev5: no gen particle at all; jet 90 with an L1 jet
JETS = [
    [(100, 0.0, 0.0), (50, 0.0, 2.0)],
    [(80, 0.5, 1.0)],
    [(60, 1.0, -1.0), (30, -1.0, 2.5)],
    [(40, 0.0, 0.0)],
    [(70, 0.0, 0.0)],
    [(90, 0.2, 0.2)],
]
PARTS = [
    [(98, 0.05, 0.0, 13, 1, PROMPT), (20, 0.0, -2.0, 12, 1, PROMPT)],
    [(15, 0.5, 1.0, 13, 1, 0)],
    [(55, 1.0, -1.1, -11, 1, TAUDECAY)],
    [(5, 0.0, 0.0, 13, 1, PROMPT)],
    [(65, 0.0, 0.0, 22, 1, PROMPT)],
    [],
]
L1JETS = [
    [(48, 0.0, 2.0)],
    [(75, 0.5, 1.0)],
    [(58, 1.0, -1.0)],
    [],
    [(66, 0.0, 0.0)],
    [(85, 0.2, 0.2)],
]


def _write(d, name, fields, rows, row_group_size=None):
    arr = ak.Array(
        {
            f"{name}_{f}": [[float(p[i]) for p in ev] for ev in rows]
            if f not in ("pdgId", "status", "statusFlags")
            else [[int(p[i]) for p in ev] for ev in rows]
            for i, f in enumerate(fields)
        }
    )
    kw = {} if row_group_size is None else {"row_group_size": row_group_size}
    ak.to_parquet(arr, d / f"{VERSION}_{SAMPLE}_{name}.parquet", **kw)


@pytest.fixture
def cache(tmp_path, monkeypatch):
    d = tmp_path / VERSION
    d.mkdir()
    _write(d, "GenJet", ["pt", "eta", "phi"], JETS)
    # several row groups: the cleaning objects are read per row group
    _write(
        d,
        "GenPart",
        ["pt", "eta", "phi", "pdgId", "status", "statusFlags"],
        PARTS,
        row_group_size=2,
    )
    _write(d, "L1puppiJetSC4", ["pt", "eta", "phi"], L1JETS)
    monkeypatch.setattr(constants, "CACHE_DIR", str(tmp_path))
    return tmp_path


def _cfg(cleaning=None, trafo=None):
    cfg = {
        "sample": SAMPLE,
        "version": VERSION,
        "match_test_to_ref": trafo is None,
        "reference_object": {
            "object": "GenJet",
            "x_arg": "pt",
            "label": "Gen jets",
            "cuts": {"object": ["abs({eta}) < 2.4"]},
        },
        "test_objects": {"L1puppiJetSC4:default": "pt"},
        "binning": {"min": 0, "max": 200, "step": 50},
        "xlabel": "x",
        "ylabel": "y",
    }
    if trafo:
        cfg["reference_object"]["trafo"] = trafo
    if cleaning is not None:
        cfg["reference_cleaning"] = cleaning
    return cfg


# --- parsing ------------------------------------------------------------------------


def test_parse():
    assert parse_reference_cleaning(None) == []
    assert parse_reference_cleaning({}) == []
    one = parse_reference_cleaning(PROMPT_LEPTONS)
    assert one == [PROMPT_LEPTONS]
    two = parse_reference_cleaning([PROMPT_LEPTONS, {"object": "GenVisTau", "dR": 0.3}])
    assert [b["object"] for b in two] == ["GenPart", "GenVisTau"]
    assert two[1]["cuts"] == [] and two[1]["dR"] == 0.3
    assert parse_reference_cleaning({"object": "X", "cuts": "{pt} > 1", "dR": 1})[0][
        "cuts"
    ] == ["{pt} > 1"]
    assert PerformancePlotConfig(_cfg()).reference_cleaning == []
    assert PerformancePlotConfig(_cfg(PROMPT_LEPTONS)).reference_cleaning == [
        PROMPT_LEPTONS
    ]


@pytest.mark.parametrize(
    "block",
    [
        {"object": "GenPart"},  # no dR
        {"dR": 0.4},  # no object
        {"object": "GenPart", "dR": 0.4, "dr": 0.4},  # unknown key
        {"object": "GenPart", "dR": 0},  # dR <= 0
        "GenPart",
    ],
)
def test_parse_errors(block):
    with pytest.raises(ValueError):
        parse_reference_cleaning(block, "bad")


# --- building blocks ----------------------------------------------------------------


def test_load_cleaning_objects(cache):
    lep = load_cleaning_objects(VERSION, SAMPLE, "GenPart", PROMPT_LEPTONS["cuts"])
    assert len(lep) == len(PARTS)
    # prompt muon 98 (ev0), tau-decay electron 55 (ev2); not: neutrino, non-prompt
    # muon, 5 GeV muon, photon
    assert ak.num(lep).tolist() == [1, 0, 1, 0, 0, 0]
    assert ak.to_list(lep["eta"]) == [[0.05], [], [1.0], [], [], []]


def test_load_cleaning_objects_errors(cache):
    with pytest.raises(FileNotFoundError):
        load_cleaning_objects(VERSION, SAMPLE, "GenVisTau", [])
    with pytest.raises(KeyError):
        load_cleaning_objects(VERSION, SAMPLE, "GenPart", ["{charge} > 0"])


def test_near_mask_phi_wrap():
    ref = ak.Array([[{"eta": 0.0, "phi": 3.1}, {"eta": 0.0, "phi": 0.0}], []])
    oth = ak.Array([[{"eta": 0.0, "phi": -3.1}], [{"eta": 0.0, "phi": 0.0}]])
    assert ak.to_list(near_mask(ref, oth, 0.4)) == [[True, False], []]


def test_clean_reference_event_alignment(cache):
    ref = ak.Array([[{"eta": 0.0, "phi": 0.0}]])
    with pytest.raises(ValueError):
        clean_reference(ref, [PROMPT_LEPTONS], VERSION, SAMPLE)


# --- in the efficiency --------------------------------------------------------------


def _matching(cfg):
    coll = TurnOnCollection(cfg, threshold=-999)
    coll.create_hists()
    key = str(coll.test_objects[0][0])
    return coll, coll.hists[key][0].tolist(), coll.hists["ref"][key][0].tolist()


def test_matching_efficiency(cache):
    # leading gen jet per event: 100 (ev0, unmatched), 80, 60, 40 (unmatched), 70, 90
    _, num, den = _matching(_cfg())
    assert (num, den) == ([0, 4, 0, 0], [1, 4, 1, 0])
    # cleaned: ev0 -> 50 (matched), ev2 -> 30 (unmatched, far from the L1 jet)
    coll, num, den = _matching(_cfg(PROMPT_LEPTONS))
    assert (num, den) == ([0, 4, 0, 0], [2, 4, 0, 0])
    assert ak.to_list(ak.flatten(coll.ak_arrays["ref"]["pt"])) == [
        50,
        80,
        30,
        40,
        70,
        90,
    ]


def test_ht_reference(cache):
    coll = TurnOnCollection(_cfg(PROMPT_LEPTONS, trafo="HT"), threshold=0)
    coll._load_arrays()
    coll._apply_cuts()
    np.testing.assert_allclose(
        ak.to_numpy(coll.ak_arrays["ref"]["HT"]), [50, 80, 30, 40, 70, 90]
    )
    coll = TurnOnCollection(_cfg(trafo="HT"), threshold=0)
    coll._load_arrays()
    coll._apply_cuts()
    np.testing.assert_allclose(
        ak.to_numpy(coll.ak_arrays["ref"]["HT"]), [150, 80, 90, 40, 70, 90]
    )


# --- scalings restricted to a subset of the test objects -----------------------------


def test_scaling_objects(cache):
    cfg = _cfg(PROMPT_LEPTONS)
    cfg["test_objects"]["L1puppiJetSC4:default:barrel"] = "pt"
    cfg["scalings"] = {"method": "naive", "threshold": 0.9}
    all_objs = [str(o) for o in PerformancePlotConfig(cfg).scaling_object_instances]
    assert len(all_objs) == 2
    cfg["scalings"]["objects"] = ["L1puppiJetSC4:default:barrel"]
    sel = PerformancePlotConfig(cfg).scaling_object_instances
    assert [str(o) for o in sel] == ["L1puppiJetSC4:default:barrel"]
    cfg["scalings"]["objects"] = ["L1puppiJetSC4:default:endcap"]
    with pytest.raises(ValueError):
        PerformancePlotConfig(cfg).scaling_object_instances
    # selection by config key, also when str(obj) differs from it (":inclusive")
    cfg["test_objects"] = {"L1puppiJetSC4:default": "pt"}
    cfg["scalings"]["objects"] = ["L1puppiJetSC4:default"]
    assert len(PerformancePlotConfig(cfg).scaling_object_instances) == 1

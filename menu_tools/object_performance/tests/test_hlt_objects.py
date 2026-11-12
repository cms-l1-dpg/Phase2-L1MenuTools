"""
HLT objects (nano hlt* collections) as test objects of the turn-on code:
tiny synthetic parquet caches in tmp_path, read through the cache-directory override.
"""
import awkward as ak
import numpy as np
import pytest

from menu_tools.object_performance.plotter import ScalingCentral
from menu_tools.object_performance.turnon_collection import TurnOnCollection
from menu_tools.utils import constants
from menu_tools.utils.objects import Object, is_trigger_object, trigger_level

VERSION = "Vhlttest"
SAMPLE = "synthetic"


def _write(tmp_path, obj, fields):
    (tmp_path / VERSION).mkdir(exist_ok=True)
    arr = ak.Array({f"{obj}_{k}": v for k, v in fields.items()})
    ak.to_parquet(arr, tmp_path / VERSION / f"{VERSION}_{SAMPLE}_{obj}.parquet")


@pytest.fixture
def cache(tmp_path, monkeypatch):
    """Three DY-like events with one gen electron of 50 GeV each:
    ev0: matched HLT electron, 45 GeV, isolated   -> passes WPTight (barrel) and 30 GeV
    ev1: matched HLT electron, 45 GeV, ecalIso 20 -> fails "{ecalIso} < 9 + 0.02*{pt}"
    ev2: no HLT electron
    """
    monkeypatch.setenv("MENU_TOOLS_CACHE", str(tmp_path))
    monkeypatch.setattr(constants, "CACHE_DIR", str(tmp_path))
    _write(
        tmp_path,
        "GenPart",
        {
            "pt": [[50.0], [50.0], [50.0]],
            "eta": [[0.1], [0.2], [0.3]],
            "phi": [[0.0], [1.0], [2.0]],
            "mass": [[0.0], [0.0], [0.0]],
            "pdgId": [[11], [-11], [11]],
            "statusFlags": [[1 << 7], [1 << 7], [1 << 7]],
        },
    )
    zeros = [[0.0], [0.0], []]
    _write(
        tmp_path,
        "hltElectron",
        {
            "pt": [[45.0], [45.0], []],
            "eta": [[0.1], [0.2], []],
            "phi": [[0.0], [1.0], []],
            "m": zeros,
            "sigmaIetaIeta": [[0.009], [0.009], []],
            "hOverE": zeros,
            "ecalIso": [[1.0], [20.0], []],
            "hcalIso": zeros,
            "trackIso": zeros,
            "ooEMOop": zeros,
            "dEtaIn": zeros,
            "dPhiIn": zeros,
        },
    )
    return tmp_path


def _cfg(test_objects, matching_and_threshold=True):
    return {
        "sample": SAMPLE,
        "version": "V50nano",
        "match_test_to_ref": True,
        "matching_and_threshold": matching_and_threshold,
        "reference_object": {
            "object": "GenPart",
            "x_arg": "pt",
            "label": "Gen Electrons",
            "cuts": {
                "event": ["(({statusFlags}>>7)&1) == 1", "abs({pdgId}) == 11"],
                "object": ["abs({eta}) < 2.4"],
            },
        },
        "test_objects": test_objects,
        "thresholds": [30],
        "binning": {"min": 0, "max": 100, "step": 25},
        "xlabel": "x",
        "ylabel": "y",
    }


@pytest.mark.parametrize(
    "obj_key, threshold, n_num",
    [
        ("hltElectron:default", -999, 2),  # matching: ev0, ev1
        ("hltElectron:default", 30, 2),
        ("hltElectron:WPTight:barrel", 30, 1),  # ev1 fails the ECAL isolation
        ("hltElectron:default", 50, 0),
    ],
)
def test_hlt_object_turnon(cache, obj_key, threshold, n_num):
    coll = TurnOnCollection(
        _cfg({obj_key: "pt"}), threshold, "test", config_version="V50nano", override_version=VERSION
    )
    coll.create_hists()
    test_obj = str(coll.test_objects[0][0])
    assert test_obj.startswith("hltElectron:")
    # all three gen electrons are in the [50, 75) bin; denominator = all of them
    assert coll.hists["ref"][test_obj][0].sum() == 3
    assert coll.hists[test_obj][0].sum() == n_num
    eff, _ = coll.get_efficiency(coll.test_objects[0][0])
    assert eff[2] == pytest.approx(n_num / 3)


def test_hlt_x_arg_not_lowercased():
    """Nano trigger objects keep the configured field name (old ntuples were lower-cased)."""
    coll = TurnOnCollection(
        _cfg({"hltHpsPFTau:default": "deepTauVSjet", "L1nnPuppiTau:default": "pt"}), 30
    )
    assert [x for _, x in coll.test_objects] == ["deepTauVSjet", "pt"]


def test_trigger_level_labels():
    assert trigger_level(["L1tkElectron:Iso:barrel", "L1EG:default"]) == "L1"
    assert trigger_level(["hltMuon:default:inclusive"]) == "HLT"
    assert trigger_level(["hltMuon:default", "L1gmtTkMuon:default"]) == "L1/HLT"
    assert is_trigger_object("hltMuon:default") and is_trigger_object("L1EG:default")
    assert not is_trigger_object("GenPart")


def test_hlt_scaling_thresholds():
    central = ScalingCentral.__new__(ScalingCentral)
    central.scaling_thresholds = {"Muon": [1, 2], "HLTMuon": [24, 50], "Jet": [3]}
    cfg = {"test_objects": {"hltMuon:default": "pt", "L1gmtTkMuon:default": "pt"}}
    hlt = Object("hltMuon:default", "V50nano")
    l1 = Object("L1gmtTkMuon:default", "V50nano")
    assert central._get_scaling_thresholds(cfg, hlt) == [24, 50]
    assert central._get_scaling_thresholds(cfg, l1) == [1, 2]
    # HLT objects fall back to the group thresholds if no HLT<group> entry exists
    cfg_jet = {"test_objects": {"hltAK4PuppiJet:default": "pt"}}
    assert central._get_scaling_thresholds(cfg_jet, Object("hltAK4PuppiJet:default", "V50nano")) == [3]


def test_cuts_with_several_fields():
    """Two fields in one cut expression without an operator in between."""
    from menu_tools.utils.objects import compute_selection_mask_for_object_cuts

    arr = ak.Array(
        {
            "pt": [[100.0, 100.0]],
            "eta": [[2.0, 2.0]],
            "ecalIso": [[10.0, 12.0]],
            "hcalIso": [[0.0, 0.0]],
            "hOverE": [[0.0, 0.0]],
            "sigmaIetaIeta": [[0.0, 0.0]],
            "trackIso": [[0.0, 0.0]],
            "ooEMOop": [[0.0, 0.0]],
            "dEtaIn": [[0.0, 0.0]],
            "dPhiIn": [[0.0, 0.0]],
        }
    )
    sel = compute_selection_mask_for_object_cuts(Object("hltElectron:WPTight", "V50nano"), arr)
    # ecalIso < 9 + 0.02 * 100 = 11
    assert ak.to_list(sel) == [[True, False]]
    assert np.all(ak.to_numpy(ak.flatten(sel)) == np.array([True, False]))

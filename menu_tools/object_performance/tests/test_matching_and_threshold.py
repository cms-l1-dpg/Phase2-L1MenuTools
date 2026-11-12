"""
Synthetic test of the `matching_and_threshold` option of matched turn-ons:
the denominator is all reference objects instead of the matched ones only.
"""
import awkward as ak
import numpy as np
import pytest

from menu_tools.object_performance.turnon_collection import TurnOnCollection


def _cfg(matching_and_threshold: bool, ref_x_arg: str = "pt") -> dict:
    return {
        "sample": "synthetic",
        "version": "V50nano",
        "match_test_to_ref": True,
        "matching_and_threshold": matching_and_threshold,
        "reference_object": {"object": "GenPart", "x_arg": ref_x_arg, "label": "Gen"},
        "test_objects": {"L1EG:default": "pt"},
        "thresholds": [30],
        "binning": {"min": 0, "max": 100, "step": 25},
        "xlabel": "x",
        "ylabel": "y",
    }


def _vec(pt, eta, phi):
    arr = ak.zip(
        {
            "pt": pt,
            "eta": eta,
            "phi": phi,
            "mass": [[0.0] * len(x) for x in pt],
        }
    )
    return ak.with_name(arr, "Momentum4D")


def _collection(matching_and_threshold: bool, ref_x_arg: str = "pt"):
    """Four reference objects with pT 50 (one per event):
    ev0 matched to a 45 GeV L1 object, ev1 matched to a 20 GeV L1 object,
    ev2 has no L1 object, ev3 has an L1 object far away (unmatched)."""
    coll = TurnOnCollection(_cfg(matching_and_threshold, ref_x_arg), threshold=30)
    coll.ak_arrays["ref"] = _vec(
        [[50.0], [50.0], [50.0], [50.0]],
        [[0.0], [0.5], [1.0], [-1.0]],
        [[0.0], [1.0], [2.0], [-1.0]],
    )
    test_obj = str(coll.test_objects[0][0])
    coll.ak_arrays[test_obj] = _vec(
        [[45.0], [20.0], [], [60.0]],
        [[0.0], [0.5], [], [1.5]],
        [[0.0], [1.0], [], [2.0]],
    )
    coll._match_test_to_ref()
    return coll, test_obj


@pytest.mark.parametrize(
    "matching_and_threshold, threshold, n_num, n_den",
    [
        (False, 30, 1, 2),  # threshold eff: 1 passing of 2 matched
        (True, 30, 1, 4),  # matching + threshold eff: 1 passing of 4 ref
        (False, -999, 2, 4),  # matching eff: 2 matched of 4 ref
        (True, -999, 2, 4),  # same: no threshold = matching eff
    ],
)
def test_matching_and_threshold_denominator(
    matching_and_threshold, threshold, n_num, n_den
):
    coll, test_obj = _collection(matching_and_threshold)
    coll.set_threshold(threshold)
    eff, _ = coll.get_efficiency(coll.test_objects[0][0])
    # all reference objects are in the [50, 75) bin
    assert coll.hists[test_obj][0].sum() == n_num
    assert coll.hists["ref"][test_obj][0].sum() == n_den
    assert eff[2] == pytest.approx(n_num / n_den)
    assert np.all(np.isnan(np.delete(eff, 2)))


def test_matching_and_threshold_requires_same_x_arg():
    coll, _ = _collection(True, ref_x_arg="eta")
    with pytest.raises(ValueError, match="matching_and_threshold"):
        coll.set_threshold(30)

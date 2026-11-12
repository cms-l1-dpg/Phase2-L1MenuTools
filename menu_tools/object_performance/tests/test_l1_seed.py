"""
Synthetic tests of the `l1_seed` option of matched turn-ons (combined L1 x HLT efficiency):
a reference object counts in the `<hlt>+L1seed` numerator only if it is matched to the HLT
object passing the HLT threshold AND to an L1 seed object passing the L1 threshold.
"""
import awkward as ak
import numpy as np
import pytest

from menu_tools.object_performance.turnon_collection import (
    L1SEED_KEY,
    L1SEED_SUFFIX,
    TurnOnCollection,
)

HLT_THR = 24
L1_THR = 20


def _cfg(l1_seed=None, matching_and_threshold=True) -> dict:
    cfg = {
        "sample": "synthetic",
        "version": "V50nano",
        "match_test_to_ref": True,
        "matching_and_threshold": matching_and_threshold,
        "reference_object": {"object": "GenPart", "x_arg": "pt", "label": "Gen"},
        "test_objects": {"hltMuon:default": "pt"},
        "thresholds": [HLT_THR],
        "binning": {"min": 0, "max": 100, "step": 25},
        "xlabel": "x",
        "ylabel": "y",
    }
    if l1_seed is not None:
        cfg["l1_seed"] = l1_seed
    return cfg


def _vec(pt, eta, phi):
    arr = ak.zip({"pt": pt, "eta": eta, "phi": phi, "mass": [[0.0] * len(x) for x in pt]})
    return ak.with_name(arr, "Momentum4D")


# One reference (gen) object with pT 50 per event, at (eta, phi) = (0.1 * i, 0.5 * i):
#   ev0: HLT 40 matched, L1 30 matched            -> L1, HLT, L1 x HLT
#   ev1: HLT 40 matched, no L1 object             -> HLT only
#   ev2: HLT 40 matched, L1 15 matched (< L1 thr) -> HLT only (L1 matched, not passing)
#   ev3: HLT 40 matched, L1 30 far away           -> HLT only (L1 unmatched)
#   ev4: HLT 10 matched (< HLT thr), L1 30        -> L1 only
#   ev5: nothing
N_EV = 6
REF_ETA = [0.1 * i for i in range(N_EV)]
REF_PHI = [0.5 * i for i in range(N_EV)]
HLT = ([[40.0], [40.0], [40.0], [40.0], [10.0], []], [[e] for e in REF_ETA[:5]] + [[]])
L1 = (
    [[30.0], [], [15.0], [30.0], [30.0], []],
    [[REF_ETA[0]], [], [REF_ETA[2]], [REF_ETA[3] + 1.0], [REF_ETA[4]], []],
)


def _collection(l1_seed=None, matching_and_threshold=True, l1=L1):
    coll = TurnOnCollection(_cfg(l1_seed, matching_and_threshold), threshold=HLT_THR)
    coll.ak_arrays["ref"] = _vec([[50.0]] * N_EV, [[e] for e in REF_ETA], [[p] for p in REF_PHI])
    hlt_key = str(coll.test_objects[0][0])
    coll.ak_arrays[hlt_key] = _vec(
        HLT[0], HLT[1], [[REF_PHI[i]] if HLT[0][i] else [] for i in range(N_EV)]
    )
    for i, (obj, _, _) in enumerate(coll.l1_seed_objects):
        coll.ak_arrays[coll._l1_seed_key(i, obj)] = _vec(
            l1[0], l1[1], [[REF_PHI[k]] * len(l1[0][k]) for k in range(N_EV)]
        )
    coll._match_test_to_ref()
    if l1_seed is not None:
        coll._match_l1_seed_to_ref()
    coll.set_threshold(HLT_THR)
    return coll, hlt_key


def _counts(coll, key):
    """(numerator, denominator) counts; all reference objects are in the [50, 75) bin."""
    num = coll.hists[key][0]
    den = coll.hists["ref"][key][0]
    assert num.sum() == num[2] and den.sum() == den[2]
    return num[2], den[2]


SEED = {"object": "L1gmtTkMuon:VLoose", "threshold": L1_THR}


def test_l1_seed_numerators():
    coll, hlt = _collection(SEED)
    assert _counts(coll, hlt) == (4, N_EV)  # HLT only: ev0-3
    assert _counts(coll, L1SEED_KEY) == (2, N_EV)  # L1 only: ev0, ev4
    assert _counts(coll, hlt + L1SEED_SUFFIX) == (1, N_EV)  # L1 x HLT: ev0 only
    eff, _ = coll.get_efficiency(hlt + L1SEED_SUFFIX)
    assert eff[2] == pytest.approx(1 / N_EV)


def test_l1_seed_threshold_per_region():
    # muons at |eta| < 0.83 are barrel: a 100 GeV barrel threshold removes all of them
    seed = {"object": "L1gmtTkMuon:VLoose", "threshold": {"barrel": 100, "endcap": L1_THR}}
    coll, hlt = _collection(seed)
    assert _counts(coll, L1SEED_KEY) == (0, N_EV)
    assert _counts(coll, hlt + L1SEED_SUFFIX) == (0, N_EV)
    # objects outside the listed regions fail
    seed = {"object": "L1gmtTkMuon:VLoose", "threshold": {"endcap": L1_THR}}
    coll, hlt = _collection(seed)
    assert _counts(coll, L1SEED_KEY) == (0, N_EV)


def test_l1_seed_or_of_objects():
    # second seed object with a low threshold recovers ev2 (L1 pT 15)
    seed = {
        "objects": [
            {"object": "L1gmtTkMuon:VLoose", "threshold": L1_THR},
            {"object": "L1gmtTkMuon:Loose", "threshold": 12, "match_dR": 0.1},
        ]
    }
    coll, hlt = _collection(seed)
    assert _counts(coll, L1SEED_KEY) == (3, N_EV)  # ev0, ev2, ev4
    assert _counts(coll, hlt + L1SEED_SUFFIX) == (2, N_EV)  # ev0, ev2


def test_l1_seed_without_matching_and_threshold():
    # threshold efficiencies: denominators are the matched reference objects
    coll, hlt = _collection(SEED, matching_and_threshold=False)
    assert _counts(coll, hlt) == (4, 5)  # HLT matched: ev0-4
    assert _counts(coll, hlt + L1SEED_SUFFIX) == (1, 5)  # same denominator as the HLT curve
    assert _counts(coll, L1SEED_KEY) == (2, 3)  # L1 matched: ev0, ev2, ev4


def test_l1_seed_apply_to_and_labels():
    coll, hlt = _collection({**SEED, "apply_to": ["hltMuon:default"], "label": "my seed"})
    assert coll.l1_seeded_test_objects == [hlt]
    assert coll.curve_label(L1SEED_KEY) == "L1 seed: my seed"
    assert coll.curve_label(hlt + L1SEED_SUFFIX).endswith("$\\wedge$ L1 seed")
    with pytest.raises(ValueError, match="apply_to"):
        _collection({**SEED, "apply_to": ["hltMuon:default:barrel"]})


def test_without_l1_seed_unchanged():
    coll, hlt = _collection(None)
    assert set(coll.hists) == {"ref", hlt}
    assert set(coll.hists["ref"]) == {hlt}
    assert coll.extra_curves == {}
    assert _counts(coll, hlt) == (4, N_EV)
    # the HLT-only curve does not depend on the presence of the seed
    coll_seed, _ = _collection(SEED)
    np.testing.assert_array_equal(coll.hists[hlt][0], coll_seed.hists[hlt][0])
    np.testing.assert_array_equal(coll.hists["ref"][hlt][0], coll_seed.hists["ref"][hlt][0])

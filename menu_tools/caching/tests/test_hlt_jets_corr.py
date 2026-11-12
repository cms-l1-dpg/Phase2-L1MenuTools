"""HLT jet energy correction (make_hlt_jets_corr.py): formula, table lookup and sums."""

import os

import awkward as ak
import numpy as np
import pytest

from menu_tools.caching.make_hlt_jets_corr import (
    JEC_DIR,
    JEC_L2,
    SRC,
    TARGET,
    correct_jets,
    l2relative,
    load_jec_table,
    make_sums,
)


@pytest.fixture(scope="module")
def table():
    return load_jec_table(os.path.join(JEC_DIR, JEC_L2))


def _formula(pt, p):
    lx = np.log10(np.clip(pt, p[3], p[4]))
    return max(1e-4, p[5] + p[6] / (lx**2 + p[7]) + p[8] * np.exp(-p[9] * (lx - p[10]) ** 2))


def test_trivial_levels_are_one():
    for lvl in ("L1FastJet", "L3Absolute"):
        fname = os.path.join(JEC_DIR, f"phase2_realistic_T35_{lvl}_AK4PFPuppiHLT.txt")
        with open(fname) as f:
            header = f.readline().split()
        # formula field (after the binning/variable declarations) is the constant 1
        assert header[-3] == "1", header


def test_l2relative_matches_formula_and_bins(table):
    rng = np.random.default_rng(1)
    eta = rng.uniform(-5.1, 5.1, 200)
    pt = rng.uniform(5, 800, 200)
    got = l2relative(pt, eta, table)
    for e, x, c in zip(eta, pt, got):
        row = table[(table[:, 0] <= e) & (e < table[:, 1])][0]
        assert c == pytest.approx(_formula(x, row), rel=1e-12)
    # raw pT outside the table range is clamped
    row = table[0]
    assert l2relative([1e5], [row[0] + 0.01], table)[0] == pytest.approx(_formula(row[4], row))


def test_correct_jets_and_sums(table):
    jets = ak.Array(
        [
            [
                {f"{SRC}_pt": 40.0, f"{SRC}_eta": 0.5, f"{SRC}_phi": 0.0, f"{SRC}_mass": 5.0},
                {f"{SRC}_pt": 60.0, f"{SRC}_eta": 3.5, f"{SRC}_phi": 1.0, f"{SRC}_mass": 8.0},
            ],
            [],
        ]
    )
    cj = correct_jets(jets, table)
    fac = l2relative([40.0, 60.0], [0.5, 3.5], table)
    pts = sorted(np.array([40.0, 60.0]) * fac, reverse=True)
    assert ak.to_list(cj[f"{TARGET}_pt"][0]) == pytest.approx(pts, rel=1e-6)
    flat = ak.flatten(cj)
    ratio = ak.to_numpy(flat[f"{TARGET}_pt"] / flat[f"{TARGET}_rawPt"])
    assert ratio == pytest.approx(ak.to_numpy(flat[f"{TARGET}_jecFactor"]), rel=1e-5)
    s = make_sums(cj)
    ht, mht = ak.to_list(s["hltPuppiJetCorrSums_pt"][0])
    # HT: |eta| < 2.4 only -> the central jet; MHT: both jets (|eta| < 5, E_T)
    assert ht == pytest.approx(40.0 * fac[0], rel=1e-6)
    assert mht > 0
    assert ak.to_list(s["hltPuppiJetCorrSums_pt"][1]) == [0.0, 0.0]
    assert ak.to_list(s["hltPuppiJetCorrSums_sumType"][0]) == [0, 1]

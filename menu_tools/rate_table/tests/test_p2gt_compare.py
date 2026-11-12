import numpy as np
import pytest

from menu_tools.rate_table import p2gt_compare as pc


def test_match_seeds_default_and_map():
    menu = ["L1_SingleTkMu", "L1_DoubleTkEle", "L1_SingleTau"]
    algos = ["pSingleTkMuon22", "pDoubleTkEle", "pOther"]
    matched, missing, unmatched = pc.match_seeds(
        menu, algos, {"L1_SingleTkMu": "pSingleTkMuon22"}
    )
    assert matched == {
        "L1_SingleTkMu": "pSingleTkMuon22",
        "L1_DoubleTkEle": "pDoubleTkEle",
    }
    assert missing == ["L1_SingleTau"]
    assert unmatched == ["pOther"]


@pytest.mark.parametrize(
    "name, algo",
    [
        ("L1_pSingleTkMuon22_final", "pSingleTkMuon22"),
        ("pSingleTkMuon22", "pSingleTkMuon22"),
    ],
)
def test_normalise_algo(name, algo):
    assert pc.normalise_algo(name) == algo


def test_output_stem_matches_rate_table():
    assert pc.output_stem("v45_Step1p5Menu", "V50") == "v45_Step1p5Menu_V50"
    assert (
        pc.output_stem("m", "V50", scalings="V49", truncated=True, signal="TT")
        == "m_V50_scalings_V49_truncated_TT"
    )


def test_names_path_by_p2gt_menu():
    step1 = pc.load_names(pc.names_path("step1_2024"))
    assert step1["L1_SingleTkMu"] == "pSingleTkMuon22"
    assert pc.names_path("step1and2_2026") == pc.names_path("step1_2024")
    assert pc.names_path("step1p5_2026") is None
    assert pc.names_path(None) is None


def test_pure_counts():
    masks = np.array(
        [[1, 0, 0], [1, 1, 0], [0, 0, 1], [0, 1, 0], [0, 0, 0]], dtype=bool
    )
    assert list(pc.pure_counts(masks)) == [1, 1, 1]


def test_compare_and_rates():
    menu = {"L1_A": np.array([1, 1, 0, 0], bool), "L1_B": np.array([0, 1, 1, 0], bool)}
    gt = {"pA": np.array([1, 0, 0, 1], bool), "pB": np.array([0, 1, 1, 0], bool)}
    df = pc.add_rates(
        pc.compare(menu, gt, {"L1_A": "pA", "L1_B": "pB"}), 4, signal=True
    )
    assert df.loc["L1_A", ["menu_only", "p2gt_only"]].tolist() == [1, 1]
    assert df.loc["L1_B", "mismatch"] == 0
    assert df.loc["L1_A", "npure_menu"] == 1 and df.loc["L1_A", "npure_p2gt"] == 2
    assert df.loc["Total", "npass_menu"] == 3 and df.loc["Total", "npass_p2gt"] == 4
    assert df.loc["L1_A", "eff_menu"] == pytest.approx(0.5)
    assert df.loc["Total", "diff"] == pytest.approx(-0.25)

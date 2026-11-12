import math

import awkward as ak
import numpy as np
import pandas as pd
import pytest

from menu_tools.rate_table import hlt_paths
from menu_tools.rate_table import menu_table as mt
from menu_tools.utils import scalings
from menu_tools.utils.objects import Object


@pytest.mark.parametrize(
    "raw_key, name, bit_record, expected",
    [
        # L1 objects: as before
        ("L1gmtTkMuon_pt", "L1gmtTkMuon", False, "pt"),
        (
            "L1gmtTkMuon_hwQual",
            "L1gmtTkMuon",
            False,
            "hwQual",
        ),  # "qual" is case-sensitive
        ("L1puppiJetSC4sums_sumType", "L1puppiJetSC4sums", False, "sumType"),
        ("L1somethingElse", "L1gmtTkMuon", False, "L1somethingElse"),
        # HLT objects: prefix stripped, case kept (was "_pt" before)
        ("hltMuon_pt", "hltMuon", False, "pt"),
        ("hltElectron_sigmaIetaIeta", "hltElectron", False, "sigmaIetaIeta"),
        ("hltPFPuppiMET_pt", "hltPFPuppiMET", False, "pt"),
        # bit records
        ("HLT_IsoMu24_FromL1TkMuon", "HLT", True, "IsoMu24_FromL1TkMuon"),
        ("HLT_Ele32_WPTight_L1Seeded", "HLT", True, "Ele32_WPTight_L1Seeded"),
        ("L1_pSingleTkMuon22_final", "L1", True, "pSingleTkMuon22_final"),
        ("HLT_SomeQualityPath", "HLT", True, "SomeQualityPath"),
        # legacy (pre-nano) keys
        ("tkElectronEt", "tkElectron", False, "et"),
        ("tkElectronQual", "tkElectron", False, "quality"),
        ("L1EG_qual", "L1EG", False, "quality"),
    ],
)
def test_transform_key(raw_key, name, bit_record, expected):
    assert mt.transform_key(raw_key, name, bit_record) == expected


def test_transform_key_method_uses_bit_records():
    """`HLT` / `L1` are bit records through configs/V50nano/objects/hlt_bits.yaml."""
    table = mt.MenuTable.__new__(mt.MenuTable)  # no config / cache needed
    assert (
        table._transform_key(
            "HLT_IsoMu24_FromL1TkMuon", Object("HLT:default", "V50nano")
        )
        == "IsoMu24_FromL1TkMuon"
    )
    assert (
        table._transform_key(
            "L1_pSingleTkMuon22_final", Object("L1:default", "V50nano")
        )
        == "pSingleTkMuon22_final"
    )
    assert (
        table._transform_key(
            "L1gmtTkMuon_hwQual", Object("L1gmtTkMuon:VLoose", "V50nano")
        )
        == "hwQual"
    )


@pytest.mark.parametrize(
    "n, lo, hi",
    [
        (0, 0.0, -math.log(0.16)),  # closed forms for n = 0 (upper) and n = 1 (lower)
        (1, -math.log(0.84), 3.2885),
        (2, 0.7120, 4.6250),
        (50, 42.988, 58.075),
    ],
)
def test_garwood_interval(n, lo, hi):
    g_lo, g_hi = mt.garwood_interval(n)
    assert g_lo == pytest.approx(lo, abs=1e-3)
    assert g_hi == pytest.approx(hi, abs=1e-3)
    assert g_lo <= n <= g_hi


def test_garwood_interval_large_n_is_sqrt_n():
    lo, hi = mt.garwood_interval(10000)
    assert (hi - lo) / 2 == pytest.approx(100, rel=0.01)


def test_make_row_has_counts_and_garwood():
    table = mt.MenuTable.__new__(mt.MenuTable)

    class _Cfg:
        is_signal = False

    table.config = _Cfg()
    row = table._make_row("HLT_IsoMu24_FromL1TkMuon", 50, 2_000_000)
    assert row["npass"] == 50
    norm = mt.constants.RATE_NORM_FACTOR / 2_000_000
    assert row["rate"] == pytest.approx(50 * norm)
    lo, hi = mt.garwood_interval(50)
    assert row["rateLo68"] == pytest.approx(lo * norm)
    assert row["rateHi68"] == pytest.approx(hi * norm)
    # binomial errors kept, and close to Garwood for a small fraction
    assert row["rate"] - row["rateErrLo"] == pytest.approx(row["rateLo68"], rel=1e-3)


def test_wrap_event_records_matches_python_lists():
    arr = ak.zip(
        {
            "pt": np.array([1.5, 2.25, 3.0], dtype=np.float32),
            "n": np.array([1, 2, 3], dtype=np.int32),
            "bit": np.array([True, False, True]),
        }
    )
    ref = ak.zip({f: [[k] for k in arr[f]] for f in arr.fields})
    new = mt.wrap_event_records(arr)
    assert str(new.type) == str(ref.type)
    assert "var" in str(new.type)
    # ak.array_equal needs awkward >= 2.6; the project pins 2.5.2
    assert new.to_list() == ref.to_list()


def test_missing_scalings_fallback():
    obj = Object("L1puppiMET:default", "V50nano")
    arr = ak.zip({"pt": np.array([10.0, 20.0], dtype=np.float32)})
    with pytest.raises(scalings.MissingScalingsError):
        scalings.add_offline_pt(arr, obj, scaling_version="__no_such_version__")
    out = scalings.add_offline_pt(
        arr, obj, scaling_version="__no_such_version__", allow_missing=True
    )
    assert ak.to_list(out.offline_pt) == [10.0, 20.0]


def test_has_pt_branch():
    assert scalings.has_pt_branch(ak.zip({"pt": [1.0]}), "hltMuon:default:inclusive")
    assert not scalings.has_pt_branch(
        ak.zip({"IsoMu24_FromL1TkMuon": [True]}), "HLT:default:inclusive"
    )


def test_hlt_paths_table():
    hlt = ak.zip(
        {"HLT_A": [True, False, True, False], "HLT_B": [False, False, True, True]}
    )
    l1 = ak.zip(
        {
            "L1_pX_final": [True, True, True, False],
            "L1_pY_final": [False, False, True, True],
        }
    )
    mapping = {"HLT_A": {"l1_seeds": ["L1_pX_final"]}, "HLT_B": {"l1_seeds": ["ANY"]}}
    df = hlt_paths.path_table(mapping, hlt, l1, as_rate=True)
    a, b, tot = (df.iloc[i] for i in range(3))
    assert (a.n_l1, a.n_hlt, a.n_l1_hlt, a.n_hlt_not_l1) == (3, 2, 2, 0)
    assert (b.n_l1, b.n_hlt, b.n_l1_hlt) == (4, 2, 2)
    assert tot.path == "Total" and (tot.n_l1, tot.n_hlt, tot.n_l1_hlt) == (4, 3, 3)
    assert isinstance(df, pd.DataFrame) and "rate_hlt_hi68" in df

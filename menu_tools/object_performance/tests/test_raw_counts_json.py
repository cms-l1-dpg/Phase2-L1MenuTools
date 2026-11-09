"""
Checks that the raw counts (distribution) plot also saves its histograms as
JSON, so they can be compared without rerunning. Uses a small fake turn-on
collection instead of ntuples, with the V29 HT config from reference_data.
"""
import json
from types import SimpleNamespace

import numpy as np
import pytest
import yaml

from menu_tools.object_performance import plotter


CFG_PATH = "menu_tools/object_performance/tests/reference_data/HT_90perc_350_V29.yaml"


@pytest.fixture
def efficiency_plotter(tmp_path, monkeypatch):
    with open(CFG_PATH) as f:
        name, cfg = next(iter(yaml.safe_load(f).items()))

    edges = np.array([0.0, 20.0, 40.0, 60.0])
    hists = {
        "trackerHT:default:inclusive": np.histogram([5, 25, 25, 45], bins=edges),
        "phase1PuppiHT:default:inclusive": np.histogram([25, 45, 45], bins=edges),
        "ref": {
            "trackerHT:default:inclusive": np.histogram(
                [5, 5, 25, 25, 25, 45, 45, 45, 45], bins=edges
            ),
            "phase1PuppiHT:default:inclusive": np.histogram(
                [5, 25, 25, 45, 45, 45, 45], bins=edges
            ),
        },
    }
    collection = SimpleNamespace(
        bins=edges,
        hists=hists,
        version="V29",
        threshold=350,
        cfg_plot=SimpleNamespace(bin_width=20.0),
        xerr=lambda obj_key: np.full(len(edges) - 1, 10.0),
    )
    monkeypatch.setattr(
        plotter.EfficiencyPlotter,
        "_outdir_distributions",
        property(lambda self: str(tmp_path)),
    )
    return plotter.EfficiencyPlotter(name, cfg, collection), tmp_path


def test_raw_counts_saved_as_json(efficiency_plotter):
    eff_plotter, outdir = efficiency_plotter
    eff_plotter._plot_raw_counts()

    stem = "HT_90perc_350_dist_V29"
    assert (outdir / f"{stem}.png").exists()
    assert (outdir / f"{stem}.yaml").exists()
    with open(outdir / f"{stem}.json") as f:
        plot = json.load(f)

    assert plot["xlabel"] == "Gen. HT (GeV)"
    assert plot["ylabel"] == "Counts"

    test = plot["trackerHT:default:inclusive"]
    assert test["label"] == "Tracker HT"
    assert test["counts"] == [1, 2, 1]
    assert test["counts_err"] == pytest.approx([1.0, 2**0.5, 1.0])
    assert test["xbins"] == [10.0, 30.0, 50.0]
    assert test["bin_edges"] == [0.0, 20.0, 40.0, 60.0]
    assert test["reference"] is False

    ref = plot["ref:trackerHT:default:inclusive"]
    assert ref["counts"] == [2, 3, 4]
    assert ref["reference"] is True
    assert ref["test_object"] == "trackerHT:default:inclusive"
    assert ref["label"] == "Gen HT (reference for Tracker HT)"

    assert plot["phase1PuppiHT:default:inclusive"]["counts"] == [0, 1, 2]

"""
Sample label in the legend title of the performance plots (menu_tools/utils/
sample_labels.py): the label map, the `sample_label` override / opt-out, the title
layout, and the legend titles of the efficiency, scaling and resolution plotters (the
path-efficiency, purity and b-tag plotters: in their own tests).

Run from the repository root (object definitions are read from configs/V50nano/objects).
"""
import copy
import glob
import os

import matplotlib.pyplot as plt
import numpy as np
import pytest
import yaml

from menu_tools.object_performance.config import PerformancePlotConfig
from menu_tools.object_performance.plotter import EfficiencyPlotter, ScalingPlotter
from menu_tools.object_performance.resolution_collection import ResolutionCollection
from menu_tools.object_performance.resolution_plotter import ResolutionPlotter
from menu_tools.object_performance.tests import test_resolution, test_split_by
from menu_tools.utils.sample_labels import (
    SEPARATOR,
    legend_title,
    pretty_sample,
    resolve_sample_label,
    sample_labels,
    visible_length,
    wrap_title,
)

HH = r"HH$\rightarrow$bb$\tau\tau$"
TT = r"$t\bar{t}$"
CONFIGS = os.path.join(os.path.dirname(__file__), "..", "..", "..", "configs")


def test_pretty_sample():
    assert pretty_sample("HHTo2B2Tau") == HH
    assert pretty_sample("DYLL_M50") == r"DY$\rightarrow\ell\ell$"
    assert pretty_sample("MinBias") == "Minimum bias"
    assert pretty_sample("NotASample") == "NotASample"  # fallback: the raw key


def test_resolve_sample_label():
    assert resolve_sample_label({"sample": "TT"}) == TT
    assert resolve_sample_label({"sample": "TT", "sample_label": True}) == TT
    assert resolve_sample_label({"sample": "TT", "sample_label": "my tt"}) == "my tt"
    assert resolve_sample_label({"sample": "TT", "sample_label": False}) is None
    assert resolve_sample_label({"sample": "TT", "sample_label": ""}) is None
    assert resolve_sample_label({}) is None
    with pytest.raises(ValueError):
        resolve_sample_label({"sample": "TT", "sample_label": 3})
    cfg = PerformancePlotConfig({"sample": "HHTo2B2Tau", "version": "V50nano"}, "p")
    assert cfg.sample_label == HH


def test_legend_title():
    assert legend_title(None) is None
    assert legend_title(HH) == HH
    assert legend_title(None, "Gen Taus") == "Gen Taus"
    # short enough: one line
    assert legend_title(HH, "Gen Taus") == f"{HH}{SEPARATOR}Gen Taus"
    # too long: sample label on the first line, the title wrapped below it
    ref = r"Gen visible taus, $|\eta| < 2.1$, subl. $p_T > 60$ GeV"
    title = legend_title(HH, ref)
    assert title is not None
    lines = title.split("\n")
    assert lines[0] == HH and len(lines) == 3
    assert " ".join(lines[1:]) == ref
    assert all(visible_length(line) <= 36 for line in lines)
    # a multi-line title is never joined onto the sample line
    assert legend_title(HH, "a\nb") == f"{HH}\na\nb"


def test_wrap_title_keeps_mathtext():
    text = r"NN PUPPI Tau, 1 leg of pDoublePuppiTau52_52 $p_T > 37.9$ GeV"
    wrapped = wrap_title(text, 20)
    assert wrapped.replace("\n", " ") == text
    for line in wrapped.split("\n"):
        assert line.count("$") % 2 == 0  # mathtext never split
    assert visible_length(r"$\tau\tau$") == 2
    assert visible_length(r"$p_{T}$") == 2


def test_labels_render_and_cover_the_configs():
    fig = plt.figure()
    for label in sample_labels().values():
        fig.text(0, 0, label)
    fig.canvas.draw()  # raises on invalid mathtext
    plt.close(fig)
    samples = set()
    pattern = os.path.join(CONFIGS, "V50nano", "object_performance", "*.yaml")
    for path in glob.glob(pattern):
        with open(path) as f:
            cfg = yaml.safe_load(f) or {}
        samples |= {c["sample"] for c in cfg.values() if isinstance(c, dict)}
    assert samples and samples <= set(sample_labels())


def test_efficiency_plotter(configs_in_cwd, legend_titles):
    coll, key = test_split_by._collection()
    coll.cfg_plot.config_dict["sample"] = "HHTo2B2Tau"
    EfficiencyPlotter("synth", None, coll).plot()
    v = coll.version
    thr = test_split_by.THR
    assert legend_titles[f"synth_{thr}_{v}"] == [HH]
    assert legend_titles[f"synth_{thr}_dist_{v}"] == [HH]
    split = [t for k, t in legend_titles.items() if k.startswith("synth_DM_")]
    assert split and all(t[0].startswith(HH) for t in split)
    # second line(s): the (wrapped) object label
    assert all(
        t[0].split("\n", 1)[1].replace("\n", " ") == coll.curve_label(key)
        for t in split
    )

    # opt-out: no title, the split plots keep the object label only
    legend_titles.clear()
    coll.cfg_plot.config_dict["sample_label"] = False
    EfficiencyPlotter("synth", None, coll).plot()
    assert legend_titles[f"synth_{thr}_{v}"] == [""]
    split = [t for k, t in legend_titles.items() if k.startswith("synth_DM_")]
    assert all(HH not in t[0] for t in split)


def test_scaling_plotter(configs_in_cwd, legend_titles):
    cfg = PerformancePlotConfig(
        {"sample": "TT", "version": "V50nano", "test_objects": {"hltMuon:default": ""}},
        "scal",
    )
    ScalingPlotter(
        "scal",
        cfg,
        {"hltMuon:default": {20: 22.0, 30: 33.0}},
        0.9,
        "V50nano",
        {"hltMuon:default": np.array([1.1, 0.0])},
    ).plot()
    assert legend_titles["scal_V50nano"] == [TT]


def test_resolution_plotter(configs_in_cwd, legend_titles, monkeypatch):
    ref, test, pu, _ = test_resolution._synthetic_matched_arrays()
    cfg = copy.deepcopy(test_resolution.CFG)
    cfg["sample"] = "TT"
    cfg["resolution"]["response_binning"] = {"pt": {"min": 0, "max": 2, "step": 0.1}}
    coll = ResolutionCollection(cfg, "res")
    obj_key = str(coll.test_objects[0][0])

    def fake_load():
        coll.ak_arrays["ref"] = ref
        coll.ak_arrays[obj_key] = test

    def fake_pileup():
        coll.pileup = pu

    monkeypatch.setattr(coll, "_load_arrays", fake_load)
    monkeypatch.setattr(coll, "_load_pileup", fake_pileup)
    coll.create()
    ResolutionPlotter("res", coll).plot()
    v = coll.version
    assert legend_titles[f"res_pt_vs_pt_{v}"] == [f"{TT}{SEPARATOR}Gen Muons"]
    dist = legend_titles[f"res_pt_vs_pt_dist_{v}"]
    assert TT in dist[-1]  # suptitle

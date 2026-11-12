import pytest

from menu_tools.rate_table import latex_table as lt


@pytest.fixture(autouse=True)
def no_object_configs(monkeypatch):
    """Don't read configs/<version>/objects; eta bounds come only from `objects_cfg`."""

    def fake_max_eta(obj_key, version, objects_cfg):
        return objects_cfg.get(obj_key.split(":")[0], {}).get("max_eta")

    monkeypatch.setattr(lt, "_object_max_eta", fake_max_eta)


OBJECTS = {
    "L1gmtTkMuon": {"plateau": "95", "max_eta": 2.4},
    "L1tkElectron": {"plateau": "93"},
    "L1puppiJetSC4": {"plateau": "100"},
}


@pytest.mark.parametrize(
    "cut, expected",
    [
        ("offline_pt >= 25.0", (25.0, False)),
        ("leg2.offline_pt >= 160.0", (160.0, False)),
        ("pt >= 7", (7.0, True)),
        ("offline_pt > 17.0", (17.0, False)),
        (None, None),
        ("(leg1+leg2).mass > 10", None),
    ],
)
def test_parse_threshold(cut, expected):
    assert lt.parse_threshold(cut) == expected


def test_cross_masks_fully_parsed():
    masks = [
        "((leg1.deltaR(leg2) < 1.6) & (leg1.deltaR(leg2) > 0))",
        "((leg1.charge*leg2.charge < 0.0))",
        "abs(leg2.z0-leg1.z0) < 1",
        "(leg1 + leg2).mass > 250",
        "abs(leg1.charge+leg2.charge+leg3.charge) == 1.0",
        "(leg2.bTagScore + leg3.bTagScore) > 2.2",
    ]
    for mask in masks:
        _, ok = lt._mask_items(mask)
        assert ok, mask


def test_unparsed_mask_is_reported():
    seed = {
        "cross_masks": ["leg1.something_new > 3"],
        "leg1": {"obj": "L1gmtTkMuon:VLoose", "threshold_cut": "offline_pt >= 5"},
    }
    derived = lt.derive_seed(seed, "V50nano", OBJECTS)
    assert derived["unparsed"] == ["leg1.something_new > 3"]


def test_derive_cross_seed():
    seed = {
        "cross_masks": ["abs(leg2.z0-leg1.z0) < 1", "abs(leg3.eta) < 2.1"],
        "leg1": {"obj": "L1PV:default", "threshold_cut": None},
        "leg2": {"obj": "L1gmtTkMuon:VLoose", "threshold_cut": "pt >= 7"},
        "leg3": {"obj": "L1tkElectron:NoIso:inclusive", "threshold_cut": "offline_pt >= 23.0"},
    }
    derived = lt.derive_seed(seed, "V50nano", OBJECTS)
    # PV leg skipped, online threshold marked, eta merged from object and mask
    assert derived["thresholds"] == "7" + lt.ONLINE_MARK + ",23"
    assert derived["requirements"] == r"$|\eta|<2.4$, $|\eta|<2.1$, ${\Delta}z<1$"
    assert derived["plateau"] == "95,93"


def test_mass_window_and_subscripts():
    seed = {
        "cross_masks": ["(leg1+leg2).mass > 7.0", "(leg1+leg2).mass < 18.0", "leg1.deltaR(leg3) < 0.4"],
        "leg1": {"obj": "L1gmtTkMuon:VLoose", "threshold_cut": "offline_pt >= 4"},
        "leg2": {"obj": "L1gmtTkMuon:VLoose", "threshold_cut": "offline_pt >= 4"},
        "leg3": {"obj": "L1puppiJetSC4:default", "threshold_cut": "offline_pt >= 40"},
    }
    req = lt.derive_seed(seed, "V50nano", OBJECTS)["requirements"]
    assert r"$7<m_{\mu \mu}<18$" in req
    assert r"${\Delta}R_{\mu j}<0.4$" in req


def test_section_hints(tmp_path):
    menu = tmp_path / "menu_cfg.yml"
    menu.write_text(
        "# Muon seeds\n"
        "L1_A:\n  cross_masks: []\n"
        "# L1_Commented:\n#   cross_masks: []\n#   leg1:\n"
        "L1_B:\n  cross_masks: []\n"
        "# # ########\n# # ### Jets\n# # ########\n"
        "L1_C:\n  cross_masks: []\n"
    )
    assert lt.read_section_hints(str(menu)) == {
        "L1_A": "Muon seeds",
        "L1_B": "Muon seeds",
        "L1_C": "Jets",
    }


def test_render_keeps_unplaced_seeds():
    menu = {
        "L1_A": {"cross_masks": [], "leg1": {"obj": "L1gmtTkMuon:VLoose", "threshold_cut": "offline_pt >= 22"}},
        "L1_B_new": {"cross_masks": [], "leg1": {"obj": "L1gmtTkMuon:VLoose", "threshold_cut": "offline_pt >= 5"}},
    }
    layout = {"sections": [{"name": "Muon seeds", "seeds": {"L1_A": {"label": "Single TkMuon"}, "L1_gone": {}}}]}
    sections, _ = lt.build_rows(menu, layout, {200: {"L1_A": 17.4, "L1_B_new": 0.2}}, "V50nano")
    assert [name for name, _ in sections][0] == "Muon seeds"
    assert sections[-1][1][0]["seed"] == r"L1\_B\_new"

    tex = lt.render_table(layout, sections, {200: 400.0}, False, ["x.csv"])
    assert r"Single TkMuon & 22 & 17 &" in tex
    assert r"$<$1" in tex  # rate 0.2 kHz
    assert "+30" not in tex  # margin line off by default
    tex = lt.render_table({**layout, "total_rate_margin": 0.3}, sections, {200: 400.0}, False, ["x.csv"])
    assert " & 520 & " in tex  # +30%
    assert "plateau" not in tex  # off by default


def test_two_pu_columns():
    menu = {"L1_A": {"cross_masks": [], "leg1": {"obj": "L1gmtTkMuon:VLoose", "threshold_cut": "offline_pt >= 22"}}}
    layout = {"sections": [{"name": "Muons", "seeds": {"L1_A": {"label": "Single TkMuon"}}}]}
    rates = {140: {"L1_A": 7.3}, 200: {"L1_A": 11.6}}
    sections, _ = lt.build_rows(menu, layout, rates, "V50nano")
    tex = lt.render_table(layout, sections, {140: 189.4, 200: 333.2}, False, ["a.csv", "b.csv"])
    assert r"\begin{tabular}{|l|c|c|c|c|}" in tex
    assert r"Single TkMuon & 22 & 7 & 12 & " in tex  # 140 PU left of 200 PU
    assert r"\multicolumn{2}{|l|}{Rate for above Trigger seeds} & 189 & 333 & " in tex


def test_resolve_rate_csvs(tmp_path, monkeypatch):
    """140 PU runs live in their own version: outputs/<version>_140PU/rate_tables."""
    monkeypatch.chdir(tmp_path)
    config = lt.MenuConfig({"version": "V50", "table_fname": "menu", "menu_config": "x", "sample": "MinBias"},
                           config_version="V50", override_version="V50_pre5")
    main = tmp_path / "outputs/V50_pre5/rate_tables/menu_V50_pre5.csv"
    pu140 = tmp_path / "outputs/V50_pre5_140PU/rate_tables/menu_V50_pre5_140PU.csv"
    for f in (main, pu140):
        f.parent.mkdir(parents=True)
        f.write_text("")
    layout = {"pu_columns": [{"pu": 140, "version_suffix": "_140PU"}, {"pu": 200, "version_suffix": ""}]}
    main_csv = lt.csv_path_for(config)
    assert lt.resolve_rate_csvs(layout, config, main_csv, None) == [
        (140, "outputs/V50_pre5_140PU/rate_tables/menu_V50_pre5_140PU.csv"), (200, main_csv)]
    # missing extra version -> column dropped
    layout["pu_columns"][0]["version_suffix"] = "_nope"
    assert lt.resolve_rate_csvs(layout, config, main_csv, None) == [(200, main_csv)]
    # explicit files win
    assert lt.resolve_rate_csvs(layout, config, main_csv, ["140=x.csv"]) == [(140, "x.csv")]
    # the old key is rejected with a pointer to the new one
    with pytest.raises(SystemExit, match="version_suffix"):
        lt.resolve_rate_csvs({"pu_columns": [{"pu": 140, "csv_suffix": "_140PU"}]}, config, main_csv, None)


def test_crop_png(tmp_path):
    Image = pytest.importorskip("PIL.Image")
    png = tmp_path / "page.png"
    im = Image.new("RGB", (400, 600), "white")
    im.paste((0, 0, 0), (100, 150, 200, 250))  # the "table"
    im.save(png)
    assert lt.crop_png(str(png), margin=10)
    assert Image.open(png).size == (120, 120)


def test_export_png_without_converters(tmp_path, monkeypatch):
    monkeypatch.setattr(lt.shutil, "which", lambda name: None)
    monkeypatch.setattr(lt, "_pymupdf_to_png", lambda *a: False)
    pdf = tmp_path / "table.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    assert lt.export_png(str(pdf)) is None


CFG = "configs/V50nano/rate_table/step1p5_cfg.yml"


def test_cli_init_writes_layout(tmp_path, monkeypatch):
    out = tmp_path / "layout.yml"
    monkeypatch.setattr(lt.sys, "argv", ["rate_table_tex", CFG, "--init", "--layout", str(out), "--title", "T"])
    lt.main()
    text = out.read_text()
    assert "title: 'T'" in text and "L1_SingleTkMu:" in text


def test_cli_init_only_options_rejected(monkeypatch):
    monkeypatch.setattr(lt.sys, "argv", ["rate_table_tex", CFG, "--inherit", "x.yml"])
    with pytest.raises(SystemExit):
        lt.main()


def _fake_tex(dir_, lacks=()):
    """A TeX bin dir whose kpsewhich finds every package except `lacks`."""
    dir_.mkdir()
    (dir_ / "pdflatex").write_text("#!/bin/sh\nexit 0\n")
    (dir_ / "kpsewhich").write_text(
        "#!/bin/sh\nfor a in \"$@\"; do case \"$a\" in " + " | ".join(lacks or ["__none__"])
        + ") ;; *) echo /tex/$a ;; esac; done\n")
    for f in ("pdflatex", "kpsewhich"):
        (dir_ / f).chmod(0o755)
    return str(dir_ / "pdflatex")


def test_find_pdflatex_falls_back_when_packages_missing(tmp_path, monkeypatch):
    system = _fake_tex(tmp_path / "system", lacks=["adjustbox.sty"])
    full = _fake_tex(tmp_path / "cvmfs")
    monkeypatch.delenv("RATE_TABLE_TEX_PDFLATEX", raising=False)
    monkeypatch.setattr(lt.shutil, "which", lambda name: system)
    monkeypatch.setattr(lt, "TEXLIVE_FALLBACK_DIRS", [str(tmp_path / "cvmfs")])
    assert lt._missing_packages(system) == ["adjustbox.sty"]
    assert lt.find_pdflatex() == full
    # a complete TeX on PATH is preferred
    monkeypatch.setattr(lt.shutil, "which", lambda name: full)
    assert lt.find_pdflatex() == full
    # explicit choice wins
    monkeypatch.setenv("RATE_TABLE_TEX_PDFLATEX", "/my/pdflatex")
    assert lt.find_pdflatex() == "/my/pdflatex"

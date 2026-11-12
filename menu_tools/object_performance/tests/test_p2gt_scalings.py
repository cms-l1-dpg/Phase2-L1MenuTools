import yaml

from menu_tools.object_performance import p2gt_scalings as ps


def write(d, name, slope, offset):
    with open(d / name, "w") as f:
        yaml.dump({"slope": slope, "offset": offset}, f)


def test_read_scalings_renames_rounds_and_skips(tmp_path):
    write(tmp_path, "L1nnPuppiTau:default:barrel.yaml", 1.2749, 2.2051)
    write(tmp_path, "L1EG:extended:endcap.yaml", 1.22, 2.28)
    write(tmp_path, "ElectronsTrigger_L1tkElectron:Iso:barrel.yaml", 9.9, 9.9)
    scalings, skipped = ps.read_scalings(str(tmp_path))
    assert scalings == {
        "CL2Taus": {"default": {"barrel": {"offset": 2.21, "slope": 1.27}}},
        "L1EG": {"extended": {"endcap": {"offset": 2.28, "slope": 1.22}}},
    }
    assert skipped == ["ElectronsTrigger_L1tkElectron:Iso:barrel.yaml"]


def test_render_round_trip(tmp_path):
    scalings = {"CL2Taus": {"default": {"barrel": {"offset": 2.21, "slope": 1.27}}}}
    path = tmp_path / "s.py"
    path.write_text(ps.render(scalings, ps.HEADER.format(provenance="X")))
    assert ps.load_scalings_file(str(path)) == scalings
    assert path.read_text().startswith("### L1T Object threshold scalings \n")


def test_release_and_provenance():
    assert ps.release_from_version("V50nano_170pre6") == "CMSSW_17_0_0_pre6"
    assert ps.release_from_version("V50nano_170X1006") is None
    assert ps.provenance(
        "V50nano_170pre6", "Annual Review 2026", "CMSSW_17_0_0_pre6"
    ) == (
        "V50 derived with the Annual Review 2026 config "
        "in the 17_0_x release (CMSSW_17_0_0_pre6)"
    )


def test_menu_key_check(tmp_path):
    (tmp_path / "seeds_cff.py").write_text(
        'a = get_object_thrs(58, "CL2Taus", "extended")\n'
        'b = get_object_thrs(450, "CL2HtSum", "HT")\n'
        'c = get_object_thrs(200, "CL2EtSum")\n'
    )
    used = ps.keys_used_by_menu(str(tmp_path))
    assert used == {
        ("CL2Taus", "extended"),
        ("CL2HtSum", "HT"),
        ("CL2EtSum", "default"),
    }
    scalings = {
        "CL2Taus": {"default": {}},
        "CL2HtSum": {"HT": {}},
        "CL2EtSum": {"default": {}},
    }
    assert ps.missing_keys(scalings, used) == ["CL2Taus:extended"]

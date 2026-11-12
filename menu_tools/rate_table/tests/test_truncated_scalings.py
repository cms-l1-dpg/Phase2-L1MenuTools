import yaml

from menu_tools.rate_table.menu_config import MenuConfig
from menu_tools.utils import scalings

CFG = {"version": "V50", "table_fname": "menu", "menu_config": "x", "sample": "MinBias"}


class FakeObject:
    version = "V50"

    def get_scaling_object(self, eta_range):
        return f"L1nnPuppiTau:default:{eta_range}"


def test_load_scaling_params_rounds_like_p2gt(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "outputs/V50/object_performance/scalings"
    d.mkdir(parents=True)
    with open(d / "L1nnPuppiTau:default:barrel.yaml", "w") as f:
        yaml.dump({"slope": 1.2749, "offset": 2.2051}, f)
    obj = FakeObject()
    assert scalings.load_scaling_params(obj, "barrel") == (1.2749, 2.2051)
    assert scalings.load_scaling_params(obj, "barrel", decimals=2) == (1.27, 2.21)


def test_truncated_suffix_and_decimals():
    nominal = MenuConfig(CFG)
    assert nominal.scalings_decimals is None and nominal.scalings_suffix == ""
    trunc = MenuConfig(CFG, override_scalings_version="V49", truncated=True)
    assert trunc.scalings_decimals == 2
    assert trunc.scalings_suffix == "_scalings_V49_truncated"

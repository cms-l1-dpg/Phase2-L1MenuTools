from pathlib import Path

from menu_tools.utils.prepare_rate_scalings import restore_scalings


def test_restore_scalings_uses_last_job_on_collision(tmp_path: Path):
    (tmp_path / "photons_L1EG:default:barrel.yaml").write_text("sample: photon\n")
    (tmp_path / "electrons_L1EG:default:barrel.yaml").write_text("sample: electron\n")

    restore_scalings(tmp_path, ["photons", "electrons"])

    assert (tmp_path / "L1EG:default:barrel.yaml").read_text() == "sample: electron\n"

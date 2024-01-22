from typing import Any


class PlotConfig:
    def __init__(self, cfg: dict[str, Any]) -> None:
        self._cfg = cfg

    @property
    def sample(self):
        return self._cfg["sample"]

    @property
    def version(self) -> str:
        return self._cfg["version"]

    @property
    def iso_vs_eff_plot(self):
        try:
            return self._cfg["iso_vs_efficiency"]
        except KeyError:
            return False

    @property
    def reference_object(self):
        return self._cfg["reference_object"]["object"]

    @property
    def reference_event_cuts(self):
        try:
            return self._cfg["reference_object"]["cuts"]["event"]
        except KeyError:
            return []

    @property
    def reference_object_cuts(self):
        try:
            return self._cfg["reference_object"]["cuts"]["object"]
        except KeyError:
            return []

    @property
    def reference_trafo(self):
        try:
            return self._cfg["reference_object"]["trafo"]
        except KeyError:
            return None

    @property
    def test_objects(self) -> dict[str, Any]:
        test_obj = {
            x: {"base_obj": x.split("-")[0], "id": x.split("-")[1], "x_arg": x_arg}
            for x, x_arg in self._cfg["test_objects"].items()
        }
        return test_obj

    @property
    def matching(self):
        try:
            return self._cfg["match_test_to_ref"]
        except KeyError:
            return False

    @property
    def reference_field(self):
        field = self._cfg["reference_object"]["x_arg"]
        return field.lower()

    @property
    def bin_width(self):
        return self._cfg["binning"]["step"]

    @property
    def bin_min(self):
        return self._cfg["binning"]["min"]

    @property
    def bin_max(self):
        return self._cfg["binning"]["max"]

    @property
    def scaling_pct(self):
        return self._cfg["scalings"]["threshold"]

    @property
    def scaling_method(self):
        return self._cfg["scalings"]["method"]

from typing import Any, Optional

from menu_tools.utils.config import BasePlotConfig


class PerformancePlotConfig(BasePlotConfig):
    def __init__(self, cfg: dict[str, Any], name: Optional[str] = None) -> None:
        super().__init__(cfg, name)

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
    def reference_trafo(self) -> Optional[str]:
        try:
            return self._cfg["reference_object"]["trafo"]
        except KeyError:
            return None

    @property
    def reference_label(self) -> str:
        try:
            return self._cfg["reference_object"]["label"]
        except KeyError:
            raise KeyError("No label defined for reference object in {self.plot_name}!")

    @property
    def test_objects(self) -> dict[str, Any]:
        # Parse to detect faulty config
        if not all([":" in x for x in self._cfg["test_objects"]]):
            raise ValueError(f"Misconfigured obj:id key in {self.plot_name}!")

        test_obj = {
            x: {"base_obj": x.split(":")[0], "id": x.split(":")[1], "x_arg": x_arg}
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
    def scaling_pct(self):
        return self._cfg["scalings"]["threshold"]

    @property
    def scaling_method(self):
        return self._cfg["scalings"]["method"]

    @property
    def xlabel(self):
        return self._cfg["xlabel"]

    @property
    def ylabel(self):
        return self._cfg["ylabel"]

from typing import Any, Optional

from menu_tools.utils.config import BasePlotConfig
from menu_tools.utils.objects import Object, ReferenceObject


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
    def reference_object(self) -> ReferenceObject:
        assert isinstance(
            self._cfg["reference_object"], dict
        ), f"Reference object is not a dict in {self.plot_name}!"
        object_id_strs = list(self._cfg["reference_object"].keys())
        assert (
            len(object_id_strs) == 1
        ), f"Multiple reference objects defined in {self.plot_name}!"
        return ReferenceObject(
            list(self._cfg["reference_object"].keys())[0], self.version
        )

    @property
    def test_objects(self) -> dict[str, Any]:
        # Parse to detect faulty config
        if not all([":" in x for x in self._cfg["test_objects"]]):
            raise ValueError(f"Misconfigured obj:id key in {self.plot_name}!")

        return self._cfg["test_objects"]

    @property
    def matching(self):
        try:
            return self._cfg["match_test_to_ref"]
        except KeyError:
            return False

    @property
    def reference_field(self):
        field = self._cfg["reference_object"][self.reference_object.object_key]
        return field.lower()

    @property
    def compute_scalings(self) -> bool:
        return "scalings" in self._cfg.keys()

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

    @property
    def test_object_instances(self) -> list:
        test_objects = []
        for obj_key in self._cfg["test_objects"]:
            test_objects.append(Object(obj_key, self.version))
        return test_objects

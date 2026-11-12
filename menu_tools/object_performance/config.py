from typing import Any, Optional

from menu_tools.object_performance.reference_cleaning import parse_reference_cleaning
from menu_tools.utils.config import BasePlotConfig
from menu_tools.utils.objects import Object


class PerformancePlotConfig(BasePlotConfig):
    def __init__(
        self,
        cfg: dict[str, Any],
        name: Optional[str] = None,
        config_version: Optional[str] = None,
        override_version: Optional[str] = None,
    ) -> None:
        super().__init__(cfg, name)
        self._config_version = config_version
        self._override_version = override_version

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
    def reference_cleaning(self) -> list[dict[str, Any]]:
        """Normalised `reference_cleaning` blocks (see reference_cleaning.py), or []."""
        return parse_reference_cleaning(
            self._cfg.get("reference_cleaning"), self.plot_name
        )

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

        return self._cfg["test_objects"]

        # DEPRECATED
        # test_obj = {
        #     x: {"base_obj": x.split(":")[0], "id": x.split(":")[1], "x_arg": x_arg}
        #     for x, x_arg in self._cfg["test_objects"].items()
        # }

        # return test_obj

    @property
    def matching(self):
        try:
            return self._cfg["match_test_to_ref"]
        except KeyError:
            return False

    @property
    def matching_and_threshold(self) -> bool:
        """Compute combined matching + threshold (trigger) efficiencies.

        If set, the denominator of the efficiency contains *all* reference
        objects (not only the ones matched to a test object), while the
        numerator contains the reference objects matched to a test object
        passing the threshold. Only effective for `match_test_to_ref: True`.
        """
        try:
            return bool(self._cfg["matching_and_threshold"])
        except KeyError:
            return False

    @property
    def threshold_field(self) -> Optional[str]:
        """Test-object field the threshold is applied to, if it differs from
        the plotted x_arg (e.g. `threshold_field: "pt"` with x_arg "eta" for a
        trigger efficiency vs eta). Default: None, i.e. the test x_arg."""
        field = self._cfg.get("threshold_field")
        return field.lower() if field else None

    @property
    def l1_seed(self) -> Optional[dict[str, Any]]:
        """Optional L1 seed requirement for HLT test objects.

        For the combined L1 x HLT efficiency.

        Normalised form of the `l1_seed` block (see docs/object-performance.md):
            {"objects": [{"object": str, "threshold": float | {region: float},
                          "match_dR": float | None}, ...],   # OR of these L1 conditions
             "apply_to": list[str] | None,     # None: all hlt* test objects
             "label": str | None}
        The single-object shorthand (`object` / `threshold` / `match_dR` at the top
        level of the block) is converted to a one-element `objects` list. None if no
        `l1_seed` is set.
        """
        block = self._cfg.get("l1_seed")
        if not block:
            return None
        if "objects" in block:
            if any(k in block for k in ("object", "threshold", "match_dR")):
                raise ValueError(
                    f"l1_seed of {self.plot_name}: give either `objects` or "
                    "`object`/`threshold`"
                )
            objects = block["objects"]
        else:
            objects = [
                {k: block[k] for k in ("object", "threshold", "match_dR") if k in block}
            ]
        norm = []
        for o in objects:
            if "object" not in o or "threshold" not in o:
                raise ValueError(
                    f"l1_seed of {self.plot_name}: each seed object needs `object` and "
                    "`threshold`"
                )
            if o["object"].count(":") < 1:
                raise ValueError(
                    f"l1_seed of {self.plot_name}: misconfigured obj:id key "
                    f"{o['object']}"
                )
            norm.append(
                {
                    "object": o["object"],
                    "threshold": o["threshold"],
                    "match_dR": o.get("match_dR"),
                }
            )
        apply_to = block.get("apply_to")
        if isinstance(apply_to, str):
            apply_to = [apply_to]
        return {"objects": norm, "apply_to": apply_to, "label": block.get("label")}

    @property
    def reference_field(self):
        field = self._cfg["reference_object"]["x_arg"]
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
    def version(self) -> str:
        if self._override_version:
            return self._override_version
        return super().version

    @property
    def version_for_objects(self) -> str:
        if self._override_version and self._config_version:
            return self._config_version
        return self.version

    @property
    def test_object_instances(self) -> list:
        test_objects = []

        for obj_key in self._cfg["test_objects"]:
            test_objects.append(Object(obj_key, self.version_for_objects))
        return test_objects

    @property
    def scaling_object_instances(self) -> list:
        """Test objects for which scalings are computed and written.

        All test objects, or only those listed in `scalings: objects:` (e.g. to keep
        a comparison curve out of the scaling files of a plot with a different
        reference definition).
        """
        selected = self._cfg.get("scalings", {}).get("objects")
        if selected is None:
            return self.test_object_instances
        unknown = set(selected) - set(self._cfg["test_objects"])
        if unknown:
            raise ValueError(
                f"{self.plot_name}: scalings objects {sorted(unknown)} "
                "are not test objects"
            )
        # match on the config keys: str(obj) adds e.g. ":inclusive" to "Sums:HT"
        return [
            obj
            for key, obj in zip(self._cfg["test_objects"], self.test_object_instances)
            if key in selected
        ]

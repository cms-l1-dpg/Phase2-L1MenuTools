class PlotConfig:
    def __init__(self, cfg: dict):
        self._cfg = cfg

    @property
    def sample(self):
        return self._cfg["sample"]

    @property
    def version_ref_object(self):
        try:
            return self._cfg["reference_object"]["version"]
        except KeyError:
            return self._cfg["default_version"]
        except TypeError:
            return None

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
    def test_objects(self):
        return self._cfg["test_objects"]

    def get_match_dR(self, test_obj):
        try:
            return self._cfg["test_objects"][test_obj]["match_dR"]
        except KeyError:
            return self._cfg["match_dR"]

    @property
    def matching_configured(self):
        if "match_dR" in self._cfg.keys():
            return True
        for test_obj in self._cfg["test_objects"].values():
            test_keys = test_obj.keys()
            if "match_dR" not in test_keys:
                return False
        return True

    @property
    def reference_object_field(self):
        ref_obj = self._cfg["reference_object"]["object"]
        field = self._cfg["reference_object"]["suffix"]
        return ref_obj + field

    @property
    def reference_field(self):
        field = self._cfg["reference_object"]["suffix"]
        return field.lower()

    @property
    def reference_iso_threshold(self):
        try:
            return self._cfg["reference_object"]["iso_threshold"]
        except KeyError:
            return None

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

    def get_object_cuts(self, obj):
        obj_cfg = self._cfg["test_objects"][obj]
        try:
            return obj_cfg["cuts"]
        except KeyError:
            return None

    def get_test_object_version(self, obj):
        obj_cfg = self._cfg["test_objects"][obj]

        try:
            return obj_cfg["version"]
        except KeyError:
            return self._cfg["default_version"]

    def get_quality_id(self, obj):
        try:
            return self._cfg["test_objects"][obj]["quality_id"]
        except KeyError:
            return None

    def get_base_obj(self, obj):
        try:
            return self._cfg["test_objects"][obj]["base_obj"]
        except KeyError:
            return obj

    def get_iso_BB(self, obj):
        try:
            return self._cfg["test_objects"][obj]["iso_BB"]
        except KeyError:
            return -1

    def get_iso_EE(self, obj):
        try:
            return self._cfg["test_objects"][obj]["iso_EE"]
        except KeyError:
            return -1

    def get_l1_iso(self, obj):
        try:
            return self._cfg["test_objects"][obj]["iso_branch"]
        except KeyError:
            return None

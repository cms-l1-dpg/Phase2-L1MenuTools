

class PlotConfig():
 
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

    @property
    def reference_object(self):
        return self._cfg["reference_object"]["object"]

    @property
    def reference_cuts(self):
        try: 
            return self._cfg["reference_object"]["cuts"]
        except KeyError:
            return None

    @property
    def reference_trafo(self):
        try: 
            return self._cfg["reference_object"]["trafo"]
        except KeyError:
            return None

    @property
    def test_objects(self):
        return self._cfg["test_objects"]

    @property
    def match_dR(self):
        return self._cfg["match_dR"]

    @property
    def reference_object_field(self):
        ref_obj = self._cfg["reference_object"]["object"]
        field = self._cfg["reference_object"]["suffix"]
        return ref_obj + field

    @property
    def reference_field(self):
        field = self._cfg["reference_object"]["suffix"]
        return field.lower()

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


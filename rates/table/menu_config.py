class MenuConfig:

    def __init__(self, cfg: dict):
        self._cfg = cfg

    @property
    def sample(self):
        return self._cfg["sample"]

    @property
    def scalings(self):
        return self._cfg["scalings"]

    @property
    def menu_cfg(self):
        return self._cfg["menu_config"]

    @property
    def menu_objects(self):
        return self._cfg["menu_objects"]

    @property
    def version(self):
        return self._cfg["version"]

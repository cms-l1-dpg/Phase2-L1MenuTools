class MenuConfig:

    def __init__(self, cfg: dict):
        self._cfg = cfg

    @property
    def sample(self):
        return self._cfg["sample"]

    @property
    def scalings_path(self):
        return self._cfg["scalings"]["scalings_path"]

    @property
    def do_scalings(self):
        return self._cfg["scalings"]["collect_scalings"]

    @property
    def scalings_file(self):
        return self._cfg["scalings"]["scalings_file"]

    @property
    def scalings_outdir(self):
        return self._cfg["scalings"]["scalings_outdir"]

    @property
    def menu_cfg(self):
        return self._cfg["menu_config"]

    @property
    def menu_objects(self):
        return self._cfg["menu_objects"]

    @property
    def version(self):
        return self._cfg["version"]

    @property
    def table_outdir(self):
        return self._cfg["table"]["table_outdir"]

    @property
    def table_fname(self):
        return self._cfg["table"]["table_fname"]
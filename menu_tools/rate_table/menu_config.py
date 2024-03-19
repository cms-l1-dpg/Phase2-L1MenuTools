class MenuConfig:
    def __init__(self, config: dict) -> None:
        self._config = config

    @property
    def sample(self) -> str:
        return self._config["sample"]

    @property
    def menu_config(self):
        return self._config["menu_config"]

    @property
    def menu_objects(self):
        return self._config["menu_objects"]

    @property
    def version(self):
        return self._config["version"]

    @property
    def table_outdir(self):
        return "outputs/V29/rate_tables"

    @property
    def table_fname(self):
        return self._config["table"]["table_fname"]

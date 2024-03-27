import os


class MenuConfig:
    def __init__(self, config: dict) -> None:
        self._config = config

    @property
    def sample(self) -> str:
        return self._config["sample"]

    @property
    def menu_config(self) -> str:
        return self._config["menu_config"]

    @property
    def version(self) -> str:
        return self._config["version"]

    @property
    def table_outdir(self) -> str:
        return os.path.join("outputs", self.version, "rate_tables")

    @property
    def table_fname(self) -> str:
        try:
            return self._config["table_fname"]
        except KeyError:
            return f"{self.version}_rate_table"

import os
from typing import Optional


class MenuConfig:
    def __init__(self, config: dict, config_version: Optional[str] = None, override_version: Optional[str] = None) -> None:
        self._config = config
        self._config_version = config_version
        self._override_version = override_version

    @property
    def sample(self) -> str:
        return self._config["sample"]

    @property
    def menu_config(self) -> str:
        return self._config["menu_config"]

    @property
    def version(self) -> str:
        if self._override_version:
            return self._override_version
        return self._config["version"]

    @property
    def config_version_for_objects(self) -> str:
        if self._override_version and self._config_version:
            return self._config_version
        return self.version

    @property
    def table_outdir(self) -> str:
        return os.path.join("outputs", self.version, "rate_tables")

    @property
    def table_fname(self) -> str:
        try:
            return self._config["table_fname"]
        except KeyError:
            return f"{self.version}_rate_table"

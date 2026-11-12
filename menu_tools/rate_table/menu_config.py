import os
from typing import Optional

from menu_tools.utils.constants import P2GT_DECIMALS


def scalings_suffix(scalings_version: Optional[str], truncated: bool) -> str:
    """Filename tag of tables made with `--scalings` and/or `--truncated`."""
    suffix = f"_scalings_{scalings_version}" if scalings_version else ""
    return suffix + ("_truncated" if truncated else "")


class MenuConfig:
    def __init__(
        self,
        config: dict,
        config_version: Optional[str] = None,
        override_version: Optional[str] = None,
        override_scalings_version: Optional[str] = None,
        override_sample: Optional[str] = None,
        truncated: bool = False,
    ) -> None:
        self._config = config
        self._config_version = config_version
        self._override_version = override_version
        self._override_scalings_version = override_scalings_version
        self._override_sample = override_sample
        self._truncated = truncated

    @property
    def sample(self) -> str:
        if self._override_sample:
            return self._override_sample
        return self._config["sample"]

    @property
    def is_signal(self) -> bool:
        """True when the sample has been overridden with `--signal`.

        In that case the table holds per-seed signal efficiencies and the
        rate column is dropped, since the rate normalisation only applies
        to the minimum bias sample.
        """
        return bool(self._override_sample)

    @property
    def sample_suffix(self) -> str:
        """Tag appended to output filenames when `--signal` is used, so that
        efficiency tables do not overwrite the nominal rate table."""
        if self._override_sample:
            return f"_{self._override_sample}"
        return ""

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
    def scalings_version(self) -> str:
        """Version the online-to-offline scalings are loaded from.

        Defaults to `version` (i.e. follows `--version` if that is given),
        but `--scalings` takes precedence over `--version`.
        """
        if self._override_scalings_version:
            return self._override_scalings_version
        return self.version

    @property
    def scalings_decimals(self) -> Optional[int]:
        """Decimals the scalings are rounded to with `--truncated` (those of the
        P2GT menus), None otherwise."""
        return P2GT_DECIMALS if self._truncated else None

    @property
    def scalings_suffix(self) -> str:
        """Tag appended to output filenames when `--scalings` or `--truncated` is
        used, so that such tables do not overwrite the nominal ones."""
        return scalings_suffix(self._override_scalings_version, self._truncated)

    @property
    def table_outdir(self) -> str:
        return os.path.join("outputs", self.version, "rate_tables")

    @property
    def table_fname(self) -> str:
        try:
            return self._config["table_fname"]
        except KeyError:
            return f"{self.version}_rate_table"

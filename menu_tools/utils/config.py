from typing import Any, Optional


class BasePlotConfig:
    """Base class for yaml/dict style plot config

    Includes abstractions for test_objects and creation of Object instances.
    """

    def __init__(self, cfg: dict[str, Any], name: Optional[str] = None) -> None:
        self._cfg = cfg
        self._name = name

    @property
    def plot_name(self) -> Optional[str]:
        return self._name

    @property
    def config_dict(self) -> dict[str, Any]:
        return self._cfg

    @property
    def sample(self):
        try:
            return self._cfg["sample"]
        except KeyError:
            raise KeyError(f"No sample configured for {self.plot_name}!")

    @property
    def version(self) -> str:
        try:
            return self._cfg["version"]
        except KeyError:
            raise KeyError(f"No version configured for {self.plot_name}!")

    @property
    def nObjects(self) -> int:
        if "nObjects" in self._cfg:
            return int(self._cfg["nObjects"])
        else:
            return 1

    @property
    def bin_width(self) -> float:
        return float(self._cfg["binning"]["step"])

    @property
    def bin_min(self) -> float:
        return float(self._cfg["binning"]["min"])

    @property
    def bin_max(self) -> float:
        return float(self._cfg["binning"]["max"])

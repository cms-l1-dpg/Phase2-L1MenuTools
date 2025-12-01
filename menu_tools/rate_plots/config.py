from menu_tools.utils.config import BasePlotConfig
from menu_tools.utils.objects import Object
from typing import Optional


class RatePlotConfig(BasePlotConfig):
    def __init__(self, cfg: dict, name: str, config_version: Optional[str] = None, override_version: Optional[str] = None):
        super().__init__(cfg, name)
        self._config_version = config_version
        self._override_version = override_version

    @property
    def compare_versions(self) -> bool:
        """
        Returns a boolean specifying if a plot comparing two versions
        is to be produced. If a list of two versions is given this is true.
        """
        return len(self.versions) == 2

    @property
    def version(self) -> str:
        if self._override_version:
            return self._override_version
        return super().version

    @property
    def versions(self) -> list[str]:
        if self._override_version:
            return [self._override_version]
            
        if "version" in self._cfg.keys():
            version = self._cfg["version"]
            if isinstance(version, str):
                return [version]
        try:
            versions = self._cfg["versions"]
        except KeyError:
            raise ValueError(
                "`version(s)` must be specified as either a single"
                "version (e.g. `V30`) or a list of exactly two versions"
                "(e.g. [`V29`, `V30`])."
            )
        if isinstance(versions, str):
            return [versions]
        if isinstance(versions, list):
            assert (
                len(versions) == 2
            ), "To compare versions, exactly two must be specified."
            return versions
        raise RuntimeError("Somthing is wrong with the version config!")

    @property
    def test_objects(self) -> list:
        return self._cfg["test_objects"]

    @property
    def test_object_instances(self) -> dict[str, dict[str, Object]]:
        test_objects: dict[str, dict[str, Object]] = {}
        for obj_key in self._cfg["test_objects"]:
            test_objects[obj_key] = {}
            for version in self.versions:
                # Use config_version for object definition if override is active
                # Otherwise use the version from the config
                obj_version = version
                if self._override_version and self._config_version:
                    obj_version = self._config_version
                    
                test_objects[obj_key][version] = Object(obj_key, obj_version)
        return test_objects

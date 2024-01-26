from menu_tools.utils.config import BasePlotConfig
from menu_tools.utils.objects import Object


class RatePlotConfig(BasePlotConfig):
    def __init__(self, cfg: dict, name: str):
        super().__init__(cfg, name)

    @property
    def compare_versions(self) -> bool:
        """
        Returns a boolean specifying if a plot comparing two versions
        is to be produced. If a list of two versions is given this is true.
        """

        return len(self.versions) == 2

    @property
    def versions(self) -> list[str]:
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

    @property
    def test_objects(self) -> list:
        return self._cfg["test_objects"]

    @property
    def test_object_instances(self) -> dict[str, dict[str, Object]]:
        test_objects: dict[str, dict[str, Object]] = {}
        for obj in self._cfg["test_objects"]:
            nano_obj_name = obj.split(":")[0]
            obj_id_name = obj.split(":")[1]
            test_objects[obj] = {}
            for version in self.versions:
                test_objects[obj][version] = Object(nano_obj_name, obj_id_name, version)
        return test_objects

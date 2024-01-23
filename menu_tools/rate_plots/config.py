from menu_tools.utils.objects import Object


class RatePlotConfig:
    def __init__(self, name: str, cfg: dict):
        self._name = name
        self._cfg = cfg

    @property
    def plot_name(self) -> str:
        return self._name

    @property
    def sample(self) -> str:
        return self._cfg["sample"]

    @property
    def bin_width(self):
        return self._cfg["binning"]["step"]

    @property
    def xmin(self):
        return self._cfg["binning"]["min"]

    @property
    def xmax(self):
        return self._cfg["binning"]["max"]

    @property
    def compare_versions(self) -> bool:
        """
        Returns a boolean specifying if a plot comparing two versions
        is to be produced. If a list of two versions is given this is true.
        """

        return len(self.versions) == 2

    @property
    def versions(self):
        try:
            versions = self._cfg["versions"]
        except KeyError:
            raise ValueError(
                "`versions` must be specified as either a single"
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
    def version(self) -> str:
        """
        Returns the version if only one version is configured.
        This property should only be used when a single version
        is specified and not a list of two versions for a comparison
        plot.
        """
        version = self._cfg["versions"]
        assert isinstance(version, str)
        return version

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
        print(test_objects)
        return test_objects

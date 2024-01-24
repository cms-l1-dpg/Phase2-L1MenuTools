from menu_tools.utils.config import BasePlotConfig


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
    def test_objects(self) -> list:
        return self._cfg["test_objects"]

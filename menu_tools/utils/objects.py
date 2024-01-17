import glob
import yaml


class Object:
    """This class represents a physics object.

    The objects are configurable under `configs/<version>/objects`.

    Attributes:
        eta_ranges: ranges with different cuts/quality criteria
        cuts: the cuts to be applied in the different eta ranges
        version: version of the menu
    """

    def __init__(self, nano_obj_name: str, obj_id_name: str, version: str) -> None:
        """Initializes an Object loading the parameters from the
           corresponding config file.

        Args:
            nano_obj_name: name of the physics object in the l1 ntuples
            obj_id_name: name of the l1 object id as defined in `configs`
            version: version of the menu
        """
        self.nano_obj_name = nano_obj_name
        self.obj_id_name = obj_id_name
        self.version = version
        self.obj_name = f"{nano_obj_name}_{obj_id_name}"

    @property
    def _nano_obj(self) -> dict[str, dict]:
        """
        Loads all object configuration files from self.version,
        merges them and returns the configuration of self.nano_obj_name.

        Returns:
            nano_obj_configs: dictionary containing the object parameters and ids
        """
        nano_obj_configs = {}
        config_path = f"configs/{self.version}/objects/e*.y*ml"
        config_files = glob.glob(config_path)

        for config in config_files:
            with open(config, "r") as f:
                _conf_dict = yaml.safe_load(f)
            nano_obj_configs = nano_obj_configs | _conf_dict

        return nano_obj_configs[self.nano_obj_name]

    def _get_object_default_params(self) -> dict:
        """Get default paramters of the object.

        Returns:
            default_object_params: dict contianing all parameters of the nano
            object except ids.
        """
        default_object_params = {x: y for x, y in self._nano_obj.items() if x != "ids"}
        return default_object_params

    def _get_object_id_params(self) -> dict:
        """Get the specific parameters specified in the object id.

        Returns:
            id_params: parameters specifically definied for the object id.
        """
        id_params = self._nano_obj["ids"][self.obj_id_name]
        return id_params

    @property
    def _object_params(self) -> dict:
        """
        Returns:
            object_parameters: Parameters of the objects as a dict where
            defaults are overwritten if id specific params are configured.
        """
        defaults = self._get_object_default_params()
        id_specific = self._get_object_id_params()
        object_parameters = defaults | id_specific
        return object_parameters

    @property
    def match_dR(self) -> float:
        return self._object_params["match_dR"]

    @property
    def plot_label(self) -> str:
        return self._object_params["label"]

    @property
    def eta_ranges(self) -> dict[str, tuple]:
        return self._object_params["eta_ranges"]

    @property
    def cuts(self) -> dict[str, list[str]]:
        return self._object_params["cuts"]


if __name__ == "__main__":
    x = Object("tkElectron", "Iso", "V29")
    print(x.match_dR)
    print(x.plot_label)
    print(x.eta_ranges)
    print(x.cuts)

import glob
import re
from typing import Optional
import yaml

import awkward as ak


class Object:
    """This class represents a physics object.

    The objects are configurable under `configs/<version>/objects`.

    Attributes:
        eta_ranges: ranges with different cuts/quality criteria
        cuts: the cuts to be applied in the different eta ranges
        version: version of the menu
    """

    def __init__(
        self,
        object_key: str,
        version: str,
    ) -> None:
        """Initializes an Object loading the parameters from the
           corresponding config file.

        Args:
            object_key: object/id specifier of the form l1_object:id[:eta_range]
            version: version of the menu
        """
        self.object_key = object_key
        self.version = version
        self._nano_obj  # fail early if no config can be found

    def __str__(self) -> str:
        return f"{self.nano_obj_name}:{self.obj_id_name}:{self.eta_range}"

    @property
    def nano_obj_name(self) -> str:
        return self.object_key.split(":")[0]

    @property
    def obj_id_name(self) -> str:
        return self.object_key.split(":")[1]

    @property
    def eta_range(self) -> str:
        """If an eta range other than "inclusive" is specified, a cut to that
        range is added to `cuts`.

        Returns:
            eta_range_key: `barrel`/`endcap`/`overlap`/`forward`/`inclusive`
        """
        try:
            eta_range_key = self.object_key.split(":")[2]
        except IndexError:
            eta_range_key = "inclusive"
        assert (
            eta_range_key in self.eta_ranges.keys()
        ), "`eta` range specifier not found in object definition!"
        return eta_range_key

    @property
    def _nano_obj(self) -> dict[str, dict]:
        """
        Loads all object configuration files from self.version,
        merges them and returns the configuration of self.nano_obj_name.

        Returns:
            nano_obj_configs: dictionary containing the object parameters and ids
            or None if no configuration is found.
        """
        nano_obj_configs: dict[str, dict] = {}
        config_path = f"configs/{self.version}/objects/*.y*ml"
        config_files = glob.glob(config_path)

        for config in config_files:
            with open(config, "r") as f:
                _conf_dict = yaml.safe_load(f)
            nano_obj_configs = nano_obj_configs | _conf_dict

        try:
            return nano_obj_configs[self.nano_obj_name]
        except KeyError:
            raise FileNotFoundError(
                f"No config file found for {self.nano_obj_name}:{self.obj_id_name}!"
            )

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
        _eta_ranges = self._object_params["eta_ranges"]
        if "inclusive" not in _eta_ranges:
            _eta_ranges["inclusive"] = [0, 7]
        return _eta_ranges

    @property
    def cuts(self) -> Optional[dict[str, list[str]]]:
        _cuts = {}
        if "cuts" in self._object_params.keys():
            _cuts = self._object_params["cuts"]
        if self.eta_range != "inclusive":
            # if a region other than inclusive is specified an eta cut
            eta_min = self.eta_ranges[self.eta_range][0]
            eta_max = self.eta_ranges[self.eta_range][1]
            global_eta_cut = f"abs({{eta}}) > {eta_min} & abs({{eta}}) < {eta_max}"
            try:
                _cuts["inclusive"].append(global_eta_cut)
            except KeyError:
                _cuts["inclusive"] = [global_eta_cut]
        if not _cuts:
            print(f"No cuts will be applied for {self}!")
        return _cuts


def compute_selection_mask_for_object_cuts(obj: Object, ak_array: ak.Array) -> ak.Array:
    """Compute selection mask for object cuts on array

    obj: Object that specifies the cuts to be applied
    ak_array: array on which the selection is evaluated

    Returns:
        sel: boolean selection mask for entries passing all cuts form obj
    """
    # Initialize mask with True everywhere
    sel = abs(ak_array["phi"]) > 0

    # If no cut are specified in object return true everywhere
    if not obj.cuts:
        return sel

    for range_i, range_cuts in obj.cuts.items():
        # Initialize temporary mask (for rangei) with True everywhere
        _sel = abs(ak_array["phi"]) > 0
        for cut in range_cuts:
            cut = re.sub(r"{([^&|]*)}", r"ak_array['\1']", cut)
            eta_sel = (abs(ak_array["eta"]) > obj.eta_ranges[range_i][0]) & (
                abs(ak_array["eta"]) < obj.eta_ranges[range_i][1]
            )
            _sel = _sel & (eval(cut) + ~eta_sel)
        # apply OR logic
        sel = sel & _sel
    return sel


if __name__ == "__main__":
    x = Object("tkElectron:Iso", "V29")
    x = Object("caloJet:default", "V29")
    print(x)
    print(x.match_dR)
    print(x.plot_label)
    print(x.eta_ranges)
    print(x.cuts)

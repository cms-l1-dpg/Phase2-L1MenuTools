import glob
import re
from typing import Optional
import yaml

import awkward as ak


class BaseObject:
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
        if eta_range_key not in self.eta_ranges.keys():
            raise ValueError(
                f"`eta` range specifier `{eta_range_key}` not "
                f"found in object definition of {self.nano_obj_name}!"
            )
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
    def plot_label(self) -> str:
        """Label of the object in the plots"""
        return self._object_params["label"]

    def get_scaling_object(self, eta_range: str) -> str:
        """
        This enables the definition of an object/id which uses
        the scalings from a different object.
        """
        if "use_scalings_from_object" in self._object_params:
            return self._object_params["use_scalings_from_object"]
        return str(self).replace("inclusive", eta_range)

    @property
    def eta_ranges(self) -> dict[str, tuple[float, float]]:
        _eta_ranges = {}
        if "eta_ranges" in self._object_params.keys():
            _eta_ranges = self._object_params["eta_ranges"]
        if "inclusive" not in _eta_ranges:
            _eta_ranges["inclusive"] = [0, 7]
        return _eta_ranges

    @property
    def cuts(self) -> dict[str, list[str]]:
        """Necessary interface for Object classes.
        To be implemented in derived class.

        Returns:
            cut_dict: Dicitionary of the type
                ```
                {"eta_range_1: [
                    "<cut string 1.1>",
                    "<cut string 1.2>",
                    ...
                 ],
                 "eta_range_2: [
                     "<cut string 2.1>",
                     ...
                  ],
                 ...
                }
                ```
                where `<cut string>` are the requirements
                as specified in the object config files.
        """
        raise NotImplementedError(
            "This method should be implemented in the derived class."
        )


class Object(BaseObject):
    """This class represents a physics test object.
    It inherits from BaseObject which it shares with the implementation of
    ReferenceObject.

    The objects are configurable under `configs/<version>/objects`.

    Attributes:
        eta_ranges: ranges with different cuts/quality criteria
        cuts: the cuts to be applied in the different eta ranges
        version: version of the menu
    """

    def __init__(self, object_key: str, version: str) -> None:
        super().__init__(object_key, version)

    @property
    def cuts(self) -> dict[str, list[str]]:
        _cuts = {}
        if "cuts" in self._object_params.keys():
            _cuts = self._object_params["cuts"]
        if self.eta_range != "inclusive":
            # if a region other than inclusive is specified, add an eta cut
            eta_min = self.eta_ranges[self.eta_range][0]
            eta_max = self.eta_ranges[self.eta_range][1]
            global_eta_cut = (
                f"((abs({{eta}}) > {eta_min}) & (abs({{eta}}) < {eta_max}))"
            )
            try:
                _cuts["inclusive"].append(global_eta_cut)
            except KeyError:
                _cuts["inclusive"] = [global_eta_cut]
        return _cuts

    @property
    def match_dR(self) -> float:
        return self._object_params["match_dR"]


class ReferenceObject(BaseObject):
    def __init__(self, object_key: str, version: str) -> None:
        super().__init__(object_key, version)

    @property
    def trafo(self) -> Optional[str]:
        """Returns the trafo key of the (reference) object
        if it is defined (HT, MHT, etc).
        This is intended only for the *reference* object.
        """
        try:
            return self._object_params["trafo"]
        except KeyError:
            # No transformation defined in reference object `self.object_key`
            return None

    def _get_cuts(self, event_or_object: str) -> dict[str, list[str]]:
        assert event_or_object in [
            "event",
            "object",
        ], "Cuts are either event or object level"
        _cuts = {}
        if "cuts" in self._object_params.keys():
            if event_or_object in self._object_params["cuts"].keys():
                _cuts = self._object_params["cuts"][event_or_object]
            elif self.eta_range == "inclusive":
                return {}
        if self.eta_range != "inclusive":
            # if a region other than inclusive is specified, add an eta cut
            eta_min = self.eta_ranges[self.eta_range][0]
            eta_max = self.eta_ranges[self.eta_range][1]
            global_eta_cut = (
                f"((abs({{eta}}) > {eta_min}) & (abs({{eta}}) < {eta_max}))"
            )
            try:
                _cuts["inclusive"].append(global_eta_cut)
            except KeyError:
                _cuts["inclusive"] = [global_eta_cut]
        return _cuts

    @property
    def cuts(self) -> dict[str, list[str]]:
        """OBJECT level cuts! I.e. individual objects that don't fulfill the
        criteria are removed from the events, but the events themselves are
        retained.
        For info on the structure of the returned object see docstring of base
        class.

        Returns:
            object_cut_dict: For info on the structure of the returned object
            see docstring of base class.
        """
        return self._get_cuts("object")

    @property
    def event_cuts(self) -> dict[str, list[str]]:
        """EVENT level cuts! Applied after selection of highest pT object per
        event.
        Is meant to provied cuts to remove *events* whose object doesn't fulfill the
        criteria.

        Returns:
            event_cut_dict: For info on the structure of the returned object
            see docstring of base class.
        """
        return self._get_cuts("event")


def compute_selection_mask_for_cuts(
    obj: BaseObject, ak_array: ak.Array, cuts: dict
) -> ak.Array:
    """Compute selection mask for object/event cuts on array

    obj: Object that specifies the cuts to be applied
    ak_array: array on which the selection is evaluated

    Returns:
        sel: boolean selection mask for entries passing all cuts form obj
    """
    # Initialize mask with True everywhere
    sel = ak.ones_like(ak_array[ak_array.fields[0]]) > 0

    # If no cut are specified in object, return True everywhere.
    # That case will be `cuts = {}`.
    if not cuts:
        return sel

    ## add mock eta
    if "eta" not in ak_array.fields:
        ak_array["eta"] = 0

    for range_i, range_cuts in cuts.items():
        # Initialize temporary mask (for rangei) with True everywhere
        _sel = ak.ones_like(ak_array[ak_array.fields[0]]) > 0
        for cut in range_cuts:
            cut = re.sub(r"{([^&|]*)}", r"ak_array['\1']", cut)
            eta_sel = (abs(ak_array["eta"]) >= obj.eta_ranges[range_i][0]) & (
                abs(ak_array["eta"]) < obj.eta_ranges[range_i][1]
            )
            _sel = _sel & (eval(cut) + ~eta_sel)
        # apply OR logic
        sel = sel & _sel
    return sel


def compute_selection_mask_for_event_cuts(
    obj: BaseObject, ak_array: ak.Array
) -> ak.Array:
    return compute_selection_mask_for_cuts(obj, ak_array, obj.event_cuts)


def compute_selection_mask_for_object_cuts(
    obj: BaseObject, ak_array: ak.Array
) -> ak.Array:
    return compute_selection_mask_for_cuts(obj, ak_array, obj.cuts)


if __name__ == "__main__":
    x = Object("caloJet:default", "V29")
    print(x)
    print(x.match_dR)
    print(x.plot_label)
    print(x.eta_ranges)
    print(x.cuts)
    y = Object("tkElectron:Iso", "V29")
    z = ReferenceObject("jet:ht", "V29")

import os
import warnings

import awkward as ak
import yaml

from menu_tools.utils.objects import Object


def load_scaling_params(obj: Object, eta_range: str) -> tuple[float, float]:
    """Retrieves scalings for object+id from `outputs`

    obj: Object for which to retrive scaling parameters
    eta_range: specifier of the range for which scalings are to be retrieved

    Returns:
        scaling_params: parameters computed in object_performance
        for the online-offline scaling
    """
    fname = str(obj).replace("inclusive", eta_range)
    fpath = os.path.join(
        "outputs",
        obj.version,
        "object_performance",
        "scalings",
        obj.scaling_object + ".yaml",
    )
    try:
        with open(fpath, "r") as f:
            scaling_params = yaml.safe_load(f)
    except FileNotFoundError:
        warnings.warn_explicit(
            (f"No file was found at `{fpath}`"),
            UserWarning,
            filename="utils/scalings.py",
            lineno=26,
        )
        raise UserWarning
    return scaling_params["slope"], scaling_params["offset"]


def get_pt_branch(arr: ak.Array, obj_name: str) -> ak.Array:
    if "pt" in arr.fields:
        pt_orig = arr.pt
    elif "et" in arr.fields:
        pt_orig = arr.et
    elif "" in arr.fields:
        pt_orig = arr[""]
    ### HACK
    elif "TrackHT:MHT" in obj_name:
        pt_orig = arr["mht"]
    elif "TrackHT:HT" in obj_name:
        pt_orig = arr["ht"]
    else:
        raise RuntimeError(f"Unknown pt branch for {obj_name}! in fields", arr.fields)
    return pt_orig


def add_offline_pt(arr: ak.Array, obj: Object) -> ak.Array:
    """
    Add offline pt to filed called `offline_pt` and return array
    """
    pt_orig = get_pt_branch(arr, str(obj))
    new_pt = ak.zeros_like(pt_orig)

    if len(obj.eta_ranges) == 1 and list(obj.eta_ranges)[0] == "inclusive":
        # if only a single eta range is configured, the scalings are applied
        # inclusively on that region
        slope, offset = load_scaling_params(obj, "inclusive")
        new_pt = new_pt + (pt_orig * slope + offset)
    else:
        # if multiple eta ranges are found, the "inclusive" range is skipped
        # and all other ranges are applied
        for eta_range, eta_min_max in obj.eta_ranges.items():
            if eta_range == "inclusive":
                continue
            slope, offset = load_scaling_params(obj, eta_range)
            eta_mask = (abs(arr.eta) >= eta_min_max[0]) & (
                abs(arr.eta) < eta_min_max[1]
            )
            new_pt = new_pt + eta_mask * (pt_orig * slope + offset)

    if "eta" in arr.fields:
        arr["mass"] = 0.0 * ak.ones_like(arr["eta"])

    arr["idx"] = ak.local_index(arr)

    return ak.with_field(arr, new_pt, "offline_pt")

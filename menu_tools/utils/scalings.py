import os
import warnings
from typing import Optional

import awkward as ak
import yaml

from menu_tools.utils.objects import Object


def load_scaling_params(obj: Object) -> dict:
    """Retrieves scalings for object (incl. id) from `outputs`

    Returns:
        scaling_params: parameters computed in object_performance
        for the online-offline scaling
    """
    fpath = os.path.join(
        "outputs", "object_performance", obj.version, "scalings", f"{str(obj)}.yaml"
    )
    try:
        with open(fpath, "r") as f:
            scaling_params = yaml.safe_load(f)
    except FileNotFoundError:
        warnings.warn_explicit(
            (f"No file was found at `{fpath}`"),
            UserWarning,
            filename="utils.py",
            lineno=18,
        )
        raise UserWarning
    return scaling_params


def compute_offline_pt(
    arr: ak.Array, obj_scaling_params: dict[str, float], pt_var: Optional[str] = None
) -> ak.Array:
    # initialise array of zeros identical to the original pt
    if pt_var is not None:
        pt_orig = arr[pt_var]
    elif "et" in arr.fields:
        pt_orig = arr.et
    elif "pt" in arr.fields:
        pt_orig = arr.pt
    elif "" in arr.fields:
        pt_orig = arr[""][:, 0]
    else:
        raise ValueError(
            "No branch to which to apply the scalings."
            " One of `et`, `pt` or `` must exist to compute offline pt/et."
        )

    # scale pt for non-masked elements of this eta region
    offline_pt = pt_orig * obj_scaling_params["slope"] + obj_scaling_params["offset"]

    return offline_pt


def add_offline_pt(
    arr: ak.Array, obj_scaling_params: dict, pt_var: Optional[str] = None
) -> ak.Array:
    """
    Use the scalings to convert online pT to offline pT.
    The `pt_var` argument can be used to specify which observables
    should be used as "pT" for a given object.
    If `pt_var` is not specified, `pt` or `et` are used.
    For each object, a dedicated scaling in the barrel/endcap regions
    is applied to the online pT.
    """
    new_pt = compute_offline_pt(arr, obj_scaling_params, pt_var)
    return ak.with_field(arr, new_pt, "offline_pt")

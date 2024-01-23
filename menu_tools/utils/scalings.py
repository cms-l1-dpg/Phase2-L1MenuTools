from typing import Optional

import awkward as ak
import yaml

from menu_tools.utils.objects import Object


def load_scaling_params(obj: Object) -> dict:
    fpath = f"outputs/scalings/{obj.version}/{obj.nano_obj_name}.yaml"
    with open(fpath, "r") as f:
        return yaml.safe_load(f)[obj.obj_id_name]


def compute_offline_pt(
    arr: ak.Array, obj_scaling_params: dict, pt_var: Optional[str] = None
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
    new_pt = ak.zeros_like(pt_orig)

    # loop through eta regions with its scaling parameters
    for region, values in obj_scaling_params.items():
        # create eta mask for this eta region
        eta_mask = (abs(arr.eta) >= values["eta_min"]) & (
            abs(arr.eta) < values["eta_max"]
        )
        # scale pt for non-masked elements of this eta region
        new_pt = new_pt + eta_mask * (pt_orig * values["slope"] + values["offset"])

    return new_pt


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

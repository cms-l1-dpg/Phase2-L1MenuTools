import os
import warnings
from typing import Optional

import awkward as ak
import numpy as np
import yaml

from menu_tools.utils.objects import Object


class MissingScalingsError(UserWarning):
    """No scaling file for an object/eta range. A `UserWarning` subclass, as the bare
    `UserWarning` raised before, so callers catching that keep working."""


# Objects for which the missing-scalings fallback was already reported (warn once).
_warned_missing: set = set()


def load_scaling_params(
    obj: Object,
    eta_range: str,
    scaling_version: Optional[str] = None,
    decimals: Optional[int] = None,
) -> tuple[float, float]:
    """Retrieves scalings for object+id from `outputs`

    obj: Object for which to retrive scaling parameters
    eta_range: specifier of the range for which scalings are to be retrieved
    scaling_version: version to load scalings from (overrides obj.version)
    decimals: round the parameters to this many decimals, as np.round

    Returns:
        scaling_params: parameters computed in object_performance
        for the online-offline scaling
    """
    version = scaling_version if scaling_version else obj.version
    fpath = os.path.join(
        "outputs",
        version,
        "object_performance",
        "scalings",
        obj.get_scaling_object(eta_range) + ".yaml",
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
        raise MissingScalingsError(fpath)
    slope = float(scaling_params["slope"])
    offset = float(scaling_params["offset"])
    if decimals is not None:
        slope = float(np.round(slope, decimals))
        offset = float(np.round(offset, decimals))
    return slope, offset


def has_pt_branch(arr: ak.Array, obj_name: str) -> bool:
    """True if `get_pt_branch` finds a pt-like field (False e.g. for trigger bits)."""
    return any(f in arr.fields for f in ("pt", "et", "")) or (
        "TrackHT:MHT" in obj_name or "TrackHT:HT" in obj_name
    )


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


def _scaling_params_or_identity(
    obj: Object,
    eta_range: str,
    scaling_version: Optional[str],
    allow_missing: bool,
    decimals: Optional[int] = None,
) -> tuple[float, float]:
    """`load_scaling_params`, or (1, 0) with a warning (once per object) if the file
    is missing and `allow_missing` is set."""
    if not allow_missing:
        return load_scaling_params(obj, eta_range, scaling_version, decimals)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return load_scaling_params(obj, eta_range, scaling_version, decimals)
    except MissingScalingsError as err:
        key = (str(obj), scaling_version)
        if key not in _warned_missing:
            _warned_missing.add(key)
            warnings.warn(
                f"No scalings for {obj} ({err}): using offline_pt = pt "
                "(allow_missing_scalings is set)",
                UserWarning,
            )
        return 1.0, 0.0


def add_offline_pt(
    arr: ak.Array,
    obj: Object,
    scaling_version: Optional[str] = None,
    allow_missing: bool = False,
    decimals: Optional[int] = None,
) -> ak.Array:
    """
    Add offline pt to filed called `offline_pt` and return array

    allow_missing: if a scaling file is missing, use offline_pt = pt for that
    object/eta range (with one warning per object) instead of failing.
    An object config with `apply_scalings: false` always gets offline_pt = pt,
    e.g. for HLT objects, whose pt is already offline-like.
    """
    pt_orig = get_pt_branch(arr, str(obj))
    new_pt = ak.zeros_like(pt_orig)

    if not obj._object_params.get("apply_scalings", True):
        new_pt = pt_orig
    elif len(obj.eta_ranges) == 1 and list(obj.eta_ranges)[0] == "inclusive":
        # if only a single eta range is configured, the scalings are applied
        # inclusively on that region
        slope, offset = _scaling_params_or_identity(
            obj, "inclusive", scaling_version, allow_missing, decimals
        )
        new_pt = new_pt + (pt_orig * slope + offset)
    else:
        # if multiple eta ranges are found, the "inclusive" range is skipped
        # and all other ranges are applied
        for eta_range, eta_min_max in obj.eta_ranges.items():
            if eta_range == "inclusive":
                continue
            slope, offset = _scaling_params_or_identity(
                obj, eta_range, scaling_version, allow_missing, decimals
            )
            eta_mask = (abs(arr.eta) >= eta_min_max[0]) & (
                abs(arr.eta) < eta_min_max[1]
            )
            new_pt = new_pt + eta_mask * (pt_orig * slope + offset)

    if "eta" in arr.fields:
        arr["mass"] = 0.0 * ak.ones_like(arr["eta"])

    arr["idx"] = ak.local_index(arr)

    return ak.with_field(arr, new_pt, "offline_pt")

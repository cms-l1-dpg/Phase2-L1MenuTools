"""Cross-object cleaning of the reference objects (`reference_cleaning`).

Removes reference objects (e.g. GenJets) within `dR` of any selected object of a second
cached collection (e.g. prompt gen leptons from GenPart), before the reference cuts. See
docs/object-performance.md#reference-cleaning-reference_cleaning.

Config block (top level of a plot config), one block or a list of blocks (OR-ed: a
reference object is removed if it is close to an object of any block):

    reference_cleaning:
      object: GenPart               # cached object <version>_<sample>_<object>.parquet
      cuts:                         # selection of the cleaning objects, {field} syntax
        - "{status} == 1"
        - "(abs({pdgId}) == 11) | (abs({pdgId}) == 13)"
        - "({statusFlags} & 33) > 0"   # isPrompt | isDirectPromptTauDecayProduct
        - "{pt} > 10"
      dR: 0.4

Configs without the key are unchanged.
"""
import os
import re
from typing import Any, Optional

import awkward as ak
import numpy as np
import pyarrow.parquet as pq

from menu_tools.utils import constants
from menu_tools.utils.objects import CUT_FIELD_RE


def parse_reference_cleaning(
    block: Any, plot_name: Optional[str] = None
) -> list[dict[str, Any]]:
    """Normalised `reference_cleaning` blocks: [{"object", "cuts", "dR"}, ...].

    Empty list if the key is absent or empty.
    """
    if not block:
        return []
    blocks = block if isinstance(block, list) else [block]
    out = []
    for b in blocks:
        if not isinstance(b, dict) or "object" not in b or "dR" not in b:
            raise ValueError(
                f"reference_cleaning of {plot_name}: each block needs `object` and `dR`"
            )
        unknown = set(b) - {"object", "cuts", "dR"}
        if unknown:
            raise ValueError(
                f"reference_cleaning of {plot_name}: unknown keys {sorted(unknown)}"
            )
        cuts = b.get("cuts") or []
        if isinstance(cuts, str):
            cuts = [cuts]
        dr = float(b["dR"])
        if dr <= 0:
            raise ValueError(f"reference_cleaning of {plot_name}: dR must be > 0")
        out.append({"object": str(b["object"]), "cuts": list(cuts), "dR": dr})
    return out


def _strip(key: str, obj: str) -> str:
    return key[len(obj) + 1 :] if key.startswith(obj + "_") else key


def load_cleaning_objects(
    version: str, sample: str, obj: str, cuts: list[str]
) -> ak.Array:
    """(eta, phi) of the selected objects of `obj`, per event.

    Read row group by row group (GenPart caches are large) and keep only the
    selected objects.
    """
    fname = f"{constants.CACHE_DIR}/{version}/{version}_{sample}_{obj}.parquet"
    if not os.path.exists(fname):
        raise FileNotFoundError(
            f"reference_cleaning: {fname} not found (cache {obj} for {sample})"
        )
    fields = {"eta", "phi"} | {f for c in cuts for f in re.findall(CUT_FIELD_RE, c)}
    parts = []
    for rg in range(pq.ParquetFile(fname).num_row_groups):
        raw = ak.from_parquet(fname, row_groups=[rg])
        arr = ak.zip({_strip(k, obj): raw[k] for k in raw.fields})
        missing = fields - set(arr.fields)
        if missing:
            raise KeyError(
                f"reference_cleaning: fields {sorted(missing)} not in {fname}"
            )
        sel = ak.ones_like(arr["eta"], dtype=bool)
        for cut in cuts:
            sel = sel & eval(re.sub(CUT_FIELD_RE, r"arr['\1']", cut))
        arr = arr[sel]
        parts.append(ak.zip({"eta": arr["eta"], "phi": arr["phi"]}))
        del raw
    return parts[0] if len(parts) == 1 else ak.concatenate(parts, axis=0)


def near_mask(ref: ak.Array, others: ak.Array, dr: float) -> ak.Array:
    """Per reference object: is any object of `others` (same event) within `dr`?"""
    pairs = ak.cartesian({"r": ref, "o": others}, nested=True)
    deta = pairs["r"]["eta"] - pairs["o"]["eta"]
    dphi = (pairs["r"]["phi"] - pairs["o"]["phi"] + np.pi) % (2 * np.pi) - np.pi
    return ak.any(deta**2 + dphi**2 < dr**2, axis=-1)


def clean_reference(
    ref: ak.Array, blocks: list[dict[str, Any]], version: str, sample: str
) -> ak.Array:
    """`ref` without the objects within dR of a selected object of any block."""
    # (eta, phi) per object: `ref` can also be a record of per-event lists (the
    # unzipped reference of HT/MHT trafo plots)
    pos = ak.zip({"eta": ref["eta"], "phi": ref["phi"]})
    remove = None
    for b in blocks:
        others = load_cleaning_objects(version, sample, b["object"], b["cuts"])
        if len(others) != len(ref):
            raise ValueError(
                f"reference_cleaning: {b['object']} has {len(others)} events, the "
                f"reference {len(ref)}: the caches are not event-aligned"
            )
        m = near_mask(pos, others, b["dR"])
        remove = m if remove is None else (remove | m)
    if remove is None:
        return ref
    return ref[~remove]

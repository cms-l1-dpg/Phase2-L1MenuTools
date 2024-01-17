from unittest.mock import MagicMock

import awkward as ak

from turnon_collection import TurnOnCollection


def test_select_highest_pt_ref_object():
    """
    Tests that no more than one reference object per event is
    selected. If there are multiple reference objects in the event
    the highest pt one should be selected. If there are no reference
    objects in the event, the selection should yield an empty array
    element.
    """
    # Set up mock TurnOnCollection object
    TurnOnCollection._set_bins = MagicMock()
    turnon_collection = TurnOnCollection(None, None)
    arr_content = [[], [None]] + [
        [float(f"{i}.{k}") for k in range(3)] for i in range(5)
    ]
    idx_empty = [i for i, x in enumerate(arr_content) if len(x) == 0 or x[0] is None]
    turnon_collection.ak_arrays = {}
    turnon_collection.ak_arrays["ref"] = ak.Array(
        {"pt": arr_content, "other": arr_content}
    )

    # Execute selection of highest pt reference object
    turnon_collection._select_highest_pt_ref_object()
    ref_objects = turnon_collection.ak_arrays["ref"]

    # Assert outcome of selection as expected
    # The number of events should remain unchanged in all variables
    assert len(arr_content) == len(ref_objects["pt"])
    assert len(arr_content) == len(ref_objects["other"])
    # Each event should contain exactly one refernce object or a None entry
    assert all(ak.num(ref_objects["pt"], axis=-1) == 1)
    assert all(ak.num(ref_objects["other"], axis=-1) == 1)
    # Events without reference objects should contain a None entry
    assert all([not ref_objects["pt"][i] for i in idx_empty])

"""
These tests check if V29 electron object performance plots can be reproduced.
"""
import json
from unittest.mock import patch
import sys

import numpy as np

from menu_tools.object_performance import plotter


def test_isolation_barrel():
    # Prepare patching of the command line arguments for argparse
    testargs = [
        "foo",
        "menu_tools/object_performance/tests/reference_data/ElectronsIsolation_Barrel_-999_V29.yaml",
    ]

    # Run Plotting
    with patch.object(sys, "argv", testargs):
        plotter.run()

    # Load result and assert correct outcome
    with open(
        "outputs/object_performance/V29/turnons/ElectronsIsolation_Barrel_-999_V29.json",
        "r",
    ) as f:
        test_result = json.load(f)
    with open(
        "menu_tools/object_performance/tests/reference_data/ElectronsIsolation_Barrel_-999_V29.json",
        "r",
    ) as f:
        reference_data = json.load(f)

    for key, val in reference_data.items():
        if isinstance(val, dict):
            if "tkEle" in key:
                test_key = "tkElectron:NoIso:inclusive"
            efficiencies_test = np.array(
                test_result[test_key]["efficiency"], dtype=np.float64
            )
            efficiencies_reference = np.array(val["efficiency"], dtype=np.float64)
            print(efficiencies_reference)
            differences = efficiencies_test - efficiencies_reference
            assert not np.any(abs(differences) > 1e-4)
        else:
            assert val == test_result[key]

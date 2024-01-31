"""
These tests check if V29 electron object performance plots can be reproduced.
"""
import json
from unittest.mock import patch
import sys

import numpy as np
import pytest

from menu_tools.object_performance import plotter


testdata = [
    "HT_50perc_350_V29",
    "HT_90perc_350_V29",
    "ElectronsIsolation_Barrel_-999_V29",
]


@pytest.mark.parametrize("test_name", testdata)
def test_matching_plots_reproduced(test_name):
    # Prepare patching of the command line arguments for argparse
    testargs = [
        "foo",
        f"menu_tools/object_performance/tests/reference_data/{test_name}.yaml",
    ]

    # Run Plotting
    with patch.object(sys, "argv", testargs):
        plotter.main()

    # Load result and assert correct outcome
    with open(
        f"outputs/object_performance/V29/turnons/{test_name}.json",
        "r",
    ) as f:
        test_result = json.load(f)
    with open(
        f"menu_tools/object_performance/tests/reference_data/{test_name}.json",
        "r",
    ) as f:
        reference_data = json.load(f)

    for key, val in reference_data.items():
        if isinstance(val, dict):
            efficiencies_test = np.array(
                test_result[key]["efficiency"], dtype=np.float64
            )
            efficiencies_reference = np.array(val["efficiency"], dtype=np.float64)
            print(efficiencies_reference)
            differences = efficiencies_test - efficiencies_reference
            assert not np.any(abs(differences) > 1e-4)
        else:
            assert val == test_result[key]

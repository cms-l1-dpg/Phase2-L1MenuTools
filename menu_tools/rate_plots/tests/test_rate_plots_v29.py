"""
These tests check if V29 electron object performance plots can be reproduced.
"""
import json
from unittest.mock import patch
import re
import sys

import numpy as np
import pytest

from menu_tools.rate_plots import plotter


testdata = [
    "HTRates",
]


@pytest.mark.parametrize("test_name", testdata)
def test_matching_plots_reproduced(test_name):
    # Prepare patching of the command line arguments for argparse
    testargs = [
        "foo",
        f"menu_tools/rate_plots/tests/reference_data/{test_name}.yaml",
    ]

    # Run Plotting
    with patch.object(sys, "argv", testargs):
        plotter.main()
        pass

    # Load result and assert correct outcome (Offline)
    for online_offline in ["Online", "Offline"]:
        with open(
            f"outputs/rate_plots/V29_{online_offline}_{test_name}.json",
            "r",
        ) as f:
            test_result = json.load(f)
        with open(
            f"menu_tools/rate_plots/tests/reference_data/V29_{online_offline}_{test_name}.json",
            "r",
        ) as f:
            reference_data = json.load(f)

        for key, val in reference_data.items():
            print(key)
            if isinstance(val, dict):
                efficiencies_test = np.array(
                    test_result[key]["y_values"], dtype=np.float64
                )
                efficiencies_reference = np.array(val["y_values"], dtype=np.float64)
                differences = efficiencies_test - efficiencies_reference
                print(differences)
                try:
                    assert not np.any(abs(differences) > 1e-4)
                except Exception as e:
                    print(online_offline)
                    print(efficiencies_test)
                    print(efficiencies_reference)
                    raise e
            else:
                assert val == test_result[key]

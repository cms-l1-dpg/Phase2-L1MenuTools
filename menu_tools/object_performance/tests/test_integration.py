from turnon_collection import TurnOnCollection


def off_test_turnon_collection_met(met_config):
    """
    This integration test tests whether the MET histograms for the
    MET plots for V22 are produced as expected. The cache files
    included in the test directory should lead to the bin values
    specified below.
    """
    turnon_collection = TurnOnCollection(met_config, 70)
    turnon_collection.create_hists()

    assert all(
        [
            x == y
            for x, y in zip(
                list(turnon_collection.hists["trackerMET"][0]),
                met_config["trackerMETTruth"],
            )
        ]
    )

    assert all(
        [
            x == y
            for x, y in zip(
                list(turnon_collection.hists["puppiMET"][0]),
                met_config["puppiMETTruth"],
            )
        ]
    )

    assert all(
        [
            x == y
            for x, y in zip(
                list(turnon_collection.hists["ref"][0]), met_config["genMETTruth"]
            )
        ]
    )

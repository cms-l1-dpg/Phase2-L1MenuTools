import utils


def test_get_pdg_id():
    electrons = ["e", "ele", "electron"]
    muons = ["mu", "muon"]
    taus = ["tau"]
    photons = ["photon", "gamma"]

    for particle in electrons:
        assert utils.get_pdg_id(particle) == 11

    for particle in muons:
        assert utils.get_pdg_id(particle) == 13

    for particle in taus:
        assert utils.get_pdg_id(particle) == 15

    for particle in photons:
        assert utils.get_pdg_id(particle) == 22


def test_str_to_op():
    op_less_than = utils.str_to_op("<")
    op_less_equal = utils.str_to_op("<=")
    op_equal = utils.str_to_op("==")
    op_unequal = utils.str_to_op("!=")
    op_greater_than = utils.str_to_op(">")
    op_greater_equal = utils.str_to_op(">=")

    assert op_less_than(2, 5)
    assert not op_less_than(5, 2)

    assert op_less_equal(2, 5)
    assert op_less_equal(3, 3)
    assert not op_less_equal(5, 2)

    assert op_equal(5, 5)
    assert not op_equal(4, 5)

    assert op_unequal(4, 5)
    assert not op_unequal(5, 5)

    assert op_greater_than(5, 2)
    assert not op_greater_than(2, 5)

    assert op_greater_equal(5, 2)
    assert op_greater_equal(5, 5)
    assert not op_greater_equal(5, 8)

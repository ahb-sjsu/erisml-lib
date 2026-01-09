from erisml.examples.hello_deme import make_simple_option


def test_make_simple_option_structure():
    """
    Verify that make_simple_option returns a properly structured EthicalFacts object.
    """
    # 1. Setup variables
    opt_id = "test_option_1"
    benefit = 0.95
    is_violation = False

    # 2. Execute the function
    result = make_simple_option(opt_id, is_violation, benefit)

    # 3. Assert (Verify) the results
    assert result.option_id == opt_id
    assert result.consequences.expected_benefit == benefit
    assert result.rights_and_duties.violates_rights == is_violation


def test_make_simple_option_violation():
    """
    Verify that setting violates_rights=True actually updates the object.
    """
    # Create an option that violates rights
    result = make_simple_option("bad_option", True, 0.5)

    # Verify the flag is set to True
    assert result.rights_and_duties.violates_rights is True

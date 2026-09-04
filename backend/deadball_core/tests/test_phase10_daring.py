import pytest

from deadball_core import (
    FixedDice,
    ManagerError,
    ManagerState,
    generate_manager_daring,
    resolve_daring,
)


@pytest.mark.parametrize(("roll", "expected"), [(1, 1), (19, 19), (20, 19)])
def test_published_daring_generation_caps_twenty_at_nineteen(roll, expected):
    assert generate_manager_daring(FixedDice([roll])) == expected


@pytest.mark.parametrize(
    ("roll", "selected", "daring_choice"),
    [
        (1, "steal_second", True),
        (13, "steal_second", True),
        (14, "hold", False),
        (20, "hold", False),
    ],
)
def test_published_roll_at_or_below_daring_selects_risky_choice(
    roll, selected, daring_choice
):
    decision = resolve_daring(13, "steal_second", "hold", FixedDice([roll]))

    assert decision.roll == roll
    assert decision.daring == 13
    assert decision.selected_choice == selected
    assert decision.chose_daring is daring_choice


@pytest.mark.parametrize("rating", [0, 20, True, 10.5])
def test_daring_rating_must_be_in_published_range(rating):
    with pytest.raises(ManagerError, match="between 1 and 19"):
        resolve_daring(rating, "risky", "safe", FixedDice([10]))
    with pytest.raises(ManagerError, match="between 1 and 19"):
        ManagerState(rating)


def test_manager_state_retains_a_valid_daring_rating():
    assert ManagerState(13).daring == 13


def test_decision_records_both_choices_and_explanation_fields():
    decision = resolve_daring(
        8,
        "leave_pitcher",
        "change_pitcher",
        FixedDice([9]),
        decision_type="starter_after_sixth",
        reason="starter completed six innings",
    )

    assert decision.decision_type == "starter_after_sixth"
    assert decision.risky_choice == "leave_pitcher"
    assert decision.conservative_choice == "change_pitcher"
    assert decision.selected_choice == "change_pitcher"
    assert decision.reason == "starter completed six innings"

"""The settings a person chooses, and what the physics does with them."""

import pytest

from yerkon.design import Design, derive
from yerkon.hardware import E28_2G4M27S, SX1280
from yerkon.regulatory import EUROPE, TURKEY, UNITED_STATES
from yerkon.rf import DEFAULT_SEARCH_LIMIT_M
from yerkon.world import BILLBOARD, ROADSIDE_SIGN, TALL_MAST


# --- The settings themselves ----------------------------------------------


def test_editing_a_design_leaves_the_original_alone():
    original = Design()
    edited = original.with_(target_ranging_sigma_m=2.0)
    assert original.target_ranging_sigma_m == 5.0
    assert edited.target_ranging_sigma_m == 2.0


def test_a_typo_in_a_setting_name_is_refused_rather_than_ignored():
    """Silently accepting an unknown field would let a whole edit vanish."""
    with pytest.raises(ValueError, match="not a setting: taget_ranging_sigma_m"):
        Design().with_(taget_ranging_sigma_m=2.0)


def test_a_tolerance_of_zero_is_refused():
    with pytest.raises(ValueError, match="tolerance of zero"):
        Design(target_ranging_sigma_m=0.0)


# --- What follows from them -----------------------------------------------


def test_height_is_the_largest_lever_on_range():
    sign = derive(Design(mounting=ROADSIDE_SIGN)).usable_range_m
    billboard = derive(Design(mounting=BILLBOARD)).usable_range_m
    mast = derive(Design(mounting=TALL_MAST)).usable_range_m
    assert sign < billboard < mast
    assert mast > 2.0 * sign


def test_the_five_kilometre_requirement_needs_a_purpose_built_mast():
    """The report asks for 5 to 10 km. Roadside furniture does not reach it."""
    assert derive(Design(mounting=TALL_MAST)).usable_range_m >= 5_000.0
    assert derive(Design(mounting=BILLBOARD)).usable_range_m < 5_000.0


def test_turkey_and_europe_allow_the_same_power():
    """Turkey cites the harmonised standard, so the limits coincide."""
    assert derive(Design(region=TURKEY)).eirp_dbm == pytest.approx(
        derive(Design(region=EUROPE)).eirp_dbm
    )


def test_the_amplifier_is_inert_in_turkey_and_worth_having_in_america():
    """The band caps radiated density here and conducted power there.

    Same part, same antenna: under the Turkish rule the module's own
    27 dBm never reaches the air, and under the American one most of it
    does.
    """
    plain_tr = derive(Design(region=TURKEY, anchor_radio=SX1280))
    amped_tr = derive(Design(region=TURKEY, anchor_radio=E28_2G4M27S))
    assert amped_tr.eirp_dbm == pytest.approx(plain_tr.eirp_dbm)
    assert amped_tr.usable_range_m == pytest.approx(plain_tr.usable_range_m)

    plain_us = derive(Design(region=UNITED_STATES, anchor_radio=SX1280))
    amped_us = derive(Design(region=UNITED_STATES, anchor_radio=E28_2G4M27S))
    assert amped_us.eirp_dbm - plain_us.eirp_dbm > 10.0
    assert amped_us.usable_range_m > 2.0 * plain_us.usable_range_m


def test_a_link_reaches_far_beyond_where_it_still_measures():
    """ADR-0007. Quoting the closure distance as coverage is the error."""
    outcome = derive(Design())
    assert outcome.closure_range_m > 5.0 * outcome.usable_range_m


def test_a_tolerance_below_the_radios_own_floor_is_met_nowhere():
    """The SX1280 measures to about three metres however strong the signal.

    No distance, and no mast, buys a tolerance under that.
    """
    assert derive(Design(target_ranging_sigma_m=1.0)).usable_range_m == 0.0


def test_rough_ground_helps_rather_than_hurts():
    """Smooth ground returns the reflection that cancels the direct ray.

    Roughness scatters it, so the cancellation weakens. The counterintuitive
    direction is the point: this is not a loss term.
    """
    smooth = derive(Design(surface_roughness_m=0.0)).usable_range_m
    rough = derive(Design(surface_roughness_m=0.5)).usable_range_m
    assert rough > smooth


def test_a_saturated_search_is_visible_as_such():
    """A design that outruns the search must not read as one that stopped."""
    outcome = derive(
        Design(region=UNITED_STATES, anchor_radio=E28_2G4M27S)
    )
    assert outcome.closure_range_m == pytest.approx(DEFAULT_SEARCH_LIMIT_M)


# --- The named catalogues -------------------------------------------------


def test_every_setting_can_be_chosen_by_a_typed_name():
    """A front end should never need to know what a SpectrumRule is."""
    from yerkon.design import (
        ANTENNA_CHOICES,
        MOUNTING_CHOICES,
        RADIO_CHOICES,
        REGION_CHOICES,
        chosen,
    )

    assert chosen(REGION_CHOICES, "TR", "region") is TURKEY
    assert chosen(RADIO_CHOICES, "e28", "radio") is E28_2G4M27S
    assert chosen(MOUNTING_CHOICES, "mast", "mounting") is TALL_MAST
    assert ANTENNA_CHOICES


def test_a_name_is_matched_whatever_case_it_is_typed_in():
    from yerkon.design import REGION_CHOICES, chosen

    assert chosen(REGION_CHOICES, "tr", "region") is TURKEY
    assert chosen(REGION_CHOICES, " US-PTP ", "region") is not TURKEY


def test_an_unknown_name_lists_the_ones_that_exist():
    """A bare KeyError tells a person nothing they can act on."""
    from yerkon.design import MOUNTING_CHOICES, chosen

    with pytest.raises(ValueError, match="billboard, column, gantry, mast, sign"):
        chosen(MOUNTING_CHOICES, "lamppost", "mounting")


def test_every_mounting_in_the_catalogue_derives_without_error():
    from yerkon.design import MOUNTING_CHOICES

    for name, mounting in MOUNTING_CHOICES.items():
        outcome = derive(Design(mounting=mounting))
        assert outcome.usable_range_m > 0.0, name
        assert outcome.closure_range_m >= outcome.usable_range_m, name

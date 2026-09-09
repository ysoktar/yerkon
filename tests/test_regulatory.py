"""Region rules, and how much they move the answer."""

import pytest

from yerkon.regulatory import (
    EUROPE,
    LICENSED_ASSIGNMENT,
    REGIONS,
    TURKEY,
    UNITED_STATES,
    UNITED_STATES_POINT_TO_POINT,
)

W24P_U_GAIN = 3.2
SX1280_OUTPUT = 12.5
E28_OUTPUT = 27.0
RANGING_BANDWIDTH = 1625e3


def test_turkey_and_europe_agree_because_one_adopts_the_other():
    for bandwidth in (203e3, 406e3, 812e3, 1625e3):
        assert TURKEY.permitted_eirp_dbm(
            bandwidth, W24P_U_GAIN, E28_OUTPUT
        ) == pytest.approx(
            EUROPE.permitted_eirp_dbm(bandwidth, W24P_U_GAIN, E28_OUTPUT)
        )


def test_the_european_ceiling_rises_with_bandwidth_and_the_american_one_does_not():
    """The two rules are shaped differently, not just set differently.

    Europe caps power per megahertz, so a wider signal is allowed more of
    it. America caps what leaves the transmitter, which bandwidth does not
    touch. A design that widens its ranging bandwidth gains power in one
    jurisdiction and nothing in the other.
    """
    narrow_eu = EUROPE.permitted_eirp_dbm(203e3, W24P_U_GAIN, E28_OUTPUT)
    wide_eu = EUROPE.permitted_eirp_dbm(1625e3, W24P_U_GAIN, E28_OUTPUT)
    assert wide_eu - narrow_eu == pytest.approx(9.03, abs=0.05)

    narrow_us = UNITED_STATES.permitted_eirp_dbm(203e3, W24P_U_GAIN, E28_OUTPUT)
    wide_us = UNITED_STATES.permitted_eirp_dbm(1625e3, W24P_U_GAIN, E28_OUTPUT)
    assert wide_us == pytest.approx(narrow_us)


def test_the_rural_amplifier_is_dead_weight_in_turkey_and_useful_in_america():
    """Whether the E28's power amplifier does anything is a legal question.

    Under the density cap both anchor radios radiate 12,1 dBm and the
    amplifier is inert. Under the American conducted limit it delivers
    18 dB more, which is most of a factor of three in range.
    """
    plain_tr = TURKEY.permitted_eirp_dbm(RANGING_BANDWIDTH, W24P_U_GAIN, SX1280_OUTPUT)
    amplified_tr = TURKEY.permitted_eirp_dbm(RANGING_BANDWIDTH, W24P_U_GAIN, E28_OUTPUT)
    assert amplified_tr == pytest.approx(plain_tr)

    plain_us = UNITED_STATES.permitted_eirp_dbm(
        RANGING_BANDWIDTH, W24P_U_GAIN, SX1280_OUTPUT
    )
    amplified_us = UNITED_STATES.permitted_eirp_dbm(
        RANGING_BANDWIDTH, W24P_U_GAIN, E28_OUTPUT
    )
    assert amplified_us - plain_us == pytest.approx(14.5, abs=0.1)
    assert amplified_us - amplified_tr == pytest.approx(18.1, abs=0.1)


def test_a_rule_never_makes_the_hardware_louder_than_it_is():
    """Headroom in the rule is not power in the transmitter."""
    generous = LICENSED_ASSIGNMENT.permitted_eirp_dbm(
        RANGING_BANDWIDTH, W24P_U_GAIN, SX1280_OUTPUT
    )
    assert generous == pytest.approx(SX1280_OUTPUT + W24P_U_GAIN)


def test_high_gain_antennas_are_paid_for_out_of_transmit_power():
    """The American rule allows 6 dBi free and charges for the rest.

    Uses a transmitter that can actually reach the conducted ceiling. The
    E28's 27 dBm cannot, so with a modest antenna the hardware binds
    before the rule does and the payback never shows.
    """
    full_watt = 30.0
    at_allowance = UNITED_STATES.permitted_eirp_dbm(RANGING_BANDWIDTH, 6.0, full_watt)
    above = UNITED_STATES.permitted_eirp_dbm(RANGING_BANDWIDTH, 15.0, full_watt)
    assert at_allowance == pytest.approx(36.0)
    assert above == pytest.approx(at_allowance)


def test_a_modest_antenna_leaves_the_hardware_binding_not_the_rule():
    """The E28 at 3,2 dBi is limited by its own amplifier under the FCC."""
    permitted = UNITED_STATES.permitted_eirp_dbm(
        RANGING_BANDWIDTH, W24P_U_GAIN, E28_OUTPUT
    )
    assert permitted == pytest.approx(E28_OUTPUT + W24P_U_GAIN)


def test_a_fixed_point_to_point_link_keeps_more_of_its_antenna_gain():
    """47 CFR 15.247(c)(1) charges one decibel per three, not one per one.

    It applies to fixed links only, so anchor-to-anchor backhaul could use
    it and a link to a moving vehicle could not.
    """
    mobile = UNITED_STATES.permitted_eirp_dbm(RANGING_BANDWIDTH, 15.0, E28_OUTPUT)
    fixed = UNITED_STATES_POINT_TO_POINT.permitted_eirp_dbm(
        RANGING_BANDWIDTH, 15.0, E28_OUTPUT
    )
    assert fixed > mobile + 5.0


def test_every_region_is_reachable_by_key():
    assert set(REGIONS) == {"TR", "EU", "US", "US-PTP", "LICENSED"}
    for rule in REGIONS.values():
        assert rule.region.strip()

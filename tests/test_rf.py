"""The link budget, and the claims the study rests on."""

import math

import pytest

from yerkon.hardware import DWM3000, E28_2G4M27S, SX1280, W24P_U
from yerkon.rf import (
    Obstruction,
    Terminal,
    diffraction_loss_db,
    earth_bulge_m,
    cramer_rao_sigma_m,
    evaluate_link,
    first_fresnel_radius_m,
    free_space_path_loss_db,
    ranging_sigma_m,
    regulatory_eirp_limit_dbm,
)


def mast(height_m, radio=E28_2G4M27S, x=0.0):
    return Terminal(radio, W24P_U, (x, 0.0, height_m))


def vehicle(distance_m, radio=SX1280):
    return Terminal(radio, W24P_U, (distance_m, 0.0, 2.0))


def test_free_space_loss_matches_the_closed_form():
    assert free_space_path_loss_db(100.0, 2450e6) == pytest.approx(80.24, abs=0.05)


def test_loss_rises_six_decibels_per_doubling():
    near = free_space_path_loss_db(1000.0, 2450e6)
    far = free_space_path_loss_db(2000.0, 2450e6)
    assert far - near == pytest.approx(6.02, abs=0.01)


def test_the_fresnel_zone_is_widest_in_the_middle():
    """A link needs an ellipsoid of clear space, not a clear ray."""
    middle = first_fresnel_radius_m(10_000.0, 2450e6, 0.5)
    near_end = first_fresnel_radius_m(10_000.0, 2450e6, 0.1)
    assert middle > near_end
    assert middle == pytest.approx(17.5, abs=0.2)


def test_earth_curvature_pushes_the_ground_into_long_paths():
    """Midpoint sag below the chord, not the tangent-plane drop.

    The two differ by a factor of four and it is an easy slip: over 15 km
    the tangent-plane figure is 13 m, the midpoint figure 3,3 m. The
    midpoint one is what intrudes into a link between two masts.
    """
    assert earth_bulge_m(1_000.0) < 0.02
    assert earth_bulge_m(15_000.0) == pytest.approx(3.31, abs=0.05)


def test_an_obstacle_level_with_the_line_of_sight_costs_six_decibels():
    """The knife-edge result. Grazing is already a real loss."""
    assert diffraction_loss_db(0.0, 17.5) == pytest.approx(6.0, abs=0.5)


def test_clearing_the_fresnel_zone_costs_nothing():
    assert diffraction_loss_db(20.0, 17.5) == 0.0


def test_blocking_the_path_costs_much_more_than_grazing():
    grazing = diffraction_loss_db(0.0, 17.5)
    blocked = diffraction_loss_db(-40.0, 17.5)
    assert blocked > grazing + 10.0


# --- The claims the study rests on ---------------------------------------


def test_the_stock_hardware_reaches_ten_kilometres():
    """The requirement: 5 to 10 km links on the parts the report names.

    No better antenna, no more power than the band allows. If this fails,
    the rural deployment needs different hardware and the cost model
    changes with it.
    """
    budget = evaluate_link(mast(35.0), vehicle(10_000.0))
    assert budget.closes
    assert budget.margin_db > 20.0


def test_fifteen_kilometres_is_limited_by_mast_height_not_by_power():
    """Which constraint actually binds at the far end of the range.

    The radio has tens of decibels to spare at 15 km. What it does not
    automatically have is a clear Fresnel zone, because the earth's own
    bulge is 13 m by then. Raising the mast fixes it; more power does not.
    """
    low = evaluate_link(mast(6.0), vehicle(15_000.0))
    high = evaluate_link(mast(45.0), vehicle(15_000.0))

    assert low.margin_db > 20.0, "power was never the problem"
    assert not low.has_fresnel_clearance
    assert high.has_fresnel_clearance
    assert low.diffraction_loss_db > high.diffraction_loss_db


def test_the_density_cap_binds_at_every_sx1280_bandwidth():
    """Legal power rises with bandwidth, so widening it costs no range."""
    for bandwidth in (203e3, 406e3, 812e3, 1625e3):
        assert regulatory_eirp_limit_dbm(bandwidth) < 20.0
    assert regulatory_eirp_limit_dbm(1625e3) == pytest.approx(12.1, abs=0.05)


def test_the_amplifier_buys_nothing_the_regulation_allows_to_be_used():
    """The rural module is rated 27 dBm; the band allows 12,1 dBm.

    Both modules therefore radiate the same power, and the rural link is
    not longer for having the amplifier. That is a finding about the
    deployment, so it is pinned here.
    """
    weak = evaluate_link(mast(35.0, radio=SX1280), vehicle(8_000.0))
    strong = evaluate_link(mast(35.0, radio=E28_2G4M27S), vehicle(8_000.0))
    assert strong.eirp_dbm == pytest.approx(weak.eirp_dbm)

    unrestricted = evaluate_link(
        mast(35.0, radio=E28_2G4M27S), vehicle(8_000.0),
        respect_regulatory_limit=False,
    )
    assert unrestricted.eirp_dbm > strong.eirp_dbm


def test_range_responds_to_antenna_height():
    """ADR-0002: geometry moves reachability, not a constant.

    This is the behaviour the previous codebase could not produce, because
    reachability came from a hardcoded distance.
    """
    terrain = Obstruction(peak_terrain_m=30.0)
    low = evaluate_link(mast(6.0), vehicle(12_000.0), obstruction=terrain)
    high = evaluate_link(mast(60.0), vehicle(12_000.0), obstruction=terrain)
    assert high.received_dbm > low.received_dbm + 10.0


def test_clutter_reduces_received_power_decibel_for_decibel():
    clear = evaluate_link(mast(20.0), vehicle(2_000.0))
    wooded = evaluate_link(
        mast(20.0), vehicle(2_000.0), obstruction=Obstruction(clutter_loss_db=15.0)
    )
    assert clear.received_dbm - wooded.received_dbm == pytest.approx(15.0)


# --- Ranging precision ----------------------------------------------------


def test_the_waveform_bound_worsens_with_distance():
    """Halving the signal-to-noise ratio costs a factor of root two."""
    near = evaluate_link(mast(35.0), vehicle(5_000.0))
    far = evaluate_link(mast(35.0), vehicle(10_000.0))
    assert cramer_rao_sigma_m(far, E28_2G4M27S) == pytest.approx(
        2.0 * cramer_rao_sigma_m(near, E28_2G4M27S), rel=0.02
    )


def test_wider_bandwidth_times_arrivals_more_precisely():
    """Why the ultra-wideband radio is in the tunnel at all.

    Both radios are handed the same budget, so they see the same
    signal-to-noise ratio and bandwidth is the only difference left. The
    bound then scales exactly inversely with root-mean-square bandwidth,
    and 499,2 MHz against 1,625 MHz is a factor of 307.

    Comparing the two at the same distance instead would measure the link
    budget, not the waveform.
    """
    shared = evaluate_link(mast(6.0, radio=SX1280), vehicle(300.0))

    narrow = cramer_rao_sigma_m(shared, SX1280)
    wide = cramer_rao_sigma_m(shared, DWM3000)

    bandwidth_ratio = DWM3000.rms_bandwidth_hz / SX1280.rms_bandwidth_hz
    assert narrow / wide == pytest.approx(bandwidth_ratio, rel=1e-6)
    assert bandwidth_ratio == pytest.approx(307.2, rel=0.01)


def test_a_narrowband_radio_does_not_deliver_centimetres_up_close():
    """The bound alone would claim 2 cm at 100 m. The part measures 3 m.

    Without the implementation floor this model would report centimetre
    ranging from a narrowband radio standing near an anchor, which is the
    single most dangerous number this study could publish.
    """
    close = evaluate_link(mast(6.0, radio=SX1280), vehicle(100.0))
    assert cramer_rao_sigma_m(close, SX1280) < 0.1
    assert ranging_sigma_m(close, SX1280) == pytest.approx(2.94, abs=0.01)


def test_the_floor_stops_binding_once_the_signal_gets_weak():
    far = evaluate_link(mast(45.0), vehicle(25_000.0))
    assert cramer_rao_sigma_m(far, E28_2G4M27S) > float(
        E28_2G4M27S.implementation_floor_m.value
    )
    assert ranging_sigma_m(far, E28_2G4M27S) == cramer_rao_sigma_m(far, E28_2G4M27S)


def test_a_dead_link_has_no_precision_to_report():
    dead = evaluate_link(mast(2.0), vehicle(400_000.0))
    assert not dead.closes
    with pytest.raises(ValueError, match="does not close"):
        ranging_sigma_m(dead, E28_2G4M27S)


@pytest.mark.parametrize("bad", [0.0, -1.0])
def test_a_link_needs_a_positive_distance(bad):
    with pytest.raises(ValueError):
        free_space_path_loss_db(bad, 2450e6)

"""The link budget, and the claims the study rests on."""

import math

import pytest

from yerkon.hardware import DWM3000, E28_2G4M27S, SX1280, W24P_U
from yerkon.rf import (
    Obstruction,
    Terminal,
    diffraction_loss_db,
    earth_bulge_m,
    breakpoint_distance_m,
    cramer_rao_sigma_m,
    evaluate_link,
    first_fresnel_radius_m,
    free_space_path_loss_db,
    ranging_sigma_m,
    regulatory_eirp_limit_dbm,
    specular_fraction,
    two_ray_path_loss_db,
    usable_range_m,
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
    # Eight decibels, not the thirty an earlier version of this model
    # claimed by counting the despreading gain twice (ADR-0017). It still
    # closes, and it is no longer comfortable.
    assert budget.margin_db > 5.0


def test_height_buys_range_because_of_ground_reflection():
    """Which constraint actually binds, measured rather than assumed.

    Over flat ground the reflected ray cancels the direct one beyond the
    breakpoint, and loss then grows with the fourth power of distance.
    The breakpoint moves with antenna height, so height is worth far more
    than power: a 6 m mount is past it at 400 m, a 45 m mast at 2,9 km.
    """
    low = evaluate_link(mast(6.0), vehicle(15_000.0))
    high = evaluate_link(mast(45.0), vehicle(15_000.0))

    assert low.path_loss_db > high.path_loss_db + 15.0

    # The breakpoint is linear in height, so the ratio is the height ratio.
    tall = breakpoint_distance_m(45.0, 2.0, 2450e6)
    short = breakpoint_distance_m(6.0, 2.0, 2450e6)
    assert tall / short == pytest.approx(45.0 / 6.0)
    assert tall == pytest.approx(2942.0, rel=0.01)


def test_a_link_that_closes_is_not_a_link_that_ranges():
    """The distinction the siting problem turns on.

    A spread link keeps demodulating long after its timing precision has
    gone. Reporting the closure distance as the range would overstate what
    an anchor covers by a factor of several.
    """
    far = evaluate_link(mast(25.0), vehicle(10_000.0))
    assert far.closes
    assert far.margin_db > 0.0
    assert ranging_sigma_m(far, E28_2G4M27S) > 10.0

    useful = usable_range_m(mast(25.0), vehicle(1.0), E28_2G4M27S, target_sigma_m=5.0)
    assert 3_000.0 < useful < far.distance_m


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
    """Beyond the breakpoint, doubling the distance costs a factor of four.

    Loss grows at 40 dB per decade there rather than 20, and the bound
    goes as the square root of the signal-to-noise ratio, so the sigma
    quadruples. Below the breakpoint it would only double.
    """
    near = evaluate_link(mast(35.0), vehicle(5_000.0))
    far = evaluate_link(mast(35.0), vehicle(10_000.0))
    assert near.distance_m > breakpoint_distance_m(35.0, 2.0, 2450e6)
    assert cramer_rao_sigma_m(far, E28_2G4M27S) == pytest.approx(
        4.0 * cramer_rao_sigma_m(near, E28_2G4M27S), rel=0.03
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
    far = evaluate_link(mast(45.0), vehicle(12_000.0))
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


# --- Ground reflection over real ground -----------------------------------


def test_a_shallow_grazing_angle_stays_specular_however_lumpy_the_ground():
    """Why rough terrain does not rescue a long link.

    A surface is smooth relative to the angle that strikes it. At 10 km
    the grazing angle is under a tenth of a degree, so ground that looks
    thoroughly broken from standing height still returns a coherent ray.
    It takes metres of scatter to break it, and by 2 km a metre is enough.
    """
    near = specular_fraction(2_000.0, 25.0, 2.0, roughness_m=1.0, frequency_hz=2450e6)
    far = specular_fraction(10_000.0, 25.0, 2.0, roughness_m=1.0, frequency_hz=2450e6)

    assert near < 0.5, "a metre of scatter breaks the 2 km reflection"
    assert far > 0.9, "the same metre barely touches the 10 km one"


def test_roughness_moves_the_model_between_its_two_extremes():
    smooth = two_ray_path_loss_db(10_000.0, 25.0, 2.0, 2450e6, roughness_m=0.0)
    broken = two_ray_path_loss_db(10_000.0, 25.0, 2.0, 2450e6, roughness_m=50.0)
    free = free_space_path_loss_db(10_000.0, 2450e6)

    assert smooth > free + 10.0
    assert broken == pytest.approx(free, abs=0.5)


def test_height_is_measured_above_the_reflecting_surface():
    """Why a mast on a ridge behaves like a much taller mast.

    The same 25 m structure over a valley floor 40 m below it reflects as
    though it were 65 m up, and the breakpoint moves out with it.
    """
    on_the_flat = evaluate_link(mast(25.0), vehicle(8_000.0))
    on_a_ridge = evaluate_link(
        mast(25.0), vehicle(8_000.0),
        obstruction=Obstruction(reflection_surface_m=-40.0),
    )
    assert on_a_ridge.path_loss_db < on_the_flat.path_loss_db - 5.0


# --- Which ratio a threshold is quoted on ---------------------------------


def test_a_lora_link_closes_where_its_in_band_ratio_meets_its_threshold():
    """ADR-0017, and the check that would have caught the bug.

    A LoRa datasheet's -20 dB is quoted in the occupied bandwidth:
    despreading is what makes it workable and is already assumed in the
    figure. Adding the correlation gain on top grants the link thirty
    decibels twice, which is what the first version of this model did.
    """
    edge = usable = None
    for distance_m in range(1000, 40_000, 50):
        budget = evaluate_link(mast(25.0), vehicle(float(distance_m)))
        if not budget.closes:
            break
        edge = budget
    assert edge is not None
    threshold = float(E28_2G4M27S.demodulation_threshold_db.value)
    assert edge.snr_db == pytest.approx(threshold, abs=0.3)


def test_an_impulse_link_closes_on_the_ratio_after_its_accumulation():
    """It does not spread a symbol, so its working point is quoted after
    the preamble accumulation rather than before it."""
    from yerkon.hardware import DWM3000

    anchor = Terminal(DWM3000, W24P_U, (0.0, 0.0, 4.5))
    edge = None
    for distance_m in range(20, 2000, 5):
        budget = evaluate_link(
            anchor, Terminal(DWM3000, W24P_U, (float(distance_m), 0.0, 1.5))
        )
        if not budget.closes:
            break
        edge = budget
    assert edge is not None
    threshold = float(DWM3000.demodulation_threshold_db.value)
    assert edge.effective_snr_db == pytest.approx(threshold, abs=1.0)


def test_a_link_never_closes_far_below_the_part_it_is_made_of():
    """The sanity check the model failed for a fortnight.

    Its claimed closure range needed -156 dBm at the receiver against a
    part whose best-case sensitivity is -132 dBm. No arrangement of
    antennas makes a radio hear twenty-four decibels below itself.
    """
    edge = None
    for distance_m in range(1000, 40_000, 50):
        budget = evaluate_link(mast(25.0), vehicle(float(distance_m)))
        if not budget.closes:
            break
        edge = budget
    assert edge.received_dbm > float(E28_2G4M27S.sensitivity_dbm.value)


# --- What a blocked path does to a measurement ----------------------------


def test_a_clear_path_adds_no_distance():
    """The direct ray arrives first and a receiver times that."""
    from yerkon.rf import excess_path_m

    assert excess_path_m(clearance_m=12.0, distance_m=5000.0,
                         peak_at_fraction=0.5) == 0.0


def test_a_blocked_path_is_longer_than_the_straight_line():
    """The signal goes over the obstacle, and the range measures that.

    Always positive, which is what makes obstruction worse for
    positioning than the loss alone suggests: noise averages out over
    repeated measurements and a detour does not (ADR-0019).
    """
    from yerkon.rf import excess_path_m

    excess = excess_path_m(
        clearance_m=-100.0, distance_m=2000.0, peak_at_fraction=0.5
    )
    assert excess == pytest.approx(10.0, rel=0.01)


def test_a_taller_obstacle_makes_a_longer_detour():
    from yerkon.rf import excess_path_m

    low = excess_path_m(-10.0, 5000.0, 0.5)
    high = excess_path_m(-50.0, 5000.0, 0.5)
    assert high > low
    # The detour goes as the square of the intrusion, so five times the
    # height is twenty-five times the delay.
    assert high == pytest.approx(25.0 * low, rel=0.01)


def test_an_obstacle_near_one_end_costs_less_than_one_in_the_middle():
    """The same as the Fresnel zone, and for the same reason."""
    from yerkon.rf import excess_path_m

    middle = excess_path_m(-20.0, 4000.0, 0.5)
    near_end = excess_path_m(-20.0, 4000.0, 0.05)
    assert near_end > middle, "a detour near an end is sharper, not gentler"


def test_the_link_budget_reports_the_detour_it_implies():
    from yerkon.rf import Obstruction

    clear = evaluate_link(mast(25.0), vehicle(5000.0))
    blocked = evaluate_link(
        mast(25.0), vehicle(5000.0),
        obstruction=Obstruction(peak_terrain_m=50.0),
    )
    assert clear.excess_path_m == 0.0
    assert blocked.excess_path_m > 0.0


# --- Diffraction over the whole profile (ADR-0053) ------------------------


def a_plain(height_m=0.0, samples=64):
    """A profile at one height, which is what a plane looks like."""
    return tuple((i / samples, height_m) for i in range(samples + 1))


def test_one_edge_on_the_line_of_sight_costs_the_classic_six_decibels():
    """ITU-R P.526-15 equation (31) at v = 0, which every one of these
    methods is built from and which the single-edge function already
    used. Shared rather than written twice."""
    from yerkon.rf import knife_edge_db

    assert knife_edge_db(0.0) == pytest.approx(6.0, abs=0.1)
    assert knife_edge_db(-0.78) == 0.0, "clear of the zone that matters"
    assert knife_edge_db(-5.0) == 0.0
    assert knife_edge_db(3.0) > knife_edge_db(1.0) > knife_edge_db(0.0)

    # And the older, single-point function is the same J(v), reached
    # through a clearance and a Fresnel radius instead of through v.
    zone = first_fresnel_radius_m(1000.0, 2450e6)
    assert diffraction_loss_db(0.0, zone) == pytest.approx(knife_edge_db(0.0))


def test_two_edges_cost_more_than_the_worse_one_alone():
    """The whole reason for the change. A path across a town is not one
    obstacle: over Kızılay at 6 m to 1,5 m, of 215 links between 200 m
    and 1,2 km only 15 % are clear, the median has three edges blocking
    it and the worst has sixteen. Taking the worst of those and
    forgetting the rest is optimistic exactly where the urban row is.
    """
    from yerkon.rf import bullington_db

    one = list(a_plain())
    one[20] = (20 / 64, 8.0)
    two = list(one)
    two[44] = (44 / 64, 8.0)

    alone = bullington_db(tuple(one), 6.0, 1.5, 1000.0, 2450e6, curved=False)
    both = bullington_db(tuple(two), 6.0, 1.5, 1000.0, 2450e6, curved=False)
    assert both > alone + 1.0, (alone, both)


def test_a_path_with_nothing_in_it_pays_almost_nothing():
    from yerkon.rf import bullington_db, delta_bullington_db

    high = a_plain(0.0)
    assert bullington_db(high, 60.0, 60.0, 1000.0, 2450e6) < 0.5
    assert delta_bullington_db(high, 60.0, 60.0, 1000.0, 2450e6) < 1.0


def test_a_grazing_path_is_answered_rather_than_divided_by_zero():
    """The two steepest lines are parallel and never cross, so there is
    no equivalent edge to place. It is a real arrangement — an obstacle
    exactly on the line between the ends — and it used to raise."""
    from yerkon.rf import bullington_db

    grazing = list(a_plain())
    grazing[32] = (0.5, 3.75)           # the midpoint of a 6 m -> 1,5 m line
    said = bullington_db(tuple(grazing), 6.0, 1.5, 1000.0, 2450e6,
                         curved=False)
    assert said > 6.0, "an edge on the line is not a clear path"
    assert math.isfinite(said)


def test_a_smooth_earth_still_gets_in_the_way_over_a_long_path():
    """What the equivalent-edge construction cannot see: a profile with
    no edge in it has no edge to stand for, and over twenty kilometres
    the thing in the way is the planet. ITU-R P.526-15 4.2."""
    from yerkon.rf import bullington_db, delta_bullington_db, spherical_earth_db

    flat = a_plain()
    assert bullington_db(flat, 25.0, 1.5, 20_000.0, 2450e6) < 12.0
    far = delta_bullington_db(flat, 25.0, 1.5, 20_000.0, 2450e6)
    assert far > 15.0, far

    # It grows with distance and shrinks with height, both of which are
    # the whole point of a mast.
    assert (spherical_earth_db(30_000.0, 25.0, 1.5, 2450e6)
            > spherical_earth_db(20_000.0, 25.0, 1.5, 2450e6))
    assert (spherical_earth_db(20_000.0, 50.0, 1.5, 2450e6)
            < spherical_earth_db(20_000.0, 25.0, 1.5, 2450e6))
    assert spherical_earth_db(500.0, 6.0, 1.5, 2450e6) < 1.0


def test_the_delta_never_takes_loss_away():
    """It is `max(smooth earth - the same construction over a smooth
    earth, 0)`, so the real profile's answer is a floor."""
    from yerkon.rf import bullington_db, delta_bullington_db

    rough = list(a_plain())
    rough[16] = (0.25, 12.0)
    rough[40] = (40 / 64, 7.0)
    for distance_m in (800.0, 5000.0, 20_000.0):
        over_ground = bullington_db(tuple(rough), 20.0, 1.5, distance_m, 2450e6)
        with_delta = delta_bullington_db(tuple(rough), 20.0, 1.5, distance_m,
                                         2450e6)
        assert with_delta >= over_ground - 1e-9, distance_m


def test_the_budget_reads_the_ground_when_it_is_given_some():
    """And falls back to the single worst point when it is not: an
    Obstruction built by hand out of two numbers has no ground to walk
    along, and one edge is then the honest reading of what it says."""
    from dataclasses import replace

    ridge = list(a_plain())
    ridge[24] = (24 / 64, 30.0)
    ridge[40] = (40 / 64, 30.0)
    carried = Obstruction(peak_terrain_m=30.0, peak_at_fraction=24 / 64,
                          profile=tuple(ridge))

    over_ground = evaluate_link(mast(25.0), vehicle(2000.0),
                                obstruction=carried)
    one_point = evaluate_link(mast(25.0), vehicle(2000.0),
                              obstruction=replace(carried, profile=()))
    assert over_ground.diffraction_loss_db > one_point.diffraction_loss_db
    assert one_point.diffraction_loss_db > 0.0, "the single edge still works"


def test_one_piece_of_ground_is_charged_once():
    """ADR-0058. The link pays the larger of the two excesses over free
    space, not their sum.

    Ground reflection and diffraction describe the same ground doing two
    things to the same link, and adding them charges the link twice.
    They also do not happen together: the cancellation two-ray describes
    needs a direct ray to cancel, and where a ridge blocks the path
    there is no direct ray.

    Over eight kilometres from a 20 m mast to a 2 m receiver, both cases
    are worked here. Over the plane the reflection costs 15,7 dB and the
    curvature 6,1, and the link pays 15,7. Put a 25 m ridge at the
    midpoint and the diffraction rises to 27,1 while the reflection is
    unchanged, and the link pays 27,1. Summed it would have paid 42,8.
    """
    from yerkon.rf import free_space_path_loss_db, two_ray_path_loss_db

    distance_m = 8000.0
    clear = Obstruction(peak_terrain_m=0.0, peak_at_fraction=0.5,
                        profile=a_plain())
    ridge_profile = list(a_plain())
    ridge_profile[32] = (0.5, 25.0)
    blocked = Obstruction(peak_terrain_m=25.0, peak_at_fraction=0.5,
                          profile=tuple(ridge_profile))

    free_space_db = free_space_path_loss_db(distance_m, 2450e6)
    reflection_db = two_ray_path_loss_db(
        distance_m, 20.0, 2.0, 2450e6) - free_space_db

    over_the_plane = evaluate_link(mast(20.0), vehicle(distance_m),
                                   obstruction=clear)
    over_the_ridge = evaluate_link(mast(20.0), vehicle(distance_m),
                                   obstruction=blocked)

    # Both terms are real in both cases, which is what makes the sum
    # tempting and wrong.
    assert reflection_db > 10.0, reflection_db
    assert over_the_plane.diffraction_loss_db > 4.0
    assert over_the_ridge.diffraction_loss_db > reflection_db

    paid_on_the_plane = over_the_plane.path_loss_db - free_space_db
    paid_on_the_ridge = over_the_ridge.path_loss_db - free_space_db
    assert paid_on_the_plane == pytest.approx(reflection_db, abs=0.01)
    assert paid_on_the_ridge == pytest.approx(
        over_the_ridge.diffraction_loss_db, abs=0.01)

    # And the sum, which is what this replaced, is a different number.
    assert paid_on_the_ridge < (
        reflection_db + over_the_ridge.diffraction_loss_db) - 10.0


def test_real_ground_is_read_from_the_terrain_rather_than_summarised():
    """The terrain hands the whole profile to the budget, so the roofs a
    fetched site folds into its surface are edges this counts."""
    from yerkon.viewer.state import from_scenario

    state = from_scenario("urban")
    ground = state.terrain()
    here = (300.0, 1500.0, ground.height_at(300.0, 1500.0) + 6.0)
    there = (1500.0, 1500.0, ground.height_at(1500.0, 1500.0) + 1.5)
    obstruction = ground.obstruction_between(here, there)

    assert len(obstruction.profile) > 32, "the ground travels with it"
    assert obstruction.profile[0][0] == 0.0
    assert obstruction.profile[-1][0] == pytest.approx(1.0)


def test_the_construction_is_the_recommendation_s_arithmetic():
    """One edge, worked by hand against ITU-R P.526-15 4.5.1.

    A single obstacle is the case where Bullington's construction must
    land on the obstacle itself, so the answer is checkable without the
    construction: v from the Fresnel parameter, J(v) from equation (31),
    and the Recommendation's own empirical term on top.
    """
    from yerkon.rf import bullington_db, knife_edge_db

    wavelength_m = 299792458.0 / 2450e6
    above_the_line = 30.0 - (25.0 + 2.0) / 2.0
    v = above_the_line * math.sqrt(
        2.0 / wavelength_m * 2000.0 / (1000.0 * 1000.0))
    plain = knife_edge_db(v)
    by_hand = plain + (1.0 - math.exp(-plain / 6.0)) * (10.0 + 0.02 * 2.0)

    profile = [(i / 64, 0.0) for i in range(65)]
    profile[32] = (0.5, 30.0)
    said = bullington_db(tuple(profile), 25.0, 2.0, 2000.0, 2450e6,
                         curved=False)

    assert v == pytest.approx(2.983, abs=0.001)
    assert said == pytest.approx(by_hand, abs=0.01)
    assert said == pytest.approx(32.17, abs=0.05)

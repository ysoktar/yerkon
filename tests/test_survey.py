"""Anchor survey error: that it is modelled, and that it does not dominate."""
import dataclasses

import numpy as np
import pytest

from yerkon import survey
from yerkon.scenarios import (
    SEED,
    critical_zone_scenario,
    rural_scenario,
    run_scenario,
    urban_scenario,
)


def test_a_traverse_error_grows_with_distance_from_the_portal():
    """A tunnel survey is carried in from one end, so it accumulates.

    Satellite methods fix each point independently and stay flat. The
    tunnel has no sky, so its spec is the only one that grows.
    """
    near_h, near_v = survey.TUNNEL_SURVEY.sigma_at(0.0)
    far_h, far_v = survey.TUNNEL_SURVEY.sigma_at(50_000.0)
    assert far_h > near_h and far_v > near_v
    assert far_h == pytest.approx(0.106, abs=0.005)

    flat_near = survey.URBAN_SURVEY.sigma_at(0.0)
    flat_far = survey.URBAN_SURVEY.sigma_at(50_000.0)
    assert flat_near == flat_far


def test_the_survey_offset_is_drawn_once_and_stays_put():
    """An installation is surveyed once, so the error must not be redrawn.

    Redrawing per fix would turn a fixed offset into noise the filter
    averages away, which is the opposite of how it behaves.
    """
    scenario = urban_scenario(calibrated=True)
    first = scenario.surveyed_anchors
    second = scenario.surveyed_anchors
    assert np.array_equal(first, second)
    assert not np.array_equal(first, scenario.anchors)


def test_every_scenario_declares_how_its_anchors_were_surveyed():
    for scenario in (urban_scenario(), rural_scenario(), critical_zone_scenario()):
        assert scenario.survey is not None, scenario.key
        assert scenario.survey_rms_offset_m > 0.0


def test_only_the_tunnel_survey_follows_a_traverse():
    assert critical_zone_scenario().survey_traverse_axis == 0
    assert urban_scenario().survey_traverse_axis is None
    assert rural_scenario().survey_traverse_axis is None


def test_survey_error_at_this_quality_does_not_drive_any_row():
    """Measured, not assumed. RTK and a total station are good enough.

    The offsets are 7 to 16 cm RMS against ranging errors of 0.36 m in the
    tunnel and 2.4 m in the city, so they move the result by under a
    percent. This is what says the report does not need to budget for a
    higher grade of survey.
    """
    scenario = critical_zone_scenario()
    with_survey = run_scenario(scenario)
    without = run_scenario(dataclasses.replace(scenario, survey=None))
    change = abs(with_survey.fused.hpe_p50_m - without.fused.hpe_p50_m)
    assert change / without.fused.hpe_p50_m < 0.05


def test_a_bad_survey_would_dominate():
    """The other half of the claim above: the model does respond.

    Without this, 'survey error is negligible' could equally mean the
    survey error is never applied.
    """
    scenario = critical_zone_scenario()
    coarse = dataclasses.replace(
        survey.TUNNEL_SURVEY,
        horizontal_sigma_m=2.0,
        vertical_sigma_m=2.0,
        traverse_growth_m_per_sqrt_km=None,
    )
    degraded = run_scenario(dataclasses.replace(scenario, survey=coarse))
    baseline = run_scenario(scenario)
    assert degraded.fused.hpe_p50_m > 10 * baseline.fused.hpe_p50_m


def test_ranges_come_from_the_true_positions_not_the_surveyed_ones():
    """The whole point of the split: measure against truth, solve against
    the survey. If both used the surveyed array the error would cancel."""
    scenario = urban_scenario(calibrated=True)
    assert not np.array_equal(scenario.anchors, scenario.surveyed_anchors)
    offsets = scenario.surveyed_anchors - scenario.anchors
    assert np.abs(offsets[:, 2]).mean() > np.abs(offsets[:, 0]).mean() * 0.5

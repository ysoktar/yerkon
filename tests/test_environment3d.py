"""3D environment variables and the Poisson coverage planning approximation.

rho_3D and the Poisson mu formula are explicitly a planning approximation,
not a claim about achieved geometry validity.
"""
import pytest

from locbench3d.environment.environment3d import (
    Environment3D,
    anchor_density_3d,
    poisson_expected_anchors_in_range,
)


def test_environment_derives_area_and_volume():
    env = Environment3D(
        environment_id="env-1",
        width_m=10.0,
        length_m=20.0,
        height_m=3.0,
        floor_count=1,
        floor_height_m=3.0,
        indoor_outdoor="indoor",
        environment_class="office",
        los_fraction=0.8,
        nlos_fraction=0.2,
    )
    assert env.floor_area_m2 == pytest.approx(200.0)
    assert env.volume_m3 == pytest.approx(600.0)


def test_los_and_nlos_fraction_must_be_consistent():
    with pytest.raises(ValueError):
        Environment3D(
            environment_id="bad",
            width_m=1.0,
            length_m=1.0,
            height_m=1.0,
            floor_count=1,
            floor_height_m=1.0,
            indoor_outdoor="indoor",
            environment_class="test",
            los_fraction=0.9,
            nlos_fraction=0.9,
        )


def test_anchor_density_3d_is_count_over_volume():
    density = anchor_density_3d(n_anchors=12, volume_m3=600.0)
    assert density == pytest.approx(12 / 600.0)


def test_poisson_expected_anchors_in_range_is_planning_approximation():
    density = anchor_density_3d(n_anchors=12, volume_m3=600.0)
    mu = poisson_expected_anchors_in_range(density_3d=density, radius_m=10.0)
    import math

    expected = density * (4.0 / 3.0) * math.pi * 10.0**3
    assert mu == pytest.approx(expected)


def test_anchors_per_square_meter_and_cubic_meter_both_retained():
    env = Environment3D(
        environment_id="env-2",
        width_m=10.0,
        length_m=10.0,
        height_m=4.0,
        floor_count=1,
        floor_height_m=4.0,
        indoor_outdoor="indoor",
        environment_class="warehouse",
        los_fraction=1.0,
        nlos_fraction=0.0,
        anchor_count=8,
    )
    assert env.anchors_per_sqm == pytest.approx(8 / 100.0)
    assert env.anchors_per_cubic_m == pytest.approx(8 / 400.0)

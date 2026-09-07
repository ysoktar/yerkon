import numpy as np
import pytest

from yerkon.evidence import EvidenceRecord, EvidenceType
from yerkon.path import straight_line_path
from yerkon.simulate import (
    RangingMethod,
    anchors_in_range,
    simulate_path_fixes,
    solve_position_3d,
)

EVIDENCE = EvidenceRecord(
    evidence_type=EvidenceType.SIMULATED_MONTE_CARLO,
    source_name="test",
    source_scope="Fixture for unit tests only.",
)

BOX = np.array(
    [[0.0, 0.0, 8.0], [100.0, 0.0, 20.0], [0.0, 100.0, 35.0],
     [100.0, 100.0, 12.0], [50.0, 50.0, 30.0]]
)


def zero_error(n):
    return np.zeros(n)


def test_solver_recovers_the_true_position_from_clean_ranges():
    truth = np.array([30.0, 40.0, 2.0])
    ranges = np.linalg.norm(BOX - truth[None, :], axis=1)
    estimate, ok = solve_position_3d(BOX, ranges)
    assert ok
    assert estimate == pytest.approx(truth, abs=1e-3)


def test_solver_estimates_height_jointly_not_as_a_second_pass():
    # A tag well below the anchors must still come out at the right height.
    truth = np.array([50.0, 50.0, -15.0])
    ranges = np.linalg.norm(BOX - truth[None, :], axis=1)
    estimate, ok = solve_position_3d(BOX, ranges)
    assert ok
    assert estimate[2] == pytest.approx(-15.0, abs=1e-3)


def test_anchors_beyond_the_link_range_do_not_take_part_in_a_fix():
    anchors = np.array([[0.0, 0.0, 5.0], [10.0, 0.0, 5.0], [5000.0, 0.0, 5.0]])
    mask = anchors_in_range(np.zeros(3), anchors, max_range_m=100.0)
    assert mask.tolist() == [True, True, False]


def test_no_range_limit_reaches_every_anchor():
    anchors = np.array([[0.0, 0.0, 5.0], [50_000.0, 0.0, 5.0]])
    assert anchors_in_range(np.zeros(3), anchors, None).all()


def test_a_position_with_too_few_anchors_in_range_is_a_coverage_gap():
    # Two clusters far apart: the path point sits by the first cluster, so
    # the far cluster must not rescue the fix.
    anchors = np.array(
        [[0.0, 0.0, 8.0], [20.0, 0.0, 9.0], [10_000.0, 0.0, 8.0],
         [10_020.0, 0.0, 9.0], [10_040.0, 20.0, 12.0], [10_010.0, 30.0, 20.0]]
    )
    path = straight_line_path("p", (5.0, 5.0, 1.5), (5.0, 5.0, 1.5), 1, 1.0)
    fixes = simulate_path_fixes(
        scenario_id="gap",
        anchors=anchors,
        path=path,
        error_sampler=zero_error,
        evidence=EVIDENCE,
        n_repeats=5,
        max_range_m=500.0,
    )
    assert all(f.out_of_coverage for f in fixes)
    assert not any(f.success for f in fixes)
    assert all(f.anchors_in_range == 2 for f in fixes)


def test_poor_geometry_still_produces_a_fix_rather_than_a_coverage_gap():
    # A receiver among nearly coplanar anchors gets a bad position, not no
    # position. Refusing to solve would move that error out of the accuracy
    # columns and hide it in the availability column.
    flat = np.array([[0.0, 0.0, 6.0], [200.0, 0.0, 6.0],
                     [0.0, 200.0, 6.0], [200.0, 200.0, 6.0]])
    path = straight_line_path("p", (100.0, 100.0, 1.5), (100.0, 100.0, 1.5), 1, 1.0)
    fixes = simulate_path_fixes(
        scenario_id="flat",
        anchors=flat,
        path=path,
        error_sampler=lambda n: np.full(n, 0.5),
        evidence=EVIDENCE,
        n_repeats=3,
        max_range_m=1000.0,
    )
    assert all(not f.out_of_coverage for f in fixes)
    assert all(f.success for f in fixes)
    assert all(not f.geometry_valid for f in fixes)


def test_undelivered_attempts_are_kept_as_failures_not_dropped():
    path = straight_line_path("p", (30.0, 30.0, 1.5), (60.0, 60.0, 1.5), 4, 10.0)
    fixes = simulate_path_fixes(
        scenario_id="loss",
        anchors=BOX,
        path=path,
        error_sampler=zero_error,
        evidence=EVIDENCE,
        n_repeats=50,
        seed=7,
        delivery_probability=0.5,
    )
    assert len(fixes) == 4 * 50
    assert any(f.timeout for f in fixes)
    assert all(f.estimated_x is None for f in fixes if f.timeout)


def test_the_same_seed_reproduces_the_same_fixes():
    path = straight_line_path("p", (30.0, 30.0, 1.5), (60.0, 60.0, 1.5), 3, 10.0)
    kwargs = dict(
        scenario_id="repeat",
        anchors=BOX,
        path=path,
        error_sampler=lambda n: np.random.default_rng(1).normal(0, 1, n),
        evidence=EVIDENCE,
        n_repeats=10,
        seed=99,
        delivery_probability=0.8,
    )
    first = simulate_path_fixes(**kwargs)
    second = simulate_path_fixes(**kwargs)
    assert [f.to_dict() for f in first] == [f.to_dict() for f in second]


def test_three_anchors_are_rejected_as_a_minimum_for_a_3d_fix():
    path = straight_line_path("p", (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), 2, 1.0)
    with pytest.raises(ValueError):
        simulate_path_fixes(
            scenario_id="bad",
            anchors=BOX,
            path=path,
            error_sampler=zero_error,
            evidence=EVIDENCE,
            minimum_anchors=3,
        )


def test_only_two_way_ranging_methods_exist():
    assert {m.value for m in RangingMethod} == {"SS_TWR", "DS_TWR"}


def test_a_receiver_ranges_to_the_nearest_anchors_not_to_every_audible_one():
    from yerkon.simulate import select_anchors

    anchors = np.array(
        [[0.0, 0.0, 8.0], [10.0, 0.0, 9.0], [20.0, 0.0, 10.0],
         [30.0, 0.0, 11.0], [400.0, 0.0, 12.0], [450.0, 0.0, 13.0]]
    )
    chosen = select_anchors(np.zeros(3), anchors, max_range_m=1000.0, max_anchors=4)
    assert len(chosen) == 4
    assert chosen[:, 0].max() == 30.0


def test_the_anchor_cap_never_reaches_past_the_link_range():
    from yerkon.simulate import select_anchors

    anchors = np.array(
        [[0.0, 0.0, 8.0], [10.0, 0.0, 9.0], [5000.0, 0.0, 10.0], [6000.0, 0.0, 11.0]]
    )
    chosen = select_anchors(np.zeros(3), anchors, max_range_m=100.0, max_anchors=4)
    assert len(chosen) == 2

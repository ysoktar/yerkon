"""Multi-objective Pareto analysis.

Infeasible scenarios must never be ranked ahead of feasible ones by score,
and domination/front information must be retained, not just a single
composite number.
"""
import pytest

from locbench3d.pareto.pareto import Objective, compute_pareto


def test_dominated_point_is_not_pareto_optimal():
    records = [
        {"cost": 100.0, "p95": 1.0},  # dominates the next
        {"cost": 200.0, "p95": 2.0},  # dominated
    ]
    objectives = [Objective("cost", minimize=True), Objective("p95", minimize=True)]
    results = compute_pareto(records, [True, True], objectives)
    assert results[0].pareto_optimal is True
    assert results[1].pareto_optimal is False
    assert 0 in results[1].dominated_by


def test_non_dominated_tradeoff_points_are_both_optimal():
    records = [
        {"cost": 100.0, "p95": 2.0},  # cheap, less accurate
        {"cost": 200.0, "p95": 1.0},  # expensive, more accurate
    ]
    objectives = [Objective("cost", minimize=True), Objective("p95", minimize=True)]
    results = compute_pareto(records, [True, True], objectives)
    assert results[0].pareto_optimal is True
    assert results[1].pareto_optimal is True


def test_infeasible_scenario_is_excluded_from_the_front_regardless_of_score():
    records = [
        {"cost": 1.0, "p95": 0.01},  # best score, but infeasible
        {"cost": 200.0, "p95": 2.0},  # only feasible option
    ]
    objectives = [Objective("cost", minimize=True), Objective("p95", minimize=True)]
    results = compute_pareto(records, [False, True], objectives)
    assert results[0].pareto_optimal is False
    assert results[0].pareto_front_index is None
    assert results[1].pareto_optimal is True
    assert results[1].pareto_front_index == 0


def test_maximize_objective_direction_is_respected():
    records = [
        {"availability": 0.99},
        {"availability": 0.90},
    ]
    objectives = [Objective("availability", minimize=False)]
    results = compute_pareto(records, [True, True], objectives)
    assert results[0].pareto_optimal is True
    assert results[1].pareto_optimal is False


def test_front_index_layers_are_peeled_in_order():
    records = [
        {"x": 1.0, "y": 1.0},  # front 0
        {"x": 2.0, "y": 2.0},  # dominated by first -> front 1
        {"x": 3.0, "y": 3.0},  # dominated by both -> front 2
    ]
    objectives = [Objective("x", minimize=True), Objective("y", minimize=True)]
    results = compute_pareto(records, [True, True, True], objectives)
    assert [r.pareto_front_index for r in results] == [0, 1, 2]


def test_weighted_score_is_optional_and_secondary():
    records = [{"cost": 100.0, "p95": 1.0}, {"cost": 50.0, "p95": 2.0}]
    objectives = [Objective("cost", minimize=True), Objective("p95", minimize=True)]
    results = compute_pareto(
        records, [True, True], objectives, weights={"cost": 0.5, "p95": 0.5}
    )
    for r in results:
        assert r.weighted_score is not None


def test_weighted_score_absent_when_no_weights_given():
    records = [{"cost": 100.0, "p95": 1.0}]
    objectives = [Objective("cost", minimize=True), Objective("p95", minimize=True)]
    results = compute_pareto(records, [True], objectives)
    assert results[0].weighted_score is None

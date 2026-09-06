"""Multi-objective Pareto analysis.

Only feasible records participate in dominance/front computation.
Infeasible records are always excluded from the front (``pareto_front_index
= None``, ``pareto_optimal = False``) regardless of how good their raw
objective values look, so an infeasible configuration can never rank ahead
of a feasible one through this mechanism. A weighted score is computed
only when the caller supplies weights, and is documented as secondary to
the Pareto front, never a replacement for it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Objective:
    name: str
    minimize: bool = True


@dataclass(frozen=True)
class ParetoResult:
    index: int
    feasible: bool
    pareto_optimal: bool
    pareto_front_index: Optional[int]
    dominated_by: list[int] = field(default_factory=list)
    normalized_score: Optional[float] = None
    weighted_score: Optional[float] = None


def _direction(value: float, minimize: bool) -> float:
    return value if minimize else -value


def _dominates(a: dict, b: dict, objectives: list[Objective]) -> bool:
    """True if record a dominates record b (at least as good everywhere,
    strictly better somewhere), all objectives converted to "smaller is better"."""
    at_least_as_good = True
    strictly_better = False
    for obj in objectives:
        va = _direction(a[obj.name], obj.minimize)
        vb = _direction(b[obj.name], obj.minimize)
        if va > vb:
            at_least_as_good = False
            break
        if va < vb:
            strictly_better = True
    return at_least_as_good and strictly_better


def compute_pareto(
    records: list[dict],
    feasible_flags: list[bool],
    objectives: list[Objective],
    weights: Optional[dict[str, float]] = None,
) -> list[ParetoResult]:
    if len(records) != len(feasible_flags):
        raise ValueError("records and feasible_flags must be the same length")

    n = len(records)
    feasible_indices = [i for i in range(n) if feasible_flags[i]]

    dominated_by: dict[int, list[int]] = {i: [] for i in range(n)}
    for i in feasible_indices:
        for j in feasible_indices:
            if i == j:
                continue
            if _dominates(records[j], records[i], objectives):
                dominated_by[i].append(j)

    # Onion-peel into fronts among feasible records only.
    front_index: dict[int, int] = {}
    remaining = set(feasible_indices)
    current_front = 0
    while remaining:
        this_front = [
            i for i in remaining
            if not any(d in remaining for d in dominated_by[i])
        ]
        if not this_front:
            # Numerical/cycle edge case guard; assign the rest to one final front.
            this_front = list(remaining)
        for i in this_front:
            front_index[i] = current_front
        remaining -= set(this_front)
        current_front += 1

    normalized_scores: dict[int, float] = {}
    weighted_scores: dict[int, Optional[float]] = {i: None for i in range(n)}
    if weights and feasible_indices:
        for obj in objectives:
            values = [_direction(records[i][obj.name], obj.minimize) for i in feasible_indices]
            lo, hi = min(values), max(values)
            span = hi - lo if hi > lo else 1.0
            for i in feasible_indices:
                normalized = (_direction(records[i][obj.name], obj.minimize) - lo) / span
                normalized_scores.setdefault(i, 0.0)
                normalized_scores[i] += normalized * weights.get(obj.name, 0.0)
        for i in feasible_indices:
            weighted_scores[i] = normalized_scores[i]

    results = []
    for i in range(n):
        if i not in feasible_indices:
            results.append(
                ParetoResult(
                    index=i,
                    feasible=False,
                    pareto_optimal=False,
                    pareto_front_index=None,
                    dominated_by=[],
                    weighted_score=None,
                )
            )
        else:
            results.append(
                ParetoResult(
                    index=i,
                    feasible=True,
                    pareto_optimal=(front_index[i] == 0),
                    pareto_front_index=front_index[i],
                    dominated_by=dominated_by[i],
                    weighted_score=weighted_scores[i],
                )
            )
    return results

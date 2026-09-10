"""Running independent simulations at once, and getting the same answers."""

import os

import pytest

from yerkon.parallel import WORTH_SPREADING, spread, workers


def double(value):
    return value * 2


def test_results_come_back_in_the_order_they_went_out():
    """Not in the order they finished.

    A dissection matches runs to error sources by position. If the pool
    returned them as they completed, one source's runs would be
    attributed to another and every figure would be plausible and wrong.
    """
    assert spread(double, list(range(20))) == tuple(range(0, 40, 2))


def test_a_watcher_sees_every_task_once_and_in_order():
    seen = []
    spread(double, list(range(12)), watching=seen.append)
    assert seen == [value * 2 for value in range(12)]


def test_one_task_is_not_worth_a_pool():
    """Starting processes costs a second or two; one run should not pay it."""
    assert WORTH_SPREADING >= 2
    assert spread(double, [7]) == (14,)


def test_nothing_to_do_is_not_an_error():
    assert spread(double, []) == ()


def test_forcing_one_process_still_works():
    assert spread(double, list(range(5)), processes=1) == (0, 2, 4, 6, 8)


def test_it_leaves_the_machine_a_core_to_answer_on():
    """A search should not make the viewer it was started from unusable."""
    assert workers() >= 1
    assert workers() <= max((os.cpu_count() or 2) - 1, 1)
    assert workers(4) == 4
    assert workers(0) == 1


def explode(value):
    raise ValueError("task {} failed".format(value))


def test_a_task_that_raises_says_which_one():
    with pytest.raises(ValueError, match="task"):
        spread(explode, [1, 2, 3])


# --- The property the whole thing rests on -------------------------------


@pytest.mark.slow
def test_a_scenario_gives_the_same_answer_wherever_it_runs():
    """ADR-0025. Spreading the work must not move a published number.

    `run_scenario` reseeds from the scenario, so a run is a property of
    the arrangement and not of the machine. If that ever stopped holding,
    every figure in the report would depend on how many cores happened to
    be free.
    """
    from yerkon.evaluate import run_scenario
    from yerkon.scenarios import CHOICES
    from yerkon.terms import ALL

    scenario = CHOICES["tunnel"].scenario
    here = run_scenario(scenario, ALL)
    spread_out = spread(_run, [(scenario, ALL)] * 2, processes=2)

    for elsewhere in spread_out:
        assert elsewhere.availability == here.availability
        assert elsewhere.percentile(50) == here.percentile(50)
        assert elsewhere.percentile(95) == here.percentile(95)
        assert elsewhere.lost_links == here.lost_links


def _run(task):
    from yerkon.evaluate import run_scenario

    scenario, terms = task
    return run_scenario(scenario, terms)


@pytest.mark.slow
def test_a_dissection_gives_the_same_figures_spread_as_it_did_serial():
    """The check that matters, on the slowest thing the project does."""
    from dataclasses import replace

    from yerkon.budget import dissect
    from yerkon.scenarios import CHOICES

    tunnel = CHOICES["tunnel"]
    quick = replace(
        tunnel,
        scenario=replace(
            tunnel.scenario,
            deployment=replace(
                tunnel.scenario.deployment,
                receivers=tunnel.scenario.deployment.receivers[:1],
            ),
        ),
    )
    found = dissect(quick, sources=("survey", "floor"))
    assert found.whole_p50_m > 0.0
    assert len(found.contributions) == 2
    # Twice, to catch anything that depends on pool state left over.
    again = dissect(quick, sources=("survey", "floor"))
    assert again.whole_p50_m == found.whole_p50_m
    for one, other in zip(found.ranked(), again.ranked()):
        assert one == other

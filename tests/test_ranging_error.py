import numpy as np
import pytest

from yerkon.evidence import EvidenceRecord, EvidenceType
from yerkon.ranging_error import (
    ROBINSON_OBSERVATIONS,
    ROBINSON_VALID_RANGE_M,
    add_nlos,
    build_dwm3000_model,
    build_sx1280_model,
    robinson_errors_m,
)


def test_published_errors_match_the_source_observations():
    assert robinson_errors_m() == pytest.approx((4.4, 7.6, 3.0, -2.0, 1.0, 3.0))
    assert len(ROBINSON_OBSERVATIONS) == 6


def test_calibration_removes_the_mean_bias_and_keeps_the_spread():
    raw = build_sx1280_model(seed=1, calibrated=False)
    calibrated = build_sx1280_model(seed=1, calibrated=True)
    raw_pop = np.array(raw.population_errors_m)
    cal_pop = np.array(calibrated.population_errors_m)

    assert raw_pop.mean() == pytest.approx(2.8333, abs=1e-3)
    assert cal_pop.mean() == pytest.approx(0.0, abs=1e-9)
    # Calibration removes an offset. It cannot make the hardware quieter.
    assert cal_pop.std() == pytest.approx(raw_pop.std(), abs=1e-9)


def test_the_uncalibrated_model_declares_its_bias():
    raw = build_sx1280_model(seed=1, calibrated=False)
    assert raw.mean_bias_m == pytest.approx(2.8333, abs=1e-3)
    assert "2.83" in raw.evidence.caveats


def test_sx1280_model_is_labelled_as_calibrated_against_hardware():
    model = build_sx1280_model(seed=1)
    assert model.evidence.evidence_type is EvidenceType.HARDWARE_CALIBRATED_MODEL
    assert "250 m" in model.evidence.source_scope


def test_dwm3000_model_is_not_labelled_as_hardware_calibrated():
    # No calibrated DWM3000 data was available. The model is a design
    # target expressed as a distribution, and the evidence type has to say
    # so or the tunnel row would read as measured.
    model = build_dwm3000_model(seed=1)
    assert model.evidence.evidence_type is EvidenceType.SIMULATED_MONTE_CARLO
    assert model.population_errors_m is None


def test_dwm3000_sigma_matches_its_configured_value():
    model = build_dwm3000_model(seed=3, sigma_m=0.03, nlos_probability=0.0)
    assert model.sigma_m(20000) == pytest.approx(0.03, rel=0.1)


def test_nlos_bias_only_shifts_a_fraction_of_links():
    base = build_dwm3000_model(seed=5, sigma_m=0.01, nlos_probability=0.0)
    biased = add_nlos(base, seed=5, nlos_probability=0.5, nlos_bias_m=10.0)
    sample = biased.sample(20000)
    # Half the links should sit near zero and half near the bias.
    assert np.mean(sample > 5.0) == pytest.approx(0.5, abs=0.05)


def test_nlos_layer_records_that_it_is_an_assumption():
    model = add_nlos(build_sx1280_model(seed=2), seed=2,
                     nlos_probability=0.35, nlos_bias_m=1.5)
    assert "assumption" in model.evidence.caveats
    # The underlying evidence type is unchanged: the measured distribution
    # is still measured, the NLOS layer is declared in the caveats.
    assert model.evidence.evidence_type is EvidenceType.HARDWARE_CALIBRATED_MODEL


def test_calibrated_range_envelope_is_the_one_the_source_covers():
    assert ROBINSON_VALID_RANGE_M == (0.0, 250.0)


def test_evidence_without_a_scope_is_refused():
    with pytest.raises(ValueError):
        EvidenceRecord(
            evidence_type=EvidenceType.ENGINEERING_ASSUMPTION,
            source_name="something",
            source_scope="",
        )


def test_a_model_can_be_reseeded_so_two_runs_agree():
    """The sampler closes over a generator, so it carries state.

    Without reseeding, the second scenario in a process draws from
    wherever the first one stopped, and two runs of the same scenario
    disagree. Every swept comparison in docs/ depends on this holding.
    """
    model = build_sx1280_model(seed=3, calibrated=True)
    first = model.sample(500)
    drifted = model.sample(500)
    assert not np.allclose(first, drifted), "sampler must be stateful"

    again = model.reseed(3).sample(500)
    assert np.allclose(first, again)


def test_reseeding_survives_the_nlos_wrapper():
    base = build_sx1280_model(seed=5, calibrated=True)
    layered = add_nlos(base, seed=11, nlos_probability=0.4, nlos_bias_m=2.0)
    assert layered.respawn is not None, "the wrapper must know how to rebuild"

    # Reseeding rebuilds the whole chain from one seed, so it does not
    # reproduce a model whose two layers were seeded separately. What
    # run_scenario needs is weaker and is what this checks: reseeding to
    # the same value twice gives the same draws, whatever state the
    # sampler was left in.
    first = layered.reseed(7).sample(4000)
    layered.sample(4000)
    assert np.allclose(layered.reseed(7).sample(4000), first)

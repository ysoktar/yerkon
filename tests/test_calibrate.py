"""Turning a measurement back into a default."""

import pytest

from yerkon.calibrate import READERS, clock_residual, read
from yerkon.settings import DEFAULTS

HEADER = "offset_ppm,snr_db,residual_ppm_rms,single_sided_error_m,reply_s\n"
ROWS = (
    "2,5,0.0912,0.2193,0.016054\n"      # below where the link closes
    "2,10,0.0389,0.0935,0.016054\n"
    "2,40,0.0164,0.0394,0.016054\n"
    "10,10,0.0354,0.0851,0.016054\n"
    "20,10,0.0443,0.1065,0.016054\n"
)


def write(tmp_path, text, name="clock_residual.csv"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_the_figure_taken_is_the_worst_over_the_range_that_closes(tmp_path):
    """Not the best, and not the mean. A default that holds only at the
    strong end of a link fails at the far end, which is the end that
    decides how many anchors a corridor needs."""
    measured = clock_residual(write(tmp_path, HEADER + ROWS))
    assert measured.value == pytest.approx(0.0443)


def test_rows_below_where_the_link_closes_are_left_out(tmp_path):
    """A +5 dB row describes a link nobody has (ADR-0017), and it is the
    worst row in the file, so including it would set the default from a
    condition that never occurs."""
    measured = clock_residual(write(tmp_path, HEADER + ROWS))
    assert measured.value < 0.0912


def test_a_file_with_nothing_usable_says_what_to_re_run(tmp_path):
    text = HEADER + "2,5,0.0912,0.2193,0.016054\n"
    with pytest.raises(ValueError, match="Re-run"):
        clock_residual(write(tmp_path, text))


def test_the_key_it_writes_is_one_the_defaults_file_holds(tmp_path):
    """Otherwise the entry it prints goes nowhere."""
    measured = clock_residual(write(tmp_path, HEADER + ROWS))
    assert measured.key in DEFAULTS.entries


def test_what_it_prints_is_a_settings_entry_that_loads(tmp_path):
    from yerkon.settings import load

    measured = clock_residual(write(tmp_path, HEADER + ROWS))
    entry = measured.as_toml() + '\naffects = "the ranging clock term"\n'
    settings = load(write(tmp_path, entry, "one.toml"))

    assert settings.number(measured.key) == pytest.approx(0.0443)
    assert not settings.entry(measured.key).is_assumed


def test_a_measurement_stops_being_an_assumption(tmp_path):
    measured = clock_residual(write(tmp_path, HEADER + ROWS))
    assert "MEASUREMENT" in measured.as_toml()
    assert "yerkon_clock_residual" in measured.source


def test_the_note_says_what_the_simulation_left_out(tmp_path):
    """Additive noise only. A default that hides that would be read as
    the answer rather than as a floor."""
    measured = clock_residual(write(tmp_path, HEADER + ROWS))
    assert "phase noise" in measured.note
    assert "worse" in measured.note


def test_a_missing_file_says_to_run_the_script(tmp_path):
    with pytest.raises(FileNotFoundError, match="Run the MATLAB script"):
        clock_residual(str(tmp_path / "nothing.csv"))


def test_a_file_missing_a_column_says_which(tmp_path):
    with pytest.raises(ValueError, match="residual_ppm_rms"):
        clock_residual(write(tmp_path, "offset_ppm,snr_db\n2,10\n"))


def test_an_empty_file_is_refused(tmp_path):
    with pytest.raises(ValueError, match="header and no rows"):
        clock_residual(write(tmp_path, HEADER))


def test_a_file_it_does_not_recognise_lists_what_it_reads(tmp_path):
    with pytest.raises(ValueError, match="clock_residual"):
        read(write(tmp_path, HEADER + ROWS, "something_else.csv"))


def test_the_implementation_floor_is_not_offered_as_a_simulation():
    """One chip at 1625 kHz is 184 m of flight, so a waveform simulation
    says the part ranges to about 18 m. It measurably ranges to 2,94 m.
    Shipping a script that contradicts a measurement for a reason already
    understood is worse than shipping none."""
    assert "ranging_floor" not in READERS
    assert set(READERS) == {"clock_residual"}

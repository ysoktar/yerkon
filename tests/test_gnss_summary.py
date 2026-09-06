"""Session-level GNSS summary: fix-state rates and error statistics.

Rates are computed over fixes that actually have a fix_state; a session
with zero fixes must not report a rate of 0 as if it were a measured
value.
"""
import pytest

from locbench3d.gnss.model import FixState, GnssFix, PositioningMode
from locbench3d.metrics.gnss import summarize_gnss_session


def _fix(state, h_err=None, v_err=None):
    return GnssFix(
        fix_state=state,
        positioning_mode=PositioningMode.RTK_FIXED,
        horizontal_error_m=h_err,
        vertical_error_m=v_err,
    )


def test_fix_state_rates_sum_to_one():
    fixes = [
        _fix(FixState.RTK_FIXED),
        _fix(FixState.RTK_FIXED),
        _fix(FixState.RTK_FLOAT),
        _fix(FixState.STANDALONE),
    ]
    summary = summarize_gnss_session(fixes)
    assert summary.rtk_fixed_rate == pytest.approx(0.5)
    assert summary.rtk_float_rate == pytest.approx(0.25)
    assert summary.standalone_rate == pytest.approx(0.25)
    total = summary.rtk_fixed_rate + summary.rtk_float_rate + summary.standalone_rate
    assert total == pytest.approx(1.0)


def test_empty_session_returns_none_not_zero():
    summary = summarize_gnss_session([])
    assert summary.rtk_fixed_rate is None
    assert summary.horizontal_rmse_m is None


def test_horizontal_rmse_ignores_fixes_missing_error():
    fixes = [_fix(FixState.RTK_FIXED, h_err=0.02), _fix(FixState.RTK_FIXED, h_err=None)]
    summary = summarize_gnss_session(fixes)
    assert summary.horizontal_rmse_m == pytest.approx(0.02)

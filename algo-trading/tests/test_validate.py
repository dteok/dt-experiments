"""Tests for algomvp.data.validate.

Each test corrupts clean data in exactly one way and asserts that the
corresponding check notices. That structure matters: if a test broke the data
in three ways at once, a passing result would not tell you which check works.
"""

import pandas as pd

from algomvp.data import validate
from tests.conftest import make_bars


def test_clean_data_reports_no_problems(clean_bars):
    report = validate.validate_bars(clean_bars, "TEST")
    assert report.is_clean, report.summary()
    assert report.row_count == len(clean_bars)


def test_empty_frame_is_reported():
    report = validate.validate_bars(pd.DataFrame(), "TEST")
    assert not report.is_clean
    assert "no rows" in report.problems[0]


def test_duplicate_dates_are_detected(clean_bars):
    corrupted = pd.concat([clean_bars, clean_bars.iloc[[10]]], ignore_index=True)
    report = validate.validate_bars(corrupted, "TEST")
    assert any("duplicate" in problem for problem in report.problems)


def test_negative_price_is_detected(clean_bars):
    corrupted = clean_bars.copy()
    corrupted.loc[5, "close"] = -1.0
    report = validate.validate_bars(corrupted, "TEST")
    assert any("<= 0" in problem for problem in report.problems)


def test_inverted_high_low_is_detected(clean_bars):
    corrupted = clean_bars.copy()
    corrupted.loc[7, "high"] = corrupted.loc[7, "low"] - 1.0
    report = validate.validate_bars(corrupted, "TEST")
    assert any("high < low" in problem for problem in report.problems)


def test_zero_volume_is_detected(clean_bars):
    corrupted = clean_bars.copy()
    corrupted.loc[3, "volume"] = 0
    report = validate.validate_bars(corrupted, "TEST")
    assert any("zero or negative volume" in problem for problem in report.problems)


def test_unexplained_price_jump_is_detected(clean_bars):
    corrupted = clean_bars.copy()
    corrupted.loc[50:, "adj_close"] = corrupted.loc[50:, "adj_close"] * 3
    report = validate.validate_bars(corrupted, "TEST")
    assert any("unexplained move" in problem for problem in report.problems)


def test_correctly_adjusted_split_is_not_flagged(clean_bars):
    """The normal case: raw price halves, adjusted price stays continuous.

    This is what a well-behaved vendor sends for a 2-for-1 split, and the
    check must stay quiet because it reads adjusted prices.
    """
    split = clean_bars.copy()
    split.loc[50, "split_factor"] = 2.0
    split.loc[50:, ["open", "high", "low", "close"]] /= 2

    report = validate.validate_bars(split, "TEST")
    assert not any("unexplained move" in problem for problem in report.problems)


def test_unadjusted_split_is_excused_by_the_split_factor(clean_bars):
    """The imperfect case: the vendor left the split in the adjusted series.

    Both the drop and the rebound must be excused, or the day after every
    split looks like corrupt data.
    """
    split = clean_bars.copy()
    split.loc[50, "split_factor"] = 2.0
    split.loc[50, "adj_close"] /= 2

    report = validate.validate_bars(split, "TEST")
    assert not any("unexplained move" in problem for problem in report.problems)


def test_calendar_gap_is_detected(clean_bars):
    """Deleting a month of history should be noticed, not absorbed."""
    corrupted = clean_bars.drop(index=range(100, 130)).reset_index(drop=True)
    report = validate.validate_bars(corrupted, "TEST")
    assert any("calendar gap" in problem for problem in report.problems)


def test_stale_prices_are_detected(clean_bars):
    corrupted = clean_bars.copy()
    corrupted.loc[20:35, "close"] = 100.0
    report = validate.validate_bars(corrupted, "TEST")
    assert any("unchanged" in problem for problem in report.problems)


def test_validate_many_returns_one_report_per_ticker():
    combined = pd.concat(
        [make_bars("AAA", seed=1), make_bars("BBB", seed=2)], ignore_index=True
    )
    reports = validate.validate_many(combined)
    assert [report.ticker for report in reports] == ["AAA", "BBB"]
    assert all(report.is_clean for report in reports)

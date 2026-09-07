"""Tests for algomvp.universe.pit.

The first two tests are the most valuable in the suite. They assert that a
company which stopped trading in 2021 is present in a 2020 universe and absent
from a 2022 one. That single behaviour is the difference between a backtest
and a fairy tale.
"""

from datetime import date

import pandas as pd

from algomvp.universe import pit
from tests.conftest import make_bars


def test_delisted_company_is_present_before_delisting(catalogue):
    tradeable = pit.filter_catalogue(catalogue)
    members = pit.members_on(tradeable, date(2020, 6, 30))
    assert "GONE" in members


def test_delisted_company_is_absent_after_delisting(catalogue):
    tradeable = pit.filter_catalogue(catalogue)
    members = pit.members_on(tradeable, date(2022, 6, 30))
    assert "GONE" not in members
    assert "ALIVE" in members


def test_company_is_absent_before_it_listed(catalogue):
    tradeable = pit.filter_catalogue(catalogue)
    members = pit.members_on(tradeable, date(2020, 6, 30))
    assert "LATE" not in members
    assert "LATE" in pit.members_on(tradeable, date(2024, 1, 2))


def test_non_us_and_non_equity_rows_are_filtered_out(catalogue):
    tradeable = pit.filter_catalogue(catalogue)
    assert set(tradeable["ticker"]) == {"ALIVE", "GONE", "LATE"}


def test_liquidity_screen_rejects_penny_stocks():
    bars = make_bars("CHEAP", start_price=1.0, periods=300)
    rules = pit.EligibilityRules()
    passing = pit.screen_by_liquidity(bars, date(2021, 1, 1), rules)
    assert passing == []


def test_liquidity_screen_rejects_thin_volume():
    bars = make_bars("THIN", start_price=50.0, volume=1_000, periods=300)
    rules = pit.EligibilityRules()
    passing = pit.screen_by_liquidity(bars, date(2021, 1, 1), rules)
    assert passing == []


def test_liquidity_screen_rejects_short_history():
    bars = make_bars("NEW", periods=30)
    rules = pit.EligibilityRules()
    passing = pit.screen_by_liquidity(bars, date(2020, 3, 1), rules)
    assert passing == []


def test_liquidity_screen_accepts_a_normal_stock():
    bars = make_bars("GOOD", start_price=80.0, volume=3_000_000, periods=400)
    rules = pit.EligibilityRules()
    passing = pit.screen_by_liquidity(bars, date(2021, 6, 1), rules)
    assert passing == ["GOOD"]


def test_screen_ignores_data_after_the_as_of_date():
    """The screen must not see the future, even when the future is on disk.

    The ticker has only 100 bars before the cutoff, which is below the
    252-bar minimum. If the screen accidentally reads the whole frame it will
    see 400 bars and wrongly pass the stock.
    """
    bars = make_bars("FUTURE", start="2020-01-01", periods=400, volume=3_000_000)
    cutoff = bars["date"].iloc[99].date()
    rules = pit.EligibilityRules()
    assert pit.screen_by_liquidity(bars, cutoff, rules) == []


def test_build_universe_combines_listing_and_liquidity(catalogue):
    tradeable = pit.filter_catalogue(catalogue)
    bars = pd.concat(
        [
            make_bars("ALIVE", start="2018-01-01", periods=700, volume=3_000_000),
            make_bars("GONE", start="2018-01-01", periods=700, volume=3_000_000),
        ],
        ignore_index=True,
    )

    before = pit.build_universe(tradeable, bars, date(2020, 6, 30))
    assert before == ["ALIVE", "GONE"]


def test_build_universe_drops_delisted_names_afterwards(catalogue):
    tradeable = pit.filter_catalogue(catalogue)
    bars = pd.concat(
        [
            make_bars("ALIVE", start="2018-01-01", periods=1200, volume=3_000_000),
            make_bars("GONE", start="2018-01-01", periods=1200, volume=3_000_000),
        ],
        ignore_index=True,
    )

    after = pit.build_universe(tradeable, bars, date(2022, 6, 30))
    assert after == ["ALIVE"]

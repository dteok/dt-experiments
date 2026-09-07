"""Shared test fixtures.

Every fixture here builds synthetic data. No test in this project touches the
network, because a test that depends on a vendor's uptime is not a test, it is
a weather report.

The ``@pytest.fixture`` decorator is the only decorator you will meet in the
test suite. It marks a function as a named ingredient: when a test declares an
argument with the same name as a fixture, pytest calls the fixture and passes
the result in. That is all it does.
"""

from datetime import date

import numpy as np
import pandas as pd
import pytest

PRICE_COLUMNS = [
    "ticker",
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "adj_open",
    "adj_high",
    "adj_low",
    "adj_close",
    "adj_volume",
    "dividend_cash",
    "split_factor",
]


def make_bars(
    ticker: str = "TEST",
    start: str = "2020-01-01",
    periods: int = 300,
    start_price: float = 100.0,
    daily_drift: float = 0.0004,
    volume: float = 2_000_000.0,
    seed: int = 42,
) -> pd.DataFrame:
    """Build a synthetic but well-formed frame of daily bars.

    The price path is a random walk with a small upward drift, which is close
    enough to a real equity to exercise the code without pretending to be a
    simulation of anything.

    Args:
        ticker: Symbol to label the rows with.
        start: First business date, as YYYY-MM-DD.
        periods: Number of business days to generate.
        start_price: Opening price of the series.
        daily_drift: Mean daily log return.
        volume: Constant share volume per bar.
        seed: Random seed, so tests are deterministic.

    Returns:
        A frame in the internal bar shape.
    """
    generator = np.random.default_rng(seed)
    dates = pd.bdate_range(start=start, periods=periods)

    shocks = generator.normal(loc=daily_drift, scale=0.012, size=periods)
    closes = start_price * np.exp(np.cumsum(shocks))

    opens = closes * (1 + generator.normal(0, 0.002, periods))
    highs = np.maximum(opens, closes) * (1 + abs(generator.normal(0, 0.003, periods)))
    lows = np.minimum(opens, closes) * (1 - abs(generator.normal(0, 0.003, periods)))

    frame = pd.DataFrame(
        {
            "ticker": ticker,
            "date": dates,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volume,
            "adj_open": opens,
            "adj_high": highs,
            "adj_low": lows,
            "adj_close": closes,
            "adj_volume": volume,
            "dividend_cash": 0.0,
            "split_factor": 1.0,
        }
    )
    return frame[PRICE_COLUMNS]


@pytest.fixture
def clean_bars() -> pd.DataFrame:
    """A single ticker with no data quality problems."""
    return make_bars()


@pytest.fixture
def catalogue() -> pd.DataFrame:
    """A small ticker catalogue including one delisted company.

    GONE is the important row. It stopped trading in 2021, so it must appear
    in a 2020 universe and vanish from a 2022 one. If that behaviour breaks,
    survivorship bias has crept back in.
    """
    return pd.DataFrame(
        {
            "ticker": ["ALIVE", "GONE", "LATE", "FOREIGN", "FUND"],
            "exchange": ["NYSE", "NASDAQ", "NYSE", "LSE", "NASDAQ"],
            "asset_type": ["Stock", "Stock", "Stock", "Stock", "Mutual Fund"],
            "currency": ["USD", "USD", "USD", "GBP", "USD"],
            "start_date": pd.to_datetime(
                ["2010-01-04", "2010-01-04", "2023-06-01", "2010-01-04", "2010-01-04"]
            ),
            "end_date": pd.to_datetime([None, "2021-03-15", None, None, None]),
        }
    )


@pytest.fixture
def as_of_2020() -> date:
    """A date on which the delisted test company was still trading."""
    return date(2020, 6, 30)

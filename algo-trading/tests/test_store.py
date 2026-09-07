"""Tests for algomvp.data.store and the Tiingo payload normaliser.

``tmp_path`` is a pytest built-in fixture giving each test its own throwaway
directory, so nothing here touches the real data folder.
"""

from datetime import date

import pandas as pd
import pytest

from algomvp.data import store
from algomvp.data.tiingo import RateLimiter, normalise_price_payload
from tests.conftest import make_bars

SAMPLE_PAYLOAD = [
    {
        "date": "2023-01-03T00:00:00.000Z",
        "open": 130.28,
        "high": 130.90,
        "low": 124.17,
        "close": 125.07,
        "volume": 112117471,
        "adjOpen": 129.62,
        "adjHigh": 130.24,
        "adjLow": 123.54,
        "adjClose": 124.44,
        "adjVolume": 112117471,
        "divCash": 0.0,
        "splitFactor": 1.0,
    },
    {
        "date": "2023-01-04T00:00:00.000Z",
        "open": 126.89,
        "high": 128.66,
        "low": 125.08,
        "close": 126.36,
        "volume": 89113633,
        "adjOpen": 126.24,
        "adjHigh": 128.00,
        "adjLow": 124.45,
        "adjClose": 125.72,
        "adjVolume": 89113633,
        "divCash": 0.0,
        "splitFactor": 1.0,
    },
]


def test_normalise_renames_columns_and_adds_ticker():
    frame = normalise_price_payload(SAMPLE_PAYLOAD, "aapl")
    assert list(frame["ticker"]) == ["AAPL", "AAPL"]
    assert "adj_close" in frame.columns
    assert "adjClose" not in frame.columns


def test_normalise_strips_timezone_from_dates():
    frame = normalise_price_payload(SAMPLE_PAYLOAD, "AAPL")
    assert frame["date"].dt.tz is None
    assert frame["date"].iloc[0] == pd.Timestamp("2023-01-03")


def test_normalise_rejects_a_payload_missing_fields():
    broken = [{"date": "2023-01-03T00:00:00.000Z", "close": 125.07}]
    with pytest.raises(ValueError, match="missing fields"):
        normalise_price_payload(broken, "AAPL")


def test_write_and_read_round_trip(tmp_path):
    bars = make_bars("AAPL")
    store.write_bars(tmp_path, "AAPL", bars)
    loaded = store.read_bars(tmp_path, "AAPL")
    pd.testing.assert_frame_equal(bars, loaded)


def test_read_bars_filters_by_date(tmp_path):
    bars = make_bars("AAPL", start="2020-01-01", periods=300)
    store.write_bars(tmp_path, "AAPL", bars)
    loaded = store.read_bars(tmp_path, "AAPL", start=date(2020, 6, 1))
    assert loaded["date"].min() >= pd.Timestamp("2020-06-01")
    assert len(loaded) < len(bars)


def test_read_bars_raises_for_unknown_ticker(tmp_path):
    with pytest.raises(FileNotFoundError, match="No curated data"):
        store.read_bars(tmp_path, "NOPE")


def test_read_many_skips_missing_tickers(tmp_path):
    store.write_bars(tmp_path, "AAA", make_bars("AAA", seed=1))
    store.write_bars(tmp_path, "BBB", make_bars("BBB", seed=2))
    combined = store.read_many(tmp_path, ["AAA", "BBB", "MISSING"])
    assert sorted(combined["ticker"].unique()) == ["AAA", "BBB"]


def test_read_many_returns_empty_frame_when_nothing_found(tmp_path):
    assert store.read_many(tmp_path, ["NOPE"]).empty


def test_raw_payload_round_trip(tmp_path):
    store.write_raw(tmp_path, "AAPL", SAMPLE_PAYLOAD)
    assert store.read_raw(tmp_path, "AAPL") == SAMPLE_PAYLOAD


def test_stored_tickers_lists_what_is_on_disk(tmp_path):
    store.write_bars(tmp_path, "AAA", make_bars("AAA"))
    store.write_bars(tmp_path, "BBB", make_bars("BBB"))
    assert store.stored_tickers(tmp_path) == ["AAA", "BBB"]


def test_rate_limiter_allows_requests_under_the_quota():
    """Under quota there should be no sleeping, so this returns immediately."""
    limiter = RateLimiter(max_requests=5, window_seconds=3600)
    for _ in range(5):
        limiter.acquire()
    assert len(limiter._timestamps) == 5


def test_rate_limiter_expires_old_requests():
    """A zero-length window means every timestamp is immediately stale."""
    limiter = RateLimiter(max_requests=1, window_seconds=0.0)
    limiter.acquire()
    limiter.acquire()
    assert len(limiter._timestamps) == 1

"""Client for the Tiingo end-of-day price API.

This module is the only place in the codebase that knows Tiingo exists. Every
other module asks for "daily bars for a ticker" and is indifferent to who
supplied them. If Tiingo raises its prices or goes out of business, this one
file changes and nothing else does.

Two things are fetched here:

* the *ticker catalogue* -- every symbol Tiingo covers, with the first and last
  date it has data for. The last date is what makes survivorship-bias-free
  research possible, because it tells you when a company stopped existing.
* *daily price bars* for one ticker at a time.

Prices arrive in two flavours. The unadjusted ones are what actually printed on
the exchange that day. The adjusted ones are restated to account for later
stock splits and dividends. Backtests must use adjusted prices, or a 2-for-1
split looks like a 50% overnight crash. Order sizing must use unadjusted
prices, because that is what you will really pay. Both are kept.
"""

import csv
import io
import time
import zipfile
from collections import deque
from datetime import date

import httpx
import pandas as pd

from algomvp.config import Settings

# The catalogue is a public file and needs no API key.
TICKER_CATALOGUE_URL = (
    "https://apimedia.tiingo.com/docs/tiingo/daily/supported_tickers.zip"
)

# The columns a price response is expected to contain. Anything missing is a
# fault worth failing loudly on rather than discovering during a backtest.
EXPECTED_PRICE_FIELDS = (
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "adjOpen",
    "adjHigh",
    "adjLow",
    "adjClose",
    "adjVolume",
    "divCash",
    "splitFactor",
)


class RateLimiter:
    """Blocks the caller so a request quota is never exceeded.

    Tiingo's free tier allows 50 requests per hour. Exceeding it earns an
    HTTP 429 and, on repeat offences, a suspended key. This limiter keeps the
    timestamps of recent requests and sleeps when the window is full.

    It is deliberately simple and single-process. It will not protect you if
    you run two copies of the fetcher at once.
    """

    def __init__(self, max_requests: int, window_seconds: float = 3600.0) -> None:
        """Allow ``max_requests`` calls in any rolling ``window_seconds``."""
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._timestamps: deque[float] = deque()

    def acquire(self) -> None:
        """Wait, if necessary, until another request is permitted."""
        now = time.monotonic()

        # Forget anything that has aged out of the window.
        while self._timestamps and now - self._timestamps[0] > self.window_seconds:
            self._timestamps.popleft()

        if len(self._timestamps) >= self.max_requests:
            oldest = self._timestamps[0]
            sleep_for = self.window_seconds - (now - oldest) + 0.1
            time.sleep(max(sleep_for, 0.0))
            self.acquire()  # re-check after sleeping
            return

        self._timestamps.append(now)


class TiingoClient:
    """Fetches ticker metadata and daily price bars from Tiingo."""

    def __init__(
        self,
        settings: Settings,
        client: httpx.Client | None = None,
    ) -> None:
        """Build a client.

        Args:
            settings: Application settings supplying the API key and quota.
            client: An optional pre-built HTTP client. Tests pass a fake one
                here; production code leaves it as None and gets a real one.

        """
        if not settings.tiingo_api_key:
            raise ValueError(
                "No Tiingo API key found. Copy .env.example to .env and add it."
            )

        self.settings = settings
        self.limiter = RateLimiter(settings.tiingo_requests_per_hour)
        self._client = client or httpx.Client(
            base_url=settings.tiingo_base_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Token {settings.tiingo_api_key}",
            },
            timeout=30.0,
        )

    def fetch_ticker_catalogue(self) -> pd.DataFrame:
        """Download the full list of symbols Tiingo covers.

        Returns:
            A frame with columns ``ticker``, ``exchange``, ``asset_type``,
            ``currency``, ``start_date`` and ``end_date``. Roughly 85,000 rows,
            most of them irrelevant to us; filtering happens in the universe
            module, not here.

        """
        response = httpx.get(TICKER_CATALOGUE_URL, timeout=120.0, follow_redirects=True)
        response.raise_for_status()

        archive = zipfile.ZipFile(io.BytesIO(response.content))
        name = archive.namelist()[0]
        with archive.open(name) as handle:
            text = io.TextIOWrapper(handle, encoding="utf-8")
            rows = list(csv.DictReader(text))

        frame = pd.DataFrame(rows)
        frame = frame.rename(
            columns={
                "assetType": "asset_type",
                "priceCurrency": "currency",
                "startDate": "start_date",
                "endDate": "end_date",
            }
        )
        for column in ("start_date", "end_date"):
            frame[column] = pd.to_datetime(frame[column], errors="coerce")
        return frame

    def fetch_daily_bars(
        self,
        ticker: str,
        start: date,
        end: date,
    ) -> pd.DataFrame:
        """Fetch daily OHLCV bars for one ticker.

        Args:
            ticker: Symbol to fetch, for example ``"AAPL"``.
            start: First calendar date to request, inclusive.
            end: Last calendar date to request, inclusive.

        Returns:
            A frame indexed by date with both raw and adjusted price columns.
            An empty frame if Tiingo has no data for the period, which is a
            normal outcome for a company that had not yet listed.

        """
        self.limiter.acquire()

        response = self._client.get(
            f"/tiingo/daily/{ticker.lower()}/prices",
            params={
                "startDate": start.isoformat(),
                "endDate": end.isoformat(),
                "format": "json",
                "resampleFreq": "daily",
            },
        )
        response.raise_for_status()
        payload = response.json()

        if not payload:
            return pd.DataFrame()

        return normalise_price_payload(payload, ticker)

    def close(self) -> None:
        """Release the underlying HTTP connection pool."""
        self._client.close()


def normalise_price_payload(payload: list[dict], ticker: str) -> pd.DataFrame:
    """Turn a raw Tiingo JSON response into our internal frame shape.

    Kept as a standalone function rather than a method so it can be tested
    against saved sample payloads without any network involved.

    Args:
        payload: The decoded JSON list returned by the prices endpoint.
        ticker: The symbol the payload belongs to.

    Returns:
        A frame indexed by a timezone-naive ``date``, with snake_case columns
        and a ``ticker`` column added.

    Raises:
        ValueError: If the payload is missing any expected field, which
            usually means the API contract has changed underneath us.

    """
    frame = pd.DataFrame(payload)

    missing = set(EXPECTED_PRICE_FIELDS) - set(frame.columns)
    if missing:
        raise ValueError(
            f"Tiingo response for {ticker} is missing fields: {sorted(missing)}"
        )

    frame["date"] = pd.to_datetime(frame["date"], utc=True).dt.tz_localize(None)
    frame["date"] = frame["date"].dt.normalize()

    frame = frame.rename(
        columns={
            "adjOpen": "adj_open",
            "adjHigh": "adj_high",
            "adjLow": "adj_low",
            "adjClose": "adj_close",
            "adjVolume": "adj_volume",
            "divCash": "dividend_cash",
            "splitFactor": "split_factor",
        }
    )
    frame["ticker"] = ticker.upper()

    ordered = [
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
    return frame[ordered].sort_values("date").reset_index(drop=True)

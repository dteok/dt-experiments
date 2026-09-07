"""On-disk storage for price data.

Parquet files, one per ticker, in a plain directory. No database.

That choice deserves a defence, because "use a database" is the reflex. Daily
bars for 200 tickers over 25 years is roughly 1.2 million rows and about 20 MB
on disk. Pandas reads that in well under a second. A database would add a
schema to migrate, a service to run and a connection to manage, in exchange for
query features this project does not use. Simple is better than complex.

Two directories, with different rules:

* ``raw/`` holds the vendor payload as it arrived, and is append-only. Nothing
  in this codebase is permitted to edit a raw file.
* ``curated/`` holds validated, normalised frames, and is regenerated freely
  from raw whenever the cleaning logic changes.

The separation costs a little disk and buys you the ability to answer "did the
data change, or did my code change?" -- which you will need, probably at 1am.
"""

import json
from datetime import date
from pathlib import Path

import pandas as pd


def raw_path(raw_dir: Path, ticker: str) -> Path:
    """Return the file path holding the raw vendor payload for a ticker."""
    return raw_dir / f"{ticker.upper()}.json"


def curated_path(curated_dir: Path, ticker: str) -> Path:
    """Return the file path holding the curated bars for a ticker."""
    return curated_dir / f"{ticker.upper()}.parquet"


def write_raw(raw_dir: Path, ticker: str, payload: list[dict]) -> Path:
    """Save a vendor payload verbatim, so it can be re-examined later.

    Args:
        raw_dir: Directory for immutable vendor responses.
        ticker: Symbol the payload belongs to.
        payload: The decoded JSON exactly as the vendor returned it.

    Returns:
        The path written.

    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_path(raw_dir, ticker)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def read_raw(raw_dir: Path, ticker: str) -> list[dict]:
    """Load a previously saved vendor payload."""
    path = raw_path(raw_dir, ticker)
    if not path.exists():
        raise FileNotFoundError(f"No raw payload stored for {ticker} at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_bars(curated_dir: Path, ticker: str, bars: pd.DataFrame) -> Path:
    """Save curated daily bars for one ticker.

    Args:
        curated_dir: Directory for validated data.
        ticker: Symbol the bars belong to.
        bars: Frame in the shape produced by ``normalise_price_payload``.

    Returns:
        The path written.

    """
    curated_dir.mkdir(parents=True, exist_ok=True)
    path = curated_path(curated_dir, ticker)
    bars.to_parquet(path, index=False)
    return path


def read_bars(
    curated_dir: Path,
    ticker: str,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Load curated daily bars for one ticker, optionally date-filtered.

    Args:
        curated_dir: Directory holding curated parquet files.
        ticker: Symbol to load.
        start: If given, drop rows before this date.
        end: If given, drop rows after this date.

    Returns:
        A frame of bars sorted by date.

    Raises:
        FileNotFoundError: If the ticker has not been downloaded yet.

    """
    path = curated_path(curated_dir, ticker)
    if not path.exists():
        raise FileNotFoundError(
            f"No curated data for {ticker}. Run the fetch command first."
        )

    bars = pd.read_parquet(path)
    if start is not None:
        bars = bars[bars["date"] >= pd.Timestamp(start)]
    if end is not None:
        bars = bars[bars["date"] <= pd.Timestamp(end)]
    return bars.sort_values("date").reset_index(drop=True)


def read_many(
    curated_dir: Path,
    tickers: list[str],
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Load bars for several tickers into one long-format frame.

    Long format -- one row per ticker per date -- rather than a wide matrix.
    Wide is more convenient for a single price column, but every strategy here
    needs several columns at once, and long format keeps them together without
    a multi-level column index to trip over.

    Tickers with no stored data are skipped silently, because a point-in-time
    universe will legitimately contain symbols that were never downloaded.

    Args:
        curated_dir: Directory holding curated parquet files.
        tickers: Symbols to load.
        start: If given, drop rows before this date.
        end: If given, drop rows after this date.

    Returns:
        A frame sorted by date then ticker. Empty if nothing was found.

    """
    frames = []
    for ticker in tickers:
        try:
            frames.append(read_bars(curated_dir, ticker, start, end))
        except FileNotFoundError:
            continue

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    return combined.sort_values(["date", "ticker"]).reset_index(drop=True)


def stored_tickers(curated_dir: Path) -> list[str]:
    """List every ticker that has curated data on disk."""
    if not curated_dir.exists():
        return []
    return sorted(path.stem for path in curated_dir.glob("*.parquet"))

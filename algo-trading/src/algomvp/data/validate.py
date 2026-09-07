"""Data quality checks for daily price bars.

This is the least glamorous module in the project and the most important one.

A backtest is a machine for turning historical data into a number that you will
then trust with money. If the data is wrong, the machine still produces a
number, and the number still looks convincing. There is no error message. The
only defence is to check the data before it reaches the machine.

Every check here answers a question that has, at some point, silently ruined
somebody's backtest:

* Are there duplicate rows for the same day? (Double-counted returns.)
* Is a price zero or negative? (Infinite or nonsensical returns.)
* Is the high below the low? (Vendor transposition error.)
* Did the price move 60% overnight with no recorded split? (Either a real
  event worth knowing about, or corrupt data.)
* Are there long gaps where the market was open? (Missing history, which
  quietly shortens your sample.)
* Has the price not moved for days? (A stale feed, or a halted stock.)

Checks are reported, not enforced. This module never deletes or repairs data.
It tells you what it found and lets you decide, because silent auto-repair is
how a data problem becomes an invisible data problem.
"""

from dataclasses import dataclass, field

import pandas as pd

# A single-day move larger than this is treated as suspicious unless the split
# factor explains it. Real stocks do move 50% in a day, so this is a flag for
# human attention, not a verdict.
EXTREME_RETURN_THRESHOLD = 0.50

# Consecutive identical closes beyond this count suggest a stale feed.
MAX_STALE_DAYS = 5

# Missing consecutive weekdays beyond this suggest a hole in the history.
# US markets never close for more than a few days running; the 1-week
# post-9/11 shutdown is the notable exception.
MAX_CALENDAR_GAP_DAYS = 6


@dataclass
class ValidationReport:
    """The findings for one ticker.

    A dataclass is used here purely to avoid writing an ``__init__`` and a
    ``__repr__`` by hand. The ``@dataclass`` decorator inspects the annotated
    attributes below and generates both. It changes nothing else about how the
    class behaves; ``ValidationReport(ticker="AAPL")`` works as normal.

    ``field(default_factory=list)`` is needed instead of ``= []`` because a
    plain list default would be shared between every instance of the class --
    a well-known Python trap.
    """

    ticker: str
    row_count: int = 0
    first_date: pd.Timestamp | None = None
    last_date: pd.Timestamp | None = None
    problems: list[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        """True when no problems were found."""
        return not self.problems

    def summary(self) -> str:
        """Return a one-or-more line human-readable summary."""
        header = (
            f"{self.ticker}: {self.row_count} bars, "
            f"{_format_date(self.first_date)} to {_format_date(self.last_date)}"
        )
        if self.is_clean:
            return f"{header} -- clean"
        lines = [f"{header} -- {len(self.problems)} problem(s):"]
        lines.extend(f"    - {problem}" for problem in self.problems)
        return "\n".join(lines)


def _format_date(value: pd.Timestamp | None) -> str:
    """Render a timestamp as YYYY-MM-DD, or a placeholder when absent."""
    return "n/a" if value is None else value.strftime("%Y-%m-%d")


def validate_bars(bars: pd.DataFrame, ticker: str) -> ValidationReport:
    """Run every quality check against one ticker's bars.

    Args:
        bars: Frame in the shape produced by ``normalise_price_payload``.
        ticker: Symbol the bars belong to, used for reporting.

    Returns:
        A report listing everything suspicious that was found.

    """
    report = ValidationReport(ticker=ticker)

    if bars.empty:
        report.problems.append("no rows at all")
        return report

    bars = bars.sort_values("date").reset_index(drop=True)
    report.row_count = len(bars)
    report.first_date = bars["date"].iloc[0]
    report.last_date = bars["date"].iloc[-1]

    report.problems.extend(_check_duplicate_dates(bars))
    report.problems.extend(_check_price_sanity(bars))
    report.problems.extend(_check_volume(bars))
    report.problems.extend(_check_extreme_returns(bars))
    report.problems.extend(_check_calendar_gaps(bars))
    report.problems.extend(_check_stale_prices(bars))

    return report


def _check_duplicate_dates(bars: pd.DataFrame) -> list[str]:
    """Report any date appearing more than once."""
    duplicated = bars["date"][bars["date"].duplicated()]
    if duplicated.empty:
        return []
    sample = ", ".join(_format_date(d) for d in duplicated.head(3))
    return [f"{len(duplicated)} duplicate date(s), e.g. {sample}"]


def _check_price_sanity(bars: pd.DataFrame) -> list[str]:
    """Report impossible price relationships and non-positive prices."""
    problems = []
    price_columns = ["open", "high", "low", "close", "adj_close"]

    non_positive = (bars[price_columns] <= 0).any(axis=1)
    if non_positive.any():
        problems.append(f"{int(non_positive.sum())} bar(s) with a price <= 0")

    inverted = bars["high"] < bars["low"]
    if inverted.any():
        problems.append(f"{int(inverted.sum())} bar(s) where high < low")

    body_high = bars[["open", "close"]].max(axis=1)
    body_low = bars[["open", "close"]].min(axis=1)
    outside = (bars["high"] < body_high) | (bars["low"] > body_low)
    if outside.any():
        problems.append(
            f"{int(outside.sum())} bar(s) where open/close sits outside high/low"
        )

    missing = bars[price_columns].isna().any(axis=1)
    if missing.any():
        problems.append(f"{int(missing.sum())} bar(s) with a missing price")

    return problems


def _check_volume(bars: pd.DataFrame) -> list[str]:
    """Report zero-volume days, which usually mean a halt or a padded bar."""
    zero_volume = bars["volume"] <= 0
    if not zero_volume.any():
        return []
    return [f"{int(zero_volume.sum())} bar(s) with zero or negative volume"]


def _check_extreme_returns(bars: pd.DataFrame) -> list[str]:
    """Report huge one-day moves that the split factor does not explain."""
    returns = bars["adj_close"].pct_change()
    extreme = returns.abs() > EXTREME_RETURN_THRESHOLD

    # Adjusted prices should already have absorbed splits, so a large move in
    # adj_close is suspicious even on a split date. The split factor is kept
    # as a safety valve for vendors that adjust imperfectly.
    #
    # The exemption covers the split bar *and the one after it*. If a vendor
    # leaves an unadjusted spike in the series, that single bad price creates
    # two extreme returns: one moving on to it, one moving off it again. Only
    # exempting the split bar itself would flag the rebound as a mystery.
    split_day = bars["split_factor"] != 1.0
    near_split = split_day | split_day.shift(1, fill_value=False)

    unexplained = extreme & ~near_split
    if not unexplained.any():
        return []

    worst = returns[unexplained].abs().max()
    return [
        f"{int(unexplained.sum())} unexplained move(s) over "
        f"{EXTREME_RETURN_THRESHOLD:.0%} (largest {worst:.0%})"
    ]


def _check_calendar_gaps(bars: pd.DataFrame) -> list[str]:
    """Report stretches of weekdays with no data at all.

    This uses plain weekdays rather than a real exchange calendar. That makes
    it approximate -- Thanksgiving week will trip it -- but an approximate
    check that runs with no extra dependency is better than a perfect check
    that never gets written. Treat the output as a prompt to go and look.
    """
    dates = pd.DatetimeIndex(bars["date"])
    weekday_gaps = []

    for previous, current in zip(dates[:-1], dates[1:], strict=True):
        business_days = len(pd.bdate_range(previous, current)) - 1
        if business_days > MAX_CALENDAR_GAP_DAYS:
            weekday_gaps.append((previous, current, business_days))

    if not weekday_gaps:
        return []

    first = weekday_gaps[0]
    return [
        f"{len(weekday_gaps)} calendar gap(s) over {MAX_CALENDAR_GAP_DAYS} "
        f"weekdays, first {_format_date(first[0])} to {_format_date(first[1])} "
        f"({first[2]} weekdays)"
    ]


def _check_stale_prices(bars: pd.DataFrame) -> list[str]:
    """Report runs of identical closing prices."""
    closes = bars["close"]
    # Give each run of identical values its own group number, then count them.
    run_ids = (closes != closes.shift()).cumsum()
    run_lengths = closes.groupby(run_ids).transform("size")

    stale = run_lengths > MAX_STALE_DAYS
    if not stale.any():
        return []

    longest = int(run_lengths.max())
    return [f"price unchanged for up to {longest} consecutive bars"]


def validate_many(bars: pd.DataFrame) -> list[ValidationReport]:
    """Validate a long-format frame containing several tickers.

    Args:
        bars: Frame with a ``ticker`` column, as returned by ``read_many``.

    Returns:
        One report per ticker, ordered by ticker.

    """
    if bars.empty:
        return []
    return [
        validate_bars(group, str(ticker))
        for ticker, group in bars.groupby("ticker", sort=True)
    ]

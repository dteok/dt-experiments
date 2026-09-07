"""Point-in-time universe construction.

This module answers one question: *on a given past date, which securities were
we allowed to consider?*

Getting that wrong is survivorship bias, the most expensive mistake in this
whole project. The mistake looks like this. You take today's list of large US
companies, download 20 years of history for each, and backtest. Every company
in that list survived to today. Every company that went bankrupt, got acquired
or was delisted for non-compliance has been silently removed from your sample.
You have run an experiment on a group selected *because* it did well, and the
result will be beautiful and worthless.

The analogy is a study of which surgical technique keeps patients healthiest,
conducted by surveying people in the waiting room next year. Everyone who died
is absent from your data, and the technique that killed them looks excellent.

The defence has two parts. First, the ticker catalogue records a start and end
date per symbol, so a company that stopped trading in 2016 can still be a
candidate in a 2014 backtest and correctly disappears afterwards. Second, every
eligibility filter uses only data that existed on the date being tested.

The eligibility filter here is deliberately a *stub* for company financials.
It currently screens on listing status, price and liquidity. Fundamental
screens (profitability, leverage, valuation) plug into the same interface later
without any downstream module changing. See ``EligibilityRules``.
"""

from dataclasses import dataclass
from datetime import date

import pandas as pd

# Exchanges we will trade. Tiingo spells them this way in the catalogue.
TRADEABLE_EXCHANGES = ("NYSE", "NASDAQ", "NYSE ARCA", "AMEX", "NYSE MKT")

# Instrument types we accept. No options, no mutual funds.
TRADEABLE_ASSET_TYPES = ("Stock", "ETF")


@dataclass
class EligibilityRules:
    """Thresholds a security must clear to enter the tradeable universe.

    Each rule exists to keep out a specific kind of bad trade rather than to
    predict returns:

    * ``min_price`` excludes sub-$5 stocks, where the bid-ask spread can be
      several percent and a backtest's assumed fill price is fiction.
    * ``min_dollar_volume`` excludes illiquid names. If you want to hold
      $10,000 of something that trades $200,000 a day, your own order moves
      the price and the backtest never knew.
    * ``min_history_days`` ensures indicators have enough data to be meaningful
      and excludes freshly listed companies with no track record.
    """

    min_price: float = 5.0
    min_dollar_volume: float = 5_000_000.0
    min_history_days: int = 252
    liquidity_lookback_days: int = 63


def filter_catalogue(catalogue: pd.DataFrame) -> pd.DataFrame:
    """Reduce the full vendor catalogue to plausibly tradeable US securities.

    Args:
        catalogue: Frame as returned by ``TiingoClient.fetch_ticker_catalogue``.

    Returns:
        A frame with the same columns, keeping only US-listed stocks and ETFs
        priced in dollars that have a known start date.

    """
    keep = (
        catalogue["exchange"].isin(TRADEABLE_EXCHANGES)
        & catalogue["asset_type"].isin(TRADEABLE_ASSET_TYPES)
        & (catalogue["currency"] == "USD")
        & catalogue["start_date"].notna()
    )
    return catalogue[keep].reset_index(drop=True)


def members_on(catalogue: pd.DataFrame, as_of: date) -> list[str]:
    """Return every symbol that was listed and trading on a given date.

    A symbol qualifies when its first data date is on or before ``as_of`` and
    its last data date is on or after ``as_of``. A missing end date means the
    security is still trading today.

    Args:
        catalogue: A filtered catalogue from ``filter_catalogue``.
        as_of: The date being simulated.

    Returns:
        Sorted list of ticker symbols.

    """
    moment = pd.Timestamp(as_of)
    listed = catalogue["start_date"] <= moment
    not_yet_delisted = catalogue["end_date"].isna() | (catalogue["end_date"] >= moment)
    alive = catalogue[listed & not_yet_delisted]
    return sorted(alive["ticker"].str.upper().unique())


def screen_by_liquidity(
    bars: pd.DataFrame,
    as_of: date,
    rules: EligibilityRules,
) -> list[str]:
    """Apply price, liquidity and history screens as of a given date.

    Only bars dated on or before ``as_of`` are examined. That restriction is
    the entire point of this function, so it is applied first and unconditionally.

    Args:
        bars: Long-format bars for candidate tickers, from ``read_many``.
        as_of: The date being simulated.
        rules: Thresholds to apply.

    Returns:
        Sorted list of tickers that pass every screen.

    """
    if bars.empty:
        return []

    moment = pd.Timestamp(as_of)
    history = bars[bars["date"] <= moment]
    if history.empty:
        return []

    passing = []
    for ticker, group in history.groupby("ticker", sort=True):
        group = group.sort_values("date")

        if len(group) < rules.min_history_days:
            continue

        recent = group.tail(rules.liquidity_lookback_days)
        latest_close = float(recent["close"].iloc[-1])
        if latest_close < rules.min_price:
            continue

        dollar_volume = (recent["close"] * recent["volume"]).mean()
        if float(dollar_volume) < rules.min_dollar_volume:
            continue

        passing.append(str(ticker))

    return passing


def build_universe(
    catalogue: pd.DataFrame,
    bars: pd.DataFrame,
    as_of: date,
    rules: EligibilityRules | None = None,
) -> list[str]:
    """Produce the tradeable universe for one date.

    This is the single entry point strategies should use. It composes the two
    stages -- listing status, then quality screens -- so no caller can
    accidentally skip the first one.

    Args:
        catalogue: A filtered catalogue from ``filter_catalogue``.
        bars: Long-format bars covering the candidate tickers.
        as_of: The date being simulated.
        rules: Thresholds to apply. Defaults are used when omitted.

    Returns:
        Sorted list of tickers eligible to trade on ``as_of``.

    """
    rules = rules or EligibilityRules()

    listed = set(members_on(catalogue, as_of))
    if not listed:
        return []

    candidates = bars[bars["ticker"].isin(listed)]
    return screen_by_liquidity(candidates, as_of, rules)

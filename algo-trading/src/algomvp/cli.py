"""Command line interface.

Four commands, matching the four things you do at this stage of the project:

    algomvp catalogue              download the vendor's full ticker list
    algomvp fetch --seed           download price history for the watchlist
    algomvp validate               run quality checks over everything stored
    algomvp universe --as-of DATE  show what was tradeable on a past date

``argparse`` is used rather than a third-party CLI library. It is in the
standard library, it is enough for four commands, and one fewer dependency is
one fewer thing to break.
"""

import argparse
import sys
from datetime import date, datetime

import pandas as pd
import yaml

from algomvp.config import get_settings
from algomvp.data import store, validate
from algomvp.data.tiingo import TiingoClient
from algomvp.universe import pit

CATALOGUE_FILENAME = "ticker_catalogue.parquet"


def _parse_date(text: str) -> date:
    """Convert a YYYY-MM-DD string into a date, for argparse."""
    return datetime.strptime(text, "%Y-%m-%d").date()


def _load_seed_tickers(config_dir) -> list[str]:
    """Read the starting watchlist from config/universe.yaml."""
    path = config_dir / "universe.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Expected a watchlist at {path}")
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [str(ticker).upper() for ticker in document.get("seed_tickers", [])]


def command_catalogue(args: argparse.Namespace) -> int:
    """Download and cache the vendor's ticker catalogue."""
    settings = get_settings()
    settings.ensure_directories()

    client = TiingoClient(settings)
    try:
        catalogue = client.fetch_ticker_catalogue()
    finally:
        client.close()

    tradeable = pit.filter_catalogue(catalogue)
    destination = settings.curated_dir / CATALOGUE_FILENAME
    tradeable.to_parquet(destination, index=False)

    still_listed = int(tradeable["end_date"].isna().sum())
    print(f"Catalogue: {len(catalogue)} symbols from vendor")
    print(f"Tradeable: {len(tradeable)} US stocks and ETFs")
    print(f"  still listed: {still_listed}")
    print(f"  delisted:     {len(tradeable) - still_listed}")
    print(f"Saved to {destination}")
    return 0


def command_fetch(args: argparse.Namespace) -> int:
    """Download price history for the seed watchlist."""
    settings = get_settings()
    settings.ensure_directories()

    tickers = args.tickers or _load_seed_tickers(settings.config_dir)
    if not tickers:
        print("Nothing to fetch.", file=sys.stderr)
        return 1

    client = TiingoClient(settings)
    print(f"Fetching {len(tickers)} ticker(s) from {args.start} to {args.end}")

    try:
        for position, ticker in enumerate(tickers, start=1):
            bars = client.fetch_daily_bars(ticker, args.start, args.end)
            if bars.empty:
                print(f"  [{position}/{len(tickers)}] {ticker}: no data")
                continue
            store.write_bars(settings.curated_dir, ticker, bars)
            first = bars["date"].iloc[0].date()
            last = bars["date"].iloc[-1].date()
            print(
                f"  [{position}/{len(tickers)}] {ticker}: "
                f"{len(bars)} bars, {first} to {last}"
            )
    finally:
        client.close()

    return 0


def command_validate(args: argparse.Namespace) -> int:
    """Run quality checks over every stored ticker."""
    settings = get_settings()
    tickers = args.tickers or store.stored_tickers(settings.curated_dir)
    tickers = [t for t in tickers if t != CATALOGUE_FILENAME.removesuffix(".parquet")]

    if not tickers:
        print("No stored data. Run 'algomvp fetch' first.", file=sys.stderr)
        return 1

    problem_count = 0
    for ticker in tickers:
        bars = store.read_bars(settings.curated_dir, ticker)
        report = validate.validate_bars(bars, ticker)
        print(report.summary())
        if not report.is_clean:
            problem_count += 1

    print(f"\n{len(tickers)} checked, {problem_count} with problems.")
    return 1 if problem_count else 0


def command_universe(args: argparse.Namespace) -> int:
    """Show the tradeable universe as it stood on a past date."""
    settings = get_settings()
    catalogue_path = settings.curated_dir / CATALOGUE_FILENAME
    if not catalogue_path.exists():
        print("No catalogue. Run 'algomvp catalogue' first.", file=sys.stderr)
        return 1

    catalogue = pd.read_parquet(catalogue_path)
    tickers = store.stored_tickers(settings.curated_dir)
    bars = store.read_many(settings.curated_dir, tickers, end=args.as_of)

    listed = pit.members_on(catalogue, args.as_of)
    eligible = pit.build_universe(catalogue, bars, args.as_of)

    print(f"As of {args.as_of}:")
    print(f"  listed on a US exchange: {len(listed)}")
    print(f"  with data downloaded:    {bars['ticker'].nunique() if len(bars) else 0}")
    print(f"  passing eligibility:     {len(eligible)}")
    if eligible:
        print("  " + ", ".join(eligible))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser for all subcommands."""
    parser = argparse.ArgumentParser(
        prog="algomvp",
        description="Algorithmic trading research pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    catalogue = subparsers.add_parser(
        "catalogue", help="download the vendor ticker catalogue"
    )
    catalogue.set_defaults(handler=command_catalogue)

    fetch = subparsers.add_parser("fetch", help="download daily price history")
    fetch.add_argument(
        "--tickers",
        nargs="*",
        help="symbols to fetch; defaults to config/universe.yaml",
    )
    fetch.add_argument(
        "--start", type=_parse_date, default=date(2005, 1, 1), help="YYYY-MM-DD"
    )
    fetch.add_argument(
        "--end", type=_parse_date, default=date.today(), help="YYYY-MM-DD"
    )
    fetch.set_defaults(handler=command_fetch)

    check = subparsers.add_parser("validate", help="run data quality checks")
    check.add_argument("--tickers", nargs="*", help="symbols to check")
    check.set_defaults(handler=command_validate)

    universe = subparsers.add_parser(
        "universe", help="show the tradeable universe on a past date"
    )
    universe.add_argument("--as-of", type=_parse_date, required=True, help="YYYY-MM-DD")
    universe.set_defaults(handler=command_universe)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to the chosen subcommand."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())

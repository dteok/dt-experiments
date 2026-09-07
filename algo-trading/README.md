# algomvp

An end-to-end algorithmic trading system for US equities and ETFs: data
ingestion, validation, point-in-time universe construction, backtesting, risk
management and paper trading.

This repository currently contains **M0 and M1** — everything up to and
including trustworthy data. The backtest engine comes next.

---

## Why the boring parts come first

A backtest is a machine that turns historical data into a number you will then
trust with money. If the data is wrong, the machine still produces a number,
and the number still looks convincing. There is no error message.

So the order of work here is deliberate: get the data, prove the data is sound,
prove the universe is free of hindsight, and only then write something that
makes trading decisions.

---

## Setup

Requires **Python 3.12**. Later versions may work but are not pinned.

```bash
git clone <your-repo-url> algotrading-mvp
cd algotrading-mvp

python3.12 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -e ".[dev]"
```

Then get two free API keys and put them in a `.env` file:

```bash
cp .env.example .env
# edit .env and paste your keys
```

| Service | What for | Cost |
|---|---|---|
| [Tiingo](https://www.tiingo.com) | Historical daily bars, 30+ years, split and dividend adjusted | Free tier: 500 symbols/month, 50 requests/hour. The $10/month tier removes the symbol cap and is worth it once you go past the starter watchlist. |
| [Alpaca](https://alpaca.markets) | Paper trading account and live quotes | Free, no funding required, available outside the US |

Verify the install:

```bash
pytest          # 35 tests, no network access required
black --check .
ruff check .
```

---

## Usage

```bash
# 1. Download the full vendor ticker catalogue (~85,000 symbols, one request).
#    This is what makes survivorship-bias-free research possible.
algomvp catalogue

# 2. Download daily history for the starter watchlist in config/universe.yaml.
#    33 tickers, so this fits inside the free tier's hourly quota.
algomvp fetch --start 2005-01-01

# 3. Check the data before trusting it.
algomvp validate

# 4. See what was actually tradeable on a past date.
algomvp universe --as-of 2015-06-30
```

Step 4 is the one to pay attention to. The answer should differ between
`--as-of 2015-06-30` and `--as-of 2024-06-30`, and not only because prices
changed. Companies that had not yet listed must be absent from the first, and
companies that were later delisted must be present in it.

---

## Layout

```
src/algomvp/
├── config.py            All settings and secrets, in one place
├── cli.py               Four commands, argparse
├── data/
│   ├── tiingo.py        The only module that knows Tiingo exists
│   ├── store.py         Parquet on disk; raw is immutable, curated is derived
│   └── validate.py      Nine quality checks, reported not enforced
└── universe/
    └── pit.py           Point-in-time eligibility, the survivorship defence

tests/                   35 tests, all offline, all deterministic
config/universe.yaml     Starter watchlist: 4 benchmark ETFs + 29 large caps
data/raw/                Vendor payloads, never edited
data/curated/            Validated parquet, regenerated freely
```

### The two data directories

`raw/` holds vendor responses exactly as they arrived and is append-only.
`curated/` holds cleaned frames and can be rebuilt from raw at any time.

The separation costs a little disk space and buys you the ability to answer
"did the data change, or did my code change?" — which you will need, probably
at 1am.

### Adjusted versus unadjusted prices

Both are stored, and the distinction matters.

- **Adjusted** prices are restated for later splits and dividends. Backtests
  must use these, or a 2-for-1 split looks like a 50% overnight crash.
- **Unadjusted** prices are what actually printed on the exchange. Order
  sizing must use these, because that is what you will really pay.

---

## What the validator checks

| Check | The failure it prevents |
|---|---|
| Duplicate dates | Double-counted returns |
| Non-positive prices | Infinite or nonsensical returns |
| High below low | Vendor transposition errors |
| Open/close outside the high/low range | Corrupt bars |
| Missing prices | Silent gaps in indicator calculations |
| Zero volume | Padded bars and undetected trading halts |
| Extreme moves with no recorded split | Corrupt data masquerading as a signal |
| Calendar gaps | Missing history quietly shortening your sample |
| Stale prices | A dead feed you did not notice |

Nothing is auto-repaired. Silent repair is how a data problem becomes an
invisible data problem.

---

## Design commitments

These hold for every module added later.

1. **Strategies never know whether they are in a backtest or live.** They see
   the same interface either way. A flight simulator whose controls differ
   from the real cockpit is worthless as training.
2. **Nothing reads data dated after the moment being simulated.** Enforced
   structurally, not by careful coding.
3. **One vendor per module.** Swapping data provider or broker touches one
   file.
4. **Reported, never repaired.** Checks tell you what they found and stop.
5. **Every screen is point-in-time.** `screen_by_liquidity` truncates its
   input to the as-of date before doing anything else.

---

## Roadmap

- [x] **M0** Project skeleton, config, Tiingo client, Parquet storage
- [x] **M1** Data validation, point-in-time universe, ticker catalogue
- [ ] **M2** Backtest engine, validated against buy-and-hold SPY
- [ ] **M3** Strategies, transaction costs, performance metrics
- [ ] **M4** Alpaca paper broker and daily reconciliation
- [ ] **M5** Walk-forward validation

M2 has a hard acceptance test: the engine must reproduce SPY's actual
buy-and-hold total return to within a fraction of a percent. An engine that
cannot replicate the trivial case cannot be trusted on the interesting one.

---

## Conventions

PEP 8, Black at 88 characters, Ruff for linting, Google-style docstrings,
pytest for tests. Decorators are used in exactly three places — `@lru_cache`
in `config.py`, `@dataclass` in `validate.py` and `pit.py`, and
`@pytest.fixture` in the tests — and each is explained in a docstring where it
appears.

---

## Disclaimer

This is research and educational software. It is not investment advice, and
nothing in it constitutes a recommendation to buy or sell any security. Use
the paper trading endpoint until you have a very good reason not to.

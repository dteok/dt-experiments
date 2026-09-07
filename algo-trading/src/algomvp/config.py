"""Central configuration for the whole application.

Every tunable value and every secret lives here, and nowhere else. Modules ask
this file for settings rather than reading environment variables themselves.

The reason is testability. If ten modules each call ``os.environ`` directly,
there is no single place to override behaviour in a test, and no single place
to look when something is misconfigured. One object, imported everywhere, is
easier to reason about -- "there should be one obvious way to do it".

Secrets come from a ``.env`` file that is never committed. See ``.env.example``.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# The project root is two levels above this file: src/algomvp/config.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings, loaded from environment variables or ``.env``.

    Attribute names are matched against environment variables
    case-insensitively, so ``TIINGO_API_KEY`` in the environment populates
    ``tiingo_api_key`` here.
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Credentials --------------------------------------------------------
    tiingo_api_key: str = ""
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""

    # Alpaca's paper endpoint. Changing this to the live endpoint is the only
    # difference between simulated and real money, which is exactly why it is
    # a named setting rather than a string buried in the broker module.
    alpaca_base_url: str = "https://paper-api.alpaca.markets"

    # --- Data source --------------------------------------------------------
    tiingo_base_url: str = "https://api.tiingo.com"

    # Tiingo's free tier permits 50 requests per hour. The power tier permits
    # 5000. Set this to match your plan; the client throttles itself to it.
    tiingo_requests_per_hour: int = 50

    # --- Paths --------------------------------------------------------------
    # raw_dir holds responses exactly as received, and is never edited. When a
    # backtest result surprises you, the first question is always "is the data
    # wrong?", and you need an untouched copy to answer it.
    raw_dir: Path = PROJECT_ROOT / "data" / "raw"
    curated_dir: Path = PROJECT_ROOT / "data" / "curated"
    config_dir: Path = PROJECT_ROOT / "config"

    def ensure_directories(self) -> None:
        """Create the data directories if they do not already exist."""
        for directory in (self.raw_dir, self.curated_dir):
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Return the shared settings object, building it on first use.

    ``lru_cache`` is the one decorator used in this module. It means the
    ``Settings`` object is constructed once and the same instance is handed
    back on every later call, rather than re-reading the ``.env`` file each
    time. Import this function, not a module-level ``settings`` variable, so
    that tests can clear the cache and substitute their own values.
    """
    return Settings()

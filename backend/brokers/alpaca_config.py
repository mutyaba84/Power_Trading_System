import os
from pathlib import Path
from dotenv import load_dotenv

# Always load .env from project root
ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"

load_dotenv(ENV_PATH)


def get_alpaca_config():
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    symbol = os.getenv("ALPACA_SYMBOL", "SPY")

    if not api_key or not secret_key:
        raise RuntimeError("❌ Alpaca API keys missing (check .env loading)")

    return {
        "key_id": api_key,
        "secret_key": secret_key,
        "base_url": base_url,
        "symbol": symbol,
    }

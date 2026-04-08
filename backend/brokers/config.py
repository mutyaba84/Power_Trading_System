def get_alpaca_config():
    import os
    from dotenv import load_dotenv
    ENV_PATH = os.path.join(os.path.dirname(__file__), "../../.env")
    load_dotenv(ENV_PATH, override=True)

    api_key = os.environ["ALPACA_API_KEY"]
    secret_key = os.environ["ALPACA_SECRET_KEY"]

    return {
        "api_key": api_key.strip(),
        "secret_key": secret_key.strip(),
        "symbol": os.getenv("ALPACA_SYMBOL", "SPY"),
        "paper": os.getenv("ALPACA_PAPER", "true").lower() == "true",
    }
import os
from alpaca_trade_api.rest import REST

print("Testing Alpaca API connection...")

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = "https://paper-api.alpaca.markets"

if not API_KEY or not SECRET_KEY:
    print("❌ API keys not found in environment")
    exit()

try:
    api = REST(API_KEY, SECRET_KEY, BASE_URL)

    account = api.get_account()

    print("✅ Connected to Alpaca successfully")
    print("Account Status:", account.status)
    print("Equity:", account.equity)
    print("Buying Power:", account.buying_power)

except Exception as e:
    print("❌ Connection failed")
    print(e)
import os
from dotenv import load_dotenv
from alpaca_trade_api.rest import REST, TimeFrame

load_dotenv()

API_KEY = os.getenv("APCA_API_KEY_ID")
SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
SYMBOL = os.getenv("ALPACA_SYMBOL", "SPY")

print("🔍 Testing Alpaca API connection...")
print(f"Base URL: {BASE_URL}")
print(f"Symbol: {SYMBOL}")

if not API_KEY or not SECRET_KEY:
    raise RuntimeError("❌ Alpaca API keys not found in environment")

api = REST(API_KEY, SECRET_KEY, BASE_URL)

# ---- Account test ----
try:
    account = api.get_account()
    print("✅ Account connected!")
    print(f"Account ID: {account.id}")
    print(f"Equity: {account.equity}")
    print(f"Cash: {account.cash}")
except Exception as e:
    print("❌ Account connection failed")
    raise

# ---- Market data test ----
try:
    bars = api.get_bars(SYMBOL, TimeFrame.Minute, limit=3)
    print(f"\n✅ Got {len(bars)} bars for {SYMBOL}:")
    for bar in bars:
        print(f"{bar.t}  O:{bar.o} H:{bar.h} L:{bar.l} C:{bar.c} V:{bar.v}")
except Exception as e:
    print("❌ Market data request failed")
    raise

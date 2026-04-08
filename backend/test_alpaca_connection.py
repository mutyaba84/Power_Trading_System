from backend.brokers.alpaca_client import AlpacaClient

print("🔍 Testing Alpaca API (isolated)...")

client = AlpacaClient()

# AUTH
account = client.ping()
print("\n✅ AUTH OK")
print("Equity:", account.equity)

# MARKET DATA TEST
try:
    trade = client.get_latest_trade("SPY")

    if trade:
        print("\n📊 TRADE DATA RECEIVED")
        print("Price:", trade.price)
        print("Time:", trade.timestamp)
    else:
        print("\n⚠️ NO TRADE DATA")

except Exception as e:
    print("\n❌ Trade fetch failed:", str(e))
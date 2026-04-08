import backend.brokers.alpaca_client as mod
print("USING FILE:", mod.__file__)

from backend.brokers.alpaca_client import AlpacaClient

print("\n🔍 Testing Alpaca MARKET DATA...")

client = AlpacaClient()

# AUTH
account = client.ping()
print("\n✅ AUTH OK")
print("Equity:", account.equity)

# MARKET DATA
print("\n📊 Requesting latest trade...")

try:
    trade = client.get_latest_trade()

    if trade:
        print("✅ TRADE RECEIVED")
        print("Price:", trade.price)
        print("Time:", trade.timestamp)
    else:
        print("❌ NO TRADE DATA")

except Exception as e:
    print("❌ ERROR:", str(e))
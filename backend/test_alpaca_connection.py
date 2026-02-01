from backend.brokers.alpaca_client import AlpacaClient

print("🔍 Testing Alpaca API (isolated)...")

try:
    client = AlpacaClient()

    account = client.ping()
    print("✅ AUTH OK")
    print("Account ID:", account.id)
    print("Cash:", account.cash)
    print("Status:", account.status)

    bar = client.get_latest_bar()
    if bar:
        print("📈 Market Data OK")
        print("Symbol:", bar.S)
        print("Close:", bar.c)
        print("Time:", bar.t)
    else:
        print("⚠️ No market data returned")

except Exception as e:
    print("❌ Alpaca connection FAILED")
    raise

import time
import sys
import json
from pathlib import Path
from ai_core.integrative_decision_kernel import IntegrativeDecisionKernel
from backend.brokers.alpaca_broker import AlpacaBroker

EXTERNAL_MEMORY = Path("D:/AI_Trading_Storage")
AI_STATE_DIR = EXTERNAL_MEMORY / "ai_state"
AI_STATE_DIR.mkdir(parents=True, exist_ok=True)

RUN_INTERVAL = 5  # seconds

def save_json(filename, data):
    with (AI_STATE_DIR / filename).open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def main():
    mode = "paper"
    if len(sys.argv) > 1 and sys.argv[1] == "--live":
        mode = "live"

    print(f"🚀 Power Trading System Runner Initialized | Mode={mode.upper()}")
    kernel = IntegrativeDecisionKernel()

    broker = None
    if mode == "live":
        try:
            broker = AlpacaBroker()
            broker.connect()
            print("✅ Connected to Alpaca Broker")
        except Exception as e:
            print(f"❌ Failed to connect to broker: {e}")
            return

    try:
        while True:
            decision = kernel.compute_action()
            decision['timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%S")
            save_json("decision_kernel_state.json", decision)

            if mode == "live":
                try:
                    account = broker.get_account()
                    max_equity = float(account.cash)

                    qty = int(max_equity * decision['scaled_confidence'] * 0.1)

                    if decision['action_score'] > 0:
                        broker.place_order("AAPL", qty, "buy")
                    elif decision['action_score'] < 0:
                        broker.place_order("AAPL", qty, "sell")

                except Exception as e:
                    print(f"⚠️ Live trading error: {e}")
                    qty = 0
                    max_equity = 0

                live_state = {
                    "timestamp": decision['timestamp'],
                    "equity": max_equity,
                    "positions": qty
                }
                save_json("live_trading_state.json", [live_state])

                market_overview = {
                    "trend": "Bullish" if decision['action_score'] > 0 else "Bearish",
                    "volatility": abs(decision['action_score']) * 10,
                    "top_movers": ["AAPL", "TSLA", "BTC-USD"],
                    "signal_strength": abs(decision['scaled_confidence'])
                }
                save_json("market_overview.json", market_overview)

                sentiment_state = {
                    "overall": decision['scaled_confidence'],
                    "positive": int(decision['scaled_confidence'] * 10),
                    "negative": int((1 - decision['scaled_confidence']) * 5),
                    "neutral": 2,
                    "vix": 22.5
                }
                save_json("sentiment_state.json", sentiment_state)

            time.sleep(RUN_INTERVAL)

    except KeyboardInterrupt:
        print("🛑 Live Trading halted by user.")

if __name__ == "__main__":
    main()

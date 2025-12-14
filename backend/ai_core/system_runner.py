import time
import sys
import json
import os
from pathlib import Path
from ai_core.integrative_decision_kernel import IntegrativeDecisionKernel
from backend.brokers.alpaca_broker import AlpacaBroker
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()  # loads .env in current directory
EXTERNAL_MEMORY = Path(os.getenv("AI_STORAGE_PATH", Path(__file__).parent / "external_storage"))
AI_STATE_DIR = EXTERNAL_MEMORY / "ai_state"
AI_STATE_DIR.mkdir(parents=True, exist_ok=True)

AI_LOG_DIR = Path(os.getenv("AI_LOG_PATH", EXTERNAL_MEMORY / "logs"))
AI_LOG_DIR.mkdir(parents=True, exist_ok=True)

RUN_INTERVAL = 5  # seconds

def save_json(filename, data):
    path = AI_STATE_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def main():
    mode = os.getenv("AI_MODE", "paper").lower()
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "--live":
            mode = "live"
        elif sys.argv[1].lower() == "--paper":
            mode = "paper"

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

            if mode == "live" and broker:
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

            # Market Overview & Sentiment (paper/live)
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
        print("🛑 Trading halted by user.")

if __name__ == "__main__":
    main()

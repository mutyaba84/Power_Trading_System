import { useEffect, useState } from "react";
import { getStatus, getSettings, updateSettings } from "../api";

export default function Dashboard() {
  const [data, setData] = useState({});
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState("--");

  const [settings, setSettings] = useState({
    deploy_pct: 0.25,
    max_exposure_pct: 0.25,
    risk_per_trade: 0.01,
    trading_enabled: true,
  });

  useEffect(() => {
    const fetchData = async () => {
      const res = await getStatus();

      if (res && Object.keys(res).length > 0) {
        setConnected(true);
        setData(res);
        setLastUpdate(new Date().toLocaleTimeString());
      } else {
        setConnected(false);
      }
    };

    const fetchSettings = async () => {
      const cfg = await getSettings();
      if (cfg) {
        const clean = cfg.settings ? cfg.settings : cfg;
        setSettings((prev) => ({ ...prev, ...clean }));
      }
    };

    fetchData();
    fetchSettings();

    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

  const update = async (key, value) => {
    const updated = { ...settings, [key]: value };
    setSettings(updated);

    try {
      await updateSettings(updated);
    } catch (err) {
      console.error("Settings update failed:", err);
    }
  };

  const fmtMoney = (value) =>
    typeof value === "number" && !Number.isNaN(value)
      ? `$${value.toFixed(2)}`
      : "--";

  const fmtNumber = (value, decimals = 2) =>
    typeof value === "number" && !Number.isNaN(value)
      ? value.toFixed(decimals)
      : "--";

  const exposure =
    data.total_equity && data.price && data.qty
      ? (data.qty * data.price) / data.total_equity
      : 0;

  const pnlClass = (value) =>
    Number(value || 0) >= 0 ? "pnl-positive" : "pnl-negative";

  return (
    <div className="container">
      <h1>⚡ Power Trading System</h1>

      <div className="status">
        {connected ? "🟢 ONLINE" : "🔴 OFFLINE"}
        <span className="status-divider">|</span>
        Trading:{" "}
        <strong>{settings.trading_enabled ? "ENABLED" : "DISABLED"}</strong>
        <span className="status-divider">|</span>
        Last Update: {lastUpdate}
      </div>

      <div className="grid-3">
        <div className="card">
          <h3>📊 Market</h3>
          <p>Price: {fmtNumber(data.price)}</p>
        </div>

        <div className="card">
          <h3>🤖 Trading</h3>
          <p>Action: {data.last_action ?? "--"}</p>
          <p>Position: {data.position ?? "--"}</p>
          <p>Qty: {data.qty ?? 0}</p>
          <p>Entry: {fmtNumber(data.entry_price)}</p>
        </div>

        <div className="card">
          <h3>💰 Account</h3>
          <p>Total Equity: {fmtMoney(data.total_equity)}</p>
          <p>Deployable: {fmtMoney(data.deployable_capital)}</p>
          <p>Cash: {fmtMoney(data.cash)}</p>
          <p>Buying Power: {fmtMoney(data.buying_power)}</p>
          <p>Exposure: {(exposure * 100).toFixed(2)}%</p>
        </div>
      </div>

      <div className="grid-3">
        <div className="card">
          <h3>📈 Unrealized PnL</h3>
          <p className={pnlClass(data.unrealized_pnl)}>
            {fmtMoney(data.unrealized_pnl)}
          </p>
        </div>

        <div className="card">
          <h3>💵 Realized PnL</h3>
          <p className={pnlClass(data.realized_pnl)}>
            {fmtMoney(data.realized_pnl)}
          </p>
        </div>

        <div className="card">
          <h3>⚠️ Margin Pressure</h3>
          <p>{((Number(data.margin_pressure) || 0) * 100).toFixed(2)}%</p>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>⚙️ Risk Controls</h3>

          <label>Capital Allocation: {(settings.deploy_pct * 100).toFixed(0)}%</label>
          <input
            type="range"
            min="0.01"
            max="1"
            step="0.01"
            value={settings.deploy_pct}
            onChange={(e) => update("deploy_pct", parseFloat(e.target.value))}
          />

          <label>Max Exposure: {(settings.max_exposure_pct * 100).toFixed(0)}%</label>
          <input
            type="range"
            min="0.01"
            max="1"
            step="0.01"
            value={settings.max_exposure_pct}
            onChange={(e) =>
              update("max_exposure_pct", parseFloat(e.target.value))
            }
          />

          <label>Risk Per Trade: {(settings.risk_per_trade * 100).toFixed(2)}%</label>
          <input
            type="range"
            min="0.001"
            max="0.05"
            step="0.001"
            value={settings.risk_per_trade}
            onChange={(e) =>
              update("risk_per_trade", parseFloat(e.target.value))
            }
          />
        </div>

        <div className="card">
          <h3>🚨 Controls</h3>

          <button
            className="btn-stop"
            onClick={() => update("trading_enabled", false)}
          >
            🛑 STOP TRADING
          </button>

          <button
            className="btn-start"
            onClick={() => update("trading_enabled", true)}
          >
            ▶️ RESUME
          </button>

          <p className="control-state">
            Trading State:{" "}
            <strong>{settings.trading_enabled ? "ENABLED" : "DISABLED"}</strong>
          </p>
        </div>
      </div>

      <div className="card">
        <h3>📜 Trade Tape</h3>
        <div className="logs">
          <ul>
            {(data.trades || []).slice(-10).reverse().map((trade, i) => (
              <li key={i} className="trade-row">
                Qty: {trade.qty ?? "--"} | Entry:{" "}
                {typeof trade.entry === "number" ? trade.entry.toFixed(2) : "--"} |
                Exit:{" "}
                {typeof trade.exit === "number" ? trade.exit.toFixed(2) : "--"} |
                PnL:{" "}
                {typeof trade.pnl === "number" ? trade.pnl.toFixed(2) : "--"}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="card">
        <h3>🧾 Logs</h3>
        <div className="logs">
          <ul>
            {(data.logs || []).slice(-20).map((log, i) => (
              <li key={i}>{log}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
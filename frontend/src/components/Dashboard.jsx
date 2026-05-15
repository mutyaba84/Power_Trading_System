import { useEffect, useState } from "react";
import { getStatus, getSettings, updateSettings } from "../api";

export default function Dashboard() {
  const [data, setData] = useState({});
  const [connected, setConnected] = useState(false);

  const [settings, setSettings] = useState({
    deploy_pct: 0.25,
    max_exposure_pct: 0.25,
    risk_per_trade: 0.01,
    trading_enabled: true,
  });

  // -------------------------
  // LOAD DATA
  // -------------------------
  useEffect(() => {
    const fetchData = async () => {
      const res = await getStatus();

      if (res && res.price !== undefined) {
        setConnected(true);
        setData(res);
      } else {
        setConnected(false);
      }
    };

    const fetchSettings = async () => {
      const cfg = await getSettings();
      if (cfg) setSettings((prev) => ({ ...prev, ...cfg }));
    };

    fetchData();
    fetchSettings();

    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

  // -------------------------
  // UPDATE SETTINGS
  // -------------------------
  const update = (key, value) => {
    const updated = { ...settings, [key]: value };
    setSettings(updated);
    updateSettings(updated);
  };

  // -------------------------
  // DERIVED METRICS
  // -------------------------
  const exposure =
    data.position !== "flat"
      ? (data.qty * data.price) / data.total_equity
      : 0;

  return (
    <div className="container">
      <h1>⚡ Power Trading System</h1>

      <div className="status">
        Status: {connected ? "🟢 ONLINE" : "🔴 OFFLINE"}
      </div>

      {/* ========================= */}
      {/* TOP GRID */}
      {/* ========================= */}
      <div className="grid-3">

        {/* MARKET */}
        <div className="card">
          <h3>📊 Market</h3>
          <p>Price: {data.price?.toFixed?.(2)}</p>
        </div>

        {/* TRADING */}
        <div className="card">
          <h3>🤖 Trading</h3>
          <p>Action: {data.last_action}</p>
          <p>Position: {data.position}</p>
        </div>

        {/* ACCOUNT */}
        <div className="card">
          <h3>💰 Account</h3>
          <p>Total Equity: {data.total_equity?.toFixed?.(2)}</p>
          <p>Deployable: {data.deployable_capital?.toFixed?.(2)}</p>
          <p>Exposure: {(exposure * 100).toFixed(2)}%</p>
        </div>

      </div>




          {/* ========================= */}
          {     /* PNL PANEL */}
          {/* ========================= */}
        <div className="grid-3">

        <div className="card">
           <h3>📈 Unrealized PnL</h3>
         <p>
         ${data.unrealized_pnl?.toFixed?.(2)}
         </p>
       </div>

     <div className="card">
      <h3>💵 Realized PnL</h3>
       <p>
            ${data.realized_pnl?.toFixed?.(2)}
       </p>
     </div>

     <div className="card">
      <h3>⚠️ Margin Pressure</h3>
      <p>
         {(data.margin_pressure * 100)?.toFixed?.(2)}%
      </p>
      </div>

     </div>

      {/* ========================= */}
      {/* CONTROL GRID */}
      {/* ========================= */}
      <div className="grid-2">

        {/* RISK CONTROLS */}
        <div className="card">
          <h3>⚙️ Risk Controls</h3>

          <label>
            Capital Allocation: {(settings.deploy_pct * 100).toFixed(0)}%
          </label>
          <input
            type="range"
            min="0.01"
            max="1"
            step="0.01"
            value={settings.deploy_pct}
            onChange={(e) =>
              update("deploy_pct", parseFloat(e.target.value))
            }
          />

          <label>
            Max Exposure: {(settings.max_exposure_pct * 100).toFixed(0)}%
          </label>
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

          <label>
            Risk Per Trade: {(settings.risk_per_trade * 100).toFixed(2)}%
          </label>
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

        {/* KILL SWITCH */}
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
        </div>

      </div>
      {/* ========================= */}
      { /* TRADE TAPE */}
      {/* ========================= */}
     <div className="card">
     <h3>📜 Trade Tape</h3>

        <div className="logs">
          <ul>
            {(data.trades || []).slice(-10).reverse().map((trade, i) => (
             <li key={i}>
                Qty: {trade.qty} |
                Entry: {trade.entry?.toFixed?.(2)} |
                Exit: {trade.exit?.toFixed?.(2)} |
                PnL: {trade.pnl?.toFixed?.(2)}
             </li>
          ))}
        </ul>
      </div>
</div>

      

      {/* ========================= */}
      {/* LOGS */}
      {/* ========================= */}
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
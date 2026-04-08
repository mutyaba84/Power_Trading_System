import { useEffect, useState } from "react";
import { getStatus } from "../api";

export default function Dashboard() {
  const [data, setData] = useState({});
  const [connected, setConnected] = useState(false);

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

    fetchData();
    const interval = setInterval(fetchData, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h1>⚡ Power Trading System</h1>

      <p>Status: {connected ? "🟢 ONLINE" : "🔴 OFFLINE"}</p>

      <hr />

      <h2>📊 Market</h2>
      <p>Price: {data.price?.toFixed?.(2)}</p>

      <h2>🤖 Trading</h2>
      <p>Action: {data.last_action}</p>
      <p>Position: {data.position}</p>

      <h2>💰 Account</h2>
      <p>Equity: {data.equity?.toFixed?.(2)}</p>

      <h2>🧾 Logs</h2>
      <div style={{ maxHeight: "200px", overflowY: "auto" }}>
        <ul>
          {(data.logs || []).slice(-15).map((log, i) => (
            <li key={i}>{log}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
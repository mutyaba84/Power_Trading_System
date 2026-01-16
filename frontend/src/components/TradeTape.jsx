import { useEffect, useState } from "react";
import Card from "./Card.jsx";
import { getTrades } from "../api.js";

export default function TradeTape() {
  const [trades, setTrades] = useState([]);
  const [status, setStatus] = useState("LOADING");

  useEffect(() => {
    let alive = true;

    const fetchTrades = async () => {
      try {
        const data = await getTrades();
        if (!alive) return;

        const list = Array.isArray(data?.trades) ? data.trades : [];
        setTrades(list.slice(-20).reverse());
        setStatus("OK");
      } catch {
        if (!alive) return;
        setTrades([]);
        setStatus("OFFLINE");
      }
    };

    fetchTrades();
    const id = setInterval(fetchTrades, 2000);

    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  return (
    <Card title="Trade Tape">
      {status === "LOADING" && <div>Loading…</div>}
      {status === "OFFLINE" && <div>Unavailable</div>}

      {status === "OK" && trades.length === 0 && (
        <div>No trades yet</div>
      )}

      {status === "OK" && trades.length > 0 && (
        <div style={{ fontSize: 12 }}>
          {trades.map((t, i) => (
            <div key={i} style={{ opacity: 0.85 }}>
              {new Date((t.ts || Date.now()) * 1000).toLocaleTimeString()}{" "}
              <strong>{t.action}</strong>{" "}
              @{t.price?.toFixed(2) ?? "—"}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

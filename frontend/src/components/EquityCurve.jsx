import { useEffect, useState } from "react";
import Card from "./Card.jsx";
import { buildEquitySeries } from "./equity.js";
import EquityChart from "./EquityChart.jsx";
import { getTrades } from "../api.js";

export default function EquityCurve() {
  const [series, setSeries] = useState([]);
  const [status, setStatus] = useState("LOADING");

  useEffect(() => {
    let alive = true;

    const fetchTrades = async () => {
      try {
        const data = await getTrades();
        if (!alive) return;

        const trades = Array.isArray(data?.trades) ? data.trades : [];
        const eq = buildEquitySeries(trades, 10000);

        setSeries(eq.slice(-30));
        setStatus("OK");
      } catch {
        if (!alive) return;
        setSeries([]);
        setStatus("OFFLINE");
      }
    };

    fetchTrades();
    const id = setInterval(fetchTrades, 3000);

    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  return (
    <Card title="Equity Curve">
      {status === "LOADING" && <div>Loading…</div>}

      {status === "OFFLINE" && (
        <div style={{ opacity: 0.7 }}>Unavailable</div>
      )}

      {status === "OK" && series.length === 0 && (
        <div>No equity data yet</div>
      )}

      {status === "OK" && series.length > 0 && (
        <>
          <EquityChart series={series} />

          <div
            style={{
              marginTop: 8,
              fontSize: 12,
              display: "flex",
              justifyContent: "space-between",
              opacity: 0.7,
            }}
          >
            <span>
              Min: {Math.min(...series.map(s => s.equity)).toFixed(2)}
            </span>
            <span>
              Max: {Math.max(...series.map(s => s.equity)).toFixed(2)}
            </span>
          </div>
        </>
      )}
    </Card>
  );
}

import { useEffect, useMemo, useState } from "react";
import { getSystemStatus, getLogs } from "../api";
import { Card } from "./ui/card";

function fmtTime(ts) {
  if (!ts) return "—";
  try {
    return new Date(ts * 1000).toLocaleTimeString();
  } catch {
    return "—";
  }
}

function safeNum(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

export default function Dashboard() {
  const [status, setStatus] = useState({});
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      try {
        setError("");
        const statusData = await getSystemStatus();
        const logData = await getLogs();

        if (mounted) {
          setStatus(statusData || {});
          setLogs(Array.isArray(logData?.events) ? logData.events : []);
        }
      } catch (err) {
        if (mounted) setError(String(err));
      }
    };

    load();
    const interval = setInterval(load, 2000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const equity = safeNum(status?.equity);
  const riskLimit = safeNum(status?.risk_limit);
  const freeMem = safeNum(status?.free_memory_gb);

  const statusText = status?.status ?? "—";
  const equityText = equity != null ? `$${equity.toFixed(2)}` : "—";
  const riskLimitText = riskLimit != null ? `${(riskLimit * 100).toFixed(2)}%` : "—";
  const freeMemText = freeMem != null ? `${freeMem.toFixed(2)} GB` : "—";

  const prettyLogs = useMemo(() => {
    return (logs || []).slice(0, 50).map((e) => {
      const ts = e?.ts ?? e?.timestamp;
      const event = e?.event ?? e?.type ?? "event";
      const mood = e?.market_mood ?? e?.payload?.market_mood;
      const conf = safeNum(e?.confidence ?? e?.payload?.confidence);
      const vol = safeNum(e?.volatility ?? e?.payload?.volatility);

      let summary = "";
      if (event.includes("sentiment")) {
        summary = `${mood ?? "—"}${conf != null ? ` • conf ${conf.toFixed(2)}` : ""}${
          vol != null ? ` • vol ${vol.toFixed(2)}` : ""
        }`;
      } else if (event.includes("status")) {
        summary = `equity ${equityText} • risk ${riskLimitText} • free ${freeMemText}`;
      } else {
        summary = "";
      }

      return {
        key: `${event}-${ts}-${Math.random()}`,
        time: fmtTime(ts),
        event,
        summary,
        raw: e,
      };
    });
  }, [logs, equityText, riskLimitText, freeMemText]);

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 2fr",
        gap: 16,
        padding: 20,
      }}
    >
      <Card>
        <h2 style={{ fontSize: 18, marginBottom: 10, fontWeight: 700 }}>
          System Status
        </h2>

        {error && (
          <p style={{ color: "#ff6b6b", marginBottom: 10 }}>
            Error: {error}
          </p>
        )}

        <p>
          Status: <strong>{statusText}</strong>
        </p>
        <p>Equity: {equityText}</p>
        <p>Risk Limit: {riskLimitText}</p>
        <p>Free Memory: {freeMemText}</p>
      </Card>

      <Card>
        <h2 style={{ fontSize: 18, marginBottom: 10, fontWeight: 700 }}>
          Recent Activity
        </h2>

        <div style={{ maxHeight: 420, overflow: "auto", fontSize: 13 }}>
          {prettyLogs.length === 0 ? (
            <p style={{ opacity: 0.7 }}>No activity yet</p>
          ) : (
            prettyLogs.map((row) => (
              <div
                key={row.key}
                style={{
                  borderBottom: "1px solid #2a2a2a",
                  padding: "10px 0",
                }}
              >
                <div style={{ display: "flex", gap: 12, alignItems: "baseline" }}>
                  <span style={{ opacity: 0.7, fontSize: 12, minWidth: 80 }}>
                    {row.time}
                  </span>
                  <strong style={{ fontSize: 13 }}>{row.event}</strong>
                </div>

                {row.summary && (
                  <div style={{ marginTop: 6, opacity: 0.9 }}>
                    {row.summary}
                  </div>
                )}

                <details style={{ marginTop: 8, opacity: 0.8 }}>
                  <summary style={{ cursor: "pointer" }}>raw</summary>
                  <pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>
                    {JSON.stringify(row.raw, null, 2)}
                  </pre>
                </details>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}

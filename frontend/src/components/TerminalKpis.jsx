import { useEffect, useState } from "react";
import Card from "./Card.jsx";
import { getStatus } from "../api.js";

export default function TerminalKpis() {
  const [status, setStatus] = useState("UNKNOWN");
  const [equity, setEquity] = useState(null);

  useEffect(() => {
    let alive = true;

    const load = async () => {
      try {
        const data = await getStatus();
        if (!alive) return;
        setStatus("ONLINE");
        setEquity(data?.equity ?? null);
      } catch {
        if (!alive) return;
        setStatus("OFFLINE");
        setEquity(null);
      }
    };

    load();
    const id = setInterval(load, 3000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  return (
    <Card title="Terminal KPIs">
      <div>Status: {status}</div>
      <div style={{ marginTop: 6 }}>
        Equity: {equity ?? "—"}
      </div>
    </Card>
  );
}

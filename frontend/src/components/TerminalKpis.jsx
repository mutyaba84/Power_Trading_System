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
        setEquity(
          typeof data?.equity === "number"
            ? data.equity.toFixed(2)
            : null
        );
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

  const statusClass =
    status === "ONLINE"
      ? "badge badge-green"
      : status === "OFFLINE"
      ? "badge badge-red"
      : "badge badge-yellow";

  return (
  <Card title="🧾 Terminal KPIs">
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        background: "red",
        padding: 8,
      }}
    >
      <span>Status</span>
      <span>ONLINE</span>
    </div>
  </Card>
);

}

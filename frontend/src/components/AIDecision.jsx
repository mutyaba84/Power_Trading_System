import { useEffect, useState } from "react";
import Card from "./Card.jsx";
import { getDecision } from "../api.js";

export default function AIDecision() {
  const [decision, setDecision] = useState(null);
  const [status, setStatus] = useState("LOADING");

  useEffect(() => {
    let alive = true;

    const load = async () => {
      try {
        const data = await getDecision();
        if (!alive) return;
        setDecision(data);
        setStatus("OK");
      } catch {
        if (!alive) return;
        setDecision(null);
        setStatus("OFFLINE");
      }
    };

    load();
    const id = setInterval(load, 2000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  return (
    <Card title="AI Decision">
      {status === "LOADING" && <div>Loading…</div>}
      {status === "OFFLINE" && <div>Unavailable</div>}
      {status === "OK" && (
        <>
          <div>
            Action: <b>{decision?.action ?? "—"}</b>
          </div>
          <div style={{ marginTop: 6 }}>
            Confidence: {decision?.confidence ?? decision?.scaled_confidence ?? "—"}
          </div>
        </>
      )}
    </Card>
  );
}

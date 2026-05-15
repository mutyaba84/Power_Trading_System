import { useState } from "react";
import Card from "./Card.jsx";
import { startController, stopController } from "../api.js";

export default function ControllerControls() {
  const [status, setStatus] = useState("IDLE");
  const [busy, setBusy] = useState(false);

  const run = async (fn, label) => {
    setBusy(true);
    setStatus(`${label}…`);

    try {
      await fn();
      setStatus(`${label} OK`);
    } catch (err) {
      console.warn("Controller error:", err);
      setStatus(`${label} FAILED`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title="Controller">
      <div style={{ display: "flex", gap: 12 }}>
        <button
          onClick={() => run(startController, "START")}
          disabled={busy}
        >
          Start
        </button>
        <button
          onClick={() => run(stopController, "STOP")}
          disabled={busy}
        >
          Stop
        </button>
      </div>

      <div style={{ marginTop: 10, fontSize: 13 }}>
        Status: {status}
      </div>
    </Card>
  );
}

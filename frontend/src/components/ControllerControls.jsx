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
      <div className="terminal-buttons">
        <button
          className="terminal-btn btn-start"
          onClick={() => run(startController, "START")}
          disabled={busy}
        >
          Start
        </button>

        <button
          className="terminal-btn btn-stop"
          onClick={() => run(stopController, "STOP")}
          disabled={busy}
        >
          Stop
        </button>
      </div>

      <div className="terminal-row">
        <span className="terminal-label">Status</span>
        <span className="terminal-value">{status}</span>
      </div>
    </Card>
  );
}
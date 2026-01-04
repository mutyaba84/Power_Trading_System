import { useEffect, useState } from "react";
import Dashboard from "./components/Dashboard.jsx";
import { getSentiment } from "./api.js";
import { Card } from "./components/ui/card.jsx";

export default function App() {
  const [sentiment, setSentiment] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      try {
        setErr("");
        const data = await getSentiment();
        if (mounted) setSentiment(data);
      } catch (e) {
        if (mounted) setErr(String(e));
      }
    };

    load();
    const t = setInterval(load, 2000);
    return () => {
      mounted = false;
      clearInterval(t);
    };
  }, []);

  return (
    <div>
      <div style={{ padding: 20 }}>
        <Card>
          <h1 style={{ margin: 0, fontSize: 22 }}>Power Trading System</h1>
          <p style={{ marginTop: 8, opacity: 0.8 }}>
            Backend: <code>http://localhost:8000</code> | Frontend: <code>http://localhost:3000</code>
          </p>
          {err && <p style={{ color: "#ff6b6b" }}>Sentiment Error: {err}</p>}
          <pre style={{ marginTop: 10, whiteSpace: "pre-wrap" }}>
            {sentiment ? JSON.stringify(sentiment, null, 2) : "Loading sentiment..."}
          </pre>
        </Card>
      </div>

      <Dashboard />
    </div>
  );
}

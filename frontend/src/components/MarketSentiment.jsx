import { useEffect, useState } from "react";
import Card from "./Card.jsx";
import { getSentiment } from "../api.js";

export default function MarketSentiment() {
  const [sentiment, setSentiment] = useState(null);
  const [status, setStatus] = useState("LOADING");

  useEffect(() => {
    let alive = true;

    const load = async () => {
      try {
        const data = await getSentiment();
        if (!alive) return;
        setSentiment(data);
        setStatus("OK");
      } catch {
        if (!alive) return;
        setSentiment(null);
        setStatus("OFFLINE");
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
    <Card title="Market Sentiment">
      {status === "LOADING" && <div>Loading…</div>}
      {status === "OFFLINE" && <div>Unavailable</div>}
      {status === "OK" && (
        <>
          <div>Confidence: {sentiment?.confidence ?? "—"}</div>
          <div>Volatility: {sentiment?.volatility ?? "—"}</div>
          <div>Mood: {sentiment?.market_mood ?? sentiment?.mood ?? "—"}</div>
        </>
      )}
    </Card>
  );
}

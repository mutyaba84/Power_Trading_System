import { useEffect, useState } from "react";
import { getTraderState } from "../api";

export default function TraderStatus() {
  const [state, setState] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        setState(await getTraderState());
      } catch {}
    };

    load();
    const id = setInterval(load, 1000);
    return () => clearInterval(id);
  }, []);

  if (!state) return null;

  return (
    <div className="card">
      <h3>Trader State</h3>
      <p><b>Regime:</b> {state.regime}</p>
      <p><b>Strategy:</b> {state.strategy}</p>
      <p><b>Position:</b> {state.position}</p>
      <p><b>Equity:</b> ${state.equity.toFixed(2)}</p>

      <p>
        <b>Risk:</b>{" "}
        {state.risk.cooldown ? "COOLDOWN ACTIVE" : "OK"}
      </p>
    </div>
  );
}

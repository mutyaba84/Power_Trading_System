import { useEffect, useState } from "react";
import { fetchStatus, fetchLogs } from "../api";
import { Card } from "@/components/ui/card";

export default function Dashboard() {
  const [status, setStatus] = useState({});
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const interval = setInterval(async () => {
      setStatus(await fetchStatus());
      setLogs((await fetchLogs()).events);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="grid grid-cols-3 gap-4 p-6">
      <Card className="p-4 col-span-1">
        <h2 className="text-xl font-bold mb-2">System Status</h2>
        <p>Equity: ${status.equity?.toFixed(2)}</p>
        <p>Risk Limit: {status.risk_limit}</p>
        <p>Free Memory: {status.free_memory_gb?.toFixed(2)} GB</p>
      </Card>
      <Card className="p-4 col-span-2">
        <h2 className="text-xl font-bold mb-2">Recent Trades</h2>
        <ul className="max-h-96 overflow-auto text-sm">
          {logs.map((e, i) => (
            <li key={i} className="border-b border-gray-700 py-1">{e}</li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

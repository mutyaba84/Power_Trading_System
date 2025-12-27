import { useEffect, useState } from "react";
import { getSystemStatus, getLogs } from "../api";
import { Card } from "@/components/ui/card";

export default function Dashboard() {
  const [status, setStatus] = useState({});
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      try {
        const statusData = await getSystemStatus();
        const logData = await getLogs();

        if (mounted) {
          setStatus(statusData || {});
          setLogs(logData?.events || []);
        }
      } catch (err) {
        console.error("Dashboard fetch error:", err);
      }
    };

    load();
    const interval = setInterval(load, 2000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="grid grid-cols-3 gap-4 p-6">
      <Card className="p-4 col-span-1">
        <h2 className="text-xl font-bold mb-2">System Status</h2>
        <p>Equity: ${status.equity?.toFixed(2) ?? "—"}</p>
        <p>Risk Limit: {status.risk_limit ?? "—"}</p>
        <p>Free Memory: {status.free_memory_gb?.toFixed(2) ?? "—"} GB</p>
      </Card>

      <Card className="p-4 col-span-2">
        <h2 className="text-xl font-bold mb-2">Recent Activity</h2>
        <ul className="max-h-96 overflow-auto text-sm">
          {logs.length === 0 && (
            <li className="text-gray-400">No activity yet</li>
          )}

          {logs.map((e, i) => (
            <li key={i} className="border-b border-gray-700 py-1">
              <pre className="whitespace-pre-wrap text-xs">
                {JSON.stringify(e, null, 2)}
              </pre>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

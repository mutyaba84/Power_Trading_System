import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { getPaperTradingState } from '../api';

export default function EquityChart() {
  const [data, setData] = useState([]);

  useEffect(() => {
    const interval = setInterval(() => {
      const trades = getPaperTradingState() || [];
      setData(trades.map(t => ({ time: t.timestamp, equity: t.equity })));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-4 bg-gray-800 text-white rounded shadow">
      <h2 className="text-xl font-bold mb-2">Equity Curve</h2>
      <LineChart width={800} height={400} data={data}>
        <XAxis dataKey="time" />
        <YAxis />
        <Tooltip />
        <CartesianGrid stroke="#444" strokeDasharray="5 5" />
        <Line type="monotone" dataKey="equity" stroke="#82ca9d" strokeWidth={2} dot={false} />
      </LineChart>
    </div>
  );
}

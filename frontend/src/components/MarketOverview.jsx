import React, { useEffect, useState } from 'react';
import { readJSON } from '../api';

export default function MarketOverview() {
  const [market, setMarket] = useState({});

  useEffect(() => {
    const interval = setInterval(() => {
      const data = readJSON('market_overview.json') || {};
      setMarket(data);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-4 bg-gray-700 text-white rounded shadow mb-4">
      <h2 className="text-xl font-bold mb-2">Market Overview</h2>
      <p>Major Trend: {market.trend ?? 'N/A'}</p>
      <p>Current Volatility: {market.volatility?.toFixed(2) ?? 'N/A'}</p>
      <p>Top Movers: {market.top_movers?.join(', ') ?? 'N/A'}</p>
      <p>Signal Strength: {market.signal_strength?.toFixed(2) ?? 'N/A'}</p>
    </div>
  );
}

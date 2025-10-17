import React from 'react';
import Dashboard from "./components/Dashboard";

import EquityChart from './components/EquityChart';
import AIInsights from './components/AIInsights';
import SentimentDashboard from './components/SentimentDashboard';
import MarketOverview from './components/MarketOverview';
export default function App() {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <h1 className="text-3xl font-bold p-4">⚡ Power Trading System Dashboard</h1>
      <AIInsights />
      <EquityChart />
      <Dashboard />
      <SentimentDashboard />
      <MarketOverview />
    </div>
  );
}

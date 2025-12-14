import React, { useEffect, useState } from 'react';
import { readJSON } from '../api';

export default function SentimentDashboard() {
  const [sentiment, setSentiment] = useState({});

  useEffect(() => {
    const interval = setInterval(() => {
      const data = readJSON('sentiment_state.json') || {};
      setSentiment(data);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-4 bg-gray-700 text-white rounded shadow mb-4">
      <h2 className="text-xl font-bold mb-2">Market Sentiment</h2>
      <p>Overall Sentiment: {sentiment.overall?.toFixed(2) ?? 'N/A'}</p>
      <p>Positive Signals: {sentiment.positive ?? 0}</p>
      <p>Negative Signals: {sentiment.negative ?? 0}</p>
      <p>Neutral Signals: {sentiment.neutral ?? 0}</p>
      <p>Volatility Index (VIX): {sentiment.vix ?? 'N/A'}</p>
    </div>
  );
}

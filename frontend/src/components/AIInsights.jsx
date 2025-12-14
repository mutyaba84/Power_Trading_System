import React, { useEffect, useState } from 'react';
import { getLatestDecision } from '../api';

export default function AIInsights() {
  const [decision, setDecision] = useState({});

  useEffect(() => {
    const interval = setInterval(() => {
      const latest = getLatestDecision() || {};
      setDecision(latest);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-4 bg-gray-700 text-white rounded shadow mb-4">
      <h2 className="text-xl font-bold mb-2">AI Decision Insights</h2>
      <p>Strategy: {decision.strategy}</p>
      <p>Action Score: {decision.action_score?.toFixed(3)}</p>
      <p>Confidence: {decision.scaled_confidence?.toFixed(3)}</p>
      <p>Fusion Output: {decision.fusion_output}</p>
      <p>Quantum Expected: {decision.quantum_expected}</p>
      <p>Quantum Uncertainty: {decision.quantum_uncertainty}</p>
    </div>
  );
}

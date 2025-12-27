const API_BASE = "http://localhost:8000";

export async function fetchStatus() {
  const res = await fetch(`${API_BASE}/status`);
  return res.json();
}

export async function fetchLogs() {
  const res = await fetch(`${API_BASE}/logs`);
  return res.json();
}

export async function getSentiment() {
  const res = await fetch(`${API_BASE}/ai/sentiment`);
  return res.json();
}

export async function getLatestDecision() {
  const res = await fetch(`${API_BASE}/ai/decision`);
  return res.json();
}

export async function getPaperTradingState() {
  const res = await fetch(`${API_BASE}/ai/paper-state`);
  return res.json();
}

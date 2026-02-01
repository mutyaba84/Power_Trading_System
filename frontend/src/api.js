const API_BASE = "http://localhost:8000/api";

/* ---------- System ---------- */

export async function getStatus() {
  const r = await fetch(`${API_BASE}/system/status`);
  return r.json();
}

export async function getLogs() {
  const r = await fetch(`${API_BASE}/system/logs`);
  return r.json();
}

/* ---------- Trader ---------- */

export async function getTraderState() {
  const r = await fetch(`${API_BASE}/trader/state`);
  return r.json();
}

/* ---------- Controller ---------- */

export async function startController() {
  const r = await fetch(`${API_BASE}/controller/start`, { method: "POST" });
  return r.json();
}

export async function stopController() {
  const r = await fetch(`${API_BASE}/controller/stop`, { method: "POST" });
  return r.json();
}

/* ---------- AI ---------- */

export async function getDecision() {
  const r = await fetch(`${API_BASE}/ai/decision`);
  return r.json();
}

export async function getSentiment() {
  const r = await fetch(`${API_BASE}/ai/sentiment`);
  return r.json();
}

/* ---------- Trades ---------- */

export async function getTrades() {
  const r = await fetch(`${API_BASE}/trades`);
  return r.json();
}

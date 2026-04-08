const API_BASE = "http://127.0.0.1:8000";

/* ---------- CORE SYSTEM ---------- */

export async function getStatus() {
  try {
    const r = await fetch(`${API_BASE}/status`);
    return await r.json();
  } catch (err) {
    console.error("API ERROR:", err);
    return {};
  }
}
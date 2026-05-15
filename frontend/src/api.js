const API_BASE = "http://127.0.0.1:8000";

export async function getStatus() {
  try {
    const r = await fetch(`${API_BASE}/status`);
    return await r.json();
  } catch (err) {
    console.error("API ERROR:", err);
    return {};
  }
}

export async function getSettings() {
  try {
    const r = await fetch(`${API_BASE}/api/settings`);
    return await r.json();
  } catch (err) {
    console.error("SETTINGS ERROR:", err);
    return {};
  }
}

export async function updateSettings(settings) {
  try {
    const r = await fetch(`${API_BASE}/api/settings`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(settings),
    });

    return await r.json();
  } catch (err) {
    console.error("UPDATE ERROR:", err);
    return null;
  }
}

export async function startController() {
  return updateSettings({ trading_enabled: true });
}

export async function stopController() {
  return updateSettings({ trading_enabled: false });
}
const BASE_URL = "http://localhost:8000/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }

  try {
    return await res.json();
  } catch {
    return null;
  }
}

export function getStatus() {
  return request("/status");
}

/* ✅ ACTIVE + VALID */
export function getTraderState() {
  return request("/trader/state");
}

export function startController() {
  return request("/controller/start", { method: "POST" });
}

export function stopController() {
  return request("/controller/stop", { method: "POST" });
}

/* ❌ DISABLED (backend not exposing yet) */
// export function getSentiment() {
//   return request("/sentiment");
// }

// export function getDecision() {
//   return request("/decision/latest");
// }

// export function getTrades() {
//   return request("/trades");
// }

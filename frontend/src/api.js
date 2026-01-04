export async function getSystemStatus() {
  const r = await fetch("/status");
  if (!r.ok) throw new Error(`status ${r.status}`);
  return r.json();
}

export async function getLogs() {
  const r = await fetch("/logs");
  if (!r.ok) throw new Error(`logs ${r.status}`);
  return r.json();
}

export async function getSentiment() {
  const r = await fetch("/ai/sentiment");
  if (!r.ok) throw new Error(`sentiment ${r.status}`);
  return r.json();
}

export async function getTraderState() {
  const res = await fetch("/api/trader/state");
  if (!res.ok) throw new Error("Failed to fetch trader state");
  return res.json();
}

// Builds an equity time series from trades.
// Assumptions (simple + safe):
// - startEquity is a number
// - trade.pnl may exist, else we infer from BUY/SELL pairs
// - if nothing usable exists, equity stays flat

export function buildEquitySeries(trades, startEquity = 10000) {
  const series = [];
  let equity = Number(startEquity);

  if (!Number.isFinite(equity)) equity = 10000;

  let lastBuyPrice = null;

  for (const t of trades) {
    const action = String(t?.action ?? "").toUpperCase();
    const price = Number(t?.price);
    const pnl = Number(t?.pnl);

    // Prefer explicit pnl if backend provides it
    if (Number.isFinite(pnl)) {
      equity += pnl;
    } else if (action === "BUY" && Number.isFinite(price)) {
      lastBuyPrice = price;
    } else if (
      action === "SELL" &&
      Number.isFinite(price) &&
      Number.isFinite(lastBuyPrice)
    ) {
      equity += price - lastBuyPrice;
      lastBuyPrice = null;
    }

    series.push({
      t: t?.ts ?? Date.now(),
      equity,
    });
  }

  return series;
}

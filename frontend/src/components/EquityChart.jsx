export default function EquityChart({ series, width = 260, height = 120 }) {
  if (!Array.isArray(series) || series.length < 2) {
    return <div style={{ opacity: 0.6 }}>Not enough data</div>;
  }

  const values = series.map((p) => p.equity);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const points = series.map((p, i) => {
    const x = (i / (series.length - 1)) * width;
    const y = height - ((p.equity - min) / range) * height;
    return `${x},${y}`;
  });

  const lastEq = series[series.length - 1].equity;

  return (
    <>
      <svg
        width="100%"
        viewBox={`0 0 ${width} ${height}`}
        style={{ background: "#0f1620", borderRadius: 8 }}
      >
        <polyline
          points={points.join(" ")}
          fill="none"
          stroke="#4ade80"
          strokeWidth="2"
        />
      </svg>

      <div style={{ marginTop: 4, fontSize: 13 }}>
        Last Equity: {lastEq.toFixed(2)}
      </div>
    </>
  );
}

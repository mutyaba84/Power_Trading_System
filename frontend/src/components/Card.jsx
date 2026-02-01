export default function Card({ title, children }) {
  return (
    <div
      className="card"
      style={{
        display: "block",
        background: "#0f1620",
        border: "1px solid #1f2937",
        borderRadius: 12,
        padding: 16,
        minHeight: 80,
      }}
    >
      {title && (
        <div style={{ fontWeight: 600, marginBottom: 10 }}>
          {title}
        </div>
      )}
      {children}
    </div>
  );
}

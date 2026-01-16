export default function Card({ title, children }) {
  return (
    <div
      style={{
        border: "1px solid #1f2937",
        borderRadius: 14,
        padding: 20,
        background: "#0f1620",
        minWidth: 240,
      }}
    >
      {title && (
        <div
          style={{
            fontWeight: 600,
            marginBottom: 12,
            fontSize: 15,
          }}
        >
          {title}
        </div>
      )}

      <div style={{ fontSize: 14 }}>{children}</div>
    </div>
  );
}

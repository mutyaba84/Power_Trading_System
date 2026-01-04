import React from "react";

export function Card({ className = "", children, ...props }) {
  return (
    <div
      className={className}
      style={{
        border: "1px solid #2a2a2a",
        borderRadius: 12,
        padding: 16,
        background: "#111",
        color: "#fff"
      }}
      {...props}
    >
      {children}
    </div>
  );
}

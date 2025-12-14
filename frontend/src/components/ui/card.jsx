import React from "react";

export default function Card({ children, className }) {
  return (
    <div
      className={`rounded-2xl bg-gray-800 p-4 shadow-md border border-gray-700 ${className}`}
    >
      {children}
    </div>
  );
dir
}

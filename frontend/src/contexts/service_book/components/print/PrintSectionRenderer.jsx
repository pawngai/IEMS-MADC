import React from "react";

export function PrintSection({ title, children }) {
  return (
    <div className="sb-section">
      {title && <h4 className="sb-section-title">{title}</h4>}
      {children}
    </div>
  );
}

export function PrintEmpty({ message }) {
  return <p className="sb-empty">{message}</p>;
}

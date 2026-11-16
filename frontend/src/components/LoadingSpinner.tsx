import React from "react";

export const LoadingSpinner: React.FC<{ message?: string }> = ({ message = "Loading..." }) => {
  return (
    <div style={{ textAlign: "center", padding: "4rem 1rem", color: "var(--color-steel)" }}>
      <div
        style={{
          display: "inline-block",
          width: "2.5rem",
          height: "2.5rem",
          border: "3px solid rgba(0, 100, 224, 0.15)",
          borderRadius: "50%",
          borderTopColor: "var(--color-primary)",
          animation: "spin 0.8s linear infinite",
          marginBottom: "1rem",
        }}
      />
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
      <p style={{ fontSize: "14px", fontWeight: 500, color: "var(--color-charcoal)" }}>{message}</p>
    </div>
  );
};

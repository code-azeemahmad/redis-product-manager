import React, { useEffect, useState } from "react";

interface RateLimitAlertProps {
  retryAfter: number | null;
  message?: string;
  onClear: () => void;
}

export const RateLimitAlert: React.FC<RateLimitAlertProps> = ({
  retryAfter,
  message = "Rate limit reached. Please wait before retrying.",
  onClear,
}) => {
  const [secondsLeft, setSecondsLeft] = useState<number | null>(retryAfter);

  useEffect(() => {
    setSecondsLeft(retryAfter);
    if (!retryAfter || retryAfter <= 0) return;

    const timer = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev === null || prev <= 1) {
          clearInterval(timer);
          onClear();
          return null;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [retryAfter, onClear]);

  return (
    <div className="alert alert-warning" role="alert">
      <div>
        <strong style={{ fontWeight: 700 }}>Rate Limit Active:</strong> {message}
        {secondsLeft !== null && secondsLeft > 0 && (
          <span style={{ marginLeft: "0.5rem", fontWeight: 700 }}>
            (Retry available in {secondsLeft}s)
          </span>
        )}
      </div>
      <button
        onClick={onClear}
        className="btn btn-secondary btn-sm"
      >
        Dismiss
      </button>
    </div>
  );
};

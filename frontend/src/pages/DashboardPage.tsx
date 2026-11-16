import React, { useCallback, useEffect, useState } from "react";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { RateLimitAlert } from "../components/RateLimitAlert";
import { ApiError, getDashboardStats } from "../services/api";
import { DashboardStats } from "../types/product";
import { formatCurrency } from "../utils/formatters";

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [rateLimit, setRateLimit] = useState<{ retryAfter: number | null; message: string } | null>(null);

  const loadStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDashboardStats();
      setStats(data);
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 429) {
        setRateLimit({ retryAfter: err.retryAfter, message: err.message });
      } else {
        setError(err.message || "Failed to load dashboard statistics.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const categories = stats?.products_by_category ? Object.entries(stats.products_by_category) : [];

  return (
    <div>
      {/* Dashboard Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          marginBottom: "2rem",
          flexWrap: "wrap",
          gap: "1.5rem",
        }}
      >
        <div>
          <h1 className="hero-display">Inventory Analytics</h1>
        </div>
        <button
          className="btn btn-secondary"
          onClick={loadStats}
          disabled={loading}
        >
          Refresh Analytics
        </button>
      </div>

      {rateLimit && (
        <RateLimitAlert
          retryAfter={rateLimit.retryAfter}
          message={rateLimit.message}
          onClear={() => setRateLimit(null)}
        />
      )}

      {error && (
        <div className="alert alert-danger">
          <span>{error}</span>
          <button className="btn btn-secondary btn-sm" onClick={loadStats}>
            Retry
          </button>
        </div>
      )}

      {loading && !stats ? (
        <LoadingSpinner message="Calculating inventory metrics..." />
      ) : stats ? (
        <>
          {/* Key Metric Cards Grid (DESIGN.md card-icon-feature / metric-card) */}
          <div className="metrics-grid">
            <div className="metric-card">
              <span className="metric-title">TOTAL ACTIVE PRODUCTS</span>
              <span className="metric-value">{stats.total_products}</span>
              <span style={{ fontSize: "13px", color: "var(--color-steel)", marginTop: "8px" }}>
                Total catalog SKUs in database
              </span>
            </div>

            <div className="metric-card">
              <span className="metric-title">TOTAL INVENTORY VALUATION</span>
              <span className="metric-value" style={{ color: "var(--color-success)" }}>
                {formatCurrency(stats.total_inventory_value)}
              </span>
              <span style={{ fontSize: "13px", color: "var(--color-steel)", marginTop: "8px" }}>
                Formula: SUM(price &times; stock)
              </span>
            </div>

            <div className="metric-card">
              <span className="metric-title">AVERAGE PRODUCT PRICE</span>
              <span className="metric-value" style={{ color: "var(--color-primary)" }}>
                {formatCurrency(stats.average_product_price)}
              </span>
              <span style={{ fontSize: "13px", color: "var(--color-steel)", marginTop: "8px" }}>
                Formula: AVG(price) across catalog
              </span>
            </div>
          </div>

          {/* Category Distribution Breakdown Card */}
          <div className="card" style={{ padding: "2rem" }}>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "1.5rem", color: "var(--color-ink-deep)" }}>
              Inventory Distribution by Category
            </h2>

            {categories.length === 0 ? (
              <p style={{ color: "var(--color-steel)", fontStyle: "italic" }}>
                No category data available. Add products to view inventory distribution.
              </p>
            ) : (
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Category</th>
                      <th>Product Count</th>
                      <th>Share of Catalog</th>
                    </tr>
                  </thead>
                  <tbody>
                    {categories.map(([cat, count]) => {
                      const sharePct = stats.total_products > 0
                        ? Math.round((count / stats.total_products) * 100)
                        : 0;
                      return (
                        <tr key={cat}>
                          <td>
                            <span className="badge badge-category">{cat}</span>
                          </td>
                          <td style={{ fontWeight: 700, color: "var(--color-ink-deep)" }}>
                            {count} SKUs
                          </td>
                          <td>
                            <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                              <div
                                style={{
                                  flex: 1,
                                  height: "8px",
                                  backgroundColor: "var(--color-surface-soft)",
                                  borderRadius: "100px",
                                  overflow: "hidden",
                                  maxWidth: "240px",
                                }}
                              >
                                <div
                                  style={{
                                    width: `${sharePct}%`,
                                    height: "100%",
                                    backgroundColor: "var(--color-primary)",
                                    borderRadius: "100px",
                                  }}
                                />
                              </div>
                              <span style={{ fontSize: "13px", fontWeight: 700, color: "var(--color-charcoal)", minWidth: "40px" }}>
                                {sharePct}%
                              </span>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      ) : null}
    </div>
  );
};

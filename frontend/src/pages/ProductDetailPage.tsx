import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { DeleteConfirmModal } from "../components/DeleteConfirmModal";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ProductModal } from "../components/ProductModal";
import { RateLimitAlert } from "../components/RateLimitAlert";
import { ApiError, deleteProduct, getProduct, updateProduct } from "../services/api";
import { Product, ProductCreate, ProductUpdate } from "../types/product";
import { formatCurrency, formatDate } from "../utils/formatters";

export const ProductDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [notFound, setNotFound] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [rateLimit, setRateLimit] = useState<{ retryAfter: number | null; message: string } | null>(null);
  const [orderSuccess, setOrderSuccess] = useState<string | null>(null);

  const [isEditOpen, setIsEditOpen] = useState<boolean>(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const loadProduct = useCallback(async () => {
    if (!id) return;
    const productId = parseInt(id, 10);
    if (isNaN(productId)) {
      setNotFound(true);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    setNotFound(false);

    try {
      const data = await getProduct(productId);
      setProduct(data);
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 404) {
        setNotFound(true);
      } else if (err instanceof ApiError && err.status === 429) {
        setRateLimit({ retryAfter: err.retryAfter, message: err.message });
      } else {
        setError(err.message || "Failed to load product details.");
      }
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadProduct();
  }, [loadProduct]);

  const handleUpdate = async (data: ProductCreate | ProductUpdate) => {
    if (!product) return;
    setIsSubmitting(true);
    try {
      const updated = await updateProduct(product.id, data as ProductUpdate);
      setProduct(updated);
      setIsEditOpen(false);
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 429) {
        setRateLimit({ retryAfter: err.retryAfter, message: err.message });
      }
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!product) return;
    setIsSubmitting(true);
    try {
      await deleteProduct(product.id);
      setIsDeleteOpen(false);
      navigate("/");
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 429) {
        setRateLimit({ retryAfter: err.retryAfter, message: err.message });
      } else {
        setError(err.message || "Failed to delete product.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSimulateOrder = () => {
    if (!product || product.stock <= 0) return;
    setOrderSuccess(`Order placed for 1x "${product.name}". In-memory stock reserved.`);
    setTimeout(() => setOrderSuccess(null), 4000);
  };

  if (loading) {
    return <LoadingSpinner message="Loading product details..." />;
  }

  if (notFound) {
    return (
      <div className="card" style={{ textAlign: "center", padding: "4rem 2rem", maxWidth: "600px", margin: "2rem auto" }}>
        <h2 style={{ fontSize: "1.75rem", marginBottom: "0.5rem" }}>Product Not Found</h2>
        <p style={{ color: "var(--color-steel)", marginBottom: "1.75rem", fontSize: "15px" }}>
          The requested product ID #{id} was not found in the cache or database.
        </p>
        <Link to="/" className="btn btn-primary">
          Return to Catalogue
        </Link>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="alert alert-danger">
        <span>{error || "An unexpected error occurred."}</span>
        <button className="btn btn-secondary btn-sm" onClick={loadProduct}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Breadcrumb Navigation (DESIGN.md Breadcrumb PDP) */}
      <nav style={{ marginBottom: "1.5rem", fontSize: "14px", color: "var(--color-steel)" }}>
        <Link to="/" style={{ color: "var(--color-steel)" }}>
          Hardware Catalogue
        </Link>
        <span style={{ margin: "0 8px", color: "var(--color-stone)" }}>›</span>
        <span>{product.category}</span>
        <span style={{ margin: "0 8px", color: "var(--color-stone)" }}>›</span>
        <span style={{ color: "var(--color-ink)", fontWeight: 700 }}>{product.name}</span>
      </nav>

      {rateLimit && (
        <RateLimitAlert
          retryAfter={rateLimit.retryAfter}
          message={rateLimit.message}
          onClear={() => setRateLimit(null)}
        />
      )}

      {orderSuccess && (
        <div className="alert alert-warning" style={{ backgroundColor: "rgba(49, 162, 76, 0.12)", borderColor: "rgba(49, 162, 76, 0.3)", color: "var(--color-success)" }}>
          <span>{orderSuccess}</span>
          <button className="btn btn-secondary btn-sm" onClick={() => setOrderSuccess(null)}>Dismiss</button>
        </div>
      )}

      {/* 2-Column Split: Hero Gallery (58%) + Sticky Purchase Rail (42%) */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "2.5rem",
          alignItems: "start",
        }}
      >
        {/* Left Column: Hero Product Gallery & Tech Specs */}
        <div>
          {/* Main Visual Showcase (DESIGN.md product-gallery-pdp / product-thumbnail) */}
          <div className="product-thumbnail-box" style={{ minHeight: "360px", marginBottom: "2rem" }}>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: "3rem", fontWeight: 800, color: "var(--color-primary)", letterSpacing: "1px" }}>
                {product.category.slice(0, 3).toUpperCase()}
              </div>
              <span style={{ fontSize: "14px", fontWeight: 600, color: "var(--color-steel)" }}>
                SKU-{product.id.toString().padStart(5, "0")}
              </span>
            </div>
            <div style={{ position: "absolute", top: "20px", left: "20px" }}>
              <span className="badge badge-category">{product.category}</span>
            </div>
          </div>

          {/* Product Specifications Table */}
          <div className="card" style={{ padding: "1.75rem 2rem", marginBottom: "1.5rem" }}>
            <h3 style={{ fontSize: "18px", fontWeight: 700, marginBottom: "1rem", color: "var(--color-ink-deep)" }}>
              Product Specifications
            </h3>
            <table className="tech-specs-table">
              <tbody>
                <tr>
                  <td className="tech-specs-label">Category</td>
                  <td className="tech-specs-value">{product.category}</td>
                </tr>
                <tr>
                  <td className="tech-specs-label">Unit Price</td>
                  <td className="tech-specs-value">{formatCurrency(product.price)}</td>
                </tr>
                <tr>
                  <td className="tech-specs-label">Stock Status</td>
                  <td className="tech-specs-value">
                    {product.stock > 0 ? `${product.stock} units available` : "Out of stock"}
                  </td>
                </tr>
                <tr>
                  <td className="tech-specs-label">Product SKU</td>
                  <td className="tech-specs-value">SKU-{product.id.toString().padStart(5, "0")}</td>
                </tr>
                <tr>
                  <td className="tech-specs-label">Added Date</td>
                  <td className="tech-specs-value">{formatDate(product.created_at)}</td>
                </tr>
                <tr>
                  <td className="tech-specs-label">Last Updated</td>
                  <td className="tech-specs-value">{formatDate(product.updated_at)}</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Guarantee Callout */}
          <div className="warranty-card">
            <h4 style={{ fontSize: "15px", fontWeight: 700, marginBottom: "6px", color: "var(--color-ink-deep)" }}>
              Warranty & Service
            </h4>
            <p style={{ fontSize: "13px", color: "var(--color-charcoal)", lineHeight: 1.45 }}>
              Standard 1-year hardware warranty and 30-day hassle-free return policy included with every order.
            </p>
          </div>
        </div>

        {/* Right Column: Sticky Purchase Rail (DESIGN.md card-checkout-summary) */}
        <div style={{ position: "sticky", top: "84px" }}>
          <div className="card-checkout-summary">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
              <span className="badge badge-category">{product.category}</span>
              {product.stock > 0 ? (
                <span className="badge badge-success">In Stock ({product.stock})</span>
              ) : (
                <span className="badge badge-critical">Out of Stock</span>
              )}
            </div>

            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, marginBottom: "0.5rem", color: "var(--color-ink-deep)" }}>
              {product.name}
            </h1>
            <p style={{ fontSize: "13px", color: "var(--color-steel)", marginBottom: "1.25rem" }}>
              SKU-{product.id.toString().padStart(5, "0")}
            </p>

            {/* Large Price Display */}
            <div style={{ padding: "1rem 0", borderTop: "1px solid var(--color-hairline-soft)", borderBottom: "1px solid var(--color-hairline-soft)", marginBottom: "1.5rem" }}>
              <span style={{ fontSize: "12px", textTransform: "uppercase", color: "var(--color-steel)", fontWeight: 700, display: "block", marginBottom: "4px" }}>
                Price (USD)
              </span>
              <div className="price-tag-lg">
                {formatCurrency(product.price)}
              </div>
            </div>

            {/* Primary Buy CTA (DESIGN.md button-buy-cta: saturated Cobalt Blue #0064e0) */}
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              <button
                className="btn btn-buy-cta"
                style={{ width: "100%", padding: "14px" }}
                disabled={product.stock <= 0}
                onClick={handleSimulateOrder}
              >
                {product.stock > 0 ? "Order Now — Instant Fulfillment" : "Currently Unavailable"}
              </button>

              <button
                className="btn btn-secondary"
                style={{ width: "100%", padding: "12px" }}
                onClick={() => setIsEditOpen(true)}
              >
                Edit Product
              </button>

              <button
                className="btn btn-ghost"
                style={{ width: "100%", padding: "10px", color: "var(--color-critical)" }}
                onClick={() => setIsDeleteOpen(true)}
              >
                Delete Product
              </button>
            </div>

            <div style={{ marginTop: "1.5rem", borderTop: "1px solid var(--color-hairline-soft)", paddingTop: "1rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", color: "var(--color-charcoal)", marginBottom: "6px" }}>
                <span style={{ color: "var(--color-primary)", fontWeight: 700 }}>&bull;</span>
                <span>Free 2-day delivery on all domestic orders</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", color: "var(--color-charcoal)" }}>
                <span style={{ color: "var(--color-primary)", fontWeight: 700 }}>&bull;</span>
                <span>Secure and verified transaction</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {isEditOpen && (
        <ProductModal
          product={product}
          isOpen={isEditOpen}
          isSaving={isSubmitting}
          onClose={() => setIsEditOpen(false)}
          onSave={handleUpdate}
        />
      )}

      {isDeleteOpen && (
        <DeleteConfirmModal
          product={product}
          isOpen={isDeleteOpen}
          isDeleting={isSubmitting}
          onClose={() => setIsDeleteOpen(false)}
          onConfirm={handleDelete}
        />
      )}
    </div>
  );
};

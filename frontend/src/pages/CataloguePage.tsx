import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { DeleteConfirmModal } from "../components/DeleteConfirmModal";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ProductModal } from "../components/ProductModal";
import { RateLimitAlert } from "../components/RateLimitAlert";
import {
  ApiError,
  createProduct,
  deleteProduct,
  getProducts,
  updateProduct,
} from "../services/api";
import { Product, ProductCreate, ProductUpdate } from "../types/product";
import { formatCurrency, formatDate } from "../utils/formatters";

export const CataloguePage: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [page, setPage] = useState<number>(1);
  const [limit] = useState<number>(10);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalCount, setTotalCount] = useState<number>(0);

  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [categoryInput, setCategoryInput] = useState<string>("");
  const [sortBy, setSortBy] = useState<string>("id");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [rateLimit, setRateLimit] = useState<{ retryAfter: number | null; message: string } | null>(null);

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [deletingProduct, setDeletingProduct] = useState<Product | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const loadProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getProducts({
        page,
        limit,
        category: categoryFilter || undefined,
        sortBy,
        sortOrder,
      });
      setProducts(data.items);
      setTotalPages(data.pages);
      setTotalCount(data.total);
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 429) {
        setRateLimit({ retryAfter: err.retryAfter, message: err.message });
      } else {
        setError(err.message || "Failed to load products.");
      }
    } finally {
      setLoading(false);
    }
  }, [page, limit, categoryFilter, sortBy, sortOrder]);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  const handleApplyFilter = (e: React.FormEvent) => {
    e.preventDefault();
    setCategoryFilter(categoryInput.trim());
    setPage(1);
  };

  const handleClearFilter = () => {
    setCategoryInput("");
    setCategoryFilter("");
    setPage(1);
  };

  const handleCreate = async (data: ProductCreate | ProductUpdate) => {
    setIsSubmitting(true);
    try {
      await createProduct(data as ProductCreate);
      setIsCreateOpen(false);
      await loadProducts();
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 429) {
        setRateLimit({ retryAfter: err.retryAfter, message: err.message });
      }
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdate = async (data: ProductCreate | ProductUpdate) => {
    if (!editingProduct) return;
    setIsSubmitting(true);
    try {
      await updateProduct(editingProduct.id, data as ProductUpdate);
      setEditingProduct(null);
      await loadProducts();
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
    if (!deletingProduct) return;
    setIsSubmitting(true);
    try {
      await deleteProduct(deletingProduct.id);
      setDeletingProduct(null);
      await loadProducts();
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

  return (
    <div>
      {/* Header with Meta Typography Hierarchy */}
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
          <h1 className="hero-display">Hardware & Products</h1>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setIsCreateOpen(true)}
        >
          <span>+ Add Product</span>
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
          <button className="btn btn-secondary btn-sm" onClick={loadProducts}>
            Retry
          </button>
        </div>
      )}

      {/* Filter and Sorting Controls Bar */}
      <div className="card" style={{ marginBottom: "1.75rem", padding: "1.25rem 1.5rem" }}>
        <form
          onSubmit={handleApplyFilter}
          style={{ display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "center" }}
        >
          <div style={{ display: "flex", gap: "0.75rem", flex: 1, minWidth: "260px" }}>
            <input
              type="text"
              className="search-pill"
              placeholder="Search or filter by category (e.g. AI Glasses, VR Headsets)"
              value={categoryInput}
              onChange={(e) => setCategoryInput(e.target.value)}
            />
            <button type="submit" className="btn btn-secondary btn-sm">
              Filter
            </button>
            {categoryFilter && (
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={handleClearFilter}
              >
                Clear
              </button>
            )}
          </div>

          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <label style={{ fontSize: "14px", fontWeight: 700, color: "var(--color-charcoal)" }}>
              Sort:
            </label>
            <select
              className="form-input"
              style={{ width: "auto", height: "40px", borderRadius: "100px", padding: "0 16px" }}
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [field, order] = e.target.value.split("-");
                setSortBy(field);
                setSortOrder(order as "asc" | "desc");
                setPage(1);
              }}
            >
              <option value="id-desc">Newest First (ID desc)</option>
              <option value="id-asc">Oldest First (ID asc)</option>
              <option value="name-asc">Name (A-Z)</option>
              <option value="price-asc">Price (Low to High)</option>
              <option value="price-desc">Price (High to Low)</option>
              <option value="stock-desc">Stock (High to Low)</option>
            </select>
          </div>
        </form>
      </div>

      {/* Product List / Table */}
      {loading ? (
        <LoadingSpinner message="Loading products..." />
      ) : products.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "4rem 2rem" }}>
          <h3 style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>No products found</h3>
          <p style={{ color: "var(--color-steel)", marginBottom: "1.75rem", fontSize: "15px" }}>
            {categoryFilter
              ? `No products found matching category "${categoryFilter}".`
              : "Get started by adding your first product to the catalogue."}
          </p>
          <button className="btn btn-primary" onClick={() => setIsCreateOpen(true)}>
            + Add Product
          </button>
        </div>
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: "70px" }}>ID</th>
                  <th>Product</th>
                  <th>Category</th>
                  <th>Price</th>
                  <th>Stock Status</th>
                  <th>Created</th>
                  <th style={{ textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <tr key={p.id}>
                    <td style={{ color: "var(--color-steel)", fontWeight: 600 }}>#{p.id}</td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                        <div className="product-thumbnail-box-sm" style={{ fontWeight: 700, fontSize: "13px", color: "var(--color-primary)" }}>
                          {p.category.slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <Link
                            to={`/products/${p.id}`}
                            style={{
                              fontWeight: 700,
                              color: "var(--color-ink-deep)",
                              fontSize: "15px",
                              display: "block",
                            }}
                          >
                            {p.name}
                          </Link>
                          <span style={{ fontSize: "12px", color: "var(--color-steel)" }}>
                            SKU-{p.id.toString().padStart(5, "0")}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-category">{p.category}</span>
                    </td>
                    <td>
                      <span className="price-tag">{formatCurrency(p.price)}</span>
                    </td>
                    <td>
                      {p.stock > 0 ? (
                        <span className="badge badge-success">
                          In Stock ({p.stock})
                        </span>
                      ) : (
                        <span className="badge badge-critical">Out of Stock</span>
                      )}
                    </td>
                    <td style={{ fontSize: "13px", color: "var(--color-steel)" }}>
                      {formatDate(p.created_at)}
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <div style={{ display: "inline-flex", gap: "6px" }}>
                        <Link
                          to={`/products/${p.id}`}
                          className="btn btn-ghost btn-sm"
                        >
                          View
                        </Link>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => setEditingProduct(p)}
                        >
                          Edit
                        </button>
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => setDeletingProduct(p)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div className="pagination">
            <span style={{ fontSize: "14px", color: "var(--color-charcoal)" }}>
              Showing <strong>{products.length}</strong> of <strong>{totalCount}</strong> products
            </span>
            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
              <button
                className="btn btn-secondary btn-sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Previous
              </button>
              <span style={{ fontSize: "14px", fontWeight: 600, padding: "0 8px" }}>
                Page {page} of {Math.max(1, totalPages)}
              </span>
              <button
                className="btn btn-secondary btn-sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}

      {/* Creation Modal */}
      {isCreateOpen && (
        <ProductModal
          isOpen={isCreateOpen}
          isSaving={isSubmitting}
          onClose={() => setIsCreateOpen(false)}
          onSave={handleCreate}
        />
      )}

      {/* Editing Modal */}
      {editingProduct && (
        <ProductModal
          product={editingProduct}
          isOpen={!!editingProduct}
          isSaving={isSubmitting}
          onClose={() => setEditingProduct(null)}
          onSave={handleUpdate}
        />
      )}

      {/* Delete Confirmation Modal */}
      {deletingProduct && (
        <DeleteConfirmModal
          product={deletingProduct}
          isOpen={!!deletingProduct}
          isDeleting={isSubmitting}
          onClose={() => setDeletingProduct(null)}
          onConfirm={handleDelete}
        />
      )}
    </div>
  );
};

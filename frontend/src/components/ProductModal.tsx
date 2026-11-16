import React, { useState } from "react";
import { Product, ProductCreate, ProductUpdate } from "../types/product";
import { validatePrice } from "../utils/formatters";

interface ProductModalProps {
  product?: Product | null;
  isOpen: boolean;
  isSaving: boolean;
  onClose: () => void;
  onSave: (data: ProductCreate | ProductUpdate) => Promise<void>;
}

export const ProductModal: React.FC<ProductModalProps> = ({
  product,
  isOpen,
  isSaving,
  onClose,
  onSave,
}) => {
  const isEditing = !!product;

  const [name, setName] = useState(product ? product.name : "");
  const [category, setCategory] = useState(product ? product.category : "");
  const [price, setPrice] = useState(product ? product.price : "");
  const [stock, setStock] = useState(product ? product.stock.toString() : "0");
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    const trimmedName = name.trim();
    const trimmedCategory = category.trim();
    const trimmedPrice = price.trim();

    if (!trimmedName) {
      setError("Product name is required.");
      return;
    }
    if (trimmedName.length > 200) {
      setError("Product name cannot exceed 200 characters.");
      return;
    }
    if (!trimmedCategory) {
      setError("Category is required.");
      return;
    }
    if (trimmedCategory.length > 100) {
      setError("Category cannot exceed 100 characters.");
      return;
    }

    const priceValidation = validatePrice(trimmedPrice);
    if (!priceValidation.valid) {
      setError(priceValidation.error || "Invalid price format.");
      return;
    }

    const stockNum = parseInt(stock, 10);
    if (isNaN(stockNum) || stockNum < 0) {
      setError("Stock must be a non-negative whole integer.");
      return;
    }

    try {
      await onSave({
        name: trimmedName,
        category: trimmedCategory,
        price: trimmedPrice, // Exact decimal string
        stock: stockNum,
      });
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to save product.");
    }
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal-content">
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem", color: "var(--color-ink-deep)" }}>
          {isEditing ? `Edit Product #${product.id}` : "Create New Product"}
        </h2>
        <p style={{ fontSize: "14px", color: "var(--color-steel)", marginBottom: "1.5rem" }}>
          Enter the product details below.
        </p>

        {error && (
          <div className="alert alert-danger" style={{ marginBottom: "1.25rem", padding: "10px 14px" }}>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="product-name">
              Product Name
            </label>
            <input
              id="product-name"
              className="form-input"
              type="text"
              required
              maxLength={200}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Ray-Ban Meta Skyler (Gen 2)"
              disabled={isSaving}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="product-category">
              Category
            </label>
            <input
              id="product-category"
              className="form-input"
              type="text"
              required
              maxLength={100}
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="e.g. AI Glasses, VR Headsets"
              disabled={isSaving}
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div className="form-group">
              <label className="form-label" htmlFor="product-price">
                Price (USD)
              </label>
              <input
                id="product-price"
                className="form-input"
                type="text"
                required
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="299.99"
                disabled={isSaving}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="product-stock">
                Stock Quantity
              </label>
              <input
                id="product-stock"
                className="form-input"
                type="number"
                min="0"
                step="1"
                required
                value={stock}
                onChange={(e) => setStock(e.target.value)}
                disabled={isSaving}
              />
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "2rem" }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={isSaving}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSaving}
            >
              {isSaving ? "Saving..." : isEditing ? "Save Changes" : "Create Product"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

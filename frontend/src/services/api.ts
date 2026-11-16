/**
 * Client service for interacting with the backend REST API.
 * 
 * Supports same-origin routing (proxied by Nginx in production, Vite in dev).
 * Handles API errors, network failures, and 429 Rate Limiting with Retry-After.
 */

import {
  DashboardStats,
  HealthReadyResponse,
  Product,
  ProductCreate,
  ProductListResponse,
  ProductUpdate,
} from "../types/product";

export class ApiError extends Error {
  status: number;
  retryAfter: number | null;
  details: unknown;

  constructor(message: string, status: number, retryAfter: number | null = null, details: unknown = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.retryAfter = retryAfter;
    this.details = details;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return {} as T;
  }

  if (response.status === 429) {
    const retryAfterHeader = response.headers.get("Retry-After");
    const retryAfterSeconds = retryAfterHeader ? parseInt(retryAfterHeader, 10) : null;
    let detail = "Rate limit exceeded. Please wait a moment before trying again.";
    try {
      const data = await response.json();
      if (data.detail) detail = data.detail;
    } catch {
      // response body might not be JSON
    }
    throw new ApiError(detail, 429, retryAfterSeconds);
  }

  if (!response.ok) {
    let errorMessage = `HTTP Error ${response.status}`;
    let errorDetails: unknown = null;
    try {
      const data = await response.json();
      if (typeof data.detail === "string") {
        errorMessage = data.detail;
      } else if (Array.isArray(data.detail)) {
        errorMessage = data.detail.map((d: { msg?: string }) => d.msg || "").join("; ");
      }
      errorDetails = data;
    } catch {
      errorMessage = response.statusText || errorMessage;
    }
    throw new ApiError(errorMessage, response.status, null, errorDetails);
  }

  return response.json() as Promise<T>;
}

export async function getProducts(params: {
  page?: number;
  limit?: number;
  category?: string;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
} = {}): Promise<ProductListResponse> {
  const query = new URLSearchParams();
  if (params.page) query.set("page", params.page.toString());
  if (params.limit) query.set("limit", params.limit.toString());
  if (params.category && params.category.trim()) query.set("category", params.category.trim());
  if (params.sortBy) query.set("sort_by", params.sortBy);
  if (params.sortOrder) query.set("sort_order", params.sortOrder);

  const res = await fetch(`/api/products?${query.toString()}`);
  return handleResponse<ProductListResponse>(res);
}

export async function getProduct(id: number): Promise<Product> {
  const res = await fetch(`/api/products/${id}`);
  return handleResponse<Product>(res);
}

export async function createProduct(payload: ProductCreate): Promise<Product> {
  const res = await fetch("/api/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<Product>(res);
}

export async function updateProduct(id: number, payload: ProductUpdate): Promise<Product> {
  const res = await fetch(`/api/products/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<Product>(res);
}

export async function deleteProduct(id: number): Promise<void> {
  const res = await fetch(`/api/products/${id}`, {
    method: "DELETE",
  });
  return handleResponse<void>(res);
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const res = await fetch("/api/dashboard/stats");
  return handleResponse<DashboardStats>(res);
}

export async function getHealthStatus(): Promise<HealthReadyResponse> {
  const res = await fetch("/health/ready");
  return handleResponse<HealthReadyResponse>(res);
}

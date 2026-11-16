/**
 * Frontend TypeScript definitions mirroring FastAPI schemas.
 * 
 * Architectural Invariant:
 * Monetary values (price, total_inventory_value, average_product_price)
 * are strictly typed and represented as formatted strings (e.g. "149.99").
 * They are NEVER converted to binary floating point numbers for financial logic.
 */

export interface Product {
  id: number;
  name: string;
  category: string;
  price: string; // Exact decimal string e.g. "29.99"
  stock: number;
  created_at: string;
  updated_at: string;
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface ProductCreate {
  name: string;
  category: string;
  price: string; // String to guarantee Decimal fidelity
  stock: number;
}

export interface ProductUpdate {
  name?: string;
  category?: string;
  price?: string;
  stock?: number;
}

export interface DashboardStats {
  total_products: number;
  total_inventory_value: string; // Formatted numeric string e.g. "12500.50"
  average_product_price: string; // Formatted numeric string e.g. "49.95"
  products_by_category: Record<string, number>;
}

export interface HealthReadyResponse {
  status: string;
  timestamp: string;
  dependencies: {
    postgres: string;
    redis: string;
  };
  latency_ms: {
    postgres: number | null;
    redis: number | null;
  };
}

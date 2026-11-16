import { describe, expect, it } from "vitest";
import { formatCurrency, formatDate, validatePrice } from "../utils/formatters";

describe("Decimal-safe formatters", () => {
  describe("formatCurrency", () => {
    it("formats standard 2-decimal price strings with currency symbol", () => {
      expect(formatCurrency("149.99")).toBe("$149.99");
      expect(formatCurrency("0.00")).toBe("$0.00");
      expect(formatCurrency("25.50")).toBe("$25.50");
    });

    it("formats large numbers with commas without binary float precision loss", () => {
      expect(formatCurrency("12500.50")).toBe("$12,500.50");
      expect(formatCurrency("1000000.00")).toBe("$1,000,000.00");
      expect(formatCurrency("999999999.99")).toBe("$999,999,999.99");
    });

    it("handles single decimal or whole number inputs with proper zero-padding", () => {
      expect(formatCurrency("10")).toBe("$10.00");
      expect(formatCurrency("10.5")).toBe("$10.50");
    });

    it("handles empty or null values gracefully", () => {
      expect(formatCurrency(null)).toBe("$0.00");
      expect(formatCurrency("")).toBe("$0.00");
      expect(formatCurrency("   ")).toBe("$0.00");
    });
  });

  describe("validatePrice", () => {
    it("accepts valid positive decimal strings", () => {
      expect(validatePrice("10").valid).toBe(true);
      expect(validatePrice("10.5").valid).toBe(true);
      expect(validatePrice("19.99").valid).toBe(true);
      expect(validatePrice("0.00").valid).toBe(true);
      expect(validatePrice("0").valid).toBe(true);
    });

    it("rejects negative numbers", () => {
      expect(validatePrice("-10").valid).toBe(false);
      expect(validatePrice("-0.01").valid).toBe(false);
    });

    it("rejects prices with more than 2 decimal places", () => {
      expect(validatePrice("19.999").valid).toBe(false);
      expect(validatePrice("0.001").valid).toBe(false);
    });

    it("rejects non-numeric characters", () => {
      expect(validatePrice("abc").valid).toBe(false);
      expect(validatePrice("$19.99").valid).toBe(false);
      expect(validatePrice("").valid).toBe(false);
    });
  });

  describe("formatDate", () => {
    it("formats ISO timestamps to human-readable strings", () => {
      const res = formatDate("2026-11-16T12:00:00Z");
      expect(res).toContain("2026");
      expect(res).toContain("Nov");
    });

    it("handles null or undefined dates", () => {
      expect(formatDate(null)).toBe("-");
      expect(formatDate(undefined)).toBe("-");
    });
  });
});

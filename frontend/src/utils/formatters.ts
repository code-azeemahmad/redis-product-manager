/**
 * Decimal-safe formatting utilities.
 * 
 * Architectural Invariant:
 * Strictly avoids IEEE-754 JavaScript binary floating-point conversions.
 * Manipulates decimal strings directly to maintain arbitrary precision fidelity.
 */

/**
 * Safely format a monetary string into currency display with thousand separators.
 * Example: "1234567.89" -> "$1,234,567.89"
 */
export function formatCurrency(priceStr: string | null | undefined, symbol: string = "$"): string {
  if (!priceStr || priceStr.trim() === "") {
    return `${symbol}0.00`;
  }

  const clean = priceStr.trim();
  const parts = clean.split(".");
  const integerPart = parts[0] || "0";
  const fractionalPart = (parts[1] || "00").padEnd(2, "0").slice(0, 2);

  // Add thousand separators to integer component using regex
  const formattedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");

  return `${symbol}${formattedInteger}.${fractionalPart}`;
}

/**
 * Safely format an ISO 8601 date string to a localized human-readable string.
 */
export function formatDate(isoStr: string | null | undefined): string {
  if (!isoStr) return "-";
  try {
    const d = new Date(isoStr);
    if (isNaN(d.getTime())) return isoStr;
    return d.toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoStr;
  }
}

/**
 * Validate price input for product mutations.
 * Accepts strings like "10", "10.5", "10.99". Rejects negative numbers or > 2 decimals.
 */
export function validatePrice(priceStr: string): { valid: boolean; error?: string } {
  if (!priceStr || priceStr.trim() === "") {
    return { valid: false, error: "Price is required." };
  }
  const regex = /^\d+(\.\d{1,2})?$/;
  if (!regex.test(priceStr.trim())) {
    return { valid: false, error: "Price must be a positive number with at most 2 decimal places (e.g. 19.99)." };
  }
  return { valid: true };
}

/**
 * Formats a numeric value into standard Indian Rupee (₹) currency presentation.
 * Examples:
 *   1000 -> "₹1,000"
 *   25000 -> "₹25,000"
 *   125000 -> "₹1,25,000"
 */
export function formatINR(amount: number, showDecimals: boolean = false): string {
  if (isNaN(amount) || amount === null || amount === undefined) {
    return '₹0';
  }

  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: showDecimals ? 2 : 0,
    maximumFractionDigits: showDecimals ? 2 : 0,
  }).format(amount);
}

/**
 * Formats an ISO datetime string into human-readable date and time.
 * Example: "2026-10-03T16:46:02" -> "Oct 3, 2026, 4:46 PM"
 */
export function formatDate(dateStr: string): string {
  if (!dateStr) return 'N/A';
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr;
    return new Intl.DateTimeFormat('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      hour12: true,
    }).format(date);
  } catch {
    return dateStr;
  }
}

/**
 * Formats a ratio or percentage number.
 * Example: 45.678 -> "45.7%"
 */
export function formatPercentage(value: number): string {
  if (isNaN(value)) return '0%';
  return `${value.toFixed(1)}%`;
}

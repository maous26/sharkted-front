import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind classes with clsx
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format price with currency
 */
export function formatPrice(price: number | undefined | null, currency = "EUR"): string {
  if (price === undefined || price === null) return "-";

  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(price);
}

/**
 * Format relative time (e.g., "il y a 5 min")
 */
export function timeAgo(date: string | Date | null | undefined): string {
  if (!date) return "-";

  const now = new Date();
  const past = new Date(date);

  // Handle invalid dates
  if (isNaN(past.getTime())) return "-";

  const diffMs = now.getTime() - past.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "a l'instant";
  if (diffMins < 60) return `il y a ${diffMins} min`;
  if (diffHours < 24) return `il y a ${diffHours}h`;
  if (diffDays < 7) return `il y a ${diffDays}j`;

  return past.toLocaleDateString("fr-FR");
}

/**
 * Format percentage
 */
export function formatPercent(value: number | undefined | null): string {
  if (value === undefined || value === null) return "-";
  return `${value >= 0 ? "+" : ""}${value.toFixed(0)}%`;
}

/**
 * Truncate string with ellipsis
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - 3) + "...";
}

/**
 * Proxy image URL through API to bypass hotlinking protection
 */
const PROXY_DOMAINS = [
  "courir.com",
  "zalando.",
  "footlocker.",
  "jdsports.",
  "snipes.",
  "demandware.static",
  "asos.",
  "laredoute.",
  "printemps.",
  "footpatrol.",
];

export function proxyImageUrl(imageUrl: string | undefined | null): string {
  if (!imageUrl) return "";

  // Check if image needs proxying
  const needsProxy = PROXY_DOMAINS.some(domain =>
    imageUrl.toLowerCase().includes(domain)
  );

  if (!needsProxy) return imageUrl;

  // Proxy through API
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://api.sharkted.fr";
  return `${apiUrl}/v1/images/proxy?url=${encodeURIComponent(imageUrl)}`;
}

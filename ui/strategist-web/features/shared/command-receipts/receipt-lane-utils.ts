export type ReceiptFilterMode = "all" | "awaiting-refresh" | "accepted" | "attention";
export type ReceiptSortMode = "recent" | "action" | "status";
export type ReceiptPreferenceState = {
  search: string;
  filterMode: ReceiptFilterMode;
  sortMode: ReceiptSortMode;
};

export const defaultReceiptPreferences: ReceiptPreferenceState = {
  search: "",
  filterMode: "all",
  sortMode: "recent",
};

type ReceiptLike = {
  command_id: string;
  action: string;
  accepted: boolean;
  execution_mode: string;
  requires_projection_refresh: boolean;
  summary_line: string;
  operator_message: string;
  generated_at_utc: string;
};

export function filterCommandReceipts<T extends ReceiptLike>(receipts: T[], search: string, mode: ReceiptFilterMode): T[] {
  const needle = search.trim().toLowerCase();
  return receipts.filter((receipt) => {
    if (mode === "awaiting-refresh" && !receipt.requires_projection_refresh) return false;
    if (mode === "accepted" && !receipt.accepted) return false;
    if (mode === "attention" && receipt.accepted && !receipt.requires_projection_refresh) return false;
    if (!needle) return true;
    const haystack = [receipt.action, receipt.execution_mode, receipt.summary_line, receipt.operator_message].join(" ").toLowerCase();
    return haystack.includes(needle);
  });
}

export function sortCommandReceipts<T extends ReceiptLike>(receipts: T[], mode: ReceiptSortMode): T[] {
  const ordered = [...receipts];
  if (mode === "action") {
    return ordered.sort((a, b) => a.action.localeCompare(b.action) || compareRecentDesc(a.generated_at_utc, b.generated_at_utc));
  }
  if (mode === "status") {
    return ordered.sort((a, b) => receiptStatusRank(a) - receiptStatusRank(b) || compareRecentDesc(a.generated_at_utc, b.generated_at_utc));
  }
  return ordered.sort((a, b) => compareRecentDesc(a.generated_at_utc, b.generated_at_utc));
}

export function groupCommandReceiptsByStatus<T extends ReceiptLike>(receipts: T[]) {
  const groups = new Map<string, T[]>();
  for (const receipt of receipts) {
    const key = receiptStatusLabel(receipt);
    const bucket = groups.get(key) ?? [];
    bucket.push(receipt);
    groups.set(key, bucket);
  }
  return Array.from(groups.entries()).map(([status, items]) => ({ status, items }));
}

export function receiptStatusLabel(receipt: ReceiptLike): string {
  if (!receipt.accepted) return "attention";
  if (receipt.requires_projection_refresh) return "awaiting refresh";
  return "accepted";
}

function receiptStatusRank(receipt: ReceiptLike): number {
  if (!receipt.accepted) return 0;
  if (receipt.requires_projection_refresh) return 1;
  return 2;
}

function compareRecentDesc(a: string, b: string): number {
  return new Date(b).getTime() - new Date(a).getTime();
}

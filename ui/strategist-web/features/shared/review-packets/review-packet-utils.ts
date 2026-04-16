import type { ReviewPacketRecord } from "@/features/shared/review-packets/review-packet-lane-provider";

export type ReviewPacketSortMode = "recent" | "kind" | "notes";
export type ReviewPacketPreferenceState = {
  search: string;
  packetKind: string;
  sortMode: ReviewPacketSortMode;
};

export const defaultReviewPacketPreferences: ReviewPacketPreferenceState = {
  search: "",
  packetKind: "all",
  sortMode: "recent",
};

export function filterReviewPackets(
  packets: ReviewPacketRecord[],
  search: string,
  packetKind: string,
): ReviewPacketRecord[] {
  const needle = search.trim().toLowerCase();

  return packets.filter((packet) => {
    if (packetKind !== "all" && packet.packet_kind !== packetKind) {
      return false;
    }
    if (!needle) {
      return true;
    }
    return [
      packet.packet_kind,
      packet.file_name,
      packet.summary_line,
      packet.related_pack_kind ?? "",
      packet.related_work_item_key ?? "",
      packet.related_review_target ?? "",
      ...(packet.provenance_keys ?? []),
      ...(packet.notes ?? []),
    ]
      .join(" ")
      .toLowerCase()
      .includes(needle);
  });
}

export function sortReviewPackets(
  packets: ReviewPacketRecord[],
  mode: ReviewPacketSortMode,
): ReviewPacketRecord[] {
  return [...packets].sort((left, right) => {
    if (!!left.pinned !== !!right.pinned) {
      return left.pinned ? -1 : 1;
    }
    if (mode === "kind") {
      const kindOrder = left.packet_kind.localeCompare(right.packet_kind);
      if (kindOrder !== 0) return kindOrder;
    }
    if (mode === "notes") {
      const noteOrder = (right.note_count ?? 0) - (left.note_count ?? 0);
      if (noteOrder !== 0) return noteOrder;
    }
    return Date.parse(right.generated_at_utc) - Date.parse(left.generated_at_utc);
  });
}

export function groupReviewPacketsByKind(packets: ReviewPacketRecord[]) {
  const grouped = new Map<string, ReviewPacketRecord[]>();
  for (const packet of packets) {
    const items = grouped.get(packet.packet_kind) ?? [];
    items.push(packet);
    grouped.set(packet.packet_kind, items);
  }
  return Array.from(grouped.entries()).map(([packetKind, items]) => ({
    packetKind,
    items,
  }));
}

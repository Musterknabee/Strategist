"use client";

import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";

import { getSearchParam, isOpenParam, updateSearchParam } from "@/lib/url-state";

type ReviewPacketRecord = {
  packet_id: string;
  packet_kind: string;
  generated_at_utc: string;
  file_name: string;
  note_count: number;
  provenance_keys: string[];
  summary_line: string;
  pinned?: boolean;
  notes?: string[];
  review_packet?: Record<string, unknown> | null;
  related_pack_kind?: string | null;
  related_work_item_key?: string | null;
  related_review_target?: string | null;
};

type ReviewPacketLaneState = {
  packets: ReviewPacketRecord[];
  inspectedPacketId: string | null;
  isLaneOpen: boolean;
  pushPacket: (packet: ReviewPacketRecord) => void;
  dismissPacket: (packetId: string) => void;
  togglePinned: (packetId: string) => void;
  inspectPacket: (packetId: string | null) => void;
  setLaneOpen: (open: boolean) => void;
  clearPackets: () => void;
};

const STORAGE_KEY = "strategist.review-packets";
const SEARCH_PARAM = "reviewPacket";
const OPEN_PARAM = "reviewPacketLane";

const ReviewPacketLaneContext = createContext<ReviewPacketLaneState>({
  packets: [],
  inspectedPacketId: null,
  isLaneOpen: true,
  pushPacket: () => undefined,
  dismissPacket: () => undefined,
  togglePinned: () => undefined,
  inspectPacket: () => undefined,
  setLaneOpen: () => undefined,
  clearPackets: () => undefined,
});

export function ReviewPacketLaneProvider({ children }: { children: ReactNode }) {
  const [packets, setPackets] = useState<ReviewPacketRecord[]>([]);
  const [inspectedPacketId, setInspectedPacketId] = useState<string | null>(null);
  const [isLaneOpen, setIsLaneOpen] = useState(true);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        setPackets(
          parsed.filter((value) => value && typeof value.packet_id === "string").slice(0, 12),
        );
      }
    } catch {
      // ignore storage parse errors
    }
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(packets));
    } catch {
      // ignore storage write errors
    }
  }, [packets]);

  useEffect(() => {
    const syncFromUrl = () => {
      setInspectedPacketId(getSearchParam(SEARCH_PARAM));
      setIsLaneOpen(isOpenParam(OPEN_PARAM) || !!getSearchParam(SEARCH_PARAM));
    };
    syncFromUrl();
    window.addEventListener("popstate", syncFromUrl);
    return () => window.removeEventListener("popstate", syncFromUrl);
  }, []);

  const value = useMemo<ReviewPacketLaneState>(
    () => ({
      packets,
      inspectedPacketId,
      isLaneOpen,
      pushPacket: (packet) => {
        setPackets((current) => [packet, ...current.filter((entry) => entry.packet_id !== packet.packet_id)].slice(0, 12));
      },
      dismissPacket: (packetId) => {
        setPackets((current) => current.filter((entry) => entry.packet_id !== packetId));
        setInspectedPacketId((current) => {
          const nextId = current === packetId ? null : current;
          updateSearchParam(SEARCH_PARAM, nextId);
          return nextId;
        });
      },
      togglePinned: (packetId) => {
        setPackets((current) =>
          current.map((entry) =>
            entry.packet_id === packetId ? { ...entry, pinned: !entry.pinned } : entry,
          ),
        );
      },
      inspectPacket: (packetId) => {
        updateSearchParam(SEARCH_PARAM, packetId);
        updateSearchParam(OPEN_PARAM, packetId ? "open" : (isLaneOpen ? "open" : null));
        setInspectedPacketId(packetId);
        if (packetId) setIsLaneOpen(true);
      },
      setLaneOpen: (open) => {
        updateSearchParam(OPEN_PARAM, open ? "open" : null);
        setIsLaneOpen(open);
      },
      clearPackets: () => {
        setPackets([]);
        setInspectedPacketId(null);
        setIsLaneOpen(false);
        updateSearchParam(SEARCH_PARAM, null);
        updateSearchParam(OPEN_PARAM, null);
      },
    }),
    [packets, inspectedPacketId, isLaneOpen],
  );

  return <ReviewPacketLaneContext.Provider value={value}>{children}</ReviewPacketLaneContext.Provider>;
}

export function useReviewPacketLane() {
  return useContext(ReviewPacketLaneContext);
}

export type { ReviewPacketRecord };

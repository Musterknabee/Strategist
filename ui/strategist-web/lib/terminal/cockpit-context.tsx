"use client";

import { useQueryClient } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { invalidateQueriesForRoute } from "@/lib/terminal/route-refresh";

export type TapeSeverity = "ok" | "warn" | "bad" | "info" | "neutral";

export type TapeLine = {
  id: string;
  ts?: string;
  severity: TapeSeverity;
  text: string;
};

export type InspectorPayload = {
  title: string;
  subtitle?: string;
  /** Optional summary pane; raw JSON drilldown still available when set. */
  body?: ReactNode;
  rawJson?: unknown;
  digestToCopy?: string;
};

export type InspectorState = InspectorPayload | null;

type CockpitContextValue = {
  paletteOpen: boolean;
  setPaletteOpen: (v: boolean) => void;
  shortcutHelpOpen: boolean;
  setShortcutHelpOpen: (v: boolean) => void;
  inspector: InspectorState;
  openInspector: (s: InspectorPayload) => void;
  closeInspector: () => void;
  rawJsonMode: boolean;
  setRawJsonMode: (v: boolean) => void;
  toggleRawJsonMode: () => void;
  tapeLines: TapeLine[];
  setTapeLines: (lines: TapeLine[]) => void;
  tickerItems: Pick<TapeLine, "severity" | "text">[];
  setTickerItems: (items: Pick<TapeLine, "severity" | "text">[]) => void;
  refreshAllQueries: () => void;
  /** Invalidate queries for the current App Router path (toolbar / R key). */
  refreshRouteQueries: (pathname: string) => void;
  lastDigest: string | null;
  setLastDigest: (s: string | null) => void;
};

const CockpitContext = createContext<CockpitContextValue | null>(null);

export function TerminalCockpitProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [shortcutHelpOpen, setShortcutHelpOpen] = useState(false);
  const [inspector, setInspector] = useState<InspectorState>(null);
  const [rawJsonMode, setRawJsonMode] = useState(false);
  const [tapeLines, setTapeLines] = useState<TapeLine[]>([]);
  const [tickerItems, setTickerItems] = useState<Pick<TapeLine, "severity" | "text">[]>([]);
  const [lastDigest, setLastDigest] = useState<string | null>(null);

  const openInspector = useCallback((s: InspectorPayload) => setInspector(s), []);
  const closeInspector = useCallback(() => setInspector(null), []);
  const toggleRawJsonMode = useCallback(() => setRawJsonMode((x) => !x), []);

  const refreshAllQueries = useCallback(() => {
    void queryClient.invalidateQueries({
      predicate: (q) => Array.isArray(q.queryKey) && q.queryKey[0] === "strategist",
    });
  }, [queryClient]);

  const refreshRouteQueries = useCallback(
    (pathname: string) => {
      invalidateQueriesForRoute(queryClient, pathname);
    },
    [queryClient],
  );

  const value = useMemo(
    () => ({
      paletteOpen,
      setPaletteOpen,
      shortcutHelpOpen,
      setShortcutHelpOpen,
      inspector,
      openInspector,
      closeInspector,
      rawJsonMode,
      setRawJsonMode,
      toggleRawJsonMode,
      tapeLines,
      setTapeLines,
      tickerItems,
      setTickerItems,
      refreshAllQueries,
      refreshRouteQueries,
      lastDigest,
      setLastDigest,
    }),
    [
      paletteOpen,
      shortcutHelpOpen,
      inspector,
      openInspector,
      closeInspector,
      rawJsonMode,
      toggleRawJsonMode,
      tapeLines,
      tickerItems,
      refreshAllQueries,
      refreshRouteQueries,
      lastDigest,
    ],
  );

  return <CockpitContext.Provider value={value}>{children}</CockpitContext.Provider>;
}

export function useTerminalCockpit() {
  const ctx = useContext(CockpitContext);
  if (!ctx) throw new Error("useTerminalCockpit requires TerminalCockpitProvider");
  return ctx;
}

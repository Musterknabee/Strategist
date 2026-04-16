"use client";

import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";

import type { UiOperatorCommandReceipt } from "@/lib/contracts/ui";
import { getSearchParam, isOpenParam, updateSearchParam } from "@/lib/url-state";

type ReceiptLaneState = {
  receipts: UiOperatorCommandReceipt[];
  inspectedReceiptId: string | null;
  isLaneOpen: boolean;
  pushReceipt: (receipt: UiOperatorCommandReceipt) => void;
  dismissReceipt: (commandId: string) => void;
  inspectReceipt: (commandId: string | null) => void;
  setLaneOpen: (open: boolean) => void;
  clearReceipts: () => void;
};

const STORAGE_KEY = "strategist.command-receipts";
const SEARCH_PARAM = "receipt";
const OPEN_PARAM = "receiptLane";

const CommandReceiptLaneContext = createContext<ReceiptLaneState>({
  receipts: [],
  inspectedReceiptId: null,
  isLaneOpen: true,
  pushReceipt: () => undefined,
  dismissReceipt: () => undefined,
  inspectReceipt: () => undefined,
  setLaneOpen: () => undefined,
  clearReceipts: () => undefined,
});

export function CommandReceiptLaneProvider({ children }: { children: ReactNode }) {
  const [receipts, setReceipts] = useState<UiOperatorCommandReceipt[]>([]);
  const [inspectedReceiptId, setInspectedReceiptId] = useState<string | null>(null);
  const [isLaneOpen, setIsLaneOpen] = useState(true);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        setReceipts(parsed.filter((value) => value && typeof value.command_id === "string").slice(0, 10));
      }
    } catch {
      // ignore storage parse errors
    }
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(receipts));
    } catch {
      // ignore storage write errors
    }
  }, [receipts]);

  useEffect(() => {
    const syncFromUrl = () => {
      setInspectedReceiptId(getSearchParam(SEARCH_PARAM));
      setIsLaneOpen(isOpenParam(OPEN_PARAM) || !!getSearchParam(SEARCH_PARAM));
    };
    syncFromUrl();
    window.addEventListener("popstate", syncFromUrl);
    return () => window.removeEventListener("popstate", syncFromUrl);
  }, []);

  const value = useMemo<ReceiptLaneState>(
    () => ({
      receipts,
      inspectedReceiptId,
      isLaneOpen,
      pushReceipt: (receipt) => {
        setReceipts((current) => [receipt, ...current.filter((entry) => entry.command_id !== receipt.command_id)].slice(0, 10));
      },
      dismissReceipt: (commandId) => {
        setReceipts((current) => current.filter((entry) => entry.command_id !== commandId));
        setInspectedReceiptId((current) => {
          const nextId = current === commandId ? null : current;
          updateSearchParam(SEARCH_PARAM, nextId);
          return nextId;
        });
      },
      inspectReceipt: (commandId) => {
        updateSearchParam(SEARCH_PARAM, commandId);
        updateSearchParam(OPEN_PARAM, commandId ? "open" : (isLaneOpen ? "open" : null));
        setInspectedReceiptId(commandId);
        if (commandId) setIsLaneOpen(true);
      },
      setLaneOpen: (open) => {
        updateSearchParam(OPEN_PARAM, open ? "open" : null);
        setIsLaneOpen(open);
      },
      clearReceipts: () => {
        setReceipts([]);
        setInspectedReceiptId(null);
        setIsLaneOpen(false);
        updateSearchParam(SEARCH_PARAM, null);
        updateSearchParam(OPEN_PARAM, null);
      },
    }),
    [receipts, inspectedReceiptId, isLaneOpen],
  );

  return <CommandReceiptLaneContext.Provider value={value}>{children}</CommandReceiptLaneContext.Provider>;
}

export function useCommandReceiptLane() {
  return useContext(CommandReceiptLaneContext);
}

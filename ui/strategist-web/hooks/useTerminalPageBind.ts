"use client";

import { useEffect } from "react";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";

/** Push derived tape + ticker into the terminal shell for this route; cleared on unmount. */
export function useTerminalPageBind(
  tape: TapeLine[],
  ticker: Pick<TapeLine, "severity" | "text">[],
) {
  const { setTapeLines, setTickerItems } = useTerminalCockpit();
  const tapeKey = JSON.stringify(tape);
  const tickerKey = JSON.stringify(ticker);
  useEffect(() => {
    setTapeLines(tape);
    setTickerItems(ticker);
    return () => {
      setTapeLines([]);
      setTickerItems([]);
    };
    // tape/ticker captured when tapeKey/tickerKey change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tapeKey, tickerKey, setTapeLines, setTickerItems]);
}

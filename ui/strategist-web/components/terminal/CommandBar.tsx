"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import { StatusTicker } from "./StatusTicker";

const NAV: { href: string; abbr: string; title: string }[] = [
  { href: "/", abbr: "OV", title: "Overview" },
  { href: "/workboard", abbr: "WB", title: "Workboard" },
  { href: "/readiness", abbr: "RD", title: "Readiness" },
  { href: "/evidence", abbr: "EV", title: "Evidence" },
  { href: "/ledger", abbr: "LG", title: "Ledger" },
  { href: "/providers", abbr: "PR", title: "Providers" },
  { href: "/runtime", abbr: "RT", title: "Runtime" },
];

export function CommandBar() {
  const pathname = usePathname();
  const { setPaletteOpen, refreshRouteQueries, rawJsonMode, tickerItems } = useTerminalCockpit();

  return (
    <header className="term-cmdbar">
      <div className="term-cmdbar__brand">
        <Link href="/" className="term-cmdbar__title">
          SV·TERM
        </Link>
        <span className="term-cmdbar__ver muted">read-plane</span>
      </div>
      <nav className="term-cmdbar__nav" aria-label="Workspace">
        {NAV.map((n) => (
          <Link
            key={n.href}
            href={n.href}
            className={`term-cmdbar__nav-item${pathname === n.href ? " is-active" : ""}`}
            title={n.title}
          >
            <span className="term-cmdbar__abbr">{n.abbr}</span>
          </Link>
        ))}
      </nav>
      <div id="terminal-status-rail" className="term-cmdbar__ticker" tabIndex={-1}>
        <StatusTicker items={tickerItems} />
      </div>
      <div className="term-cmdbar__actions">
        {rawJsonMode && <span className="term-cmdbar__flag">RAW</span>}
        <button type="button" className="term-btn term-btn--sm" onClick={() => setPaletteOpen(true)} title="Ctrl+K">
          ⌘K
        </button>
        <button
          type="button"
          className="term-btn term-btn--sm"
          onClick={() => refreshRouteQueries(pathname)}
          title="Refresh queries for this route (R)"
        >
          Refresh
        </button>
      </div>
    </header>
  );
}

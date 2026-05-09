"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const NAV: { href: string; label: string }[] = [
  { href: "/", label: "Home" },
  { href: "/workboard", label: "Workboard" },
  { href: "/daily-operator-run", label: "Daily Run" },
  { href: "/readiness", label: "Readiness" },
  { href: "/evidence", label: "Evidence" },
  { href: "/evidence-chain", label: "Evidence Chain" },
  { href: "/evidence-bundles", label: "Evidence Bundles" },
  { href: "/operator-packs", label: "Operator Packs" },
  { href: "/operator-actions", label: "Operator Actions" },
  { href: "/operator-command-policy", label: "Command Policy" },
  { href: "/ledger", label: "Ledger" },
  { href: "/tribunal", label: "Tribunal" },
  { href: "/providers", label: "Providers" },
  { href: "/market-data-integrity", label: "Market Data" },
  { href: "/backtest-forensics", label: "Backtest Forensics" },
  { href: "/promotion-review", label: "Promotion Review" },
  { href: "/paper-execution", label: "Paper Execution" },
  { href: "/runtime", label: "Runtime" },
  { href: "/research-compute", label: "Compute" },
  { href: "/projection-registry", label: "Projection Registry" },
  { href: "/strategy-memory", label: "Memory" },
  { href: "/strategy-graveyard", label: "Graveyard" },
  { href: "/strategy-inbox", label: "Strategy Inbox" },
  { href: "/thesis", label: "Thesis" },
  { href: "/shadow-book", label: "Shadow Book" },
  { href: "/research-briefing", label: "Briefing" },
  { href: "/research-export", label: "Export" },
];

export function ConsoleShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="cockpit-root">
      <header className="cockpit-shell">
        <div className="cockpit-brand">
          <Link href="/" className="cockpit-title">
            Strategist
          </Link>
          <span className="cockpit-sub muted">Operator console · read-plane</span>
        </div>
        <nav className="cockpit-nav" aria-label="Primary">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={pathname === item.href ? "cockpit-nav-link active" : "cockpit-nav-link"}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </header>
      {children}
    </div>
  );
}

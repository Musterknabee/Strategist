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
  { href: "/ledger", label: "Ledger" },
  { href: "/providers", label: "Providers" },
  { href: "/paper-execution", label: "Paper Execution" },
  { href: "/runtime", label: "Runtime" },
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

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const NAV: { href: string; label: string }[] = [
  { href: "/", label: "Home" },
  { href: "/workboard", label: "Workboard" },
  { href: "/readiness", label: "Readiness" },
  { href: "/evidence", label: "Evidence" },
  { href: "/ledger", label: "Ledger" },
  { href: "/providers", label: "Providers" },
  { href: "/runtime", label: "Runtime" },
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

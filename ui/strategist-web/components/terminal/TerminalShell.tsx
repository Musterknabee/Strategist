"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useRef } from "react";
import { G_CHORD_ROUTES } from "@/lib/terminal/command-registry";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import { CommandBar } from "./CommandBar";
import { CommandPalette } from "./CommandPalette";
import { EventTape } from "./EventTape";
import { InspectorDrawer } from "./InspectorDrawer";
import { ShortcutHelp } from "./ShortcutHelp";
import { DemoModeBanner } from "@/components/demo/DemoModeBanner";

const RAIL: { href: string; icon: string; label: string }[] = [
  { href: "/", icon: "O", label: "Overview" },
  { href: "/readiness", icon: "R", label: "Readiness" },
  { href: "/evidence", icon: "E", label: "Evidence" },
  { href: "/evidence-bundles", icon: "G", label: "Evidence Bundles" },
  { href: "/operator-packs", icon: "O", label: "Packs" },
  { href: "/operator-actions", icon: "J", label: "Actions" },
  { href: "/ledger", icon: "L", label: "Ledger" },
  { href: "/tribunal", icon: "Q", label: "Tribunal" },
  { href: "/providers", icon: "P", label: "Providers" },
  { href: "/market-data-integrity", icon: "D", label: "Market Data" },
  { href: "/backtest-forensics", icon: "F", label: "Forensics" },
  { href: "/promotion-review", icon: "V", label: "Promotion" },
  { href: "/projection-registry", icon: "R", label: "Registry" },
  { href: "/semantic-release", icon: "H", label: "Semantic Release" },
  { href: "/semantic-validator-handoff", icon: "Y", label: "Validator Handoff" },
  { href: "/semantic-validator-handoff-lineage", icon: "N", label: "Handoff Lineage" },
  { href: "/semantic-validator-handoff-remediation", icon: "X", label: "Handoff Repair" },
  { href: "/semantic-validator-handoff-review", icon: "U", label: "Handoff Review" },
  { href: "/semantic-validator-handoff-decision", icon: "I", label: "Handoff Decision" },
  { href: "/semantic-validator-handoff-signoff", icon: "S", label: "Handoff Signoff" },
  { href: "/semantic-validator-handoff-custody", icon: "C", label: "Handoff Custody" },
  { href: "/semantic-validator-handoff-archive", icon: "A", label: "Handoff Archive" },
  { href: "/semantic-validator-handoff-closure", icon: "Z", label: "Handoff Closure" },
  { href: "/semantic-validator-handoff-continuity", icon: "G", label: "Handoff Continuity" },
  { href: "/semantic-validator-handoff-runbook", icon: "B", label: "Handoff Runbook" },
  { href: "/semantic-validator-handoff-exceptions", icon: "!", label: "Handoff Exceptions" },
  { href: "/semantic-validator-handoff-timeline", icon: "~", label: "Handoff Timeline" },
  { href: "/semantic-validator-handoff-evidence-gaps", icon: "?", label: "Handoff Gaps" },
  { href: "/semantic-validator-handoff-audit-packet", icon: "@", label: "Handoff Packet" },
  { href: "/semantic-validator-handoff-action-queue", icon: ">", label: "Handoff Queue" },
  { href: "/semantic-validator-handoff-escalation-board", icon: "^", label: "Handoff Escalations" },
  { href: "/semantic-validator-handoff-resolution-plan", icon: "=", label: "Handoff Plan" },
  { href: "/semantic-validator-handoff-clearance-gate", icon: "✓", label: "Handoff Clearance" },
  { href: "/semantic-validator-handoff-clearance-dossier", icon: "D", label: "Handoff Dossier" },
  { href: "/semantic-validator-handoff-clearance-checklist", icon: "☑", label: "Handoff Checklist" },
  { href: "/semantic-validator-handoff-clearance-evidence-matrix", icon: "M", label: "Handoff Matrix" },
  { href: "/semantic-validator-handoff-clearance-coverage-board", icon: "V", label: "Handoff Coverage" },
  { href: "/semantic-validator-handoff-clearance-operations-board", icon: "Ω", label: "Handoff Ops" },
  { href: "/semantic-validator-handoff-clearance-action-register", icon: "λ", label: "Handoff Actions" },
  { href: "/semantic-validator-handoff-clearance-resolution-plan", icon: "ρ", label: "Handoff Clear Plan" },
  { href: "/semantic-validator-handoff-clearance-verification-board", icon: "φ", label: "Handoff Verify" },
  { href: "/semantic-validator-handoff-clearance-closeout-board", icon: "χ", label: "Handoff Closeout" },
  { href: "/semantic-validator-handoff-clearance-review-docket", icon: "ψ", label: "Handoff Review" },
  { href: "/semantic-validator-handoff-clearance-signoff-packet", icon: "σ", label: "Handoff Signoff" },
  { href: "/semantic-validator-handoff-clearance-acceptance-board", icon: "α", label: "Handoff Accept" },
  { href: "/semantic-validator-handoff-clearance-release-readiness-board", icon: "β", label: "Handoff Release" },
  { href: "/semantic-validator-handoff-clearance-release-packet", icon: "γ", label: "Handoff Rel Packet" },
  { href: "/semantic-validator-handoff-clearance-release-handoff-board", icon: "δ", label: "Handoff Rel Handoff" },
  { href: "/semantic-validator-handoff-clearance-release-custody-board", icon: "ζ", label: "Handoff Custody" },
  { href: "/semantic-validator-handoff-clearance-release-receipt-board", icon: "η", label: "Handoff Receipt" },
  { href: "/semantic-validator-handoff-clearance-release-acknowledgment-board", icon: "θ", label: "Handoff Ack" },
  { href: "/semantic-validator-handoff-clearance-release-confirmation-board", icon: "κ", label: "Handoff Confirm" },
  { href: "/semantic-validator-handoff-clearance-release-completion-board", icon: "λ", label: "Handoff Complete" },
  { href: "/semantic-validator-handoff-clearance-release-closure-board", icon: "μ", label: "Handoff Closure" },
  { href: "/semantic-validator-handoff-clearance-release-archive-board", icon: "ν", label: "Handoff Archive" },
  { href: "/semantic-validator-handoff-clearance-release-retention-board", icon: "ρ", label: "Handoff Retention" },
  { href: "/semantic-validator-handoff-clearance-release-disposition-board", icon: "δ", label: "Handoff Disposition" },
  { href: "/semantic-validator-handoff-clearance-release-disposal-board", icon: "ξ", label: "Handoff Disposal" },
  { href: "/runtime", icon: "T", label: "Runtime" },
  { href: "/workboard", icon: "W", label: "Workboard" },
  { href: "/strategy-lab", icon: "S", label: "Strategy Lab" },
  { href: "/paper-tracking", icon: "K", label: "Paper" },
  { href: "/strategy-memory", icon: "M", label: "Memory" },
  { href: "/thesis", icon: "F", label: "Thesis" },
  { href: "/shadow-book", icon: "B", label: "Shadow Book" },
  { href: "/research-closure", icon: "C", label: "Closure" },
  { href: "/research-attestation", icon: "A", label: "Attest" },
  { href: "/research-briefing", icon: "D", label: "Brief" },
  { href: "/research-export", icon: "Z", label: "Export" },
  { href: "/research-run", icon: "U", label: "Run" },
  { href: "/research-catalog", icon: "I", label: "Catalog" },
  { href: "/research-drift", icon: "V", label: "Drift" },
  { href: "/research-policy-gate", icon: "Y", label: "Policy" },
  { href: "/research-exception", icon: "N", label: "Exception" },
  { href: "/research-remediation", icon: "M", label: "Remediate" },
  { href: "/research-release-readiness", icon: "Q", label: "Release" },
  { href: "/research-handoff", icon: "H", label: "Handoff" },
  { href: "/research-handoff-signoff", icon: "S", label: "Signoff" },
  { href: "/research-review-journal", icon: "J", label: "Journal" },
  { href: "/research-os", icon: "X", label: "Research OS" },
];

function typingTarget(): boolean {
  const el = document.activeElement;
  if (!el) return false;
  const tag = el.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  return el instanceof HTMLElement && el.isContentEditable;
}

const G_CHORD_MS = 1000;

export function TerminalShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const gChordRef = useRef<{ armed: boolean; t: ReturnType<typeof setTimeout> | null }>({
    armed: false,
    t: null,
  });
  const {
    setPaletteOpen,
    setShortcutHelpOpen,
    closeInspector,
    refreshRouteQueries,
    paletteOpen,
    shortcutHelpOpen,
  } = useTerminalCockpit();

  useEffect(() => {
    const disarmG = () => {
      const s = gChordRef.current;
      s.armed = false;
      if (s.t) {
        clearTimeout(s.t);
        s.t = null;
      }
    };

    const armG = () => {
      const s = gChordRef.current;
      if (s.t) clearTimeout(s.t);
      s.armed = true;
      s.t = setTimeout(() => disarmG(), G_CHORD_MS);
    };

    const onKey = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen(true);
        return;
      }
      if (e.key === "Escape") {
        disarmG();
        setPaletteOpen(false);
        setShortcutHelpOpen(false);
        closeInspector();
        return;
      }
      if (typingTarget()) return;
      const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;

      if (gChordRef.current.armed && !e.ctrlKey && !e.metaKey && !e.altKey && e.key.length === 1) {
        const path = G_CHORD_ROUTES[k];
        e.preventDefault();
        disarmG();
        if (path) router.push(path);
        return;
      }

      if (k === "g" && !e.ctrlKey && !e.metaKey && !e.altKey) {
        e.preventDefault();
        armG();
        return;
      }

      if (e.key === "/") {
        e.preventDefault();
        setPaletteOpen(true);
        return;
      }
      if (e.key === "?" || (e.shiftKey && e.key === "/")) {
        e.preventDefault();
        setShortcutHelpOpen(true);
        return;
      }
      if (e.key === "r" || e.key === "R") {
        if (!e.ctrlKey && !e.metaKey && !e.altKey) {
          e.preventDefault();
          refreshRouteQueries(pathname);
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => {
      disarmG();
      window.removeEventListener("keydown", onKey);
    };
  }, [setPaletteOpen, setShortcutHelpOpen, closeInspector, refreshRouteQueries, router, pathname]);

  return (
    <div className="term-root">
      <div className="term-layout">
        <aside className="term-rail" aria-label="Quick nav">
          <nav className="term-rail__nav" aria-label="Operator sections">
            {RAIL.map((r) => (
              <Link
                key={r.href}
                href={r.href}
                className={`term-rail__link${pathname === r.href ? " is-active" : ""}`}
                title={r.label}
              >
                <span className="term-rail__icon" aria-hidden="true">
                  {r.icon}
                </span>
                <span className="term-rail__label">{r.label}</span>
              </Link>
            ))}
          </nav>
          <div className="term-rail__bottom" aria-label="Utilities">
            <button type="button" className="term-rail__utility" title="Shortcut help" onClick={() => setShortcutHelpOpen(true)}>
              ?
            </button>
            <button type="button" className="term-rail__utility" title="Command palette" onClick={() => setPaletteOpen(true)}>
              K
            </button>
          </div>
        </aside>
        <div className="term-column">
          <DemoModeBanner />
          <CommandBar />
          <div className="term-workspace">
            <main className="term-main">{children}</main>
            <InspectorDrawer />
          </div>
          <footer className="term-footer">
            <EventTape />
            <div className="term-footer__hints muted">
              <span>⌘K palette</span>
              <span>/ palette</span>
              <span>G+O/W/R/E/G/L/P/T/U/= nav</span>
              <span>R refresh route</span>
              <span>? help</span>
              <span>Esc close</span>
              {paletteOpen && <span className="term-footer__flag">PALETTE</span>}
              {shortcutHelpOpen && <span className="term-footer__flag">HELP</span>}
            </div>
          </footer>
        </div>
      </div>
      <CommandPalette />
      <ShortcutHelp />
    </div>
  );
}

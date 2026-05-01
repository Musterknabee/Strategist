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

const RAIL: { href: string; abbr: string }[] = [
  { href: "/", abbr: "OV" },
  { href: "/workboard", abbr: "WB" },
  { href: "/readiness", abbr: "RD" },
  { href: "/evidence", abbr: "EV" },
  { href: "/ledger", abbr: "LG" },
  { href: "/providers", abbr: "PR" },
  { href: "/runtime", abbr: "RT" },
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
          {RAIL.map((r) => (
            <Link
              key={r.href}
              href={r.href}
              className={`term-rail__link${pathname === r.href ? " is-active" : ""}`}
              title={r.href}
            >
              {r.abbr}
            </Link>
          ))}
        </aside>
        <div className="term-column">
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
              <span>G+O/W/R/E/L/P/T nav</span>
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

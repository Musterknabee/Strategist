"use client";

import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import { G_CHORD_HELP_ROWS } from "@/lib/terminal/command-registry";

const ROWS: [string, string][] = [
  ["Ctrl+K / ⌘K", "Command palette"],
  ["/", "Command palette (when not typing)"],
  ...G_CHORD_HELP_ROWS,
  ["R", "Refresh queries for the current route only"],
  ["Palette: Refresh current route", "Same as R · scoped TanStack invalidation"],
  ["Palette: Refresh all (full)", "Invalidates every strategist query"],
  ["?", "This help"],
  ["Esc", "Close palette / inspector / help"],
  ["Raw JSON mode", "Toggle in palette · collapsible in inspector"],
];

export function ShortcutHelp() {
  const { shortcutHelpOpen, setShortcutHelpOpen } = useTerminalCockpit();
  if (!shortcutHelpOpen) return null;
  return (
    <div className="term-palette-backdrop" role="presentation" onClick={() => setShortcutHelpOpen(false)}>
      <div className="term-shortcut-help" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Shortcuts">
        <header className="term-shortcut-help__head">
          <strong>Strategy Validator Terminal</strong>
          <button type="button" className="term-icon-btn" onClick={() => setShortcutHelpOpen(false)}>
            ✕
          </button>
        </header>
        <p className="muted term-shortcut-help__banner">
          Frontend readiness: <strong>NOT_CLAIMED</strong>. Read-plane only; no API token in browser.
        </p>
        <table className="term-shortcut-table">
          <tbody>
            {ROWS.map(([k, v]) => (
              <tr key={k}>
                <td>
                  <kbd className="term-kbd">{k}</kbd>
                </td>
                <td>{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

"use client";

import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { filterCommands, TERMINAL_COMMANDS, type TerminalCommand } from "@/lib/terminal/command-registry";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";

export function CommandPalette() {
  const router = useRouter();
  const pathname = usePathname();
  const {
    paletteOpen,
    setPaletteOpen,
    refreshAllQueries,
    refreshRouteQueries,
    toggleRawJsonMode,
    closeInspector,
    setShortcutHelpOpen,
    setLastDigest,
    lastDigest,
  } = useTerminalCockpit();
  const [q, setQ] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const list = useMemo(() => filterCommands(q), [q]);

  useEffect(() => {
    if (paletteOpen) {
      setQ("");
      setActive(0);
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [paletteOpen]);

  const run = useCallback(
    (cmd: TerminalCommand) => {
      switch (cmd.action.type) {
        case "nav":
          router.push(cmd.action.path);
          setPaletteOpen(false);
          break;
        case "refresh-visible":
          refreshRouteQueries(pathname);
          setPaletteOpen(false);
          break;
        case "refresh-all":
          refreshAllQueries();
          setPaletteOpen(false);
          break;
        case "toggle-raw-json":
          toggleRawJsonMode();
          setPaletteOpen(false);
          break;
        case "open-palette":
          break;
        case "close-overlays":
          setPaletteOpen(false);
          closeInspector();
          setShortcutHelpOpen(false);
          break;
        case "focus-tape":
          document.getElementById("terminal-event-tape")?.focus();
          setPaletteOpen(false);
          break;
        case "focus-alerts":
          document.getElementById("terminal-status-rail")?.focus();
          setPaletteOpen(false);
          break;
        case "copy-last-digest":
          if (lastDigest) void navigator.clipboard.writeText(lastDigest);
          setPaletteOpen(false);
          break;
        case "shortcut-help":
          setShortcutHelpOpen(true);
          setPaletteOpen(false);
          break;
        default:
          break;
      }
    },
    [
      router,
      setPaletteOpen,
      refreshAllQueries,
      refreshRouteQueries,
      pathname,
      toggleRawJsonMode,
      closeInspector,
      setShortcutHelpOpen,
      lastDigest,
    ],
  );

  if (!paletteOpen) return null;

  return (
    <div className="term-palette-backdrop" role="presentation" onClick={() => setPaletteOpen(false)}>
      <div
        className="term-palette"
        role="dialog"
        aria-label="Command palette"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => {
          if (e.key === "ArrowDown") {
            e.preventDefault();
            setActive((i) => Math.min(i + 1, list.length - 1));
          } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setActive((i) => Math.max(i - 1, 0));
          } else if (e.key === "Enter" && list[active]) {
            e.preventDefault();
            run(list[active]);
          }
        }}
      >
        <input
          ref={inputRef}
          className="term-palette__input"
          placeholder="Command…"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setActive(0);
          }}
          aria-autocomplete="list"
        />
        <ul className="term-palette__list" role="listbox">
          {list.map((cmd, i) => (
            <li key={cmd.id}>
              <button
                type="button"
                role="option"
                aria-selected={i === active}
                className={`term-palette__item${i === active ? " term-palette__item--active" : ""}`}
                onMouseEnter={() => setActive(i)}
                onClick={() => run(cmd)}
              >
                {cmd.label}
              </button>
            </li>
          ))}
        </ul>
        <div className="term-palette__hint muted">
          {TERMINAL_COMMANDS.length} commands · ↑↓ enter · esc close · read-plane only
        </div>
      </div>
    </div>
  );
}

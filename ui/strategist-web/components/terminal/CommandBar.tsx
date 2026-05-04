"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useUiFacade } from "@/hooks/useUiFacade";
import { useUiEvidence } from "@/hooks/useUiEvidence";
import { useUiRuntime } from "@/hooks/useUiRuntime";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asString, asRecord } from "@/lib/operator/payload-utils";
import { readUiEvidenceCockpit } from "@/lib/operator/ui-evidence-cockpit";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { StatusTicker } from "./StatusTicker";

export function CommandBar() {
  const pathname = usePathname();
  const { setPaletteOpen, refreshRouteQueries, rawJsonMode, tickerItems } = useTerminalCockpit();
  const config = tryGetPublicStrategistApiBaseUrl();
  const facade = useUiFacade();
  const evidence = useUiEvidence(undefined);
  const runtime = useUiRuntime("operator");
  const [utc, setUtc] = useState(() => new Date().toISOString().replace(/\.\d{3}Z$/, "Z"));

  useEffect(() => {
    const id = window.setInterval(() => {
      setUtc(new Date().toISOString().replace(/\.\d{3}Z$/, "Z"));
    }, 1000);
    return () => window.clearInterval(id);
  }, []);

  const ev = evidence.data ? asRecord(evidence.data) : null;
  const cockpit = readUiEvidenceCockpit(ev);
  const deployment =
    cockpit?.deployment_status === "PASS"
      ? "DEPLOYMENT_APPROVED"
      : cockpit?.deployment_status
        ? `DEPLOYMENT_${cockpit.deployment_status}`
        : "DEPLOYMENT_UNKNOWN";
  const env =
    asString(asRecord(runtime.data)?.environment) ??
    asString(asRecord(evidence.data)?.runtime_mode) ??
    asString(asRecord(evidence.data)?.environment) ??
    "UNKNOWN";

  return (
    <header className="term-cmdbar">
      <div className="term-cmdbar__brand">
        <Link href="/" className="term-cmdbar__title">
          STRATEGIST TERMINAL
        </Link>
        <span className="term-cmdbar__ver muted">Strategy Validator Terminal</span>
      </div>
      <div className="term-cmdbar__meta" aria-label="Environment and deployment">
        <StatusBadge raw={env} />
        <StatusBadge raw={deployment} />
        <span className="term-cmdbar__endpoint">{config.ok ? config.baseUrl.replace(/^https?:\/\//, "") : "API_UNKNOWN"}</span>
      </div>
      <div id="terminal-status-rail" className="term-cmdbar__ticker" tabIndex={-1}>
        <StatusTicker items={tickerItems} />
      </div>
      <div className="term-cmdbar__actions">
        {rawJsonMode && <span className="term-cmdbar__flag">RAW</span>}
        <button type="button" className="term-command-input" onClick={() => setPaletteOpen(true)} title="Ctrl+K">
          <span>Search / command</span>
          <kbd>Ctrl+K</kbd>
        </button>
        <span className="term-cmdbar__clock">{utc}</span>
        <span className={`term-cmdbar__refresh ${facade.isFetching || evidence.isFetching ? "is-fetching" : ""}`}>
          <span aria-hidden="true" />
          30s
        </span>
        <button
          type="button"
          className="term-btn term-btn--sm"
          onClick={() => refreshRouteQueries(pathname)}
          title="Refresh queries for this route (R)"
        >
          R
        </button>
      </div>
    </header>
  );
}

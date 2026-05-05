"use client";

import { useMemo, useState } from "react";
import { Pane } from "@/components/terminal/Pane";
import { StatusBadge } from "@/components/operator/StatusBadge";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import { buildOperatorHealthAlerts } from "@/lib/operator/operator-health-alerts-model";
import type {
  OperatorHealthAlert,
  OperatorHealthAlertCategory,
  OperatorHealthAlertSeverity,
  OperatorHealthAlertsInput,
} from "@/lib/operator/operator-health-alerts-model";
import { inspectBody } from "./cockpit-utils";

const SEVERITY_FILTERS: Array<OperatorHealthAlertSeverity | "ALL"> = ["ALL", "CRITICAL", "WARNING", "INFO", "UNKNOWN"];

const CATEGORY_FILTERS: Array<OperatorHealthAlertCategory | "ALL"> = [
  "ALL",
  "Service Reachability",
  "Readiness",
  "Production Auth",
  "Ledger / Evidence Chain",
  "Provider Freshness",
  "Deployment Evidence",
  "Frontend Readiness",
  "Release / CI Drift",
  "Paper / Execution Firewall",
  "Research OS Drift",
];

function paneBadge(bundle: ReturnType<typeof buildOperatorHealthAlerts>, queryFailed: boolean): string {
  if (queryFailed) return "DEGRADED";
  if (bundle.counts.CRITICAL > 0) return "CRITICAL";
  if (bundle.counts.WARNING > 0) return "WARNING";
  if (bundle.counts.UNKNOWN > 0) return "UNKNOWN";
  return "OK";
}

function digestToCopyFromRaw(raw: Record<string, unknown>): string | undefined {
  const full = raw.digest_full;
  if (typeof full === "string" && full.length >= 16) return full;
  return undefined;
}

export type OperatorHealthAlertsPaneProps = {
  healthInput: OperatorHealthAlertsInput;
  queryFailed: boolean;
  openInspector: (payload: InspectorPayload) => void;
};

export function OperatorHealthAlertsPane({ healthInput, queryFailed, openInspector }: OperatorHealthAlertsPaneProps) {
  const bundle = useMemo(() => buildOperatorHealthAlerts(healthInput), [healthInput]);
  const [severityFilter, setSeverityFilter] = useState<OperatorHealthAlertSeverity | "ALL">("ALL");
  const [categoryFilter, setCategoryFilter] = useState<OperatorHealthAlertCategory | "ALL">("ALL");

  const filtered = useMemo(() => {
    return bundle.alerts.filter((a) => {
      if (severityFilter !== "ALL" && a.severity !== severityFilter) return false;
      if (categoryFilter !== "ALL" && a.category !== categoryFilter) return false;
      return true;
    });
  }, [bundle.alerts, severityFilter, categoryFilter]);

  const badge = paneBadge(bundle, queryFailed);

  const openAlert = (a: OperatorHealthAlert) => {
    openInspector({
      title: `Alert · ${a.alert_id}`,
      subtitle: `${a.severity} · ${a.category}`,
      body: inspectBody({
        status: a.status,
        summary: a.summary,
        warnings: [a.source_endpoint, `generated_at_utc=${a.generated_at_utc}`],
        details: [
          { k: "remediation", v: a.remediation },
          { k: "digest_prefix", v: a.evidence_digest_prefix },
        ],
      }),
      rawJson: a.raw,
      digestToCopy: digestToCopyFromRaw(a.raw),
    });
  };

  return (
    <div className="cockpit-health-alerts-row" data-testid="cockpit-operator-health-alerts">
      <Pane
        title="Operator health / alerts"
        dense
        badge={<StatusBadge raw={badge} />}
        onInspect={() =>
          openInspector({
            title: "Operator health · read-plane bundle",
            subtitle: `generated_at_utc=${bundle.generated_at_utc}`,
            body: inspectBody({
              status: badge,
              summary: "Derived from healthz, livez, readyz, runtime, evidence, evidence-chain, providers, facade, release readiness, drift, paper execution.",
              warnings: [
                `CRITICAL=${bundle.counts.CRITICAL}`,
                `WARNING=${bundle.counts.WARNING}`,
                `INFO=${bundle.counts.INFO}`,
                `UNKNOWN=${bundle.counts.UNKNOWN}`,
              ],
              details: [],
            }),
            rawJson: { counts: bundle.counts, alert_count: bundle.alerts.length },
          })
        }
      >
        <div className="pane-footer" style={{ marginBottom: 6 }}>
          Alert counts (read-plane)
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 8 }} data-testid="cockpit-health-alert-counts">
          {(["CRITICAL", "WARNING", "INFO", "UNKNOWN"] as const).map((s) => (
            <span key={s} className="term-chip" data-testid={`cockpit-health-count-${s}`}>
              {s}:{bundle.counts[s]}
            </span>
          ))}
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 8, fontSize: 11 }} data-testid="cockpit-health-alert-filters">
          <label style={{ display: "flex", gap: 4, alignItems: "center" }}>
            severity
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value as OperatorHealthAlertSeverity | "ALL")}
              className="term-select"
              aria-label="Filter alerts by severity"
            >
              {SEVERITY_FILTERS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label style={{ display: "flex", gap: 4, alignItems: "center" }}>
            category
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value as OperatorHealthAlertCategory | "ALL")}
              className="term-select"
              aria-label="Filter alerts by category"
            >
              {CATEGORY_FILTERS.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div style={{ overflow: "auto", maxHeight: "min(38vh, 300px)", fontSize: 11 }} data-testid="cockpit-health-alert-table">
          <table className="cockpit-health-alert-table" style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: "2px 4px" }}>sev</th>
                <th style={{ textAlign: "left", padding: "2px 4px" }}>category</th>
                <th style={{ textAlign: "left", padding: "2px 4px" }}>summary</th>
                <th style={{ textAlign: "left", padding: "2px 4px" }}>source</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((a) => (
                <tr key={a.alert_id}>
                  <td style={{ padding: "2px 4px", whiteSpace: "nowrap" }} data-testid={`cockpit-health-row-sev-${a.alert_id}`}>
                    <StatusBadge raw={a.severity} />
                  </td>
                  <td style={{ padding: "2px 4px" }}>{a.category}</td>
                  <td style={{ padding: "2px 4px" }}>
                    <button type="button" className="linkish" onClick={() => openAlert(a)} data-testid={`cockpit-health-row-open-${a.alert_id}`}>
                      {a.summary}
                    </button>
                    <div style={{ opacity: 0.85, marginTop: 2 }}>{a.remediation}</div>
                  </td>
                  <td style={{ padding: "2px 4px", opacity: 0.9 }}>{a.source_endpoint}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Pane>
    </div>
  );
}

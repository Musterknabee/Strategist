"use client";

import { useMemo, useState } from "react";
import { Pane } from "@/components/terminal/Pane";
import { StatusBadge } from "@/components/operator/StatusBadge";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import {
  buildRemediationGovernanceItems,
  type GovernanceItem,
  type GovernanceItemCategory,
} from "@/lib/operator/remediation-governance-model";
import type { RemediationGovernanceInput } from "@/lib/operator/remediation-governance-model";
import { inspectBody } from "./cockpit-utils";

const CAT_FILTERS: Array<GovernanceItemCategory | "ALL"> = [
  "ALL",
  "Readiness Blocker",
  "Provider / Freshness",
  "Evidence Drift",
  "Policy Gate",
  "Release Readiness",
  "Research OS Exception",
  "Remediation",
  "Review Journal",
  "Unknown",
];

const SEV_FILTERS = ["ALL", "CRITICAL", "WARNING", "INFO", "UNKNOWN"] as const;

function digestToCopyFromRaw(raw: Record<string, unknown>): string | undefined {
  const full = raw.digest_full;
  if (typeof full === "string" && full.length >= 16) return full;
  return undefined;
}

function paneBadge(bundle: ReturnType<typeof buildRemediationGovernanceItems>, queryFailed: boolean): string {
  if (queryFailed) return "DEGRADED";
  if (bundle.counts.CRITICAL > 0) return "CRITICAL";
  if (bundle.counts.WARNING > 0) return "WARNING";
  if (bundle.counts.UNKNOWN > 0) return "UNKNOWN";
  return "OK";
}

export type RemediationGovernancePaneProps = {
  governanceInput: RemediationGovernanceInput;
  queryFailed: boolean;
  openInspector: (payload: InspectorPayload) => void;
};

export function RemediationGovernancePane({ governanceInput, queryFailed, openInspector }: RemediationGovernancePaneProps) {
  const bundle = useMemo(() => buildRemediationGovernanceItems(governanceInput), [governanceInput]);
  const [cat, setCat] = useState<GovernanceItemCategory | "ALL">("ALL");
  const [sev, setSev] = useState<(typeof SEV_FILTERS)[number]>("ALL");

  const filtered = useMemo(() => {
    return bundle.items.filter((it) => {
      if (cat !== "ALL" && it.category !== cat) return false;
      if (sev !== "ALL" && it.severity !== sev) return false;
      return true;
    });
  }, [bundle.items, cat, sev]);

  const badge = paneBadge(bundle, queryFailed);

  const openRow = (it: GovernanceItem) => {
    openInspector({
      title: `Governance · ${it.item_id}`,
      subtitle: `${it.severity} · ${it.category}`,
      body: inspectBody({
        status: it.status,
        summary: it.blocker_code,
        warnings: [
          `exception=${it.exception_semantics}`,
          `remediation=${it.remediation_semantics}`,
          `owner=${it.owner_operator}`,
        ],
        details: [
          { k: "exception_scope", v: it.exception_scope },
          { k: "exception_expiry", v: it.exception_expiry },
          { k: "recommended_next_action", v: it.recommended_next_action },
          { k: "digest_prefix", v: it.evidence_digest_prefix },
        ],
      }),
      rawJson: it.raw,
      digestToCopy: digestToCopyFromRaw(it.raw),
    });
  };

  return (
    <div className="cockpit-health-alerts-row" data-testid="cockpit-remediation-governance">
      <Pane
        title="Incident / remediation / exceptions"
        dense
        badge={<StatusBadge raw={badge} />}
        onInspect={() =>
          openInspector({
            title: "Governance · read-plane bundle",
            subtitle: `generated_at_utc=${bundle.generated_at_utc}`,
            body: inspectBody({
              status: badge,
              summary: "Blockers remain visible; exceptions are scoped overlays only.",
              warnings: Object.entries(bundle.counts).map(([k, v]) => `${k}=${v}`),
              details: [],
            }),
            rawJson: { counts: bundle.counts, item_count: bundle.items.length },
          })
        }
      >
        <div className="pane-footer" style={{ marginBottom: 6 }}>
          Severity counts
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 8 }} data-testid="cockpit-governance-counts">
          {(Object.keys(bundle.counts) as Array<keyof typeof bundle.counts>).map((k) => (
            <span key={k} className="term-chip" data-testid={`cockpit-governance-count-${k}`}>
              {k}:{bundle.counts[k]}
            </span>
          ))}
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 8, fontSize: 11 }} data-testid="cockpit-governance-filters">
          <label style={{ display: "flex", gap: 4, alignItems: "center" }}>
            severity
            <select className="term-select" aria-label="Filter by severity" value={sev} onChange={(e) => setSev(e.target.value as (typeof SEV_FILTERS)[number])}>
              {SEV_FILTERS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label style={{ display: "flex", gap: 4, alignItems: "center" }}>
            category
            <select className="term-select" aria-label="Filter by category" value={cat} onChange={(e) => setCat(e.target.value as GovernanceItemCategory | "ALL")}>
              {CAT_FILTERS.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div style={{ overflow: "auto", maxHeight: "min(36vh, 280px)", fontSize: 11 }} data-testid="cockpit-governance-table">
          <table className="cockpit-health-alert-table" style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: "2px 4px" }}>sev</th>
                <th style={{ textAlign: "left", padding: "2px 4px" }}>category</th>
                <th style={{ textAlign: "left", padding: "2px 4px" }}>blocker / subject</th>
                <th style={{ textAlign: "left", padding: "2px 4px" }}>exception</th>
                <th style={{ textAlign: "left", padding: "2px 4px" }}>remediation</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((it) => (
                <tr key={it.item_id}>
                  <td style={{ padding: "2px 4px" }} data-testid={`cockpit-governance-sev-${it.item_id}`}>
                    <StatusBadge raw={it.severity} />
                  </td>
                  <td style={{ padding: "2px 4px" }}>{it.category}</td>
                  <td style={{ padding: "2px 4px" }}>
                    <button type="button" className="linkish" onClick={() => openRow(it)} data-testid={`cockpit-governance-open-${it.item_id}`}>
                      {it.blocker_code}
                    </button>
                    <div style={{ opacity: 0.85 }}>{it.recommended_next_action}</div>
                  </td>
                  <td style={{ padding: "2px 4px" }} data-testid={`cockpit-governance-ex-${it.item_id}`}>
                    <StatusBadge raw={it.exception_semantics} />
                  </td>
                  <td style={{ padding: "2px 4px" }}>
                    <StatusBadge raw={it.remediation_semantics} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Pane>
    </div>
  );
}

"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiResearchOsHandoffSignoffLatest } from "@/hooks/useUiResearchOsHandoffSignoff";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

export default function ResearchHandoffSignoffPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiResearchOsHandoffSignoffLatest();
  const root = q.data ? asRecord(q.data) : null;
  const verification = root?.latest_verification ? asRecord(root.latest_verification) : null;
  const signoff = root?.latest_signoff ? asRecord(root.latest_signoff) : null;
  const checks = Array.isArray(verification?.source_digest_checks) ? verification.source_digest_checks.map((x) => asRecord(x)) : [];
  const blockers = [...(verification ? asStringArray(verification.blockers) : []), ...(signoff ? asStringArray(signoff.blockers) : [])];
  const warnings = [...(verification ? asStringArray(verification.warnings) : []), ...(signoff ? asStringArray(signoff.warnings) : [])];

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "research-handoff-signoff",
        ts: asString(root?.generated_at_utc),
        severity: blockers.length ? "bad" : warnings.length ? "warn" : "ok",
        text: verification
          ? `HANDOFF SIGNOFF ${asString(verification.status) ?? "UNKNOWN"} · reviewer=${asString(signoff?.decision) ?? "MISSING"}`
          : "NO_RESEARCH_OS_HANDOFF_SIGNOFF",
      },
    ],
    [blockers.length, root, signoff, verification, warnings.length],
  );
  useTerminalPageBind(tape, []);

  if (!config.ok) {
    return <div className="term-page cockpit-page"><div className="term-page__banner">{config.error.message}</div></div>;
  }

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Research Handoff Signoff</h1>
          <p className="muted">Verifies handoff digests and records reviewer signoff · not deployment approval</p>
        </div>
      </div>

      <div className="readiness" role="status">
        <strong>Reviewer signoff is not DEPLOYMENT_APPROVED</strong>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          This page proves whether the handoff pack still matches its source evidence. It does not enable live trading, broker orders, or browser order controls.
        </p>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Latest handoff verification" dense onInspect={() => openInspector({ title: "Research handoff signoff", rawJson: q.data ?? {} })}>
          {q.isError && <p className="term-page__banner">Could not load /ui/research-os/handoff-signoff/latest</p>}
          {!verification ? (
            <p className="muted">No handoff verification — run <code className="json-preview">strategy-validator-research-os-handoff-signoff verify --write --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "verification_id", v: asString(verification.verification_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(verification.status) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(verification.trust_banner) ?? "—"} /> },
                { k: "source_handoff", v: asString(verification.source_handoff_id) ?? "—" },
                { k: "handoff_decision", v: <StatusBadge raw={asString(verification.source_handoff_decision) ?? "—"} /> },
                { k: "matches", v: String(verification.match_count ?? 0) },
                { k: "mismatches", v: String(verification.mismatch_count ?? 0) },
                { k: "missing", v: String(verification.missing_count ?? 0) },
                { k: "unchecked", v: String(verification.unchecked_count ?? 0) },
                { k: "verification_spine", v: (asString(verification.verification_spine_sha256) ?? "—").slice(0, 24) },
                { k: "result_sha", v: (asString(verification.result_sha256) ?? "—").slice(0, 24) },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-research-os-handoff-signoff verify --artifact-root artifacts --write --overwrite --json
          </pre>
        </Pane>

        <Pane title="Reviewer signoff" dense>
          {!signoff ? (
            <p className="muted">No reviewer signoff.</p>
          ) : (
            <TermKV
              rows={[
                { k: "signoff_id", v: asString(signoff.signoff_id) ?? "—" },
                { k: "reviewer", v: asString(signoff.reviewer_id) ?? "—" },
                { k: "decision", v: <StatusBadge raw={asString(signoff.decision) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(signoff.trust_banner) ?? "—"} /> },
                { k: "source_verification", v: asString(signoff.source_verification_id) ?? "—" },
                { k: "source_status", v: <StatusBadge raw={asString(signoff.source_verification_status) ?? "—"} /> },
                { k: "deployment_approved", v: String(Boolean(signoff.deployment_approved)) },
                { k: "manifest", v: (asString(signoff.manifest_sha256) ?? "—").slice(0, 24) },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-research-os-handoff-signoff signoff --artifact-root artifacts --reviewer-id local-reviewer --overwrite --json
          </pre>
        </Pane>

        <Pane title="Source digest checks" dense>
          {checks.length ? (
            <div className="terminal-table-wrap">
              <table className="terminal-table">
                <thead><tr><th>status</th><th>label</th><th>expected</th><th>observed</th><th>blockers</th></tr></thead>
                <tbody>
                  {checks.map((row) => (
                    <tr key={asString(row.label) ?? JSON.stringify(row)}>
                      <td><StatusBadge raw={asString(row.status) ?? "—"} /></td>
                      <td>{asString(row.label) ?? "—"}</td>
                      <td>{(asString(row.expected_manifest_sha256) ?? "—").slice(0, 16)}</td>
                      <td>{(asString(row.observed_manifest_sha256) ?? "—").slice(0, 16)}</td>
                      <td>{asStringArray(row.blockers).length}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <p className="muted">No source digest checks.</p>}
        </Pane>

        <Pane title="Constraints / followups / warnings" dense>
          <JsonDetails title="Constraints" value={signoff ? asStringArray(signoff.constraints) : []} />
          <JsonDetails title="Required followups" value={signoff ? asStringArray(signoff.required_followups) : []} />
          <JsonDetails title="Warnings" value={warnings} />
          <JsonDetails title="Blockers" value={blockers} />
        </Pane>
      </div>
    </main>
  );
}

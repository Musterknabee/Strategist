"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiResearchOsAttestationLatest } from "@/hooks/useUiResearchOsAttestation";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

type CheckRow = Record<string, unknown> & { __id: string };

export default function ResearchAttestationPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiResearchOsAttestationLatest();
  const root = q.data ? asRecord(q.data) : null;
  const verification = root?.latest_verification ? asRecord(root.latest_verification) : null;
  const attestation = root?.latest_attestation ? asRecord(root.latest_attestation) : null;
  const degraded = root ? asStringArray(root.degraded) : [];
  const vWarnings = verification ? asStringArray(verification.warnings) : [];
  const vBlockers = verification ? asStringArray(verification.blockers) : [];
  const aWarnings = attestation ? asStringArray(attestation.warnings) : [];
  const aBlockers = attestation ? asStringArray(attestation.blockers) : [];

  const checks: CheckRow[] = useMemo(() => {
    const raw = Array.isArray(verification?.artifact_checks) ? verification.artifact_checks : [];
    return raw
      .map((item, i) => {
        const r = asRecord(item);
        if (!r) return null;
        return { ...r, __id: `${asString(r.artifact_kind) ?? "artifact"}-${i}` };
      })
      .filter((x): x is CheckRow => x !== null);
  }, [verification]);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "research-attestation",
        ts: asString(root?.generated_at_utc),
        severity: vBlockers.length || aBlockers.length ? "bad" : degraded.length ? "warn" : "ok",
        text: verification
          ? `ATTESTATION ${asString(verification.status) ?? "UNKNOWN"} · checks=${checks.length}`
          : "NO_CLOSURE_VERIFICATION_RESULT",
      },
    ],
    [aBlockers.length, checks.length, degraded.length, root, verification, vBlockers.length],
  );
  useTerminalPageBind(tape, []);

  const cols: DenseColumn<CheckRow>[] = [
    { key: "kind", header: "Artifact", cell: (r) => <code>{asString(r.artifact_kind) ?? "—"}</code> },
    { key: "match", header: "Match", cell: (r) => String(r.match ?? "—") },
    { key: "exists", header: "Exists", cell: (r) => String(Boolean(r.exists_now)) },
    { key: "expected", header: "Expected", cell: (r) => (asString(r.expected_sha256) ?? "—").slice(0, 16) },
    { key: "observed", header: "Observed", cell: (r) => (asString(r.observed_sha256) ?? "—").slice(0, 16) },
  ];

  if (!config.ok) {
    return <div className="term-page cockpit-page"><div className="term-page__banner">{config.error.message}</div></div>;
  }

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Research Attestation</h1>
          <p className="muted">Closure verification + operator signoff · read-plane only · no live trading · no broker orders</p>
        </div>
      </div>

      <div className="readiness" role="status">
        <strong>Attestation is not deployment approval</strong>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          This page verifies closure digests and records operator acknowledgement. It does not authorize live execution, orders, or profitability claims.
        </p>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Closure verification" dense onInspect={() => openInspector({ title: "Research attestation", rawJson: q.data ?? {} })}>
          {q.isError && <p className="term-page__banner">Could not load /ui/research-os/attestation/latest</p>}
          {!verification ? (
            <p className="muted">No verification result — run <code className="json-preview">strategy-validator-research-os-attestation verify --write --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "verification_id", v: asString(verification.verification_id) ?? "—" },
                { k: "closure_id", v: asString(verification.closure_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(verification.status) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(verification.trust_banner) ?? "—"} /> },
                { k: "manifest_expected", v: (asString(verification.manifest_sha256_expected) ?? "—").slice(0, 24) },
                { k: "manifest_observed", v: (asString(verification.manifest_sha256_observed) ?? "—").slice(0, 24) },
                { k: "result_sha256", v: (asString(verification.result_sha256) ?? "—").slice(0, 24) },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-research-os-attestation verify --write --json
          </pre>
        </Pane>

        <Pane title="Operator attestation" dense>
          {!attestation ? (
            <p className="muted">No operator attestation — run <code className="json-preview">strategy-validator-research-os-attestation attest --operator-id local-operator --decision ACCEPTED_WITH_RESTRICTIONS --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "attestation_id", v: asString(attestation.attestation_id) ?? "—" },
                { k: "operator_id", v: asString(attestation.operator_id) ?? "—" },
                { k: "decision", v: <StatusBadge raw={asString(attestation.decision) ?? "—"} /> },
                { k: "verification_status", v: <StatusBadge raw={asString(attestation.verification_status) ?? "—"} /> },
                { k: "closure_trust_banner", v: <StatusBadge raw={asString(attestation.closure_trust_banner) ?? "—"} /> },
                { k: "attestation_sha256", v: (asString(attestation.attestation_sha256) ?? "—").slice(0, 24) },
              ]}
            />
          )}
        </Pane>

        <Pane title="Warnings / blockers" dense>
          {vWarnings.length || aWarnings.length ? <JsonDetails summary="warnings" data={[...vWarnings, ...aWarnings]} /> : <p className="muted">No warnings indexed.</p>}
          {vBlockers.length || aBlockers.length ? <JsonDetails summary="blockers" data={[...vBlockers, ...aBlockers]} /> : <p className="muted">No blockers indexed.</p>}
        </Pane>

        <Pane title="Digest checks" dense>
          <DenseTable
            columns={cols}
            rows={checks}
            rowKey={(r) => r.__id}
            onRowClick={(r) => openInspector({ title: `Digest check · ${asString(r.artifact_kind) ?? "artifact"}`, rawJson: r })}
          />
        </Pane>
      </div>
    </main>
  );
}

"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { SeverityBadge } from "@/components/terminal/SeverityBadge";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiPaperBrokerStatus } from "@/hooks/useUiPaperBroker";
import { useUiPaperTrackingLatest } from "@/hooks/useUiPaperTracking";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

export default function PaperTrackingPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const latest = useUiPaperTrackingLatest();
  const paperBroker = useUiPaperBrokerStatus();

  const root = latest.data != null ? asRecord(latest.data) : null;
  const brokerRoot = paperBroker.data != null ? asRecord(paperBroker.data) : null;
  const degraded = root ? asStringArray(root.degraded) : [];
  const bundle = root?.latest != null ? asRecord(root.latest as object) : null;
  const manifest = bundle?.manifest != null ? asRecord(bundle.manifest as object) : null;
  const candidate = manifest?.candidate != null ? asRecord(manifest.candidate as object) : null;
  const score = bundle?.scorecard != null ? asRecord(bundle.scorecard as object) : null;
  const pcf = manifest?.portfolio_carry_forward != null ? asRecord(manifest.portfolio_carry_forward as object) : null;
  const lifecycleState = asString(bundle?.lifecycle_state);
  const lifecycleBasis = asString(bundle?.lifecycle_basis_summary);
  const lifecycleDisclaimer = asString(bundle?.lifecycle_promotion_disclaimer);
  const lifecycleBlockers = asStringArray(bundle?.lifecycle_blockers);
  const killPosture = asString(bundle?.lifecycle_kill_rule_posture);
  const assessmentArtifact =
    bundle?.lifecycle_assessment_artifact != null ? asRecord(bundle.lifecycle_assessment_artifact as object) : null;

  const signals = bundle?.signal_history_recent;
  const outcomes = bundle?.outcome_history_recent;

  const lifecycleSeverity = (() => {
    if (!lifecycleState) return "neutral" as const;
    if (lifecycleState === "PROMOTION_REVIEW_READY") return "info" as const;
    if (lifecycleState === "KILLED_BY_RULE" || lifecycleState === "REJECTED") return "bad" as const;
    if (lifecycleState === "KILL_CANDIDATE" || lifecycleState === "DEGRADED") return "warn" as const;
    return "ok" as const;
  })();

  const tape: TapeLine[] = useMemo(() => {
    const ts = asString(root?.generated_at_utc);
    return [
      {
        id: "pt",
        ts,
        severity: bundle ? "ok" : "warn",
        text: bundle ? `PAPER ${asString(candidate?.strategy_id) ?? "track"}` : "NO_PAPER_TRACKING",
      },
    ];
  }, [root, bundle, candidate]);

  useTerminalPageBind(tape, []);

  if (!config.ok) {
    return (
      <div className="term-page cockpit-page">
        <div className="term-page__banner">{config.error.message}</div>
      </div>
    );
  }

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Paper tracking</h1>
          <p className="muted">
            Evidence-only paper posture · no broker orders · no live trading · read-plane
          </p>
        </div>
      </div>

      {lifecycleState === "PROMOTION_REVIEW_READY" && lifecycleDisclaimer ? (
        <div
          className="term-page__banner"
          style={{ marginBottom: "0.75rem", fontSize: "12px", lineHeight: 1.45 }}
        >
          <strong>Promotion review gate</strong> — {lifecycleDisclaimer}
        </div>
      ) : null}

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane
          title="Paper broker policy (env · read-plane)"
          dense
          onInspect={() => openInspector({ title: "Paper broker status", rawJson: brokerRoot ?? {} })}
        >
          <p className="muted" style={{ fontSize: "10px", margin: "0 0 6px" }}>
            No browser orders. Use <code>strategy-validator-paper-broker</code> CLI on a trusted host. Not live trading.
          </p>
          {paperBroker.isLoading ? (
            <p className="muted">Loading…</p>
          ) : (
            <TermKV
              rows={[
                {
                  k: "policy",
                  v: <StatusBadge raw={asString(brokerRoot?.policy_status) ?? "—"} />,
                },
                {
                  k: "blockers",
                  v: asStringArray(brokerRoot?.blockers).join("; ") || "—",
                },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Lifecycle (governed)"
          dense
          onInspect={() =>
            openInspector({
              title: "Lifecycle assessment",
              rawJson: {
                lifecycle_state: lifecycleState,
                lifecycle_basis_summary: lifecycleBasis,
                lifecycle_blockers: lifecycleBlockers,
                lifecycle_kill_rule_posture: killPosture,
                persisted_assessment_artifact: assessmentArtifact,
              },
            })
          }
        >
          {!bundle ? (
            <p className="muted">No tracking bundle.</p>
          ) : (
            <div style={{ fontSize: "11px", display: "grid", gap: "0.5rem" }}>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", alignItems: "center" }}>
                <span className="muted">State</span>
                <SeverityBadge severity={lifecycleSeverity}>
                  <strong>{lifecycleState ?? "—"}</strong>
                </SeverityBadge>
                {killPosture && killPosture !== "NONE" ? (
                  <SeverityBadge severity={killPosture.includes("HARD") ? "bad" : "warn"}>
                    kill rules · {killPosture}
                  </SeverityBadge>
                ) : null}
              </div>
              {lifecycleBasis ? <p style={{ margin: 0 }}>{lifecycleBasis}</p> : null}
              {lifecycleBlockers.length > 0 ? (
                <div>
                  <span className="muted">Blockers / notes</span>
                  <ul style={{ margin: "0.25rem 0 0", paddingLeft: "1.1rem" }}>
                    {lifecycleBlockers.slice(0, 8).map((b, i) => (
                      <li key={i}>{b}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              <p className="muted" style={{ margin: 0, fontSize: "10px" }}>
                Lifecycle is artifact-backed; run{" "}
                <code style={{ fontSize: "10px" }}>strategy-validator-paper-track assess</code> to persist{" "}
                <code style={{ fontSize: "10px" }}>candidate_lifecycle_assessment.json</code>. This UI derives the
                current gate from manifest + scorecard (same rules as assess). Not live approval.
              </p>
            </div>
          )}
        </Pane>

        <Pane
          title="Latest enrollment"
          dense
          onInspect={() =>
            openInspector({
              title: "Paper tracking · latest",
              rawJson: latest.data ?? {},
            })
          }
        >
          {latest.isError && <p className="muted">DEGRADED · could not load /ui/paper-tracking/latest</p>}
          {degraded.length > 0 && (
            <p className="muted" style={{ fontSize: "11px" }}>
              {degraded.join(", ")}
            </p>
          )}
          {bundle && manifest ? (
            <TermKV
              rows={[
                { k: "tracking_id", v: asString(bundle.tracking_id) ?? "—" },
                { k: "strategy_id", v: asString(candidate?.strategy_id) ?? "—" },
                { k: "batch_id", v: asString(candidate?.batch_id) ?? "—" },
                { k: "run_id", v: asString(candidate?.run_id) ?? "—" },
                {
                  k: "paper_posture",
                  v: asString(candidate?.paper_posture) ?? "—",
                },
                {
                  k: "synthetic_demo",
                  v: String(Boolean(candidate?.synthetic_demo)),
                },
                {
                  k: "portfolio_gate_carry",
                  v: asString(pcf?.portfolio_gate_status) ?? "—",
                },
                {
                  k: "lifecycle_state",
                  v: lifecycleState ?? "—",
                },
                {
                  k: "kill_state",
                  v: asString(score?.kill_state) ?? "—",
                },
                {
                  k: "cumulative_paper_return",
                  v:
                    typeof score?.cumulative_paper_return === "number"
                      ? String(score.cumulative_paper_return)
                      : "—",
                },
                {
                  k: "drift_score",
                  v: typeof score?.drift_score === "number" ? String(score.drift_score) : "—",
                },
                {
                  k: "execution_decay",
                  v: asString(score?.execution_realism_decay_level) ?? "—",
                },
                {
                  k: "scorecard_digest",
                  v: (asString(score?.scorecard_sha256) ?? "—").slice(0, 16),
                },
                { k: "manifest_path", v: asString(root?.manifest_path) ?? "—" },
              ]}
            />
          ) : (
            <p className="muted">No paper tracking artifacts under scan root. Enroll via CLI (paper-track enroll).</p>
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-paper-track enroll --batch-run &lt;batch_run_dir&gt; --json
          </pre>
        </Pane>

        <Pane
          title="Kill rules & portfolio carry-forward"
          dense
          onInspect={() => openInspector({ title: "Manifest drilldown", rawJson: manifest ?? {} })}
        >
          {!manifest ? (
            <p className="muted">No manifest.</p>
          ) : (
            <div style={{ fontSize: "11px" }}>
              <p style={{ margin: "0 0 0.5rem" }}>
                <strong>Enrollment notes</strong>
              </p>
              <JsonDetails
                summary="notes"
                data={{ enrollment_notes: manifest.enrollment_notes, portfolio_carry_forward: pcf }}
              />
              {score && Array.isArray(score.triggered_rules) && (score.triggered_rules as unknown[]).length > 0 ? (
                <p className="muted" style={{ marginTop: "0.5rem" }}>
                  Triggered falsifications present — inspect scorecard JSON.
                </p>
              ) : null}
            </div>
          )}
        </Pane>

        <Pane
          title="Signal & outcome history (recent)"
          dense
          onInspect={() =>
            openInspector({
              title: "Snapshots",
              rawJson: { signals, outcomes },
            })
          }
        >
          {!bundle ? (
            <p className="muted">No bundle.</p>
          ) : (
            <div style={{ fontSize: "11px", display: "grid", gap: "0.75rem" }}>
              <div>
                <strong>Signals</strong> ({Array.isArray(signals) ? signals.length : 0})
                {Array.isArray(signals) && signals.length > 0 ? (
                  <ul style={{ margin: "0.25rem 0 0", paddingLeft: "1.1rem" }}>
                    {signals.slice(-8).map((s, i) => {
                      const row = asRecord(s as object);
                      const sum = row?.summary != null ? asRecord(row.summary as object) : null;
                      return (
                        <li key={i}>
                          {asString(sum?.observation_date_utc) ?? "—"} exposure{" "}
                          {typeof sum?.signal_exposure === "number" ? sum.signal_exposure.toFixed(4) : "—"}{" "}
                          <code>{(asString(sum?.evidence_sha256) ?? "").slice(0, 8)}</code>
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <p className="muted" style={{ margin: "0.25rem 0 0" }}>
                    No snapshots yet.
                  </p>
                )}
              </div>
              <div>
                <strong>Outcomes</strong> ({Array.isArray(outcomes) ? outcomes.length : 0})
                {Array.isArray(outcomes) && outcomes.length > 0 ? (
                  <ul style={{ margin: "0.25rem 0 0", paddingLeft: "1.1rem" }}>
                    {outcomes.slice(-8).map((s, i) => {
                      const row = asRecord(s as object);
                      const sum = row?.summary != null ? asRecord(row.summary as object) : null;
                      return (
                        <li key={i}>
                          {asString(sum?.observation_date_utc) ?? "—"} 1d{" "}
                          {typeof sum?.paper_return_1d === "number" ? sum.paper_return_1d.toFixed(5) : "—"} cum_eq{" "}
                          {typeof sum?.cumulative_paper_equity_factor === "number"
                            ? sum.cumulative_paper_equity_factor.toFixed(5)
                            : "—"}
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <p className="muted" style={{ margin: "0.25rem 0 0" }}>
                    No outcomes yet.
                  </p>
                )}
              </div>
            </div>
          )}
        </Pane>
      </div>
    </main>
  );
}

"use client";

import { useMemo, useState } from "react";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { TermKV } from "@/components/terminal/TermKV";
import { useSubmitUiStrategyIntake } from "@/hooks/useUiStrategyIntake";
import { StrategistApiError } from "@/lib/api/strategist-errors";
import type { UiMutationSafetyStatus, UiStrategyIntakeReceipt, UiStrategyIntakeRequest } from "@/lib/api/types";
import {
  mutationRequiresBrowserToken,
  mutationSurfaceAllowed,
} from "@/lib/operator/operator-mutation-guard";

function buildIdempotencyKey(strategyName: string, operatorId: string): string {
  const suffix =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
  const safeName = strategyName.replace(/[^a-zA-Z0-9_.:-]+/g, "_").slice(0, 72) || "strategy";
  const safeOperator = operatorId.replace(/[^a-zA-Z0-9_.:@-]+/g, "_").slice(0, 48) || "operator";
  return `ui:strategy-intake:${safeOperator}:${safeName}:${suffix}`;
}

function formatMutationError(err: unknown): string {
  if (err instanceof StrategistApiError) {
    return `${err.message}${err.httpStatus != null ? ` · HTTP ${err.httpStatus}` : ""}`;
  }
  if (err instanceof Error) return err.message;
  return String(err);
}

export type StrategyLifecycleIntakeFormProps = {
  mutationSafety: UiMutationSafetyStatus | null;
};

export function StrategyLifecycleIntakeForm({ mutationSafety }: StrategyLifecycleIntakeFormProps) {
  const submit = useSubmitUiStrategyIntake();
  const [strategyName, setStrategyName] = useState("");
  const [operatorId, setOperatorId] = useState("");
  const [mutationToken, setMutationToken] = useState("");
  const [thesis, setThesis] = useState("");
  const [targetUniverse, setTargetUniverse] = useState("");
  const [intendedHorizon, setIntendedHorizon] = useState("");
  const [expectedEdge, setExpectedEdge] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [receipt, setReceipt] = useState<UiStrategyIntakeReceipt | null>(null);
  const [lastError, setLastError] = useState<string | null>(null);

  const surface = mutationSurfaceAllowed(mutationSafety);
  const tokenRequired = mutationRequiresBrowserToken(mutationSafety);
  const tokenOk = !tokenRequired || mutationToken.trim().length > 0;
  const operatorOk = operatorId.trim().length > 0;
  const fieldsOk = Boolean(
    strategyName.trim() &&
      thesis.trim() &&
      targetUniverse.trim() &&
      intendedHorizon.trim() &&
      expectedEdge.trim(),
  );

  const canSubmit = Boolean(surface.ok && operatorOk && tokenOk && fieldsOk && !submit.isPending);

  const disabledReasons = useMemo(() => {
    const r: string[] = [];
    if (!surface.ok) r.push(surface.reason);
    if (!operatorOk) r.push("OPERATOR_ID_REQUIRED");
    if (tokenRequired && !mutationToken.trim()) r.push("MUTATION_TOKEN_REQUIRED");
    if (!fieldsOk) r.push("INTAKE_FIELDS_INCOMPLETE");
    return r;
  }, [fieldsOk, mutationToken, operatorOk, surface.ok, surface.reason, tokenRequired]);

  async function submitIntake() {
    if (!canSubmit) return;
    const normalizedOperator = operatorId.trim();
    const idem = idempotencyKey.trim() || buildIdempotencyKey(strategyName, normalizedOperator);
    setIdempotencyKey(idem);
    setReceipt(null);
    setLastError(null);
    const request: UiStrategyIntakeRequest = {
      strategy_name: strategyName.trim(),
      thesis: thesis.trim(),
      target_universe: targetUniverse.trim(),
      intended_horizon: intendedHorizon.trim(),
      expected_edge: expectedEdge.trim(),
      required_evidence_class: "institutional",
      operator_id: normalizedOperator,
      idempotency_key: idem,
      evaluation_plan: {
        created_from: "strategist-web/strategy-lifecycle-cockpit",
        requested_checks: ["PIT", "provider_freshness", "execution_realism", "robustness"],
      },
    };
    try {
      const result = await submit.mutateAsync({
        request,
        mutationToken: tokenRequired ? mutationToken.trim() : undefined,
      });
      setReceipt(result);
      setMutationToken("");
    } catch (e) {
      setLastError(formatMutationError(e));
    }
  }

  return (
    <div className="cockpit-lifecycle-intake" data-testid="cockpit-strategy-lifecycle-intake">
      <div className="muted" style={{ fontSize: "10px", marginBottom: "8px" }}>
        Safe mutation: <code>POST /ui/strategy-intake</code> only. Token is held in memory for this submit only.
      </div>
      <TermKV
        rows={[
          { k: "mutation_posture", v: <StatusBadge raw={surface.ok ? "SURFACE_OK" : "SURFACE_BLOCKED"} /> },
          { k: "authorization_mode", v: mutationSafety?.authorization_mode ?? "UNKNOWN" },
          { k: "submit_enabled", v: <StatusBadge raw={canSubmit ? "true" : "false"} /> },
          ...disabledReasons.map((code, i) => ({ k: `blocked_${i}`, v: code })),
        ]}
      />
      <div
        style={{
          display: "grid",
          gap: "8px",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          marginTop: "8px",
        }}
      >
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">operator_id (required)</span>
          <input
            data-testid="lifecycle-intake-operator"
            value={operatorId}
            onChange={(e) => setOperatorId(e.target.value)}
            autoComplete="off"
          />
        </label>
        {tokenRequired ? (
          <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
            <span className="muted">mutation token</span>
            <input
              type="password"
              data-testid="lifecycle-intake-token"
              value={mutationToken}
              onChange={(e) => setMutationToken(e.target.value)}
              autoComplete="off"
            />
          </label>
        ) : null}
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">strategy_name</span>
          <input value={strategyName} onChange={(e) => setStrategyName(e.target.value)} autoComplete="off" />
        </label>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px", gridColumn: "1 / -1" }}>
          <span className="muted">thesis</span>
          <textarea value={thesis} onChange={(e) => setThesis(e.target.value)} rows={2} />
        </label>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">target_universe</span>
          <input value={targetUniverse} onChange={(e) => setTargetUniverse(e.target.value)} autoComplete="off" />
        </label>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">intended_horizon</span>
          <input value={intendedHorizon} onChange={(e) => setIntendedHorizon(e.target.value)} autoComplete="off" />
        </label>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px", gridColumn: "1 / -1" }}>
          <span className="muted">expected_edge</span>
          <textarea value={expectedEdge} onChange={(e) => setExpectedEdge(e.target.value)} rows={2} />
        </label>
      </div>
      <div style={{ marginTop: "8px", display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
        <button
          type="button"
          data-testid="lifecycle-intake-submit"
          disabled={!canSubmit}
          onClick={() => void submitIntake()}
        >
          Submit strategy intake
        </button>
        {submit.isPending ? <span className="muted">Submitting…</span> : null}
      </div>
      {lastError ? (
        <p className="muted" style={{ fontSize: "10px", color: "#f85149" }}>
          {lastError}
        </p>
      ) : null}
      {receipt ? (
        <TermKV
          rows={[
            { k: "receipt_accepted", v: String(receipt.accepted) },
            { k: "intake_id", v: receipt.intake_id },
            { k: "artifact_sha256", v: receipt.artifact_sha256?.slice(0, 18) ?? "—" },
          ]}
        />
      ) : null}
    </div>
  );
}

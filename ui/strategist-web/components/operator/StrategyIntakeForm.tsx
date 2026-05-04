"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useSubmitUiStrategyIntake } from "@/hooks/useUiStrategyIntake";
import { StrategistApiError } from "@/lib/api/strategist-errors";
import type { UiStrategyIntakeReceipt, UiStrategyIntakeRequest } from "@/lib/api/types";

function splitLines(value: string): string[] {
  return value
    .split(/\r?\n|,/g)
    .map((item) => item.trim())
    .filter(Boolean);
}

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

export function StrategyIntakeForm() {
  const submit = useSubmitUiStrategyIntake();
  const [strategyName, setStrategyName] = useState("Opening Range Breakout");
  const [operatorId, setOperatorId] = useState("operator");
  const [mutationToken, setMutationToken] = useState("");
  const [thesis, setThesis] = useState("Trade post-open expansion only after provider freshness and PIT-safety are verified.");
  const [targetUniverse, setTargetUniverse] = useState("DAX futures");
  const [intendedHorizon, setIntendedHorizon] = useState("intraday");
  const [expectedEdge, setExpectedEdge] = useState("Volatility expansion after compressed opening range.");
  const [requiredEvidenceClass, setRequiredEvidenceClass] = useState("institutional");
  const [dataDependencies, setDataDependencies] = useState("minute_bars\ncalendar");
  const [featureDependencies, setFeatureDependencies] = useState("");
  const [sourceRefs, setSourceRefs] = useState("");
  const [falsificationRules, setFalsificationRules] = useState("kill if slippage doubles expected edge");
  const [riskAssumptions, setRiskAssumptions] = useState("single position per symbol");
  const [tags, setTags] = useState("paper-first\nfamily:breakout");
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [receipt, setReceipt] = useState<UiStrategyIntakeReceipt | null>(null);

  const canSubmit = Boolean(strategyName.trim() && thesis.trim() && targetUniverse.trim() && intendedHorizon.trim() && expectedEdge.trim() && !submit.isPending);

  const preview = useMemo(
    () => ({
      strategy_name: strategyName.trim(),
      thesis: thesis.trim(),
      target_universe: targetUniverse.trim(),
      intended_horizon: intendedHorizon.trim(),
      expected_edge: expectedEdge.trim(),
      required_evidence_class: requiredEvidenceClass.trim() || "institutional",
      data_dependencies: splitLines(dataDependencies),
      feature_dependencies: splitLines(featureDependencies),
      source_registry_references: splitLines(sourceRefs),
      falsification_rules: splitLines(falsificationRules),
      risk_assumptions: splitLines(riskAssumptions),
      tags: splitLines(tags),
      operator_id: operatorId.trim() || "operator",
    }),
    [
      dataDependencies,
      expectedEdge,
      falsificationRules,
      featureDependencies,
      intendedHorizon,
      operatorId,
      requiredEvidenceClass,
      riskAssumptions,
      sourceRefs,
      strategyName,
      tags,
      targetUniverse,
      thesis,
    ],
  );

  async function submitIntake() {
    if (!canSubmit) return;
    const normalizedOperator = operatorId.trim() || "operator";
    const idem = idempotencyKey.trim() || buildIdempotencyKey(strategyName, normalizedOperator);
    setIdempotencyKey(idem);
    setReceipt(null);
    const request: UiStrategyIntakeRequest = {
      ...preview,
      operator_id: normalizedOperator,
      idempotency_key: idem,
      evaluation_plan: {
        created_from: "strategist-web/strategy-inbox",
        requested_checks: ["PIT", "provider_freshness", "execution_realism", "robustness"],
      },
    };
    const result = await submit.mutateAsync({ request, mutationToken });
    setReceipt(result);
  }

  return (
    <Pane title="Strategy intake form" badge={<StatusBadge raw={canSubmit ? "READY" : "INCOMPLETE"} />} dense>
      <p className="muted" style={{ fontSize: "10px", margin: "0 0 8px" }}>
        Mutation-plane: <code>POST /ui/strategy-intake</code>. This records an advisory proposal artifact only; it does not
        adjudicate, promote, place orders, or mutate the validator ledger.
      </p>

      <div style={{ display: "grid", gap: "8px", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">strategy name</span>
          <input value={strategyName} onChange={(event) => setStrategyName(event.target.value)} />
        </label>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">target universe</span>
          <input value={targetUniverse} onChange={(event) => setTargetUniverse(event.target.value)} />
        </label>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">horizon</span>
          <input value={intendedHorizon} onChange={(event) => setIntendedHorizon(event.target.value)} />
        </label>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">evidence class</span>
          <input value={requiredEvidenceClass} onChange={(event) => setRequiredEvidenceClass(event.target.value)} />
        </label>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">operator</span>
          <input value={operatorId} onChange={(event) => setOperatorId(event.target.value)} />
        </label>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">mutation token</span>
          <input
            value={mutationToken}
            onChange={(event) => setMutationToken(event.target.value)}
            placeholder="optional in local non-production"
            type="password"
            autoComplete="off"
          />
        </label>
      </div>

      <label style={{ display: "grid", gap: "2px", fontSize: "10px", marginTop: "8px" }}>
        <span className="muted">thesis</span>
        <textarea rows={3} value={thesis} onChange={(event) => setThesis(event.target.value)} />
      </label>
      <label style={{ display: "grid", gap: "2px", fontSize: "10px", marginTop: "8px" }}>
        <span className="muted">expected edge</span>
        <textarea rows={2} value={expectedEdge} onChange={(event) => setExpectedEdge(event.target.value)} />
      </label>

      <div style={{ display: "grid", gap: "8px", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", marginTop: "8px" }}>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">data dependencies</span>
          <textarea rows={3} value={dataDependencies} onChange={(event) => setDataDependencies(event.target.value)} />
        </label>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">feature dependencies</span>
          <textarea rows={3} value={featureDependencies} onChange={(event) => setFeatureDependencies(event.target.value)} />
        </label>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">source registry refs</span>
          <textarea rows={3} value={sourceRefs} onChange={(event) => setSourceRefs(event.target.value)} />
        </label>
      </div>

      <div style={{ display: "grid", gap: "8px", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", marginTop: "8px" }}>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">falsification rules</span>
          <textarea rows={3} value={falsificationRules} onChange={(event) => setFalsificationRules(event.target.value)} />
        </label>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">risk assumptions</span>
          <textarea rows={3} value={riskAssumptions} onChange={(event) => setRiskAssumptions(event.target.value)} />
        </label>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">tags</span>
          <textarea rows={3} value={tags} onChange={(event) => setTags(event.target.value)} />
        </label>
      </div>

      <label style={{ display: "grid", gap: "2px", fontSize: "10px", marginTop: "8px" }}>
        <span className="muted">idempotency key</span>
        <input value={idempotencyKey} onChange={(event) => setIdempotencyKey(event.target.value)} placeholder="auto-generated if empty" />
      </label>

      {submit.isError && (
        <p className="term-page__banner" style={{ color: "#f85149", fontSize: "11px" }}>
          Intake rejected: {formatMutationError(submit.error)}
        </p>
      )}

      <button type="button" className="linkish" disabled={!canSubmit} onClick={() => void submitIntake()}>
        {submit.isPending ? "Recording…" : "Record advisory intake"}
      </button>

      <div style={{ marginTop: "8px" }}>
        <TermKV
          rows={[
            { k: "boundary", v: "ADVISORY_ARTIFACT_ONLY" },
            { k: "promotion", v: "NONE" },
            { k: "execution", v: "NONE" },
          ]}
        />
      </div>

      {receipt && (
        <div style={{ marginTop: "8px" }}>
          <TermKV
            rows={[
              { k: "accepted", v: <StatusBadge raw={receipt.accepted ? "true" : "false"} /> },
              { k: "intake_id", v: receipt.intake_id },
              { k: "proposal_id", v: receipt.proposal_id },
              { k: "sha256", v: <code>{receipt.artifact_sha256.slice(0, 24)}</code> },
              { k: "idempotency", v: receipt.idempotency_status },
            ]}
          />
          <JsonDetails summary="Strategy intake receipt JSON" data={receipt} />
        </div>
      )}

      <JsonDetails summary="Request preview JSON" data={preview} />
    </Pane>
  );
}

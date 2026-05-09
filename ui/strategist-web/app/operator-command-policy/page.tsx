"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiOperatorCommandPolicy, type UiOperatorCommandPolicyQuery } from "@/hooks/useUiOperatorCommandPolicy";
import type { UiOperatorCommandPolicyRecord } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo, useState } from "react";

type ActionMode = "all" | "claim-item" | "acknowledge-reentry" | "renew-lease" | "unknown-command";
type TokenDelivery = "authorization" | "x_strategy_validator_token";
type PolicyRow = UiOperatorCommandPolicyRecord & { __id: string };

const ACTIONS: ActionMode[] = ["all", "claim-item", "acknowledge-reentry", "renew-lease", "unknown-command"];
const TOKEN_DELIVERIES: { value: TokenDelivery; label: string }[] = [
  { value: "authorization", label: "Authorization bearer" },
  { value: "x_strategy_validator_token", label: "X token header" },
];

function join(values: string[] | undefined): string {
  if (!values || values.length === 0) return "—";
  return values.join(", ");
}

function splitScopes(value: string): string[] {
  return value
    .split(/[\s,]+/)
    .map((scope) => scope.trim())
    .filter(Boolean);
}

export default function OperatorCommandPolicyPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const [actionMode, setActionMode] = useState<ActionMode>("all");
  const [operatorId, setOperatorId] = useState("operator");
  const [workItemKey, setWorkItemKey] = useState("DEMO-WORK-ITEM");
  const [reviewTarget, setReviewTarget] = useState("");
  const [manifestPath, setManifestPath] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [assumeTokenPresent, setAssumeTokenPresent] = useState(false);
  const [tokenDelivery, setTokenDelivery] = useState<TokenDelivery>("authorization");
  const [scopeText, setScopeText] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiOperatorCommandPolicyQuery = useMemo(
    () => ({
      action: actionMode === "all" ? null : actionMode,
      operatorId,
      workItemKey,
      reviewTarget,
      manifestPath,
      idempotencyKey,
      assumeTokenPresent,
      tokenDelivery,
      scopes: splitScopes(scopeText),
    }),
    [actionMode, assumeTokenPresent, idempotencyKey, manifestPath, operatorId, reviewTarget, scopeText, tokenDelivery, workItemKey],
  );

  const projection = useUiOperatorCommandPolicy(query);
  const rows = useMemo<PolicyRow[]>(() => {
    const policies = Array.isArray(projection.data?.policies) ? projection.data.policies : [];
    return policies.map((policy, index) => ({ ...policy, __id: `${policy.action}:${index}` }));
  }, [projection.data?.policies]);
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const guidance = asStringArray(projection.data?.operator_guidance);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "operator-command-policy-state",
        severity: projection.data?.overall_lifecycle_state === "ALLOWED" ? "ok" : "warn",
        text: `command_policy actions=${projection.data?.action_count ?? 0} allowed=${projection.data?.allowed_count ?? 0} blocked=${projection.data?.blocked_count ?? 0} target=${String(projection.data?.target_identity_present ?? false)}`,
      },
      {
        id: "operator-command-policy-guardrail",
        severity: "info",
        text: "read-plane preview only · token values are never accepted or echoed here; actual mutations stay behind POST /ui/commands/{action}",
      },
    ],
    [projection.data],
  );
  const ticker = useMemo(
    () => [
      { severity: projection.data?.overall_lifecycle_state === "ALLOWED" ? ("ok" as const) : ("warn" as const), text: `CMD ${projection.data?.overall_lifecycle_state ?? "LOAD"}` },
      { severity: projection.data?.no_token_value_echoed ? ("ok" as const) : ("warn" as const), text: "NO TOKEN ECHO" },
    ],
    [projection.data],
  );
  useTerminalPageBind(tape, ticker);

  const cols: DenseColumn<PolicyRow>[] = useMemo(
    () => [
      { key: "action", header: "action", width: "18%", cell: (row) => <code>{row.action}</code> },
      { key: "state", header: "state", width: "12%", cell: (row) => <StatusBadge raw={row.lifecycle_state} /> },
      { key: "supported", header: "supported", width: "10%", cell: (row) => String(row.is_supported_action) },
      { key: "allowed", header: "allowed", width: "10%", cell: (row) => String(row.is_allowed) },
      { key: "target", header: "target fields", width: "18%", cell: (row) => <code>{join(row.target_fields_present)}</code> },
      { key: "reasons", header: "blocking reasons", cell: (row) => join(row.blocking_reasons) },
    ],
    [],
  );

  if (!config.ok) {
    return (
      <div className="term-page">
        <h1 className="term-page__title">OPERATOR · COMMAND POLICY</h1>
        <p className="muted">{config.error.message}</p>
      </div>
    );
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">OPERATOR · COMMAND POLICY</h1>
      <p className="muted" style={{ fontSize: "10px" }}>
        GET /ui/commands/policy · read-only mutation policy preview · no token values accepted, stored, or echoed
      </p>

      {projection.isLoading && <p className="muted">Loading…</p>}
      {projection.isError && (
        <p className="term-page__banner" style={{ color: "#f85149" }}>
          {projection.error instanceof Error ? projection.error.message : String(projection.error)}
        </p>
      )}

      {projection.data && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Policy summary" onInspect={() => openInspector({ title: "Operator command policy", rawJson: projection.data })}>
              <TermKV rows={[{ k: "schema", v: projection.data.schema_version }, { k: "state", v: projection.data.overall_lifecycle_state }, { k: "allowed", v: String(projection.data.allowed_count) }, { k: "blocked", v: String(projection.data.blocked_count) }, { k: "unsupported", v: String(projection.data.unsupported_count) }]} />
            </Pane>
            <Pane title="Auth posture">
              <TermKV rows={[{ k: "runtime", v: projection.data.auth_context.runtime_mode }, { k: "auth_mode", v: projection.data.auth_context.authorization_mode }, { k: "token_configured", v: String(projection.data.auth_context.token_configured) }, { k: "token_source", v: projection.data.auth_context.token_source }, { k: "scopes", v: join(projection.data.auth_context.scopes) }]} />
            </Pane>
            <Pane title="Selected policy" onInspect={selectedRow ? () => openInspector({ title: `Policy · ${selectedRow.action}`, rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "action", v: selectedRow?.action ?? "—" }, { k: "state", v: selectedRow?.lifecycle_state ?? "—" }, { k: "allowed", v: String(selectedRow?.is_allowed ?? false) }, { k: "required_scope", v: selectedRow?.required_scope ?? projection.data.required_scope }, { k: "reasons", v: join(selectedRow?.blocking_reasons) }]} />
            </Pane>
          </PaneGrid>

          <Pane title="Preview controls" dense>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
              <label className="muted" style={{ fontSize: "10px" }}>operator&nbsp;<input className="term-input" value={operatorId} onChange={(event) => setOperatorId(event.target.value)} placeholder="operator_id" style={{ width: "150px" }} /></label>
              <label className="muted" style={{ fontSize: "10px" }}>work item&nbsp;<input className="term-input" value={workItemKey} onChange={(event) => setWorkItemKey(event.target.value)} placeholder="work_item_key" style={{ width: "170px" }} /></label>
              <label className="muted" style={{ fontSize: "10px" }}>review target&nbsp;<input className="term-input" value={reviewTarget} onChange={(event) => setReviewTarget(event.target.value)} placeholder="candidate/run id" style={{ width: "170px" }} /></label>
              <label className="muted" style={{ fontSize: "10px" }}>manifest path&nbsp;<input className="term-input" value={manifestPath} onChange={(event) => setManifestPath(event.target.value)} placeholder="artifact manifest" style={{ width: "180px" }} /></label>
              <label className="muted" style={{ fontSize: "10px" }}>idempotency&nbsp;<input className="term-input" value={idempotencyKey} onChange={(event) => setIdempotencyKey(event.target.value)} placeholder="optional" style={{ width: "140px" }} /></label>
            </div>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center", marginTop: "8px" }}>
              <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                {ACTIONS.map((action) => (
                  <button key={action} type="button" className={`term-btn term-btn--sm${actionMode === action ? " is-active" : ""}`} onClick={() => setActionMode(action)}>{action.toUpperCase()}</button>
                ))}
              </div>
              <label className="muted" style={{ fontSize: "10px", display: "inline-flex", alignItems: "center", gap: "4px" }}><input type="checkbox" checked={assumeTokenPresent} onChange={(event) => setAssumeTokenPresent(event.target.checked)} />assume token present</label>
              <select className="term-input" value={tokenDelivery} onChange={(event) => setTokenDelivery(event.target.value as TokenDelivery)} style={{ width: "190px" }}>
                {TOKEN_DELIVERIES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
              </select>
              <label className="muted" style={{ fontSize: "10px" }}>scope override&nbsp;<input className="term-input" value={scopeText} onChange={(event) => setScopeText(event.target.value)} placeholder="operator:command:write operator:projection:read" style={{ width: "320px" }} /></label>
            </div>
          </Pane>

          <Pane title="Policy matrix" dense onInspect={() => openInspector({ title: "Command policy rows", rawJson: rows })}>
            <DenseTable columns={cols} rows={rows} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => { setSelected(row.__id); openInspector({ title: `Command policy · ${row.action}`, rawJson: row }); }} empty="No policy rows returned." />
          </Pane>

          <PaneGrid cols={3}>
            <Pane title="Target identity"><TermKV rows={[{ k: "target_present", v: String(projection.data.target_identity_present) }, { k: "target_fields", v: join(projection.data.target_fields_present) }, { k: "mutation_route", v: projection.data.mutation_route }, { k: "journal_family", v: projection.data.journal_family }, { k: "no_token_echo", v: String(projection.data.no_token_value_echoed) }]} /></Pane>
            <Pane title="Supported actions"><TermKV rows={projection.data.supported_actions.map((action) => ({ k: action, v: "supported" }))} /></Pane>
            <Pane title="Operator guidance"><div className="term-tape" style={{ maxHeight: "140px" }}>{guidance.map((line) => <div key={line} className="term-tape__line"><span className="sev sev--info">INFO</span><span className="term-tape__text">{line}</span></div>)}</div></Pane>
          </PaneGrid>
        </>
      )}

      {projection.data && <JsonDetails summary="Drilldown: full /ui/commands/policy JSON" data={projection.data} />}
    </div>
  );
}

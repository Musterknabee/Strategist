"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { digest } from "@/components/cockpit/cockpit-utils";
import { useUiOperatorCommandMutation } from "@/hooks/useUiOperatorCommand";
import type { StrategistMutationTokenDelivery } from "@/lib/api/strategist-client";
import { StrategistApiError } from "@/lib/api/strategist-errors";
import type {
  UiMutationSafetyStatus,
  UiOperatorCommandAction,
  UiOperatorCommandReceipt,
  UiWorkboardQueueEntry,
} from "@/lib/api/types";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import {
  mutationRequiresBrowserToken,
  mutationSurfaceAllowed,
} from "@/lib/operator/operator-mutation-guard";

const ACTIONS: UiOperatorCommandAction[] = ["claim-item", "acknowledge-reentry", "renew-lease"];

export type OperatorCommandPanelProps = {
  target: UiWorkboardQueueEntry | null;
  boardLabel?: string;
  /** Pane title override (cockpit vs workboard). */
  title?: string;
  /** From GET /ui/runtime `mutation_safety`; when absent, commands stay disabled (fail-closed). */
  mutationSafety?: UiMutationSafetyStatus | null;
  /** From GET /ui/facade `mutation_route` (display only). */
  mutationRoute?: string | null;
  readPlaneOnly?: boolean | null;
  runtimeEnvironment?: string | null;
  onInspectPosture?: (payload: InspectorPayload) => void;
  onInspectReceipt?: (payload: InspectorPayload) => void;
};

function primitiveString(value: unknown): string | null {
  if (value === undefined || value === null) return null;
  if (typeof value === "string") return value.trim() || null;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return null;
}

function getTargetField(target: UiWorkboardQueueEntry | null, key: string): string | null {
  if (!target) return null;
  return primitiveString(target[key]);
}

function buildIdempotencyKey(action: UiOperatorCommandAction, operatorId: string, targetIdentity: string): string {
  const suffix =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
  const safeTarget = targetIdentity.replace(/[^a-zA-Z0-9_.:-]+/g, "_").slice(0, 80) || "target";
  const safeOperator = operatorId.replace(/[^a-zA-Z0-9_.:@-]+/g, "_").slice(0, 48) || "operator";
  return `ui:${action}:${safeOperator}:${safeTarget}:${suffix}`;
}

function formatCommandError(err: unknown): string {
  if (err instanceof StrategistApiError) {
    const detail = err.detail?.trim() ? ` · ${err.detail.trim().slice(0, 240)}` : "";
    return `${err.message}${err.httpStatus != null ? ` · HTTP ${err.httpStatus}` : ""}${detail}`;
  }
  if (err instanceof Error) return err.message;
  return String(err);
}

export function OperatorCommandPanel({
  target,
  boardLabel = "operator",
  title = "Operator command center",
  mutationSafety = null,
  mutationRoute = null,
  readPlaneOnly = null,
  runtimeEnvironment = null,
  onInspectPosture,
  onInspectReceipt,
}: OperatorCommandPanelProps) {
  const [action, setAction] = useState<UiOperatorCommandAction>("claim-item");
  const [operatorId, setOperatorId] = useState("");
  const [mutationToken, setMutationToken] = useState("");
  const [useHeaderToken, setUseHeaderToken] = useState(false);
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [receipt, setReceipt] = useState<UiOperatorCommandReceipt | null>(null);
  const command = useUiOperatorCommandMutation(boardLabel);

  const surface = mutationSurfaceAllowed(mutationSafety);
  const tokenRequired = mutationRequiresBrowserToken(mutationSafety);
  const tokenOk = !tokenRequired || mutationToken.trim().length > 0;

  const workItemKey = getTargetField(target, "work_item_key");
  const reviewTarget = getTargetField(target, "review_target");
  const packKind = getTargetField(target, "pack_kind");
  const manifestPath = getTargetField(target, "manifest_path");
  const targetIdentity = workItemKey ?? reviewTarget ?? manifestPath ?? "";

  const operatorOk = operatorId.trim().length > 0;
  const canSubmit = Boolean(
    surface.ok && targetIdentity && operatorOk && tokenOk && !command.isPending,
  );

  const badgeRaw = !surface.ok ? "BLOCKED" : !operatorOk ? "NO_OPERATOR" : !targetIdentity ? "NO_TARGET" : !tokenOk ? "TOKEN_REQUIRED" : "READY";

  const postureRows = useMemo(() => {
    const rows = [
      { k: "mutation_route", v: mutationRoute ?? "—" },
      { k: "read_plane_only", v: readPlaneOnly === null ? "UNKNOWN" : String(readPlaneOnly) },
      { k: "runtime", v: runtimeEnvironment ?? "UNKNOWN" },
      {
        k: "mutation_routes_safe",
        v: mutationSafety ? <StatusBadge raw={mutationSafety.mutation_routes_safe ? "true" : "false"} /> : "UNKNOWN",
      },
      { k: "authorization_mode", v: mutationSafety?.authorization_mode ?? "UNKNOWN" },
      { k: "detail_code", v: mutationSafety?.detail_code ?? "MUTATION_SAFETY_UNKNOWN" },
    ];
    return rows;
  }, [mutationRoute, mutationSafety, readPlaneOnly, runtimeEnvironment]);

  const targetRows = useMemo(
    () => [
      { k: "work_item_key", v: workItemKey ?? "—" },
      { k: "review_target", v: reviewTarget ?? "—" },
      { k: "pack_kind", v: packKind ?? "—" },
      { k: "manifest_path", v: manifestPath ?? "—" },
    ],
    [manifestPath, packKind, reviewTarget, workItemKey],
  );

  const disabledReasons = useMemo(() => {
    const r: string[] = [];
    if (!surface.ok) r.push(surface.reason);
    if (!operatorOk) r.push("OPERATOR_ID_REQUIRED");
    if (!targetIdentity) r.push("WORK_ITEM_TARGET_REQUIRED");
    if (tokenRequired && !mutationToken.trim()) r.push("MUTATION_TOKEN_REQUIRED");
    return r;
  }, [mutationToken, operatorOk, surface.ok, surface.reason, targetIdentity, tokenRequired]);

  async function submitCommand() {
    if (!canSubmit) return;
    const normalizedOperator = operatorId.trim();
    const idem = idempotencyKey.trim() || buildIdempotencyKey(action, normalizedOperator, targetIdentity);
    setIdempotencyKey(idem);
    setReceipt(null);
    const tokenDelivery: StrategistMutationTokenDelivery = useHeaderToken
      ? "x_strategy_validator_token"
      : "authorization_bearer";
    const result = await command.mutateAsync({
      action,
      mutationToken: mutationToken.trim() || undefined,
      tokenDelivery,
      request: {
        operator_id: normalizedOperator,
        work_item_key: workItemKey,
        review_target: reviewTarget,
        pack_kind: packKind,
        manifest_path: manifestPath,
        idempotency_key: idem,
      },
    });
    setReceipt(result);
    setMutationToken("");
  }

  const inspectPosture = () => {
    if (!onInspectPosture) return;
    onInspectPosture({
      title: "Mutation / auth posture",
      subtitle: "Read-plane runtime fields (no secrets)",
      body: null,
      rawJson: {
        mutation_safety: mutationSafety,
        mutation_route: mutationRoute,
        read_plane_only: readPlaneOnly,
        environment: runtimeEnvironment,
      },
    });
  };

  const inspectReceipt = () => {
    if (!receipt || !onInspectReceipt) return;
    onInspectReceipt({
      title: "Command receipt",
      subtitle: receipt.command_id ?? "receipt",
      body: null,
      rawJson: receipt,
      digestToCopy: typeof receipt.event_hash === "string" ? receipt.event_hash : undefined,
    });
  };

  return (
    <Pane
      title={title}
      badge={<StatusBadge raw={badgeRaw} />}
      dense
      onInspect={onInspectPosture ? inspectPosture : undefined}
    >
      <p className="muted" style={{ fontSize: "10px", margin: "0 0 6px" }}>
        Mutation plane only: <code>POST /ui/commands/{"{action}"}</code>. Token exists in component state until submit; never
        persisted to localStorage.
      </p>

      <div style={{ marginBottom: "6px" }}>
        <TermKV rows={postureRows} />
      </div>

      {!surface.ok && (
        <p className="term-page__banner" style={{ fontSize: "11px" }} role="status">
          Commands disabled: {surface.reason}. Fix server mutation auth posture before journaling from the browser.
        </p>
      )}

      <div style={{ display: "grid", gap: "6px", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">action</span>
          <select
            value={action}
            disabled={!surface.ok}
            onChange={(event) => setAction(event.target.value as UiOperatorCommandAction)}
          >
            {ACTIONS.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </label>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">operator id (required)</span>
          <input
            value={operatorId}
            disabled={!surface.ok}
            onChange={(event) => setOperatorId(event.target.value)}
            placeholder="e.g. operator-jane"
            autoComplete="off"
            data-testid="operator-command-operator-id"
          />
        </label>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">mutation token {tokenRequired ? "(required)" : "(optional)"}</span>
          <input
            value={mutationToken}
            disabled={!surface.ok}
            onChange={(event) => setMutationToken(event.target.value)}
            placeholder={tokenRequired ? "paste API token for this session" : "optional for non-production bypass"}
            type="password"
            autoComplete="off"
            data-testid="operator-command-mutation-token"
          />
        </label>
      </div>

      <label style={{ display: "flex", gap: "6px", alignItems: "center", fontSize: "10px", marginTop: "4px" }}>
        <input
          type="checkbox"
          checked={useHeaderToken}
          disabled={!surface.ok}
          onChange={(e) => setUseHeaderToken(e.target.checked)}
        />
        <span className="muted">Send token as X-Strategy-Validator-Token (instead of Bearer)</span>
      </label>

      <label style={{ display: "grid", gap: "2px", fontSize: "10px", marginTop: "6px" }}>
        <span className="muted">idempotency key</span>
        <input
          value={idempotencyKey}
          disabled={!surface.ok}
          onChange={(event) => setIdempotencyKey(event.target.value)}
          placeholder="auto-generated if empty"
        />
      </label>

      <div style={{ marginTop: "6px" }}>
        <TermKV rows={targetRows} />
      </div>

      {disabledReasons.length > 0 && surface.ok && (
        <p className="muted" style={{ fontSize: "10px" }} data-testid="operator-command-disabled-reasons">
          {disabledReasons.join(" · ")}
        </p>
      )}

      {!targetIdentity && surface.ok && (
        <p className="muted" style={{ fontSize: "10px" }}>
          Select a queue row with <code>work_item_key</code>, <code>review_target</code>, or <code>manifest_path</code> before
          issuing a command.
        </p>
      )}

      {command.isError && (
        <p className="term-page__banner" style={{ color: "#f85149", fontSize: "11px" }} role="alert">
          Command rejected: {formatCommandError(command.error)}
        </p>
      )}

      <button
        type="button"
        className="linkish"
        disabled={!canSubmit}
        data-testid="operator-command-submit"
        onClick={() => void submitCommand()}
      >
        {command.isPending ? "Journaling…" : `Journal ${action}`}
      </button>

      {receipt && (
        <div style={{ marginTop: "8px" }}>
          <TermKV
            rows={[
              { k: "accepted", v: <StatusBadge raw={receipt.accepted ? "true" : "false"} /> },
              { k: "status", v: receipt.status ?? "—" },
              { k: "command_id", v: receipt.command_id ?? "—" },
              { k: "event_hash", v: receipt.event_hash ? digest(receipt.event_hash) : "—" },
              { k: "idempotency", v: receipt.idempotency_status ?? "—" },
              {
                k: "projection_refresh",
                v: receipt.requires_projection_refresh === true ? "REQUIRED" : receipt.requires_projection_refresh === false ? "NO" : "—",
              },
            ]}
          />
          {onInspectReceipt && (
            <button type="button" className="linkish" style={{ marginTop: "4px" }} onClick={inspectReceipt}>
              Inspect receipt (JSON)
            </button>
          )}
          <JsonDetails summary="Command receipt JSON" data={receipt} />
        </div>
      )}
    </Pane>
  );
}

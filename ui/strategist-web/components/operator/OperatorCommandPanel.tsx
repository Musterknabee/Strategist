"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useUiOperatorCommand } from "@/hooks/useUiOperatorCommand";
import { StrategistApiError } from "@/lib/api/strategist-errors";
import type {
  UiOperatorCommandAction,
  UiOperatorCommandReceipt,
  UiWorkboardQueueEntry,
} from "@/lib/api/types";

const ACTIONS: UiOperatorCommandAction[] = ["claim-item", "acknowledge-reentry", "renew-lease"];

type OperatorCommandPanelProps = {
  target: UiWorkboardQueueEntry | null;
  boardLabel?: string;
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
    return `${err.message}${err.status ? ` · HTTP ${err.status}` : ""}`;
  }
  if (err instanceof Error) return err.message;
  return String(err);
}

export function OperatorCommandPanel({ target, boardLabel = "operator" }: OperatorCommandPanelProps) {
  const [action, setAction] = useState<UiOperatorCommandAction>("claim-item");
  const [operatorId, setOperatorId] = useState("operator");
  const [mutationToken, setMutationToken] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [receipt, setReceipt] = useState<UiOperatorCommandReceipt | null>(null);
  const command = useUiOperatorCommand(boardLabel);

  const workItemKey = getTargetField(target, "work_item_key");
  const reviewTarget = getTargetField(target, "review_target");
  const packKind = getTargetField(target, "pack_kind");
  const manifestPath = getTargetField(target, "manifest_path");
  const targetIdentity = workItemKey ?? reviewTarget ?? manifestPath ?? "";
  const canSubmit = Boolean(targetIdentity && operatorId.trim() && !command.isPending);

  const targetRows = useMemo(
    () => [
      { k: "work_item_key", v: workItemKey ?? "—" },
      { k: "review_target", v: reviewTarget ?? "—" },
      { k: "pack_kind", v: packKind ?? "—" },
      { k: "manifest_path", v: manifestPath ?? "—" },
    ],
    [manifestPath, packKind, reviewTarget, workItemKey],
  );

  async function submitCommand() {
    if (!canSubmit) return;
    const normalizedOperator = operatorId.trim() || "operator";
    const idem = idempotencyKey.trim() || buildIdempotencyKey(action, normalizedOperator, targetIdentity);
    setIdempotencyKey(idem);
    setReceipt(null);
    const result = await command.mutateAsync({
      action,
      mutationToken,
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
  }

  return (
    <Pane title="Operator command center" badge={<StatusBadge raw={canSubmit ? "READY" : "NO_TARGET"} />} dense>
      <p className="muted" style={{ fontSize: "10px", margin: "0 0 6px" }}>
        Mutation-plane: <code>POST /ui/commands/{"{action}"}</code>. Token is supplied only from this runtime form;
        production still fails closed without backend mutation auth.
      </p>

      <div style={{ display: "grid", gap: "6px", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">action</span>
          <select value={action} onChange={(event) => setAction(event.target.value as UiOperatorCommandAction)}>
            {ACTIONS.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </label>
        <label style={{ display: "grid", gap: "2px", fontSize: "10px" }}>
          <span className="muted">operator</span>
          <input value={operatorId} onChange={(event) => setOperatorId(event.target.value)} placeholder="operator" />
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

      <label style={{ display: "grid", gap: "2px", fontSize: "10px", marginTop: "6px" }}>
        <span className="muted">idempotency key</span>
        <input
          value={idempotencyKey}
          onChange={(event) => setIdempotencyKey(event.target.value)}
          placeholder="auto-generated if empty"
        />
      </label>

      <div style={{ marginTop: "6px" }}>
        <TermKV rows={targetRows} />
      </div>

      {!targetIdentity && (
        <p className="muted" style={{ fontSize: "10px" }}>
          Select a queue row with <code>work_item_key</code>, <code>review_target</code>, or <code>manifest_path</code> before issuing a command.
        </p>
      )}

      {command.isError && (
        <p className="term-page__banner" style={{ color: "#f85149", fontSize: "11px" }}>
          Command rejected: {formatCommandError(command.error)}
        </p>
      )}

      <button type="button" className="linkish" disabled={!canSubmit} onClick={() => void submitCommand()}>
        {command.isPending ? "Journaling…" : `Journal ${action}`}
      </button>

      {receipt && (
        <div style={{ marginTop: "8px" }}>
          <TermKV
            rows={[
              { k: "accepted", v: <StatusBadge raw={receipt.accepted ? "true" : "false"} /> },
              { k: "status", v: receipt.status ?? "—" },
              { k: "command_id", v: receipt.command_id ?? "—" },
              { k: "event_hash", v: receipt.event_hash ?? "—" },
              { k: "idempotency", v: receipt.idempotency_status ?? "—" },
            ]}
          />
          <JsonDetails summary="Command receipt JSON" data={receipt} />
        </div>
      )}
    </Pane>
  );
}

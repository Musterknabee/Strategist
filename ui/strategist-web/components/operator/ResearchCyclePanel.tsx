"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import {
  useTriggerUiResearchCycle,
  useUiResearchCycleStatusLatest,
  type UiResearchCycleTriggerReceipt,
} from "@/hooks/useUiResearchCycle";
import { StrategistApiError } from "@/lib/api/strategist-errors";
import { asRecord, asString } from "@/lib/operator/payload-utils";

function formatMutationError(err: unknown): string {
  if (err instanceof StrategistApiError) {
    return `${err.message}${err.httpStatus != null ? ` · HTTP ${err.httpStatus}` : ""}`;
  }
  if (err instanceof Error) return err.message;
  return String(err);
}

export function ResearchCyclePanel() {
  const statusQ = useUiResearchCycleStatusLatest();
  const trigger = useTriggerUiResearchCycle();
  const [operatorId, setOperatorId] = useState("operator");
  const [mutationToken, setMutationToken] = useState("");
  const [mode, setMode] = useState<"light" | "heavy">("light");
  const [receipt, setReceipt] = useState<UiResearchCycleTriggerReceipt | null>(null);

  const root = statusQ.data ? asRecord(statusQ.data) : null;
  const scheduler = root?.scheduler ? asRecord(root.scheduler) : null;
  const lastCycle = root?.last_cycle ? asRecord(root.last_cycle) : null;
  const degraded = root ? (Array.isArray(root.degraded) ? (root.degraded as string[]) : []) : [];

  const daemonOk = scheduler?.daemon_pid != null;
  const lastOk = lastCycle?.ok === true;

  const statusLine = useMemo(() => {
    if (!scheduler) return "Scheduler state unknown";
    const iter = asString(scheduler.iteration) ?? "0";
    const last = asString(scheduler.last_cycle_finished_at_utc) ?? "never";
    return `iteration=${iter} · last finished ${last}`;
  }, [scheduler]);

  async function queueCycle() {
    setReceipt(null);
    try {
      const data = await trigger.mutateAsync({
        request: { operator_id: operatorId.trim() || "operator", mode },
        mutationToken: mutationToken.trim() || null,
      });
      setReceipt(data);
    } catch (err) {
      setReceipt({ accepted: false, operator_message: formatMutationError(err) });
    }
  }

  return (
    <Pane title="Research cycle (24/7)" dense>
      <p className="muted" style={{ fontSize: "11px", marginTop: 0 }}>
        Queues a paper-only cycle on the host daemon: batch → Oracle → wiring → operator run. Requires{" "}
        <code className="json-preview">scripts/start_research_cycle_daemon.ps1</code> on the artifact host.
      </p>

      <TermKV
        rows={[
          { k: "daemon", v: daemonOk ? <StatusBadge raw="RUNNING" /> : <StatusBadge raw="NOT_REGISTERED" /> },
          { k: "daemon_pid", v: asString(scheduler?.daemon_pid) ?? "—" },
          { k: "interval", v: scheduler ? `${asString(scheduler.interval_seconds) ?? "?"}s` : "—" },
          { k: "lock", v: root?.lock_held === true ? "held" : "free" },
          { k: "pending", v: root?.pending_trigger === true ? "yes" : "no" },
          { k: "last cycle", v: lastCycle ? <StatusBadge raw={lastOk ? "OK" : "FAILED"} /> : "—" },
          { k: "oracle posture", v: asString(root?.oracle_fusion_posture) ?? "—" },
        ]}
      />
      <p className="muted" style={{ fontSize: "10px" }}>{statusLine}</p>
      {degraded.length > 0 && <JsonDetails summary="degraded" data={degraded} />}

      <form
        style={{ display: "grid", gap: "0.5rem", marginTop: "0.75rem", maxWidth: "28rem" }}
        onSubmit={(e) => {
          e.preventDefault();
          void queueCycle();
        }}
      >
        <label className="muted" style={{ fontSize: "11px" }}>
          Operator id
          <input
            className="term-input"
            value={operatorId}
            onChange={(e) => setOperatorId(e.target.value)}
            style={{ display: "block", width: "100%", marginTop: "0.2rem" }}
          />
        </label>
        <label className="muted" style={{ fontSize: "11px" }}>
          Mode
          <select
            className="term-input"
            value={mode}
            onChange={(e) => setMode(e.target.value as "light" | "heavy")}
            style={{ display: "block", width: "100%", marginTop: "0.2rem" }}
          >
            <option value="light">light (one rotating batch)</option>
            <option value="heavy">heavy (+ runtime full Research OS cycle)</option>
          </select>
        </label>
        <label className="muted" style={{ fontSize: "11px" }}>
          Mutation token (production)
          <input
            className="term-input"
            type="password"
            autoComplete="off"
            value={mutationToken}
            onChange={(e) => setMutationToken(e.target.value)}
            style={{ display: "block", width: "100%", marginTop: "0.2rem" }}
          />
        </label>
        <button type="submit" className="term-btn" disabled={trigger.isPending}>
          {trigger.isPending ? "Queueing…" : "Run research cycle now"}
        </button>
      </form>

      {receipt && (
        <p className="muted" style={{ fontSize: "11px", marginTop: "0.5rem" }}>
          {receipt.accepted ? "Queued." : "Not queued."} {receipt.operator_message ?? ""}
        </p>
      )}

      <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
        {`# 24/7 host daemon (PowerShell, repo root)
.\\scripts\\start_research_cycle_daemon.ps1

# Faster dev interval (optional)
$env:RESEARCH_CYCLE_INTERVAL_SECONDS = "900"
$env:RESEARCH_CYCLE_HEAVY_EVERY = "6"`}
      </pre>
    </Pane>
  );
}

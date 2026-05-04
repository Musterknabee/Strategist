"use client";

import { useMemo } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { StrategyIntakeForm } from "@/components/operator/StrategyIntakeForm";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiStrategyIntakeLatest } from "@/hooks/useUiStrategyIntake";
import type { UiStrategyIntakeIndexEntry } from "@/lib/api/types";
import { StrategistApiError } from "@/lib/api/strategist-errors";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";

function formatError(err: unknown): { title: string; detail: string } {
  if (err instanceof StrategistApiError) {
    if (err.kind === "unauthorized") return { title: "Unauthorized", detail: err.message };
    if (err.kind === "unavailable") return { title: "Backend unavailable", detail: err.message };
    return { title: "API error", detail: err.message };
  }
  if (err instanceof Error) return { title: "Error", detail: err.message };
  return { title: "Error", detail: String(err) };
}

function shortDigest(value: string | undefined): string {
  return value ? value.slice(0, 12) : "—";
}

export default function StrategyInboxPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const latest = useUiStrategyIntakeLatest();
  const err = latest.isError ? formatError(latest.error) : null;
  const entries = latest.data?.latest.entries ?? [];

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "strategy-inbox",
        severity: latest.data?.degraded?.length ? "warn" : "info",
        text: `strategy_intake count=${entries.length} boundary=${latest.data?.authority_boundary ?? "?"}`,
      },
    ],
    [entries.length, latest.data?.authority_boundary, latest.data?.degraded?.length],
  );
  const ticker = useMemo(
    () => [
      {
        severity: latest.data?.degraded?.length ? ("warn" as const) : ("neutral" as const),
        text: `INTAKE ${entries.length} LIVE_AUTH NONE`,
      },
    ],
    [entries.length, latest.data?.degraded?.length],
  );
  useTerminalPageBind(tape, ticker);

  const cols: DenseColumn<UiStrategyIntakeIndexEntry>[] = useMemo(
    () => [
      { key: "name", header: "strategy", width: "24%", cell: (r) => r.strategy_name },
      { key: "universe", header: "universe", width: "18%", cell: (r) => r.target_universe },
      { key: "horizon", header: "horizon", width: "12%", cell: (r) => r.intended_horizon },
      { key: "state", header: "state", width: "18%", cell: (r) => <StatusBadge raw={r.readiness_state} /> },
      { key: "proposal", header: "proposal", width: "18%", cell: (r) => <code>{r.proposal_id}</code> },
      { key: "sha", header: "sha", width: "10%", cell: (r) => <code>{shortDigest(r.artifact_sha256)}</code> },
    ],
    [],
  );

  if (!config.ok) {
    return (
      <div className="term-page">
        <h1 className="term-page__title">STRATEGY INBOX</h1>
        <p className="muted">{config.error.message}</p>
      </div>
    );
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">STRATEGY INBOX · ADVISORY INTAKE</h1>
      <p className="muted" style={{ fontSize: "10px" }}>
        Read-plane: <code>/ui/strategy-intake/latest</code> · mutation-plane: <code>POST /ui/strategy-intake</code> · <code>{config.baseUrl}</code>
      </p>

      {latest.isLoading && <p className="muted">Loading…</p>}
      {err && (
        <p className="term-page__banner" style={{ color: "#f85149" }}>
          {err.title}: {err.detail}
        </p>
      )}

      <StrategyIntakeForm />

      <PaneGrid cols={2}>
        <Pane title="Intake posture" dense>
          <TermKV
            rows={[
              { k: "schema", v: latest.data?.schema_version ?? "—" },
              { k: "boundary", v: latest.data?.authority_boundary ?? "ADVISORY_ARTIFACT_ONLY" },
              { k: "read_plane_only", v: String(latest.data?.read_plane_only ?? true) },
              { k: "no_live_trading", v: String(latest.data?.no_live_trading ?? true) },
              { k: "intake_count", v: String(latest.data?.latest.intake_count ?? 0) },
            ]}
          />
        </Pane>
        <Pane title="Projection paths" dense>
          <TermKV
            rows={[
              { k: "scan_root", v: latest.data?.scan_root ?? "—" },
              { k: "index_path", v: latest.data?.index_path ?? "—" },
              { k: "degraded", v: latest.data?.degraded?.join(", ") || "NONE" },
            ]}
          />
        </Pane>
      </PaneGrid>

      <Pane title="Latest intake index" dense>
        {entries.length === 0 ? (
          <p className="muted" style={{ fontSize: "11px" }}>
            No strategy intakes recorded yet. Use the form above to create an advisory proposal artifact.
          </p>
        ) : (
          <DenseTable
            columns={cols}
            rows={entries}
            rowKey={(r) => r.intake_id}
            onRowClick={(r) =>
              openInspector({
                title: r.strategy_name,
                body: (
                  <TermKV
                    rows={[
                      { k: "intake_id", v: r.intake_id },
                      { k: "proposal_id", v: r.proposal_id },
                      { k: "artifact", v: r.artifact_path },
                      { k: "created", v: r.created_at_utc },
                    ]}
                  />
                ),
                rawJson: r,
              })
            }
          />
        )}
      </Pane>

      {latest.data && <JsonDetails summary="Drilldown: /ui/strategy-intake/latest JSON" data={latest.data} />}
    </div>
  );
}

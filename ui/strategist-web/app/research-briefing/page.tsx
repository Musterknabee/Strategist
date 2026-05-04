"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiResearchOsBriefingLatest } from "@/hooks/useUiResearchOsBriefing";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

type SectionRow = Record<string, unknown> & { __id: string };
type ActionRow = Record<string, unknown> & { __id: string };

export default function ResearchBriefingPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiResearchOsBriefingLatest();
  const root = q.data ? asRecord(q.data) : null;
  const briefing = root?.latest_briefing ? asRecord(root.latest_briefing) : null;
  const degraded = root ? asStringArray(root.degraded) : [];
  const warnings = briefing ? asStringArray(briefing.warnings) : [];
  const blockers = briefing ? asStringArray(briefing.blockers) : [];

  const sections: SectionRow[] = useMemo(() => {
    const raw = Array.isArray(briefing?.sections) ? briefing.sections : [];
    return raw
      .map((item, i) => {
        const r = asRecord(item);
        if (!r) return null;
        return { ...r, __id: `${asString(r.section_id) ?? "section"}-${i}` };
      })
      .filter((x): x is SectionRow => x !== null);
  }, [briefing]);

  const actions: ActionRow[] = useMemo(() => {
    const raw = Array.isArray(briefing?.action_items) ? briefing.action_items : [];
    return raw
      .map((item, i) => {
        const r = asRecord(item);
        if (!r) return null;
        return { ...r, __id: `${asString(r.action_id) ?? "action"}-${i}` };
      })
      .filter((x): x is ActionRow => x !== null);
  }, [briefing]);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "research-briefing",
        ts: asString(root?.generated_at_utc),
        severity: blockers.length ? "bad" : degraded.length || warnings.length ? "warn" : "ok",
        text: briefing
          ? `BRIEFING ${asString(briefing.status) ?? "UNKNOWN"} · sections=${sections.length} actions=${actions.length}`
          : "NO_RESEARCH_OS_BRIEFING_PACK",
      },
    ],
    [actions.length, blockers.length, briefing, degraded.length, root, sections.length, warnings.length],
  );
  useTerminalPageBind(tape, []);

  const sectionCols: DenseColumn<SectionRow>[] = [
    { key: "section", header: "Section", cell: (r) => <code>{asString(r.section_id) ?? "—"}</code> },
    { key: "status", header: "Status", cell: (r) => <StatusBadge raw={asString(r.status) ?? "—"} /> },
    { key: "warnings", header: "Warn", cell: (r) => String(asStringArray(r.warnings).length) },
    { key: "blockers", header: "Block", cell: (r) => String(asStringArray(r.blockers).length) },
    { key: "digest", header: "Digest", cell: (r) => (asString(r.digest) ?? "—").slice(0, 16) },
  ];

  const actionCols: DenseColumn<ActionRow>[] = [
    { key: "severity", header: "Severity", cell: (r) => <StatusBadge raw={asString(r.severity) ?? "—"} /> },
    { key: "title", header: "Action", cell: (r) => asString(r.title) ?? "—" },
    { key: "section", header: "Section", cell: (r) => asString(r.related_section_id) ?? "—" },
    { key: "command", header: "Command", cell: (r) => asString(r.suggested_command) ?? "—" },
  ];

  if (!config.ok) {
    return <div className="term-page cockpit-page"><div className="term-page__banner">{config.error.message}</div></div>;
  }

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Research Briefing</h1>
          <p className="muted">Daily Research OS evidence briefing · read-plane only · no live trading · no broker orders</p>
        </div>
      </div>

      <div className="readiness" role="status">
        <strong>Briefing is not deployment approval</strong>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          It packages current evidence posture and suggested operator actions. It does not authorize execution or profitability claims.
        </p>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Briefing summary" dense onInspect={() => openInspector({ title: "Research briefing", rawJson: q.data ?? {} })}>
          {q.isError && <p className="term-page__banner">Could not load /ui/research-os/briefing/latest</p>}
          {!briefing ? (
            <p className="muted">No briefing pack — run <code className="json-preview">strategy-validator-research-os-briefing build --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "briefing_id", v: asString(briefing.briefing_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(briefing.status) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(briefing.trust_banner) ?? "—"} /> },
                { k: "headline", v: asString(briefing.headline) ?? "—" },
                { k: "sections", v: String(sections.length) },
                { k: "actions", v: String(actions.length) },
                { k: "briefing_sha256", v: (asString(briefing.briefing_sha256) ?? "—").slice(0, 24) },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-research-os-briefing build --overwrite --json
          </pre>
        </Pane>

        <Pane title="Warnings / blockers" dense>
          {warnings.length ? <JsonDetails summary="warnings" data={warnings} /> : <p className="muted">No warnings indexed.</p>}
          {blockers.length ? <JsonDetails summary="blockers" data={blockers} /> : <p className="muted">No blockers indexed.</p>}
        </Pane>

        <Pane title="Evidence sections" dense>
          <DenseTable
            columns={sectionCols}
            rows={sections}
            rowKey={(r) => r.__id}
            onRowClick={(r) => openInspector({ title: `Briefing section · ${asString(r.section_id) ?? "section"}`, rawJson: r })}
          />
        </Pane>

        <Pane title="Action items" dense>
          <DenseTable
            columns={actionCols}
            rows={actions}
            rowKey={(r) => r.__id}
            onRowClick={(r) => openInspector({ title: `Action · ${asString(r.action_id) ?? "action"}`, rawJson: r })}
          />
        </Pane>
      </div>
    </main>
  );
}

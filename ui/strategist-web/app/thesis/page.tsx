"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiStrategyThesisGenerationLatest, useUiStrategyThesisLatest } from "@/hooks/useUiStrategyThesis";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

export default function ThesisPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiStrategyThesisLatest();
  const gq = useUiStrategyThesisGenerationLatest();
  const root = q.data ? asRecord(q.data) : null;
  const latest = root?.latest ? asRecord(root.latest) : null;
  const degraded = root ? asStringArray(root.degraded) : [];
  const contradictions = latest ? asStringArray(latest.contradictions) : [];
  const missing = latest ? asStringArray(latest.missing_evidence) : [];
  const genRoot = gq.data ? asRecord(gq.data) : null;
  const latestGeneration = genRoot?.latest_generation ? asRecord(genRoot.latest_generation) : null;
  const generatedTheses = Array.isArray(latestGeneration?.generated_theses) ? latestGeneration.generated_theses : [];

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "thesis",
        ts: asString(root?.generated_at_utc),
        severity: degraded.length || contradictions.length ? "warn" : "ok",
        text: latest ? `THESIS ${asString(latest.support_status)}` : "NO_THESIS_EVALUATION",
      },
    ],
    [contradictions.length, degraded.length, latest, root],
  );
  useTerminalPageBind(tape, []);

  if (!config.ok) {
    return <div className="term-page__banner">{config.error.message}</div>;
  }

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Strategy Thesis</h1>
          <p className="muted">Hypothesis · evidence requirements · falsification criteria · research only</p>
        </div>
      </div>

      <div className="readiness" role="status">
        <strong>Falsification-first</strong>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          Thesis evaluation can falsify or leave evidence inconclusive. It never certifies profitability and never enables live trading.
        </p>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Latest thesis evaluation" dense onInspect={() => openInspector({ title: "Strategy Thesis latest", rawJson: q.data ?? {} })}>
          {q.isError && <p className="muted">DEGRADED · could not load /ui/strategy-thesis/latest</p>}
          {degraded.length > 0 && <p className="muted">{degraded.join(", ")}</p>}
          <TermKV
            rows={[
              { k: "strategy_id", v: asString(latest?.strategy_id) ?? "—" },
              { k: "thesis_id", v: asString(latest?.thesis_id) ?? "—" },
              { k: "support_status", v: asString(latest?.support_status) ?? "—" },
              { k: "evaluation_sha256", v: (asString(latest?.evaluation_sha256) ?? "—").slice(0, 16) },
              { k: "scan_root", v: asString(root?.scan_root) ?? "—" },
            ]}
          />
          <p style={{ marginTop: "0.75rem" }}>
            <StatusBadge raw={asString(latest?.support_status) ?? "NOT_EVALUATED"} />
          </p>
        </Pane>

        <Pane title="Contradictions" dense>
          {contradictions.length ? (
            <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: "11px" }}>
              {contradictions.map((x) => <li key={x}>{x}</li>)}
            </ul>
          ) : (
            <p className="muted">No contradictions in latest evaluation.</p>
          )}
        </Pane>

        <Pane title="Missing evidence" dense>
          {missing.length ? (
            <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: "11px" }}>
              {missing.map((x) => <li key={x}>{x}</li>)}
            </ul>
          ) : (
            <p className="muted">No missing required evidence in latest evaluation.</p>
          )}
        </Pane>

        <Pane title="Oracle-generated theses" dense onInspect={() => openInspector({ title: "Strategy Thesis generation", rawJson: gq.data ?? {} })}>
          {gq.isError && <p className="muted">DEGRADED · could not load /ui/strategy-thesis/generation/latest</p>}
          {genRoot && asStringArray(genRoot.degraded).length > 0 && <p className="muted">{asStringArray(genRoot.degraded).join(", ")}</p>}
          <TermKV
            rows={[
              { k: "run_id", v: asString(latestGeneration?.run_id) ?? "—" },
              { k: "generated_count", v: String(latestGeneration?.generated_count ?? "—") },
              { k: "evaluated_count", v: String(latestGeneration?.evaluated_count ?? "—") },
              { k: "report_sha256", v: (asString(latestGeneration?.report_sha256) ?? "—").slice(0, 16) },
            ]}
          />
          {generatedTheses.length ? (
            <ul style={{ margin: "0.75rem 0 0", paddingLeft: "1.1rem", fontSize: "11px" }}>
              {generatedTheses.slice(0, 5).map((item, idx) => {
                const row = asRecord(item);
                return <li key={`${asString(row?.strategy_id) ?? "strategy"}-${idx}`}>{asString(row?.strategy_id) ?? "—"} · {asString(row?.support_status) ?? "NOT_EVALUATED"}</li>;
              })}
            </ul>
          ) : (
            <p className="muted">Run strategy-validator-thesis generate-from-batch.</p>
          )}
        </Pane>

        <Pane title="Raw evaluation" dense>
          {latest ? <JsonDetails summary="thesis_evaluation.json" data={latest} /> : <p className="muted">Run strategy-validator-thesis evaluate.</p>}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-thesis generate-from-batch --strategy-run artifacts/strategy_runs/&lt;run-id&gt; --json
strategy-validator-thesis evaluate --strategy-run artifacts/strategy_runs/&lt;run-id&gt; --thesis configs/strategy_theses/&lt;id&gt;.json --json
          </pre>
        </Pane>
      </div>
    </main>
  );
}

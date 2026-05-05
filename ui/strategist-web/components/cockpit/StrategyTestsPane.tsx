import { DenseTable } from "@/components/terminal/DenseTable";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import { asRecord, asString } from "@/lib/operator/payload-utils";
import type { StrategyRow } from "./cockpit-types";
import { UNKNOWN, buildStrategyColumns, digest, inspectBody, value } from "./cockpit-utils";

export type StrategyTestsPaneProps = {
  journaledCount: number;
  strategyRows: StrategyRow[];
  selectedKey: string | null;
  setSelectedKey: (k: string | null) => void;
  openInspector: (s: InspectorPayload) => void;
};

const strategyColumns = buildStrategyColumns();

export function StrategyTestsPane({
  journaledCount,
  strategyRows,
  selectedKey,
  setSelectedKey,
  openInspector,
}: StrategyTestsPaneProps) {
  return (
    <>
      <div className="pane-subtitle">STRATEGY TESTS</div>
      {journaledCount === 0 && strategyRows.length > 0 && (
        <p className="muted" style={{ fontSize: "11px", margin: "0 0 0.5rem", lineHeight: 1.35 }}>
          Ranked list is driven by the operator queue: you always have at least the primary governed item. Extra rows
          require{" "}
          <code style={{ fontSize: "10px" }}>STRATEGY_VALIDATOR_LEDGER_DB_PATH</code> plus accepted actions in the
          operator journal (see QUEUE below).
        </p>
      )}
      <DenseTable
        columns={strategyColumns}
        rows={strategyRows}
        rowKey={(r) => r.__id}
        selectedKey={selectedKey}
        onRowClick={(r) => {
          setSelectedKey(r.__id);
          const readiness = asRecord(r.command_readiness);
          const brief = asRecord(r.operator_brief);
          openInspector({
            title: `Strategy/Test · ${digest(r.work_item_key)}`,
            subtitle: asString(r.review_target) ?? "workboard ranked item",
            body: inspectBody({
              status: asString(r.attention_state) ?? UNKNOWN,
              summary:
                asString(brief?.summary_line) ??
                asString(r.recommended_action) ??
                "No strategy/test summary supplied.",
              warnings: [asString(r.blocking_reason), asString(asRecord(r.policy_recommendation)?.operator_line)].filter(
                (x): x is string => !!x,
              ),
              details: [
                { k: "priority_score", v: value(r.priority_score ?? r.score, "0") },
                { k: "top_action", v: asString(readiness?.top_action) ?? "PENDING" },
                {
                  k: "ready/caution/blocked",
                  v: `${value(readiness?.ready_count, "0")}/${value(readiness?.caution_count, "0")}/${value(
                    readiness?.blocked_count,
                    "0",
                  )}`,
                },
              ],
            }),
            rawJson: r,
          });
        }}
        empty="PENDING · no ranked strategy/test items"
      />
    </>
  );
}

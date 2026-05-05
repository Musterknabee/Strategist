import { DenseTable } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import type { MatrixRow } from "./cockpit-types";
import { buildReadinessColumns, inspectBody } from "./cockpit-utils";

export type ReadinessMatrixPaneProps = {
  readyStatus: string;
  pass: number;
  warn: number;
  fail: number;
  crit: number;
  readinessPct: number;
  readinessRows: MatrixRow[];
  warnings: readonly { code: string }[];
  selectedKey: string | null;
  setSelectedKey: (k: string | null) => void;
  readyBody: Record<string, unknown> | null;
  openInspector: (s: InspectorPayload) => void;
};

const readinessColumns = buildReadinessColumns();

export function ReadinessMatrixPane({
  readyStatus,
  pass,
  warn,
  fail,
  crit,
  readinessPct,
  readinessRows,
  warnings,
  selectedKey,
  setSelectedKey,
  readyBody,
  openInspector,
}: ReadinessMatrixPaneProps) {
  return (
    <Pane
      title="Readiness Matrix"
      dense
      onInspect={() =>
        openInspector({
          title: "Readiness Matrix",
          body: inspectBody({
            status: readyStatus,
            summary: `${pass} PASS / ${warn} WARN / ${fail} FAIL / ${crit} CRIT`,
            warnings: warnings.map((w) => w.code),
            details: [{ k: "readiness_pct", v: `${readinessPct}%` }],
          }),
          rawJson: readyBody,
        })
      }
    >
      <DenseTable
        columns={readinessColumns}
        rows={readinessRows.slice(0, 8)}
        rowKey={(r) => r.checkId}
        selectedKey={selectedKey}
        onRowClick={(r) => {
          setSelectedKey(r.checkId);
          openInspector({
            title: `Readiness · ${r.checkId}`,
            body: inspectBody({
              status: r.status,
              summary: r.remediation,
              details: [
                { k: "severity", v: r.severity },
                { k: "blocker", v: r.blockerCode },
              ],
            }),
            rawJson: r.raw,
          });
        }}
        empty="UNKNOWN · no readiness checks returned"
      />
      <div className="pane-footer">
        PASS={pass} WARN={warn} FAIL={fail} CRIT={crit} READINESS={readinessPct}%
      </div>
    </Pane>
  );
}

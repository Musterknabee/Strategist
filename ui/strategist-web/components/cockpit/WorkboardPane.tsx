import { EvidenceProvenanceBar } from "@/components/cockpit/EvidenceProvenanceBar";
import { DenseTable } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { StatusBadge } from "@/components/operator/StatusBadge";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import { asString } from "@/lib/operator/payload-utils";
import type { UiWorkboardPayload } from "@/lib/api/types";
import type { PaneEvidenceProvenance } from "./cockpit-provenance-types";
import type { StrategyRow, WorkRow } from "./cockpit-types";
import { UNKNOWN, buildWorkColumns, inspectBody } from "./cockpit-utils";
import { StrategyTestsPane } from "./StrategyTestsPane";

export type WorkboardPaneProps = {
  workboardData: UiWorkboardPayload | null | undefined;
  wbCount: number | null;
  strategyRows: StrategyRow[];
  workRows: WorkRow[];
  selectedKey: string | null;
  setSelectedKey: (k: string | null) => void;
  openInspector: (s: InspectorPayload) => void;
  provenance: PaneEvidenceProvenance;
  inspectorPayload: InspectorPayload;
  setLastDigest: (s: string | null) => void;
};

const workColumns = buildWorkColumns();

export function WorkboardPane({
  workboardData,
  wbCount,
  strategyRows,
  workRows,
  selectedKey,
  setSelectedKey,
  openInspector,
  provenance,
  inspectorPayload,
  setLastDigest,
}: WorkboardPaneProps) {
  return (
    <Pane title="Workboard" dense onInspect={() => openInspector(inspectorPayload)}>
      <EvidenceProvenanceBar
        {...provenance}
        openInspector={openInspector}
        inspectorPayload={inspectorPayload}
        setLastDigest={setLastDigest}
        data-testid="workboard-provenance"
      />
      {workboardData && (
        <TermKV
          rows={[
            { k: "active", v: String(workboardData.stats.active_count) },
            { k: "governed", v: String(workboardData.stats.governed_count) },
            { k: "journaled", v: String(workboardData.stats.journaled_count) },
            { k: "freshness", v: <StatusBadge raw={workboardData.stats.freshness_state} /> },
            { k: "items", v: String(wbCount ?? UNKNOWN) },
          ]}
        />
      )}
      <StrategyTestsPane
        journaledCount={workboardData?.stats.journaled_count ?? 0}
        strategyRows={strategyRows}
        selectedKey={selectedKey}
        setSelectedKey={setSelectedKey}
        openInspector={openInspector}
      />
      <div className="pane-subtitle">QUEUE</div>
      <DenseTable
        columns={workColumns}
        rows={workRows}
        rowKey={(r) => r.__id}
        selectedKey={selectedKey}
        onRowClick={(r) => {
          setSelectedKey(r.__id);
          openInspector({
            title: `Work item · ${asString(r.work_item_key) ?? r.__id}`,
            body: inspectBody({
              status: asString(r.status) ?? UNKNOWN,
              summary: asString(r.summary_line) ?? asString(r.title) ?? "No work item summary supplied.",
              details: [
                { k: "owner", v: asString(r.owner) ?? "PENDING" },
                { k: "updated", v: asString(r.updated_at_utc) ?? "PENDING" },
              ],
            }),
            rawJson: r,
          });
        }}
        empty="PENDING · no queue entries"
      />
    </Pane>
  );
}

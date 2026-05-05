"use client";

import { EvidenceProvenanceBar } from "@/components/cockpit/EvidenceProvenanceBar";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { StatusBadge } from "@/components/operator/StatusBadge";
import type { EvidenceDrilldownRow } from "@/lib/operator/cockpit-evidence-drilldown-rows";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import type { PaneEvidenceProvenance } from "./cockpit-provenance-types";
import { UNKNOWN, digest, inspectBody } from "./cockpit-utils";

const columns: DenseColumn<EvidenceDrilldownRow>[] = [
  { key: "s", header: "SURFACE", cell: (r) => r.surface },
  { key: "st", header: "STATUS", cell: (r) => <StatusBadge raw={r.status} /> },
  { key: "tr", header: "TRUST", cell: (r) => <StatusBadge raw={r.trust} /> },
  { key: "b", header: "BLK", width: "44px", cell: (r) => String(r.blockers) },
  { key: "w", header: "WRN", width: "44px", cell: (r) => String(r.warnings) },
  { key: "t", header: "AT", cell: (r) => <span title={r.at}>{digest(r.at)}</span> },
  { key: "d", header: "DIG", cell: (r) => <code>{r.digestPreview}</code> },
];

export type PaperExecutionEvidenceDrilldownPaneProps = {
  rows: EvidenceDrilldownRow[];
  queryFailed: boolean;
  selectedKey: string | null;
  setSelectedKey: (k: string | null) => void;
  openInspector: (p: InspectorPayload) => void;
  setLastDigest: (s: string | null) => void;
  provenance: PaneEvidenceProvenance;
  inspectorPayload: InspectorPayload;
};

export function PaperExecutionEvidenceDrilldownPane({
  rows,
  queryFailed,
  selectedKey,
  setSelectedKey,
  openInspector,
  setLastDigest,
  provenance,
  inspectorPayload,
}: PaperExecutionEvidenceDrilldownPaneProps) {
  return (
    <div className="cockpit-drilldown-pane" data-testid="cockpit-paper-execution-drilldown">
      <Pane title="Paper Execution Evidence" dense onInspect={() => openInspector(inspectorPayload)}>
        {queryFailed ? (
          <div className="cockpit-drilldown-banner" role="status">
            READ_PLANE · /ui/paper-execution/latest unavailable — rows show UNKNOWN.
          </div>
        ) : null}
        <EvidenceProvenanceBar
          {...provenance}
          openInspector={openInspector}
          inspectorPayload={inspectorPayload}
          setLastDigest={setLastDigest}
          data-testid="paper-execution-drilldown-provenance"
        />
        <DenseTable
          columns={columns}
          rows={rows}
          rowKey={(r) => r.__id}
          selectedKey={selectedKey}
          onRowClick={(r) => {
            setSelectedKey(r.__id);
            openInspector({
              title: `Paper execution · ${r.surface}`,
              subtitle: "Read-plane cockpit row (no order submission)",
              body: inspectBody({
                status: r.status,
                summary: `Trust ${r.trust}; blockers=${r.blockers}; warnings=${r.warnings}.`,
                warnings: queryFailed ? ["QUERY_FAILED"] : [],
                details: [
                  { k: "generated_at_utc", v: r.at },
                  { k: "digest", v: r.digestPreview },
                ],
              }),
              rawJson: r.raw ?? { note: "no_payload" },
              digestToCopy: r.digestFull ?? undefined,
            });
          }}
          empty={UNKNOWN + " · no paper execution cockpit"}
        />
      </Pane>
    </div>
  );
}

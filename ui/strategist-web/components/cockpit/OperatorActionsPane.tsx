import { EvidenceProvenanceBar } from "@/components/cockpit/EvidenceProvenanceBar";
import { DenseTable } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import { asBool, asRecord, asString } from "@/lib/operator/payload-utils";
import type { PaneEvidenceProvenance } from "./cockpit-provenance-types";
import type { ActionRow } from "./cockpit-types";
import { UNKNOWN, boolStatus, buildActionColumns, digest, entryTime, inspectBody, value } from "./cockpit-utils";

export type OperatorActionsPaneProps = {
  operatorIdxData: unknown;
  actionRows: ActionRow[];
  selectedKey: string | null;
  setSelectedKey: (k: string | null) => void;
  openInspector: (s: InspectorPayload) => void;
  setLastDigest: (s: string | null) => void;
  provenance: PaneEvidenceProvenance;
  inspectorPayload: InspectorPayload;
};

const actionColumns = buildActionColumns();

export function OperatorActionsPane({
  operatorIdxData,
  actionRows,
  selectedKey,
  setSelectedKey,
  openInspector,
  setLastDigest,
  provenance,
  inspectorPayload,
}: OperatorActionsPaneProps) {
  const idx = asRecord(operatorIdxData);
  return (
    <Pane title="Ledger / Operator Actions" dense onInspect={() => openInspector(inspectorPayload)}>
      <EvidenceProvenanceBar
        {...provenance}
        openInspector={openInspector}
        inspectorPayload={inspectorPayload}
        setLastDigest={setLastDigest}
        data-testid="operator-actions-provenance"
      />
      <TermKV
        rows={[
          { k: "events", v: value(idx?.event_count, "0") },
          {
            k: "latest_digest",
            v: actionRows.length ? digest(actionRows[actionRows.length - 1].event_hash) : "PENDING",
          },
          { k: "chain_status", v: boolStatus(asBool(idx?.chain_ok), "OK", "DEGRADED") },
          { k: "immutable", v: asBool(idx?.chain_ok) !== false ? "YES" : "NO" },
        ]}
      />
      <DenseTable
        columns={actionColumns}
        rows={actionRows}
        rowKey={(r) => r.__id}
        selectedKey={selectedKey}
        onRowClick={(r) => {
          setSelectedKey(r.__id);
          const h = asString(r.event_hash);
          if (h) setLastDigest(h);
          openInspector({
            title: `Action · ${asString(r.action) ?? UNKNOWN}`,
            body: inspectBody({
              status: asString(r.status) ?? "PENDING",
              summary: `Actor ${asString(r.operator_id) ?? UNKNOWN} targeted ${asString(r.target) ?? "PENDING"}.`,
              details: [
                { k: "time", v: entryTime(r) },
                { k: "digest", v: digest(h) },
              ],
            }),
            rawJson: r,
            digestToCopy: h ?? undefined,
          });
        }}
        empty="PENDING · no operator actions returned"
      />
    </Pane>
  );
}

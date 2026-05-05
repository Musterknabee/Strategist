import { EvidenceProvenanceBar } from "@/components/cockpit/EvidenceProvenanceBar";
import { DenseTable } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import { asRecord, asString } from "@/lib/operator/payload-utils";
import type { PaneEvidenceProvenance } from "./cockpit-provenance-types";
import type { ProviderRow } from "./cockpit-types";
import { UNKNOWN, buildProviderColumns, inspectBody, value } from "./cockpit-utils";

export type ProviderMatrixPaneProps = {
  providerRows: ProviderRow[];
  providerWarnings: number;
  providersData: unknown;
  selectedKey: string | null;
  setSelectedKey: (k: string | null) => void;
  openInspector: (s: InspectorPayload) => void;
  provenance: PaneEvidenceProvenance;
  inspectorPayload: InspectorPayload;
  setLastDigest: (s: string | null) => void;
};

const providerColumns = buildProviderColumns();

export function ProviderMatrixPane({
  providerRows,
  providerWarnings,
  providersData,
  selectedKey,
  setSelectedKey,
  openInspector,
  provenance,
  inspectorPayload,
  setLastDigest,
}: ProviderMatrixPaneProps) {
  return (
    <Pane title="Provider Matrix" dense onInspect={() => openInspector(inspectorPayload)}>
      <EvidenceProvenanceBar
        {...provenance}
        openInspector={openInspector}
        inspectorPayload={inspectorPayload}
        setLastDigest={setLastDigest}
        data-testid="provider-matrix-provenance"
      />
      <DenseTable
        columns={providerColumns}
        rows={providerRows.slice(0, 8)}
        rowKey={(r) => r.__id}
        selectedKey={selectedKey}
        onRowClick={(r) => {
          setSelectedKey(r.__id);
          const exec = asRecord(r.execution_posture);
          const rowWarnings = [
            ...((Array.isArray(r.warnings) ? r.warnings : []) as string[]),
            ...((Array.isArray(exec?.execution_policy_blockers) ? exec?.execution_policy_blockers : []) as string[]),
          ];
          openInspector({
            title: `Provider · ${asString(r.display_name) ?? r.__id}`,
            subtitle: r.__id === "alpaca" ? "Alpaca execution posture is explicitly surfaced" : undefined,
            body: inspectBody({
              status: asString(r.classified_status) ?? UNKNOWN,
              summary: `${value(r.access_type)} · ${value(r.trust_level)} · ${value(r.pit_suitability)}`,
              warnings: rowWarnings,
              details: [
                { k: "http", v: value(r.http_status, "PENDING") },
                { k: "configured", v: value(r.configured) },
                { k: "reachable", v: value(r.reachable) },
              ],
            }),
            rawJson: r,
            digestToCopy: asString(r.sample_digest_prefix),
          });
        }}
        empty="UNKNOWN · provider health unavailable"
      />
    </Pane>
  );
}

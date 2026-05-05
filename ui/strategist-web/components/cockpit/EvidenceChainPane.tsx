import { EvidenceProvenanceBar } from "@/components/cockpit/EvidenceProvenanceBar";
import { DenseTable } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import { asString } from "@/lib/operator/payload-utils";
import type { PaneEvidenceProvenance } from "./cockpit-provenance-types";
import type { EvidenceRow } from "./cockpit-types";
import { UNKNOWN, buildEvidenceColumns, digest, inspectBody } from "./cockpit-utils";

export type EvidenceChainPaneProps = {
  deploymentStatus: string | undefined;
  evidenceRows: EvidenceRow[];
  registryProjectionDigest: unknown;
  selectedKey: string | null;
  setSelectedKey: (k: string | null) => void;
  openInspector: (s: InspectorPayload) => void;
  setLastDigest: (s: string | null) => void;
  provenance: PaneEvidenceProvenance;
  inspectorPayload: InspectorPayload;
};

const evidenceColumns = buildEvidenceColumns();

export function EvidenceChainPane({
  deploymentStatus,
  evidenceRows,
  registryProjectionDigest,
  selectedKey,
  setSelectedKey,
  openInspector,
  setLastDigest,
  provenance,
  inspectorPayload,
}: EvidenceChainPaneProps) {
  return (
    <Pane title="Evidence Chain" dense onInspect={() => openInspector(inspectorPayload)}>
      <EvidenceProvenanceBar
        {...provenance}
        openInspector={openInspector}
        inspectorPayload={inspectorPayload}
        setLastDigest={setLastDigest}
        data-testid="evidence-chain-provenance"
      />
      <DenseTable
        columns={evidenceColumns}
        rows={evidenceRows}
        rowKey={(r) => r.step}
        selectedKey={selectedKey}
        onRowClick={(r) => {
          setSelectedKey(r.step);
          if (r.digest !== "PENDING") setLastDigest(r.digest);
          openInspector({
            title: `Evidence · ${r.step}`,
            body: inspectBody({
              status: r.status,
              summary: `Evidence step ${r.step} at ${r.time}`,
              details: [{ k: "digest", v: r.digest }],
            }),
            rawJson: r.raw,
            digestToCopy: r.digest !== "PENDING" ? r.digest : undefined,
          });
        }}
      />
      <div className="pane-footer">
        CHAIN_STATUS={deploymentStatus ?? UNKNOWN} LENGTH={evidenceRows.length}
      </div>
    </Pane>
  );
}

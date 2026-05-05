import { EvidenceProvenanceBar } from "@/components/cockpit/EvidenceProvenanceBar";
import { Pane } from "@/components/terminal/Pane";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import type { PaneEvidenceProvenance } from "./cockpit-provenance-types";
import type { OverviewTile } from "./cockpit-types";
import { inspectBody, metricTone } from "./cockpit-utils";

export type OverviewPaneProps = {
  overviewTiles: OverviewTile[];
  provenance: PaneEvidenceProvenance;
  inspectorPayload: InspectorPayload;
  openInspector: (s: InspectorPayload) => void;
  setLastDigest: (s: string | null) => void;
};

export function OverviewPane({
  overviewTiles,
  provenance,
  inspectorPayload,
  openInspector,
  setLastDigest,
}: OverviewPaneProps) {
  return (
    <Pane
      title="Overview"
      dense
      onInspect={() => openInspector(inspectorPayload)}
    >
      <EvidenceProvenanceBar
        {...provenance}
        openInspector={openInspector}
        inspectorPayload={inspectorPayload}
        setLastDigest={setLastDigest}
        data-testid="overview-evidence-provenance"
      />
      <div className="status-tile-grid">
        {overviewTiles.map((tile) => (
          <button
            key={tile.label}
            type="button"
            className={`status-tile status-tile--${metricTone(tile.status)}`}
            onClick={() =>
              openInspector({
                title: tile.label,
                subtitle: "Overview tile",
                body: inspectBody({
                  status: tile.status,
                  summary: tile.hint,
                  details: [{ k: "source", v: "read-plane" }],
                }),
                rawJson: tile.raw,
              })
            }
          >
            <span>{tile.label}</span>
            <strong>{tile.status}</strong>
            <em>{tile.hint}</em>
          </button>
        ))}
      </div>
    </Pane>
  );
}

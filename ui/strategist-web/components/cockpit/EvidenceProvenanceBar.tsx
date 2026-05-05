"use client";

import { StatusBadge } from "@/components/operator/StatusBadge";
import { normalizeTrustVerificationForBadge, projectionVerifiedLabel } from "@/lib/operator/evidence-provenance-map";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import type { PaneEvidenceProvenance } from "./cockpit-provenance-types";
import { UNKNOWN } from "./cockpit-utils";

const PENDING = "PENDING";

export type EvidenceProvenanceBarProps = PaneEvidenceProvenance & {
  onInspect?: () => void;
  openInspector?: (p: InspectorPayload) => void;
  inspectorPayload?: InspectorPayload;
  setLastDigest?: (s: string | null) => void;
  "data-testid"?: string;
};

export function EvidenceProvenanceBar({
  sourceLabel,
  schemaVersion,
  generatedAtUtc,
  digestPreview,
  digestFull,
  trustStatus,
  projectionSnapshotVerified,
  freshnessStatus,
  blockerCount,
  warningCount,
  supplementalLine,
  onInspect,
  openInspector,
  inspectorPayload,
  setLastDigest,
  "data-testid": testId = "evidence-provenance-bar",
}: EvidenceProvenanceBarProps) {
  const schema = (schemaVersion ?? "").trim() || PENDING;
  const gen = (generatedAtUtc ?? "").trim() || PENDING;
  const digestLabel = (digestPreview ?? "").trim() || PENDING;
  const trustBadge = normalizeTrustVerificationForBadge(trustStatus);
  const verifyRaw =
    projectionSnapshotVerified === undefined || projectionSnapshotVerified === null
      ? null
      : projectionVerifiedLabel(projectionSnapshotVerified);
  const freshnessBadge = (freshnessStatus ?? "").trim() || UNKNOWN;
  const blk =
    typeof blockerCount === "number" && !Number.isNaN(blockerCount) ? String(blockerCount) : UNKNOWN;
  const wrn =
    typeof warningCount === "number" && !Number.isNaN(warningCount) ? String(warningCount) : UNKNOWN;

  const handleInspect = () => {
    if (inspectorPayload && openInspector) {
      openInspector(inspectorPayload);
      return;
    }
    onInspect?.();
  };

  const copyDigest = () => {
    const full = (digestFull ?? "").trim();
    if (!full) return;
    setLastDigest?.(full.slice(0, 18));
    void navigator.clipboard?.writeText?.(full);
  };

  return (
    <div className="evidence-provenance-bar" data-testid={testId} role="status">
      <span className="evidence-provenance-bar__source">{sourceLabel}</span>
      <span className="evidence-provenance-bar__kv">
        <abbr title="schema_version">SCHEMA</abbr> <code>{schema}</code>
      </span>
      <span className="evidence-provenance-bar__kv">
        <abbr title="generated_at_utc">GEN</abbr> <time dateTime={gen !== PENDING ? gen : undefined}>{gen}</time>
      </span>
      <span className="evidence-provenance-bar__kv">
        <abbr title="digest / hash prefix">DIG</abbr>{" "}
        {digestFull ? (
          <button type="button" className="evidence-provenance-bar__digest" onClick={copyDigest} title="Copy full digest">
            <code>{digestLabel}</code>
          </button>
        ) : (
          <code>{digestLabel}</code>
        )}
      </span>
      <span className="evidence-provenance-bar__kv">
        <abbr title="trust / lineage">TRUST</abbr> <StatusBadge raw={trustBadge} />
      </span>
      {verifyRaw ? (
        <span className="evidence-provenance-bar__kv">
          <abbr title="projection snapshot verification">VERIFY</abbr> <StatusBadge raw={verifyRaw} />
        </span>
      ) : null}
      <span className="evidence-provenance-bar__kv">
        <abbr title="freshness / deployment posture">FRESH</abbr> <StatusBadge raw={freshnessBadge} />
      </span>
      <span className="evidence-provenance-bar__kv">
        <abbr title="blocker count">BLK</abbr> {blk}
      </span>
      <span className="evidence-provenance-bar__kv">
        <abbr title="warning count">WRN</abbr> {wrn}
      </span>
      {supplementalLine ? (
        <span className="evidence-provenance-bar__supplemental" title={supplementalLine}>
          {supplementalLine}
        </span>
      ) : null}
      {(onInspect || inspectorPayload) && (
        <button type="button" className="evidence-provenance-bar__inspect" onClick={handleInspect} title="Inspect evidence payload">
          ⓘ
        </button>
      )}
    </div>
  );
}

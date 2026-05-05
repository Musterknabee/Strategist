/** Read-plane provenance strip inputs (narrow; unknown-tolerant at call sites). */
export type PaneEvidenceProvenance = {
  sourceLabel: string;
  schemaVersion?: string | null;
  generatedAtUtc?: string | null;
  digestPreview?: string | null;
  digestFull?: string | null;
  trustStatus?: string | null;
  /** When set, shows VERIFY badge alongside TRUST (projection snapshot verification). */
  projectionSnapshotVerified?: boolean | null;
  freshnessStatus?: string | null;
  blockerCount?: number | null;
  warningCount?: number | null;
  supplementalLine?: string | null;
};

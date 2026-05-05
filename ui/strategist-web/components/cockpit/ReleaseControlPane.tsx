"use client";

import { useMemo } from "react";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { StatusBadge } from "@/components/operator/StatusBadge";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import { LocalOpsCommandHintsSection } from "@/components/cockpit/LocalOpsCommandHintsSection";
import { RELEASE_CONTROL_COMMAND_IDS } from "@/lib/operator/local-ops-command-hints";
import { buildReleaseControlModel, type ReleaseControlRow } from "@/lib/operator/release-control-model";
import { readUiEvidenceCockpit } from "@/lib/operator/ui-evidence-cockpit";
import { asRecord } from "@/lib/operator/payload-utils";

export type ReleaseControlPaneProps = {
  facade: unknown;
  evidence: unknown;
  evidenceChain: unknown;
  releaseReadiness: unknown;
  handoff: unknown;
  handoffSignoff: unknown;
  reviewJournal: unknown;
  queryFailed: boolean;
  openInspector: (payload: InspectorPayload) => void;
  setLastDigest?: (digest: string) => void;
};

const columns: DenseColumn<ReleaseControlRow>[] = [
  { key: "section", header: "Section", width: "200px", cell: (row) => row.section },
  { key: "stage", header: "Stage", width: "160px", cell: (row) => <StatusBadge raw={row.stage} /> },
  { key: "status", header: "Status", width: "120px", cell: (row) => <StatusBadge raw={row.status} /> },
  {
    key: "bw",
    header: "Blk/Wrn",
    width: "80px",
    cell: (row) => `${row.blocker_count}/${row.warning_count}`,
  },
  { key: "digest", header: "Digest", width: "120px", cell: (row) => row.digest_prefix },
  { key: "time", header: "Generated", cell: (row) => row.generated_at_utc },
];

function paneBadge(model: ReturnType<typeof buildReleaseControlModel>, queryFailed: boolean): string {
  if (queryFailed) return "DEGRADED";
  if (model.readiness_bucket === "FAIL") return "FAIL";
  if (model.readiness_bucket === "WARN") return "WARN";
  if (model.readiness_bucket === "PASS") return "PASS";
  return "UNKNOWN";
}

export function ReleaseControlPane({
  facade,
  evidence,
  evidenceChain,
  releaseReadiness,
  handoff,
  handoffSignoff,
  reviewJournal,
  queryFailed,
  openInspector,
  setLastDigest,
}: ReleaseControlPaneProps) {
  const cockpit = useMemo(() => readUiEvidenceCockpit(asRecord(evidence)), [evidence]);

  const model = useMemo(
    () =>
      buildReleaseControlModel({
        facade,
        evidence,
        evidenceChain,
        releaseReadiness,
        handoff,
        handoffSignoff,
        reviewJournal,
        cockpit,
      }),
    [cockpit, evidence, evidenceChain, facade, handoff, handoffSignoff, releaseReadiness, reviewJournal],
  );

  return (
    <div className="cockpit-release-control-row" data-testid="cockpit-release-control">
      <Pane
        title="Release control & operator signoff"
        dense
        badge={<StatusBadge raw={paneBadge(model, queryFailed)} />}
        onInspect={() =>
          openInspector({
            title: "Release control · read-plane bundle",
            subtitle: model.next_action,
            rawJson: {
              facade: facade ?? {},
              evidence: evidence ?? {},
              evidence_chain: evidenceChain ?? {},
              release_readiness: releaseReadiness ?? {},
              handoff: handoff ?? {},
              handoff_signoff: handoffSignoff ?? {},
              review_journal: reviewJournal ?? {},
              normalized: model,
            },
          })
        }
      >
        <TermKV
          rows={[
            { k: "release_control_id", v: model.release_control_id },
            { k: "readiness_bucket", v: <StatusBadge raw={model.readiness_bucket} /> },
            { k: "current_stage", v: <StatusBadge raw={model.current_stage} /> },
            { k: "trust_freshness", v: <StatusBadge raw={model.trust_or_freshness} /> },
            { k: "blockers_total", v: String(model.blocker_count) },
            { k: "warnings_total", v: String(model.warning_count) },
            { k: "digest_prefix", v: model.digest_prefix },
            { k: "next_action", v: <StatusBadge raw={model.next_action} /> },
            { k: "primary_command_hint", v: <code className="json-preview">{model.command_hint_primary}</code> },
          ]}
        />
        <div className="muted" style={{ fontSize: "10px", margin: "10px 0" }} data-testid="cockpit-release-control-frontend-claim-note">
          <strong>Frontend readiness</strong> is separate from package detection: <code>frontend_package_present</code> only means
          the UI subtree exists on disk. <code>frontend_readiness_claimed</code> (facade + deployment evidence) is an opt-in operator
          signal that the frontend adopted the read-plane contract — it is <strong>not</strong> automatic production certification
          and <strong>not</strong> deployment approval.
        </div>
        <DenseTable
          columns={columns}
          rows={model.rows}
          rowKey={(row) => row.__id}
          onRowClick={(row) => {
            if (row.digest_full) setLastDigest?.(row.digest_full);
            openInspector({
              title: `${row.section}`,
              subtitle: row.review_hint,
              rawJson: row.raw,
            });
          }}
          empty="UNKNOWN · release-control evidence unavailable"
        />
        <h3 className="muted" style={{ fontSize: "11px", margin: "12px 0 0", fontWeight: 600 }}>
          Registry-backed CLI hints
        </h3>
        <LocalOpsCommandHintsSection
          commandIds={RELEASE_CONTROL_COMMAND_IDS}
          testIdPrefix="cockpit-release-control-command-hints"
          intro="Commands are validated against pyproject.toml and scripts/ by repository_truth_check.py."
        />
      </Pane>
    </div>
  );
}

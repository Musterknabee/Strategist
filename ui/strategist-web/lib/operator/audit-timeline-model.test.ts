import { describe, expect, it } from "vitest";
import { buildAuditTimelineModel, buildForensicDiffs, filterAuditTimeline } from "./audit-timeline-model";

describe("buildAuditTimelineModel", () => {
  it("renders UNKNOWN-friendly model when evidence chain absent", () => {
    const m = buildAuditTimelineModel({
      evidenceChain: null,
      operatorActions: null,
      evidence: null,
      releaseReadiness: null,
      handoff: null,
      handoffSignoff: null,
      reviewJournal: null,
      exportLatest: null,
      driftLatest: null,
      paperExecution: null,
    });
    expect(m.chain_summary_ok).toBeNull();
    expect(m.entry_count).toBe(0);
    expect(m.forensic_diffs.some((b) => b.baseline === "NO_BASELINE")).toBe(true);
  });

  it("marks CHAINED when backend sets chained without issues", () => {
    const m = buildAuditTimelineModel({
      evidenceChain: {
        schema_version: "ui_evidence_chain/v1",
        generated_at_utc: "2026-01-02T00:00:00Z",
        ok: true,
        degraded: [],
        timeline: {
          entries: [
            {
              stream_family: "decision_ledger",
              record_id: "e1",
              created_at_utc: "2026-01-02T00:00:01Z",
              event_type: "promotion",
              status: "READY",
              promotion_state: "READY",
              chained: true,
              issue_codes: [],
              event_hash: "abcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcd",
              previous_event_hash: null,
            },
          ],
        },
      },
      operatorActions: null,
      evidence: null,
      releaseReadiness: null,
      handoff: null,
      handoffSignoff: null,
      reviewJournal: null,
      exportLatest: null,
      driftLatest: null,
      paperExecution: null,
    });
    const row = m.entries.find((e) => e.source_family === "decision_ledger");
    expect(row?.chain_semantic).toBe("CHAINED");
    expect(row?.digest_full?.length).toBeGreaterThan(16);
  });

  it("marks BROKEN when issue_codes contain chain verification", () => {
    const m = buildAuditTimelineModel({
      evidenceChain: {
        schema_version: "ui_evidence_chain/v1",
        generated_at_utc: "2026-01-02T00:00:00Z",
        ok: false,
        degraded: [],
        timeline: {
          entries: [
            {
              stream_family: "operator_action_journal",
              record_id: "a1",
              action_event_id: "a1",
              created_at_utc: "2026-01-02T00:00:02Z",
              action: "claim-item",
              status: "ACCEPTED",
              chained: false,
              issue_codes: ["CHAIN_VERIFICATION_ISSUE"],
              event_hash: "1111111111111111111111111111111111111111111111111111111111111111",
            },
          ],
        },
      },
      operatorActions: null,
      evidence: null,
      releaseReadiness: null,
      handoff: null,
      handoffSignoff: null,
      reviewJournal: null,
      exportLatest: null,
      driftLatest: null,
      paperExecution: null,
    });
    const row = m.entries.find((e) => e.source_family === "operator_action_journal");
    expect(row?.chain_semantic).toBe("BROKEN");
  });
});

const stubEntry = (over: Partial<import("./audit-timeline-model").AuditTimelineEntry>): import("./audit-timeline-model").AuditTimelineEntry => ({
  timeline_id: "t",
  timestamp: "2026-01-01T00:00:00Z",
  source_family: "x",
  event_type: "e",
  action: "a",
  status: "s",
  actor: "op",
  sequence_number: null,
  chain_semantic: "UNKNOWN",
  trust_semantic: "UNKNOWN",
  pass_fail: "UNKNOWN",
  digest_prefix: "—",
  digest_full: null,
  issue_count: 0,
  issue_codes: [],
  related_artifact: "r",
  raw: {},
  ...over,
});

describe("filterAuditTimeline", () => {
  const entries = [
    stubEntry({ source_family: "decision_ledger", chain_semantic: "CHAINED", issue_count: 0, pass_fail: "PASS" }),
    stubEntry({ source_family: "research_os", chain_semantic: "UNKNOWN", issue_count: 0, pass_fail: "PASS" }),
    stubEntry({
      source_family: "operator_action_journal",
      chain_semantic: "BROKEN",
      issue_count: 1,
      pass_fail: "DEGRADED",
    }),
  ];

  it("filters promotion ledger only", () => {
    const f = filterAuditTimeline(entries, "PROMOTION_LEDGER");
    expect(f).toHaveLength(1);
    expect(f[0]?.source_family).toBe("decision_ledger");
  });

  it("filters broken lineage", () => {
    const f = filterAuditTimeline(entries, "BROKEN_LINEAGE");
    expect(f.some((e) => e.chain_semantic === "BROKEN")).toBe(true);
  });
});

describe("buildForensicDiffs", () => {
  it("emits NO_BASELINE for promotion tail when fewer than two ledger rows", () => {
    const normalized = [
      {
        source_family: "decision_ledger",
        sequence_number: 1,
        status: "A",
        digest_prefix: "x",
        digest_full: null,
        action: "x",
        event_type: "x",
        timestamp: "t",
        timeline_id: "1",
        actor: "a",
        chain_semantic: "CHAINED",
        trust_semantic: "UNKNOWN",
        pass_fail: "PASS",
        issue_count: 0,
        issue_codes: [],
        related_artifact: "r",
        raw: {},
      },
    ] as import("./audit-timeline-model").AuditTimelineEntry[];
    const blocks = buildForensicDiffs(normalized, {}, null, null, null);
    expect(blocks.find((b) => b.id === "promotion-tail")?.baseline).toBe("NO_BASELINE");
  });
});

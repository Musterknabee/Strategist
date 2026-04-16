"use client";

import Link from "next/link";
import type { Route } from "next";
import { useMemo, useState } from "react";
import { AlertTriangle, FileClock, Files, GitBranch, ShieldAlert, TimerReset } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { UiOperatorCommandReceipt, UiPackDetail, WorkItem, WorkbenchItem } from "@/lib/contracts/ui";
import { useDomainBoundary } from "@/features/shared/domain-boundary-provider";
import { derivePackReceiptCorrelation } from "@/features/control-plane/pack-correlation";

const TABS = [
  { key: "overview", label: "Overview", icon: ShieldAlert },
  { key: "timeline", label: "Timeline", icon: FileClock },
  { key: "assignment", label: "Assignment", icon: GitBranch },
  { key: "lease", label: "Lease", icon: TimerReset },
  { key: "escalation", label: "Escalation", icon: AlertTriangle },
  { key: "evidence", label: "Evidence", icon: Files },
] as const;

type TabKey = (typeof TABS)[number]["key"];

type PackDetailPanelProps = {
  selected: WorkItem | null;
  pack?: WorkbenchItem | null;
  detail?: UiPackDetail;
  receipt?: UiOperatorCommandReceipt | null;
  onCommand: (action: string) => void;
  actionsFrozen?: boolean;
  embedded?: boolean;
};

function EmptyPackState() {
  return (
    <Card className="border-zinc-800 bg-zinc-900">
      <CardHeader>
        <CardTitle className="text-base">Pack detail</CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-zinc-400">
        Select a work item to inspect timeline, assignment, lease, escalation, and evidence projections.
      </CardContent>
    </Card>
  );
}


function TabEmptyGuidance({ title, message, guidance }: { title: string; message: string; guidance: string[] }) {
  return (
    <Card className="border-zinc-800 bg-zinc-900">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm text-zinc-200">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-sm text-zinc-400">{message}</div>
        <ul className="space-y-2 text-sm text-zinc-300">
          {guidance.map((item) => (
            <li key={item}>• {item}</li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

function ReceiptCorrelationCard({ detail, pack, receipt }: { detail?: UiPackDetail; pack?: WorkbenchItem | null; receipt?: UiOperatorCommandReceipt | null }) {
  const correlation = derivePackReceiptCorrelation(receipt, detail, pack);
  if (!correlation) return null;
  const tone = correlation.status === "pending_projection"
    ? "border-amber-500/30 bg-amber-500/10 text-amber-200"
    : "border-emerald-500/30 bg-emerald-500/10 text-emerald-200";

  return (
    <Card className={`border ${tone}`}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm">{correlation.title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div>{correlation.message}</div>
        <ul className="space-y-2 text-sm">
          {correlation.recommended_actions.map((item) => (
            <li key={item}>• {item}</li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

function ListSection({ title, items, fallback }: { title: string; items?: Array<Record<string, unknown>>; fallback: string }) {
  return (
    <Card className="border-zinc-800 bg-zinc-900">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm text-zinc-200">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items && items.length ? (
          items.map((item, idx) => (
            <div key={idx} className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4 text-sm text-zinc-300">
              <pre className="overflow-x-auto whitespace-pre-wrap break-words text-[11px] leading-5 text-zinc-300">{JSON.stringify(item, null, 2)}</pre>
            </div>
          ))
        ) : (
          <div className="text-sm text-zinc-500">{fallback}</div>
        )}
      </CardContent>
    </Card>
  );
}

function OverviewTab({ selected, pack, detail, receipt, onCommand, actionsFrozen }: PackDetailPanelProps) {
  const { canPerformAction, operatorRole } = useDomainBoundary();
  return (
    <div className="space-y-4">
      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader>
          <CardTitle className="text-base">{selected?.review_target ?? pack?.pack_kind ?? "Pack overview"}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-sm text-zinc-400">{selected?.summary_line ?? pack?.summary_line ?? "No selected summary available."}</div>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-2xl border border-zinc-800 p-3 text-sm text-zinc-300">Queue: {selected?.queue_key ?? "n/a"}</div>
            <div className="rounded-2xl border border-zinc-800 p-3 text-sm text-zinc-300">Owner lane: {selected?.action_owner_lane ?? "n/a"}</div>
            <div className="rounded-2xl border border-zinc-800 p-3 text-sm text-zinc-300">Trust: {pack?.trust_status ?? "unclassified"}</div>
            <div className="rounded-2xl border border-zinc-800 p-3 text-sm text-zinc-300">Generated: {pack?.generated_at_utc ?? detail?.generated_at_utc ?? "n/a"}</div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button disabled={actionsFrozen || !canPerformAction("claim-item")} onClick={() => onCommand("claim-item")}>Claim item</Button>
            <Button variant="outline" className="border-zinc-700 bg-transparent" disabled={actionsFrozen || !canPerformAction("acknowledge-reentry")} onClick={() => onCommand("acknowledge-reentry")}>Acknowledge re-entry</Button>
            <Button variant="outline" className="border-zinc-700 bg-transparent" disabled={actionsFrozen || !canPerformAction("renew-lease")} onClick={() => onCommand("renew-lease")}>Renew lease</Button>
            {pack?.pack_kind ? (
              <Button asChild variant="ghost" className="rounded-xl">
                <Link href={`/packs/${encodeURIComponent(pack.pack_kind)}` as Route}>Open full pack page</Link>
              </Button>
            ) : null}
          </div>
          {(!canPerformAction("claim-item") && !canPerformAction("acknowledge-reentry") && !canPerformAction("renew-lease")) ? (
            <div className="rounded-2xl border border-zinc-700 bg-zinc-950/70 p-3 text-sm text-zinc-300">
              The active <span className="text-zinc-100">{operatorRole}</span> persona is read-only for control-plane commands.
            </div>
          ) : null}
          {actionsFrozen ? (
            <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-200">
              Operator commands are frozen because the read-plane is stale. Refresh the pack projection before issuing actions.
            </div>
          ) : null}
          {receipt ? (
            <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-200">
              <div className="font-medium">{receipt.summary_line}</div>
              <div className="mt-1 text-emerald-300/90">{receipt.operator_message}</div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <ListSection title="Command hints" items={detail?.command_hints?.map((hint) => ({ hint }))} fallback="No command hints projected for this pack." />
        <ListSection title="Pack outputs" items={(pack?.output_artifact_paths ?? []).map((path, idx) => ({ label: pack?.output_artifact_labels?.[idx] ?? `artifact_${idx + 1}`, path }))} fallback="No projected output artifacts for this pack." />
      </div>
      <ReceiptCorrelationCard detail={detail} pack={pack} receipt={receipt} />
    </div>
  );
}

function EvidenceTab({ pack, detail }: { pack?: WorkbenchItem | null; detail?: UiPackDetail }) {
  const navigationItems = detail?.navigation?.items ?? [];
  const artifactItems = (pack?.output_artifact_paths ?? []).map((path, idx) => ({
    artifact_label: pack?.output_artifact_labels?.[idx] ?? `artifact_${idx + 1}`,
    artifact_path: path,
  }));
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      {artifactItems.length ? (
        <ListSection title="Evidence artifacts" items={artifactItems} fallback="No output artifacts were projected for this pack." />
      ) : (
        <TabEmptyGuidance title="Evidence guidance" message="No evidence artifacts have been projected for this pack yet." guidance={["Check whether the pack has reached a stage that emits manifests or downstream outputs.", "Use review packet export to preserve current operator context while evidence catches up.", "Hold evidence-backed decisions until artifact paths appear in the projection lane."]} />
      )}
      {navigationItems.length ? (
        <ListSection title="Navigation / lineage hints" items={navigationItems} fallback="No navigation lineage hints were projected for this pack." />
      ) : (
        <TabEmptyGuidance title="Lineage guidance" message="No navigation or lineage hints were projected for this pack." guidance={["Open the evidence explorer if broader lineage context is needed immediately.", "Refresh the pack detail projection before relying on missing lineage state.", "Attach operator notes in a review packet if lineage absence affects adjudication."]} />
      )}
    </div>
  );
}

export function PackDetailPanel({ selected, pack, detail, receipt, onCommand, actionsFrozen = false, embedded = false }: PackDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<TabKey>("overview");

  const tabContent = useMemo(() => {
    if (!selected && !pack && !detail) return <EmptyPackState />;
    switch (activeTab) {
      case "timeline":
        return detail?.timeline?.items?.length ? (
          <div className="space-y-4">
            <ReceiptCorrelationCard detail={detail} pack={pack} receipt={receipt} />
            <ListSection title="Timeline" items={detail?.timeline?.items} fallback="No timeline projection available for this pack." />
          </div>
        ) : <TabEmptyGuidance title="Timeline guidance" message="No timeline projection was emitted for this pack." guidance={["Refresh the pack workbench projection and timeline read-plane.", "Check whether the pack has progressed far enough to emit timeline checkpoints.", "Export a review packet if the absence of timeline state needs operator escalation."]} />;
      case "assignment":
        return detail?.assignment?.items?.length ? <ListSection title="Assignment" items={detail?.assignment?.items} fallback="No assignment projection available for this pack." /> : <TabEmptyGuidance title="Assignment guidance" message="No assignment projection is currently attached to this pack." guidance={["Verify that the pack has been claimed or routed into an owner lane.", "Use the command receipt lane to confirm whether a prior claim action was accepted.", "Keep the pack in observation mode until assignment posture refreshes."]} />;
      case "lease":
        return (
          <div className="grid gap-4 xl:grid-cols-2">
            {detail?.claim_lease?.items?.length ? <ListSection title="Claim lease" items={detail?.claim_lease?.items} fallback="No claim lease projection available for this pack." /> : <TabEmptyGuidance title="Lease guidance" message="No active claim lease projection is available for this pack." guidance={["Confirm whether the pack has ever been claimed in the current operator session.", "Avoid lease-renew commands until the read-plane refreshes and a lease object is visible.", "Escalate persistent lease absence if command receipts suggest accepted claim activity."]} />}
            {detail?.claim_lifecycle?.items?.length ? <ListSection title="Claim lifecycle" items={detail?.claim_lifecycle?.items} fallback="No claim lifecycle projection available for this pack." /> : <TabEmptyGuidance title="Lifecycle guidance" message="No claim lifecycle milestones have been projected yet." guidance={["Wait for the next projection cycle to materialize lifecycle markers.", "Use command receipts as temporary operator evidence until lifecycle state catches up.", "Export a review packet when the missing lifecycle state blocks adjudication."]} />}
          </div>
        );
      case "escalation":
        return detail?.escalation?.items?.length ? <ListSection title="Escalation" items={detail?.escalation?.items} fallback="No escalation projection available for this pack." /> : <TabEmptyGuidance title="Escalation guidance" message="No escalation packet is attached to this pack." guidance={["Treat the pack as non-escalated until an SLA, freeze-release, or instability signal appears.", "Review operator guidance cards before escalating manually.", "Capture a review packet if missing escalation context affects a handoff."]} />;
      case "evidence":
        return <EvidenceTab pack={pack} detail={detail} />;
      case "overview":
      default:
        return <OverviewTab selected={selected} pack={pack} detail={detail} receipt={receipt} onCommand={onCommand} actionsFrozen={actionsFrozen} embedded={embedded} />;
    }
  }, [activeTab, actionsFrozen, detail, onCommand, pack, receipt, selected, embedded]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2 rounded-2xl border border-zinc-800 bg-zinc-900 p-2">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const active = tab.key === activeTab;
          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              className={active ? "inline-flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300" : "inline-flex items-center gap-2 rounded-xl border border-transparent px-3 py-2 text-sm text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100"}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>
      {pack ? (
        <div className="flex flex-wrap gap-2">
          <Badge>{pack.pack_kind}</Badge>
          {pack.trust_status ? <Badge>{pack.trust_status}</Badge> : null}
          {pack.manifest_path ? <Badge className="max-w-full truncate">manifest: {pack.manifest_path}</Badge> : null}
        </div>
      ) : null}
      {tabContent}
    </div>
  );
}

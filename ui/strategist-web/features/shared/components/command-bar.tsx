"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ArrowUpRight, Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useDomainBoundary } from "@/features/shared/domain-boundary-provider";
import { useRuntimeStatus } from "@/features/shared/hooks/use-runtime-status";
import { useCommandReceiptLane } from "@/features/shared/command-receipts/command-receipt-lane-provider";
import { useReviewPacketLane } from "@/features/shared/review-packets/review-packet-lane-provider";
import { filterCommandBarActions, getVisibleCommandBarActions } from "@/features/shared/command-bar-actions";

function jumpToLane(anchorId: string) {
  document.getElementById(anchorId)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

export function CommandBar() {
  const router = useRouter();
  const pathname = usePathname();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const { data } = useRuntimeStatus();
  const domainBoundary = useDomainBoundary();
  const redactedDomains = domainBoundary.redactedDomains ?? [];
  const allowedDomains = domainBoundary.allowedDomains ?? [];
  const {
    receipts,
    inspectedReceiptId,
    isLaneOpen: isReceiptLaneOpen,
    setLaneOpen: setReceiptLaneOpen,
    inspectReceipt,
  } = useCommandReceiptLane();
  const {
    packets,
    inspectedPacketId,
    isLaneOpen: isReviewLaneOpen,
    setLaneOpen: setReviewLaneOpen,
    inspectPacket,
  } = useReviewPacketLane();
  const [query, setQuery] = useState("");

  const latestReceipt = receipts[0];
  const latestPacket = packets[0];

  const visibleActions = useMemo(
    () => getVisibleCommandBarActions(allowedDomains),
    [allowedDomains],
  );
  const filteredActions = useMemo(
    () => filterCommandBarActions(visibleActions, query).slice(0, 6),
    [visibleActions, query],
  );

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        inputRef.current?.focus();
      }
      if (event.key === "/" && document.activeElement !== inputRef.current) {
        const activeTag = (document.activeElement as HTMLElement | null)?.tagName;
        if (activeTag !== "INPUT" && activeTag !== "TEXTAREA") {
          event.preventDefault();
          inputRef.current?.focus();
        }
      }
      if (event.key === "Escape" && document.activeElement === inputRef.current) {
        inputRef.current?.blur();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const runAction = (actionId: string) => {
    switch (actionId) {
      case "route-workboard":
        router.push("/workboard");
        break;
      case "route-burnin":
        router.push("/validator/burn-in");
        break;
      case "route-forensic":
        router.push("/validator/forensic");
        break;
      case "route-providers":
        router.push("/validator/providers");
        break;
      case "route-tribunal":
        router.push("/tribunal");
        break;
      case "route-evidence":
        router.push("/evidence");
        break;
      case "route-settings-overview":
        router.push("/settings");
        break;
      case "route-setup-checklist":
        router.push("/settings/checklist");
        break;
      case "route-quick-actions":
        router.push("/settings/quick-actions");
        break;
      case "route-diagnostics-runbook":
        router.push("/settings/runbook");
        break;
      case "route-runtime-diagnostics":
        router.push("/settings/runtime");
        break;
      case "route-frontend-preflight":
        router.push("/settings/preflight");
        break;
      case "route-diagnostics-export":
        router.push("/settings/export");
        break;
      case "route-diagnostics-history":
        router.push("/settings/history");
        break;
      case "route-diagnostics-latest":
        router.push("/settings/latest");
        break;
      case "route-diagnostics-summary":
        router.push("/settings/summary");
        break;
      case "route-diagnostics-trends":
        router.push("/settings/trends");
        break;
      case "route-diagnostics-compare":
        router.push("/settings/compare");
        break;
      case "route-diagnostics-status-board":
        router.push("/settings/status-board");
        break;
      case "route-diagnostics-recommendations":
        router.push("/settings/recommendations");
        break;
      case "route-diagnostics-action-queue":
        router.push("/settings/action-queue");
        break;
      case "route-diagnostics-escalation-matrix":
        router.push("/settings/escalation-matrix");
        break;
      case "route-diagnostics-incident-playbook":
        router.push("/settings/incident-playbook");
        break;
      case "route-diagnostics-recovery-scorecard":
        router.push("/settings/recovery-scorecard");
        break;
      case "route-diagnostics-readiness-gate":
        router.push("/settings/readiness-gate");
        break;
      case "route-diagnostics-decision-log":
        router.push("/settings/decision-log");
        break;
      case "route-diagnostics-handoff-packet":
        router.push("/settings/handoff-packet");
        break;
      case "route-diagnostics-checkpoint-register":
        router.push("/settings/checkpoint-register");
        break;
      case "shell-open-latest-receipt":
        setReceiptLaneOpen(true);
        if (latestReceipt) inspectReceipt(latestReceipt.command_id);
        jumpToLane("command-receipt-lane");
        break;
      case "shell-open-latest-packet":
        setReviewLaneOpen(true);
        if (latestPacket) inspectPacket(latestPacket.packet_id);
        jumpToLane("review-packet-lane");
        break;
      case "shell-toggle-receipts":
        setReceiptLaneOpen(!isReceiptLaneOpen);
        jumpToLane("command-receipt-lane");
        break;
      case "shell-toggle-packets":
        setReviewLaneOpen(!isReviewLaneOpen);
        jumpToLane("review-packet-lane");
        break;
      default:
        break;
    }
    setQuery("");
  };

  return (
    <div className="space-y-3 rounded-2xl border border-zinc-800 bg-zinc-900/80 px-4 py-3">
      <div className="flex flex-wrap items-center gap-3">
        <label className="flex min-w-[260px] flex-1 items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-400">
          <Search className="h-4 w-4" />
          <input
            ref={inputRef}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search routes, queues, doctrine, artifacts, or shell actions…"
            className="w-full bg-transparent text-sm text-zinc-100 outline-none placeholder:text-zinc-500"
            aria-label="Command bar search"
          />
          <span className="rounded-md border border-zinc-800 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-zinc-500">
            ⌘/Ctrl+K
          </span>
        </label>
        {data?.command_bar.allowed_actions.length ? (
          data.command_bar.allowed_actions.map((action) => <Badge key={action}>{action}</Badge>)
        ) : (
          <Badge className="border-zinc-700 bg-zinc-950 text-zinc-300">read-only persona</Badge>
        )}
        {redactedDomains.map((domain) => (
          <Badge key={domain} className="border-amber-500/30 bg-amber-500/10 text-amber-300">
            {domain} redacted
          </Badge>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-zinc-800 bg-zinc-950/60 px-3 py-2">
        <span className="text-xs uppercase tracking-[0.18em] text-zinc-500">shell lanes</span>
        <Button
          type="button"
          variant={isReceiptLaneOpen ? "default" : "outline"}
          className={isReceiptLaneOpen ? "h-8 rounded-full" : "h-8 rounded-full border-zinc-700 bg-transparent"}
          onClick={() => setReceiptLaneOpen(!isReceiptLaneOpen)}
        >
          {isReceiptLaneOpen ? "Hide receipts" : "Show receipts"}
        </Button>
        <Badge className="border-zinc-700 bg-zinc-900 text-zinc-300">{receipts.length} receipts</Badge>
        {inspectedReceiptId ? (
          <>
            <Badge className="border-sky-500/30 bg-sky-500/10 text-sky-300">focused receipt {inspectedReceiptId.slice(0, 10)}… {isReceiptLaneOpen ? "(open)" : "(collapsed)"}</Badge>
            <Button
              type="button"
              variant="outline"
              className="h-8 rounded-full border-zinc-700 bg-transparent"
              onClick={() => inspectReceipt(null)}
            >
              Clear receipt focus
            </Button>
          </>
        ) : null}
        <Button
          type="button"
          variant="outline"
          className="h-8 rounded-full border-zinc-700 bg-transparent"
          onClick={() => {
            setReceiptLaneOpen(true);
            if (latestReceipt) inspectReceipt(latestReceipt.command_id);
            jumpToLane("command-receipt-lane");
          }}
        >
          Open latest receipt
        </Button>

        <Button
          type="button"
          variant={isReviewLaneOpen ? "default" : "outline"}
          className={isReviewLaneOpen ? "h-8 rounded-full" : "h-8 rounded-full border-zinc-700 bg-transparent"}
          onClick={() => setReviewLaneOpen(!isReviewLaneOpen)}
        >
          {isReviewLaneOpen ? "Hide review packets" : "Show review packets"}
        </Button>
        <Badge className="border-zinc-700 bg-zinc-900 text-zinc-300">{packets.length} packets</Badge>
        {inspectedPacketId ? (
          <>
            <Badge className="border-sky-500/30 bg-sky-500/10 text-sky-300">focused packet {inspectedPacketId.slice(0, 10)}… {isReviewLaneOpen ? "(open)" : "(collapsed)"}</Badge>
            <Button
              type="button"
              variant="outline"
              className="h-8 rounded-full border-zinc-700 bg-transparent"
              onClick={() => inspectPacket(null)}
            >
              Clear packet focus
            </Button>
          </>
        ) : null}
        <Button
          type="button"
          variant="outline"
          className="h-8 rounded-full border-zinc-700 bg-transparent"
          onClick={() => {
            setReviewLaneOpen(true);
            if (latestPacket) inspectPacket(latestPacket.packet_id);
            jumpToLane("review-packet-lane");
          }}
        >
          Open latest packet
        </Button>
        <span className="ml-auto text-xs text-zinc-500">Lane visibility is URL-backed and shareable. Current route: {pathname}</span>
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-3">
        <div className="mb-2 flex items-center justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">quick actions</div>
            <div className="text-sm text-zinc-400">Filter routes and shell actions from one command surface.</div>
          </div>
          <Badge className="border-zinc-700 bg-zinc-900 text-zinc-300">{filteredActions.length} shown</Badge>
        </div>
        <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
          {filteredActions.map((action) => (
            <button
              key={action.id}
              type="button"
              onClick={() => runAction(action.id)}
              className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-3 text-left transition hover:border-zinc-700 hover:bg-zinc-900"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-medium text-zinc-100">{action.label}</div>
                  <div className="mt-1 text-xs text-zinc-400">{action.description}</div>
                </div>
                <ArrowUpRight className="mt-0.5 h-4 w-4 text-zinc-500" />
              </div>
              <div className="mt-3 flex items-center gap-2">
                <Badge className="border-zinc-700 bg-zinc-950 text-zinc-300">{action.domain}</Badge>
                <Badge className="border-zinc-700 bg-zinc-950 text-zinc-300">{action.kind}</Badge>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

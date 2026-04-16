"use client";

import Link from "next/link";
import type { Route } from "next";
import { ReactNode } from "react";
import { Activity, BarChart3, Files, Gavel, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { CommandBar } from "@/features/shared/components/command-bar";
import { NoDomainAccessState } from "@/features/shared/components/no-domain-access-state";
import { RuntimeStatusRail } from "@/features/shared/components/runtime-status-rail";
import { useDomainBoundary } from "@/features/shared/domain-boundary-provider";
import { CommandReceiptLane } from "@/features/shared/components/command-receipt-lane";
import { ReviewPacketLane } from "@/features/shared/components/review-packet-lane";
import { NotificationLane } from "@/features/shared/components/notification-lane";

const nav = [
  { href: "/workboard", label: "Control Plane", icon: Activity, domain: "control-plane" },
  { href: "/validator/burn-in", label: "Validator", icon: BarChart3, domain: "validator" },
  { href: "/tribunal", label: "Tribunal", icon: Gavel, domain: "tribunal" },
  { href: "/evidence", label: "Evidence", icon: Files, domain: "evidence" },
];

const settingsNav = [
  { href: "/settings", label: "Settings overview" },
  { href: "/settings/runtime", label: "Runtime diagnostics" },
  { href: "/settings/preflight", label: "Frontend preflight" },
  { href: "/settings/checklist", label: "Setup checklist" },
  { href: "/settings/export", label: "Diagnostics export" },
  { href: "/settings/history", label: "Diagnostics history" },
  { href: "/settings/latest", label: "Latest diagnostics snapshot" },
  { href: "/settings/summary", label: "Diagnostics summary" },
  { href: "/settings/trends", label: "Diagnostics trends" },
  { href: "/settings/compare", label: "Latest vs summary" },
  { href: "/settings/status-board", label: "Diagnostics status board" },
  { href: "/settings/recommendations", label: "Diagnostics recommendations" },
  { href: "/settings/action-queue", label: "Diagnostics action queue" },
  { href: "/settings/escalation-matrix", label: "Diagnostics escalation matrix" },
  { href: "/settings/incident-playbook", label: "Diagnostics incident playbook" },
  { href: "/settings/recovery-scorecard", label: "Diagnostics recovery scorecard" },
  { href: "/settings/readiness-gate", label: "Diagnostics readiness gate" },
  { href: "/settings/decision-log", label: "Diagnostics decision log" },
  { href: "/settings/handoff-packet", label: "Diagnostics handoff packet" },
  { href: "/settings/checkpoint-register", label: "Diagnostics checkpoint register" },
  { href: "/settings/certification-manifest", label: "Diagnostics certification manifest" },
  { href: "/settings/release-candidate-dossier", label: "Diagnostics release-candidate dossier" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const { operatorRole, canAccessDomain, redactedDomains, allowedDomains } = useDomainBoundary();

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="grid min-h-screen grid-cols-[260px_1fr]">
        <aside className="border-r border-zinc-800 bg-zinc-950/90 px-4 py-6">
          <div className="mb-8 flex items-center gap-3 px-2">
            <div className="rounded-2xl bg-emerald-500/15 p-2 text-emerald-300">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <div className="text-sm font-semibold tracking-wide text-zinc-100">Strategist</div>
              <div className="text-xs text-zinc-400">Institutional Adjudication UI</div>
            </div>
          </div>

          <div className="mb-6 rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
            <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">Runtime</div>
            <div className="mt-2 flex items-center justify-between"><span className="text-sm text-zinc-300">Persona</span><Badge>{operatorRole}</Badge></div>
            <div className="mt-2 flex items-center justify-between"><span className="text-sm text-zinc-300">Write Law</span><Badge className="border-emerald-500/30 bg-emerald-500/10 text-emerald-300">Command only</Badge></div>
            <div className="mt-2 flex items-center justify-between"><span className="text-sm text-zinc-300">Read Law</span><Badge>Projection-backed</Badge></div>
          </div>

          <nav className="space-y-1">
            {nav.map((item) => {
              if (!canAccessDomain(item.domain)) {
                return null;
              }
              const Icon = item.icon;
              return (
                <Link key={item.href} href={item.href as Route} className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-zinc-300 transition hover:bg-zinc-800 hover:text-white">
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {!allowedDomains.length ? (
            <div className="mt-6 rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4 text-xs text-amber-200">
              No governed routes are currently available for this persona.
            </div>
          ) : null}

          <div className="mt-6 border-t border-zinc-800 pt-4">
            <div className="px-4 pb-2 text-xs uppercase tracking-[0.18em] text-zinc-500">Settings</div>
            {settingsNav.map((item) => (
              <Link key={item.href} href={item.href as Route} className="mt-1 flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-zinc-300 transition hover:bg-zinc-800 hover:text-white">
                <ShieldCheck className="h-4 w-4" />
                <span>{item.label}</span>
              </Link>
            ))}
          </div>

          {redactedDomains.length ? (
            <div className="mt-6 rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4 text-xs text-amber-200">
              Redacted domains: {redactedDomains.join(", ")}
            </div>
          ) : null}
        </aside>

        <main className="flex min-h-screen flex-col">
          <header className="sticky top-0 z-20 border-b border-zinc-800 bg-zinc-950/90 backdrop-blur">
            <div className="flex items-center justify-between px-8 py-4">
              <div>
                <div className="text-sm font-medium text-zinc-100">Strategist Control Surface</div>
                <div className="text-xs text-zinc-400">Projection-backed, command-gated, audit-visible</div>
              </div>
              <div className="flex items-center gap-3">
                <Badge className="border-amber-500/30 bg-amber-500/10 text-amber-300">Tribunal blindness enforced</Badge>
                <Badge>{operatorRole}</Badge>
              </div>
            </div>
            <RuntimeStatusRail />
          </header>

          <div className="flex-1 px-8 py-8">
            <div className="mb-6">
              <CommandBar />
            </div>
            <NotificationLane />
            <CommandReceiptLane />
            <ReviewPacketLane />
            {allowedDomains.length ? children : <NoDomainAccessState />}
          </div>
        </main>
      </div>
    </div>
  );
}

import { ReactNode } from "react";
import Link from "next/link";
import type { Route } from "next";

import { Badge } from "@/components/ui/badge";

const nav = [
  { href: "/settings", label: "Overview" },
  { href: "/settings/runtime", label: "Runtime diagnostics" },
  { href: "/settings/preflight", label: "Frontend preflight" },
  { href: "/settings/checklist", label: "Setup checklist" },
  { href: "/settings/quick-actions", label: "Quick actions" },
  { href: "/settings/runbook", label: "Runbook" },
  { href: "/settings/export", label: "Diagnostics export" },
  { href: "/settings/history", label: "Diagnostics history" },
  { href: "/settings/latest", label: "Latest snapshot" },
  { href: "/settings/summary", label: "Summary" },
  { href: "/settings/trends", label: "Trends" },
  { href: "/settings/compare", label: "Compare" },
  { href: "/settings/status-board", label: "Status board" },
  { href: "/settings/recommendations", label: "Recommendations" },
  { href: "/settings/action-queue", label: "Action queue" },
  { href: "/settings/escalation-matrix", label: "Escalation matrix" },
  { href: "/settings/incident-playbook", label: "Incident playbook" },
  { href: "/settings/recovery-scorecard", label: "Recovery scorecard" },
  { href: "/settings/readiness-gate", label: "Readiness gate" },
  { href: "/settings/decision-log", label: "Decision log" },
  { href: "/settings/handoff-packet", label: "Handoff packet" },
  { href: "/settings/checkpoint-register", label: "Checkpoint register" },
  { href: "/settings/certification-manifest", label: "Certification manifest" },
  { href: "/settings/release-candidate-dossier", label: "Release-candidate dossier" },
];

export default function SettingsLayout({ children }: { children: ReactNode }) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">settings</div>
          <h1 className="mt-2 text-2xl font-semibold text-zinc-100">Console diagnostics</h1>
          <p className="mt-1 text-sm text-zinc-400">Bring-up, runtime, and preflight surfaces for validating the Strategist web shell locally.</p>
        </div>
        <Badge className="border-zinc-700 bg-zinc-900 text-zinc-300">read-plane only</Badge>
      </div>
      <div className="flex flex-wrap gap-2">
        {nav.map((item) => (
          <Link key={item.href} href={item.href as Route} className="rounded-full border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
            {item.label}
          </Link>
        ))}
      </div>
      {children}
    </div>
  );
}

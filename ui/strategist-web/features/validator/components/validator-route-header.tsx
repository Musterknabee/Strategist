"use client";

import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const tabs = [
  { href: "/validator/burn-in", label: "Overview" },
  { href: "/validator/forensic", label: "Forensic" },
  { href: "/validator/providers", label: "Provider health" },
];

export function ValidatorRouteHeader({
  title,
  description,
  posture,
  rightSlot,
}: {
  title: string;
  description: string;
  posture: string;
  rightSlot?: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <Card>
      <CardHeader className="gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <Badge>{posture}</Badge>
            <Badge className="border-cyan-500/30 bg-cyan-500/10 text-cyan-200">validator domain</Badge>
          </div>
          <CardTitle>{title}</CardTitle>
          <div className="mt-2 text-sm text-zinc-400">{description}</div>
        </div>
        <div className="flex flex-wrap items-center gap-2">{rightSlot}</div>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {tabs.map((tab) => {
            const active = pathname === tab.href;
            return (
              <Link
                key={tab.href}
                href={tab.href as Route}
                className={cn(
                  "rounded-2xl border px-3 py-2 text-sm transition",
                  active
                    ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"
                    : "border-zinc-800 bg-zinc-950/70 text-zinc-300 hover:bg-zinc-900"
                )}
              >
                {tab.label}
              </Link>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

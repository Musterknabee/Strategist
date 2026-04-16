"use client";

import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useDomainBoundary } from "@/features/shared/domain-boundary-provider";

export function NoDomainAccessState() {
  const { operatorRole } = useDomainBoundary();

  return (
    <Card className="border-amber-500/20 bg-amber-500/5">
      <CardHeader>
        <CardTitle className="text-zinc-100">No governed domains available</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-zinc-300">
        <p>The active <span className="font-medium text-zinc-100">{operatorRole}</span> persona currently has no accessible console domains.</p>
        <p>Switch personas from the runtime rail, confirm runtime policy hydration, or return to the landing page while projections and policy are refreshed.</p>
        <div className="flex flex-wrap gap-2 pt-1">
          <Button asChild className="rounded-xl">
            <Link href="/">Return to landing</Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

"use client";

import { ReactNode } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { NoDomainAccessState } from "@/features/shared/components/no-domain-access-state";
import { useDomainBoundary } from "@/features/shared/domain-boundary-provider";

export function DomainPolicyGate({
  domain,
  title,
  children,
}: {
  domain: string;
  title: string;
  children: ReactNode;
}) {
  const { canAccessDomain, operatorRole, allowedDomains } = useDomainBoundary();
  const visibleDomains = Array.isArray(allowedDomains) ? allowedDomains : null;

  if (visibleDomains && !visibleDomains.length) {
    return <NoDomainAccessState />;
  }

  if (canAccessDomain(domain)) {
    return <>{children}</>;
  }

  return (
    <Card className="border-zinc-800 bg-zinc-900">
      <CardHeader>
        <CardTitle>{title} restricted</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm text-zinc-400">
        <p>This domain is redacted for the active <span className="text-zinc-100">{operatorRole}</span> persona.</p>
        <p>Switch roles from the runtime status rail to view this governed surface, if your operating context permits it.</p>
      </CardContent>
    </Card>
  );
}

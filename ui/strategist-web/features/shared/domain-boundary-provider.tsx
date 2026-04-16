"use client";

import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";

export type PersonaRole = "operator" | "validator" | "tribunal";

type DomainBoundaryState = {
  blindnessMode: "enforced";
  operatorRole: PersonaRole;
  setOperatorRole: (role: PersonaRole) => void;
  allowedDomains: string[];
  redactedDomains: string[];
  allowedActions: string[];
  setPolicy: (policy: {
    allowedDomains?: string[];
    redactedDomains?: string[];
    allowedActions?: string[];
    allowed_domains?: string[];
    redacted_domains?: string[];
    allowed_actions?: string[];
  }) => void;
  canAccessDomain: (domain: string) => boolean;
  canPerformAction: (action: string) => boolean;
};

const STORAGE_KEY = "strategist-ui-role";

const DomainBoundaryContext = createContext<DomainBoundaryState>({
  blindnessMode: "enforced",
  operatorRole: "operator",
  setOperatorRole: () => undefined,
  allowedDomains: ["control-plane", "validator", "evidence", "tribunal"],
  redactedDomains: [],
  allowedActions: ["claim-item", "acknowledge-reentry", "renew-lease"],
  setPolicy: () => undefined,
  canAccessDomain: () => true,
  canPerformAction: () => true,
});

export function DomainBoundaryProvider({ children }: { children: ReactNode }) {
  const [operatorRole, setOperatorRoleState] = useState<PersonaRole>("operator");
  const [allowedDomains, setAllowedDomains] = useState<string[]>(["control-plane", "validator", "evidence", "tribunal"]);
  const [redactedDomains, setRedactedDomains] = useState<string[]>([]);
  const [allowedActions, setAllowedActions] = useState<string[]>(["claim-item", "acknowledge-reentry", "renew-lease"]);

  useEffect(() => {
    const persisted = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : null;
    if (persisted === "operator" || persisted === "validator" || persisted === "tribunal") {
      setOperatorRoleState(persisted);
    }
  }, []);

  const setOperatorRole = (role: PersonaRole) => {
    setOperatorRoleState(role);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, role);
    }
  };

  const setPolicy = (policy: {
    allowedDomains?: string[];
    redactedDomains?: string[];
    allowedActions?: string[];
    allowed_domains?: string[];
    redacted_domains?: string[];
    allowed_actions?: string[];
  }) => {
    setAllowedDomains(policy.allowedDomains ?? policy.allowed_domains ?? ["control-plane", "validator", "evidence", "tribunal"]);
    setRedactedDomains(policy.redactedDomains ?? policy.redacted_domains ?? []);
    setAllowedActions(policy.allowedActions ?? policy.allowed_actions ?? []);
  };

  const value = useMemo<DomainBoundaryState>(() => ({
    blindnessMode: "enforced",
    operatorRole,
    setOperatorRole,
    allowedDomains,
    redactedDomains,
    allowedActions,
    setPolicy,
    canAccessDomain: (domain: string) => allowedDomains.includes(domain),
    canPerformAction: (action: string) => allowedActions.includes(action),
  }), [operatorRole, allowedDomains, redactedDomains, allowedActions]);

  return <DomainBoundaryContext.Provider value={value}>{children}</DomainBoundaryContext.Provider>;
}

export function useDomainBoundary() {
  return useContext(DomainBoundaryContext);
}

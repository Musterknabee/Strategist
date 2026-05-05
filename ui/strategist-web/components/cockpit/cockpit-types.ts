export type StatusTone = "ok" | "warn" | "bad" | "neutral";

export type ProviderRow = Record<string, unknown> & { __id: string };
export type ActionRow = Record<string, unknown> & { __id: string };
export type WorkRow = Record<string, unknown> & { __id: string };
export type StrategyRow = Record<string, unknown> & { __id: string };
export type EvidenceRow = { step: string; status: string; digest: string; time: string; raw: unknown };
export type MatrixRow = {
  checkId: string;
  status: string;
  severity: string;
  blockerCode: string;
  remediation: string;
  raw: unknown;
};

export type OverviewTile = {
  label: string;
  status: string;
  hint: string;
  raw: unknown;
};

export const queryKeys = {
  uiFacade: ["strategist", "ui", "facade"] as const,
  uiWorkboard: (boardLabel: string) => ["strategist", "ui", "workboard", boardLabel] as const,
  probeHealthz: ["strategist", "probe", "healthz"] as const,
  probeLivez: ["strategist", "probe", "livez"] as const,
  probeReadyz: ["strategist", "probe", "readyz"] as const,
  probeApiRoot: ["strategist", "probe", "api-root"] as const,
  uiHealth: ["strategist", "ui", "health"] as const,
  uiEvidence: (searchRoot: string | undefined) => ["strategist", "ui", "evidence", searchRoot ?? ""] as const,
  uiOperatorActions: ["strategist", "ui", "operator-actions"] as const,
  uiProviderHealth: ["strategist", "ui", "provider-health"] as const,
  uiResearchCompute: ["strategist", "ui", "research-compute"] as const,
  uiRuntime: (role: string) => ["strategist", "ui", "runtime", role] as const,
};

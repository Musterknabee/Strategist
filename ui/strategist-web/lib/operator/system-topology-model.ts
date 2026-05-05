/**
 * Read-only system topology / dependency map derived from checked-in contracts and registries only.
 * Does not infer live routes, builders, or CI gates beyond curated mappings.
 */
import type { UiFacadeRoute } from "@/lib/api/types";
import { LOCAL_OPS_COMMAND_REGISTRY } from "@/lib/operator/local-ops-command-hints";
import { asBool, asString } from "@/lib/operator/payload-utils";

export type TopologyNodeType =
  | "FRONTEND_PANE"
  | "FRONTEND_HOOK"
  | "BACKEND_ROUTE"
  | "APPLICATION_BUILDER"
  | "CLI_COMMAND"
  | "EVIDENCE_ARTIFACT"
  | "PROVIDER"
  | "CI_GATE"
  | "AUTHORITY_BOUNDARY"
  | "SNAPSHOT"
  | "DOC";

export type TopologySafetyClass = "READ_PLANE" | "MUTATION_AUTH" | "EXPORT" | "METADATA" | "ADVISORY" | "PROBE" | "UNKNOWN";

export type TopologyNodeStatus = "OK" | "UNKNOWN" | "DEGRADED" | "PENDING";

export type TopologyNode = {
  node_id: string;
  node_type: TopologyNodeType;
  label: string;
  status: TopologyNodeStatus;
  source_file_or_endpoint: string;
  related_nodes: string[];
  safety_class: TopologySafetyClass;
  evidence_digest_prefix: string;
  raw?: Record<string, unknown>;
};

export type FacadeRoutesContract = {
  schema_version: string;
  route_count: number;
  routes_sha256: string;
  routes: UiFacadeRoute[];
};

export type SystemTopologyInput = {
  /** Checked-in UI facade route contract (null if unavailable — routes section stays UNKNOWN). */
  contract: FacadeRoutesContract | null;
  /** GET /ui/facade payload when loaded (optional inventory overlay). */
  facadePayload: Record<string, unknown> | null;
  /** Keys match `CockpitPaneLink.pane_key`; true = degraded read-plane for that pane. */
  paneDegraded: Record<string, boolean>;
};

/** Curated home-cockpit panes: hooks and primary JSON endpoints (probes listed separately). */
export type CockpitPaneLink = {
  pane_key: string;
  title: string;
  testid?: string;
  component_file: string;
  hooks: string[];
  /** Primary GET /ui/* or probe paths consumed by the shell for this pane. */
  endpoints: string[];
  degraded_hint: string;
};

export const COCKPIT_HOME_PANE_LINKS: CockpitPaneLink[] = [
  {
    pane_key: "overview",
    title: "Overview",
    testid: "cockpit-seven-pane-grid",
    component_file: "ui/strategist-web/components/cockpit/OverviewPane.tsx",
    hooks: ["useUiFacade", "useProbeHealthz", "useProbeReadyz", "useUiEvidence", "useUiOperatorActions", "useUiWorkboard"],
    endpoints: ["/healthz", "/readyz", "/ui/facade", "/ui/evidence", "/ui/operator-actions", "/ui/workboard"],
    degraded_hint: "Inspect /readyz blockers, GET /ui/evidence, and GET /ui/facade readiness flags.",
  },
  {
    pane_key: "readiness-matrix",
    title: "Readiness Matrix",
    component_file: "ui/strategist-web/components/cockpit/ReadinessMatrixPane.tsx",
    hooks: ["useProbeReadyz (via CockpitPageShell)", "useReadinessDeployment"],
    endpoints: ["/readyz", "/readiness/deployment"],
    degraded_hint: "Compare /readyz vs GET /readiness/deployment checks and deployment tier codes.",
  },
  {
    pane_key: "evidence-chain",
    title: "Evidence Chain",
    testid: "cockpit-evidence-chain-pane",
    component_file: "ui/strategist-web/components/cockpit/EvidenceChainPane.tsx",
    hooks: ["useUiEvidenceChain"],
    endpoints: ["/ui/evidence-chain"],
    degraded_hint: "Verify GET /ui/evidence-chain and ledger DB connectivity from API host.",
  },
  {
    pane_key: "operator-health-alerts",
    title: "Operator health / alerts",
    testid: "cockpit-operator-health-alerts",
    component_file: "ui/strategist-web/components/cockpit/OperatorHealthAlertsPane.tsx",
    hooks: [
      "useProbeHealthz",
      "useProbeLivez",
      "useProbeReadyz",
      "useUiRuntime",
      "useUiEvidence",
      "useUiEvidenceChain",
      "useUiProviderSetup",
      "useUiProviderHealth",
      "useUiFacade",
      "useUiResearchOsReleaseReadinessLatest",
      "useUiResearchOsDriftLatest",
      "useUiPaperExecutionCockpit",
      "useUiPaperBrokerStatus",
    ],
    endpoints: [
      "/healthz",
      "/livez",
      "/readyz",
      "/ui/runtime",
      "/ui/evidence",
      "/ui/evidence-chain",
      "/ui/provider-setup",
      "/ui/provider-health",
      "/ui/facade",
      "/ui/research-os/release-readiness/latest",
      "/ui/research-os/drift/latest",
      "/ui/paper-execution/latest",
      "/ui/paper-broker/status",
    ],
    degraded_hint: "Triage failing probe or UI route with smallest surface first (/healthz then /readyz then targeted /ui/*).",
  },
  {
    pane_key: "capital-firewall",
    title: "Capital / execution firewall",
    testid: "cockpit-execution-firewall",
    component_file: "ui/strategist-web/components/cockpit/CapitalExecutionFirewallPane.tsx",
    hooks: [
      "useUiPaperExecutionCockpit",
      "useUiPaperBrokerStatus",
      "useUiPaperTrackingLatest",
      "useUiProviderSetup",
      "useUiProviderHealth",
      "useUiRuntime",
    ],
    endpoints: [
      "/ui/paper-execution/latest",
      "/ui/paper-broker/status",
      "/ui/paper-tracking/latest",
      "/ui/provider-setup",
      "/ui/provider-health",
      "/ui/runtime",
    ],
    degraded_hint: "Check paper execution + broker status read routes; never infer live authority from the browser.",
  },
  {
    pane_key: "remediation-governance",
    title: "Incident / remediation / exceptions",
    testid: "cockpit-remediation-governance",
    component_file: "ui/strategist-web/components/cockpit/RemediationGovernancePane.tsx",
    hooks: [
      "useUiResearchOsExceptionLatest",
      "useUiResearchOsRemediationLatest",
      "useUiResearchOsPolicyGateLatest",
      "useUiResearchOsDriftLatest",
      "useUiResearchOsReleaseReadinessLatest",
      "useUiResearchOsReviewJournalLatest",
      "useProbeReadyz",
      "useReadinessDeployment",
      "useUiProviderSetup",
    ],
    endpoints: [
      "/ui/research-os/exceptions/latest",
      "/ui/research-os/remediation/latest",
      "/ui/research-os/policy-gate/latest",
      "/ui/research-os/drift/latest",
      "/ui/research-os/release-readiness/latest",
      "/ui/research-os/review-journal/latest",
      "/readyz",
      "/readiness/deployment",
      "/ui/provider-setup",
    ],
    degraded_hint: "Rebuild missing Research OS JSON artifacts via CLI registry entries; compare /readyz blockers.",
  },
  {
    pane_key: "first-run",
    title: "First-run deployment",
    testid: "cockpit-first-run-deployment",
    component_file: "ui/strategist-web/components/cockpit/FirstRunDeploymentCockpitPane.tsx",
    hooks: [
      "useReadinessDeployment",
      "useProbeReadyz",
      "useProbeHealthz",
      "useProbeLivez",
      "useUiFacade",
      "useUiEvidence",
      "useUiProviderSetup",
      "useUiEvidenceChain",
    ],
    endpoints: [
      "/readiness/deployment",
      "/readyz",
      "/healthz",
      "/livez",
      "/ui/facade",
      "/ui/evidence",
      "/ui/provider-setup",
      "/ui/evidence-chain",
    ],
    degraded_hint: "Follow FIRST_RUN_CLI_HINTS in local-ops-command-registry; fix deployment tier before UI claims.",
  },
  {
    pane_key: "release-control",
    title: "Release control",
    component_file: "ui/strategist-web/components/cockpit/ReleaseControlPane.tsx",
    hooks: [
      "useUiFacade",
      "useUiEvidence",
      "useUiEvidenceChain",
      "useUiResearchOsReleaseReadinessLatest",
      "useUiResearchOsHandoffLatest",
      "useUiResearchOsHandoffSignoffLatest",
      "useUiResearchOsReviewJournalLatest",
    ],
    endpoints: [
      "/ui/facade",
      "/ui/evidence",
      "/ui/evidence-chain",
      "/ui/research-os/release-readiness/latest",
      "/ui/research-os/handoff/latest",
      "/ui/research-os/handoff-signoff/latest",
      "/ui/research-os/review-journal/latest",
    ],
    degraded_hint:
      "Validate evidence bundle + Research OS handoff artifacts; run sensitive CLIs only on trusted workstations.",
  },
  {
    pane_key: "provider-setup-readiness",
    title: "Provider setup readiness",
    component_file: "ui/strategist-web/components/cockpit/ProviderSetupReadinessPane.tsx",
    hooks: ["useUiProviderSetup", "useUiProviderHealth"],
    endpoints: ["/ui/provider-setup", "/ui/provider-health"],
    degraded_hint: "Inspect GET /ui/provider-setup and GET /ui/provider-health; compare with deployment.env.sample keys (no secrets in UI).",
  },
];

/** Maps `cockpitPane` strings from `local-ops-command-registry.json` to `pane_key` in `COCKPIT_HOME_PANE_LINKS`. */
export const REGISTRY_COCKPIT_COMPONENT_TO_PANE_KEY: Record<string, string> = {
  ReleaseControlPane: "release-control",
  SingleTenantFirstRunWizard: "first-run",
  ProviderSetupReadinessPane: "provider-setup-readiness",
};

/** Hints keyed by `payload_schema` from `ui-facade-routes.json` — align with `strategy_validator/application/api_ui_surfaces.py` where applicable. */
export const PAYLOAD_SCHEMA_BUILDER_HINT: Partial<Record<string, string>> = {
  "ui_evidence/v1": "strategy_validator.application.ui_views:build_ui_evidence_payload",
  "ui_evidence_chain/v1": "strategy_validator.application.evidence_chain_projection:build_ui_evidence_chain_payload",
  "operator_action_event_projection_index/v1": "strategy_validator.application.operator_action_projection:build_operator_action_event_index_payload",
  "ui_runtime_status/v1": "strategy_validator.application.ui_views:build_ui_runtime_status_payload",
  "ui_provider_setup_console/v1": "strategy_validator.application.ui_provider_setup (module)",
  "provider_health_snapshot/v1": "strategy_validator.application.ui_public_facade:build_ui_provider_health_payload",
  "ui_public_facade_inventory/v1": "strategy_validator.application.ui_public_facade:build_ui_public_facade_inventory",
  "ui_command_mutation/v1": "strategy_validator.application.ui_command_actions:execute_ui_operator_command",
  "ui_research_os_status/v1": "strategy_validator.application.ui_research_os (module)",
  "ui_research_os_policy_gate/v1": "strategy_validator.application.ui_research_os (module)",
  "ui_research_os_exception/v1": "strategy_validator.application.ui_research_os (module)",
  "ui_research_os_remediation/v1": "strategy_validator.application.ui_research_os (module)",
  "ui_paper_execution_cockpit/v1": "strategy_validator.application (paper execution cockpit builders)",
  "ui_paper_broker/v1": "strategy_validator.application.ui_paper_broker (module)",
};

export const TOPOLOGY_CI_GATES: { node_id: string; label: string; script: string; invariant: string }[] = [
  {
    node_id: "ci:repository_truth",
    label: "Repository truth gate",
    script: "scripts/repository_truth_check.py",
    invariant: "Console scripts, contract snapshots, and hygiene gates declared in-repo.",
  },
  {
    node_id: "ci:ui_facade_contract",
    label: "UI facade route contract",
    script: "scripts/ui_facade_contract_snapshot.py",
    invariant: "Frontend `ui-facade-routes.json` digest matches `docs/api/ui-public-facade.snapshot.json`.",
  },
  {
    node_id: "ci:openapi_contract",
    label: "OpenAPI contract",
    script: "scripts/openapi_contract_snapshot.py",
    invariant: "Exported OpenAPI snapshot matches live `create_app()` schema.",
  },
  {
    node_id: "ci:source_health",
    label: "Source health",
    script: "scripts/source_health.py",
    invariant: "Required tooling and migration/archive verifiers remain present.",
  },
  {
    node_id: "ci:migration_truth",
    label: "Migration truth",
    script: "scripts/migration_truth_check.py",
    invariant: "SQLite migration graph is idempotent and tracked.",
  },
  {
    node_id: "ci:package_repo",
    label: "Clean archive check",
    script: "scripts/package_repo.py --check",
    invariant: "Packaging excludes transients and matches policy.",
  },
  {
    node_id: "ci:verify_repo_archive",
    label: "Archive verifier",
    script: "scripts/verify_repo_archive.py",
    invariant: "Archive digests and membership can be verified.",
  },
];

export const TOPOLOGY_AUTHORITY_BOUNDARIES: {
  node_id: string;
  label: string;
  source: string;
  summary: string;
}[] = [
  {
    node_id: "boundary:append-only-ledger",
    label: "Append-only ledger discipline",
    source: "strategy_validator/ledger/_append_only.py",
    summary: "Ledger mutations are centralized; browser and read-plane routes do not write SQLite directly.",
  },
  {
    node_id: "boundary:central-ledger-writer",
    label: "Centralized ledger writer",
    source: "strategy_validator/ledger/writer/__init__.py",
    summary: "Promotion and append paths go through the ledger writer module boundary (server-side).",
  },
  {
    node_id: "boundary:ui-mutation-route",
    label: "Token-gated UI mutation surface",
    source: "GET /ui/runtime · mutation_safety + POST /ui/commands/{action} (contract)",
    summary:
      "Operator UI mutations require server-side safe posture and bearer auth when TOKEN_PROTECTED; this cockpit pane stays read-plane-only.",
  },
  {
    node_id: "boundary:read-plane-ui",
    label: "Read-plane UI projection",
    source: "strategy_validator/application/api_ui_surfaces.py",
    summary: "UI JSON routes are thin adapters over bounded `build_*` payload constructors.",
  },
  {
    node_id: "boundary:promotion-authority",
    label: "Promotion / execution authority (server-governed)",
    source: "strategy_validator/validator/orchestrator/__init__.py",
    summary: "Live promotion and execution authority are not granted from browser-only state; see runtime + execution firewall payloads.",
  },
  {
    node_id: "boundary:frontend-read-plane",
    label: "Frontend read-plane-only posture",
    source: "ui/strategist-web (operator cockpit)",
    summary: "Browser does not execute shell commands, write artifacts, or call mutation routes from this topology view.",
  },
];

function digestPrefix(v: string | null | undefined): string {
  if (!v) return "—";
  return v.length > 14 ? `${v.slice(0, 12)}…` : v;
}

function routeSafetyClass(r: UiFacadeRoute): TopologySafetyClass {
  const m = r.method.toUpperCase();
  if (r.kind === "mutation" || m === "POST" || m === "PUT" || m === "PATCH" || m === "DELETE") return "MUTATION_AUTH";
  if (r.kind === "export") return "EXPORT";
  if (r.kind === "metadata") return "METADATA";
  if (r.kind === "read") return "READ_PLANE";
  return "UNKNOWN";
}

function bundleSafetyClass(rows: UiFacadeRoute[]): TopologySafetyClass {
  if (rows.some((r) => routeSafetyClass(r) === "MUTATION_AUTH")) return "MUTATION_AUTH";
  if (rows.some((r) => routeSafetyClass(r) === "EXPORT")) return "EXPORT";
  if (rows.some((r) => routeSafetyClass(r) === "METADATA")) return "METADATA";
  return "READ_PLANE";
}

function groupedRoutes(routes: UiFacadeRoute[]): Map<string, UiFacadeRoute[]> {
  const m = new Map<string, UiFacadeRoute[]>();
  for (const r of routes) {
    const list = m.get(r.path) ?? [];
    list.push(r);
    m.set(r.path, list);
  }
  return m;
}

function contractRouteNodeId(path: string, contract: FacadeRoutesContract | null): string | null {
  if (!contract) return null;
  const get = contract.routes.find((r) => r.path === path && r.method.toUpperCase() === "GET");
  if (get) return `route:GET:${path}`;
  const head = contract.routes.find((r) => r.path === path && r.method.toUpperCase() === "HEAD");
  if (head) return `route:HEAD:${path}`;
  const any = contract.routes.find((r) => r.path === path);
  return any ? `route:${any.method.toUpperCase()}:${path}` : null;
}

function registryPaneNodeIds(cockpitPaneField: string): string[] {
  const parts = cockpitPaneField.split(",").map((s) => s.trim());
  const out: string[] = [];
  for (const p of parts) {
    const key = REGISTRY_COCKPIT_COMPONENT_TO_PANE_KEY[p];
    if (key) out.push(`pane:${key}`);
  }
  return out;
}

export function buildSystemTopology(input: SystemTopologyInput): { nodes: TopologyNode[] } {
  const nodes: TopologyNode[] = [];
  const contract = input.contract;

  if (!contract) {
    nodes.push({
      node_id: "snapshot:facade-contract",
      node_type: "SNAPSHOT",
      label: "UI facade route contract",
      status: "UNKNOWN",
      source_file_or_endpoint: "ui/strategist-web/lib/contracts/ui-facade-routes.json",
      related_nodes: [],
      safety_class: "UNKNOWN",
      evidence_digest_prefix: "—",
      raw: { reason: "contract_missing" },
    });
  } else {
    nodes.push({
      node_id: "snapshot:facade-contract",
      node_type: "SNAPSHOT",
      label: "UI facade route contract",
      status: "OK",
      source_file_or_endpoint: "ui/strategist-web/lib/contracts/ui-facade-routes.json",
      related_nodes: [],
      safety_class: "METADATA",
      evidence_digest_prefix: digestPrefix(contract.routes_sha256),
      raw: {
        schema_version: contract.schema_version,
        route_count: contract.route_count,
        routes_sha256: contract.routes_sha256,
      },
    });

    const byPath = groupedRoutes(contract.routes);
    const builderNodes = new Set<string>();
    for (const [path, rows] of byPath.entries()) {
      const primary =
        rows.find((x) => x.method.toUpperCase() === "GET") ??
        rows.find((x) => x.method.toUpperCase() === "HEAD") ??
        rows[0];
      if (!primary) continue;
      const methodForId = primary.method.toUpperCase();
      const rid = `route:${methodForId}:${path}`;
      const mutRows = rows.filter(
        (x) => x.kind === "mutation" || ["POST", "PUT", "PATCH", "DELETE"].includes(x.method.toUpperCase()),
      );
      const hasMutation = mutRows.length > 0;
      const mutationFullyAuthed = hasMutation && mutRows.every((x) => x.auth_required);
      const st: TopologyNodeStatus = hasMutation && !mutationFullyAuthed ? "UNKNOWN" : "OK";
      const sc = bundleSafetyClass(rows);
      nodes.push({
        node_id: rid,
        node_type: "BACKEND_ROUTE",
        label: path,
        status: st,
        source_file_or_endpoint: rows.map((x) => `${x.method} ${x.path}`).join(" · "),
        related_nodes: [],
        safety_class: sc,
        evidence_digest_prefix: digestPrefix(primary.payload_schema),
        raw: { routes: rows },
      });
      const hint = PAYLOAD_SCHEMA_BUILDER_HINT[primary.payload_schema];
      if (hint) {
        const bid = `builder:${primary.payload_schema}`;
        if (!builderNodes.has(bid)) {
          builderNodes.add(bid);
          nodes.push({
            node_id: bid,
            node_type: "APPLICATION_BUILDER",
            label: primary.payload_schema,
            status: "OK",
            source_file_or_endpoint: hint,
            related_nodes: [rid],
            safety_class: "READ_PLANE",
            evidence_digest_prefix: "—",
            raw: { payload_schema: primary.payload_schema },
          });
        } else {
          const b = nodes.find((n) => n.node_id === bid);
          if (b && !b.related_nodes.includes(rid)) b.related_nodes.push(rid);
        }
      }
    }
  }

  for (const p of COCKPIT_HOME_PANE_LINKS) {
    const degraded = input.paneDegraded[p.pane_key] === true;
    nodes.push({
      node_id: `pane:${p.pane_key}`,
      node_type: "FRONTEND_PANE",
      label: p.title,
      status: degraded ? "DEGRADED" : "OK",
      source_file_or_endpoint: p.component_file,
      related_nodes: [
        ...p.hooks.map((h) => `hook:${p.pane_key}:${h}`),
        ...p.endpoints.map((e) => `endpoint:${p.pane_key}:${e}`),
      ],
      safety_class: "READ_PLANE",
      evidence_digest_prefix: "—",
      raw: { testid: p.testid, degraded_hint: p.degraded_hint },
    });
    for (const h of p.hooks) {
      nodes.push({
        node_id: `hook:${p.pane_key}:${h}`,
        node_type: "FRONTEND_HOOK",
        label: h,
        status: degraded ? "DEGRADED" : "OK",
        source_file_or_endpoint: `ui/strategist-web/hooks (see ${h})`,
        related_nodes: [`pane:${p.pane_key}`],
        safety_class: "READ_PLANE",
        evidence_digest_prefix: "—",
      });
    }
    for (const e of p.endpoints) {
      const inContract = contract?.routes.some((r) => r.path === e) ?? false;
      /** Liveness/readiness HTTP probes (not the deployment JSON route under `/readiness/`). */
      const isProbe = e === "/healthz" || e === "/readyz" || e === "/livez";
      const contractLink = contractRouteNodeId(e, contract);
      nodes.push({
        node_id: `endpoint:${p.pane_key}:${e}`,
        node_type: "BACKEND_ROUTE",
        label: e,
        status: !isProbe && !inContract ? "UNKNOWN" : degraded ? "DEGRADED" : "OK",
        source_file_or_endpoint: e,
        related_nodes: [`pane:${p.pane_key}`, ...(contractLink ? [contractLink] : [])],
        safety_class: isProbe ? "PROBE" : "READ_PLANE",
        evidence_digest_prefix: "—",
        raw: { in_ui_facade_contract: inContract, probe: isProbe },
      });
    }
  }

  for (const c of LOCAL_OPS_COMMAND_REGISTRY) {
    const paneLinks = registryPaneNodeIds(c.cockpitPane);
    nodes.push({
      node_id: `cli:${c.id}`,
      node_type: "CLI_COMMAND",
      label: c.label,
      status: "OK",
      source_file_or_endpoint: c.primaryConsoleScript,
      related_nodes: [`evidence:${c.id}`, `doc:${c.id}`, ...paneLinks],
      safety_class:
        c.safetyClass === "PRODUCTION_SENSITIVE" || c.safetyClass === "AUTH_REQUIRED"
          ? "MUTATION_AUTH"
          : "READ_PLANE",
      evidence_digest_prefix: "—",
      raw: { commandText: c.commandText, cockpitPane: c.cockpitPane, ciTruthGate: c.ciTruthGate, safetyClass: c.safetyClass },
    });
    nodes.push({
      node_id: `evidence:${c.id}`,
      node_type: "EVIDENCE_ARTIFACT",
      label: c.expectedEvidence.slice(0, 120),
      status: "OK",
      source_file_or_endpoint: c.expectedEvidence,
      related_nodes: [`cli:${c.id}`, ...paneLinks],
      safety_class: "ADVISORY",
      evidence_digest_prefix: "—",
    });
    nodes.push({
      node_id: `doc:${c.id}`,
      node_type: "DOC",
      label: c.docPath,
      status: "OK",
      source_file_or_endpoint: c.docPath,
      related_nodes: [`cli:${c.id}`],
      safety_class: "ADVISORY",
      evidence_digest_prefix: "—",
    });
  }

  for (const g of TOPOLOGY_CI_GATES) {
    nodes.push({
      node_id: g.node_id,
      node_type: "CI_GATE",
      label: g.label,
      status: "OK",
      source_file_or_endpoint: g.script,
      related_nodes: [],
      safety_class: "METADATA",
      evidence_digest_prefix: "—",
      raw: { invariant: g.invariant },
    });
  }

  for (const b of TOPOLOGY_AUTHORITY_BOUNDARIES) {
    nodes.push({
      node_id: b.node_id,
      node_type: "AUTHORITY_BOUNDARY",
      label: b.label,
      status: "OK",
      source_file_or_endpoint: b.source,
      related_nodes: [],
      safety_class: "ADVISORY",
      evidence_digest_prefix: "—",
      raw: { summary: b.summary },
    });
  }

  const psRoute = contract ? contractRouteNodeId("/ui/provider-setup", contract) : null;
  const phRoute = contract ? contractRouteNodeId("/ui/provider-health", contract) : null;
  nodes.push({
    node_id: "provider:surface",
    node_type: "PROVIDER",
    label: "Provider readiness / health",
    status: "OK",
    source_file_or_endpoint: "GET /ui/provider-setup · GET /ui/provider-health",
    related_nodes: [psRoute, phRoute].filter((x): x is string => Boolean(x)),
    safety_class: "READ_PLANE",
    evidence_digest_prefix: "—",
    raw: {
      backend_modules: "strategy_validator.application.ui_provider_setup; ui_public_facade provider health",
      env_sample: "deployment.env.sample (keys only — never paste secrets into the cockpit)",
    },
  });

  const fp = input.facadePayload;
  if (fp) {
    nodes.push({
      node_id: "snapshot:live-facade",
      node_type: "SNAPSHOT",
      label: "Live GET /ui/facade (runtime inventory)",
      status: "OK",
      source_file_or_endpoint: "/ui/facade",
      related_nodes: contract ? ["snapshot:facade-contract"] : [],
      safety_class: "METADATA",
      evidence_digest_prefix: "—",
      raw: {
        read_plane_only: asBool(fp.read_plane_only),
        mutation_route: asString(fp.mutation_route),
        route_count: fp.route_count,
      },
    });
  }

  return { nodes };
}

/** Contract-backed route nodes only (`route:METHOD:path`), including mutations. */
export function topologyContractRouteNodes(nodes: TopologyNode[]): TopologyNode[] {
  return nodes.filter((n) => n.node_type === "BACKEND_ROUTE" && n.node_id.startsWith("route:"));
}

export function topologyMutationRoutes(nodes: TopologyNode[]): TopologyNode[] {
  return topologyContractRouteNodes(nodes).filter((n) => n.safety_class === "MUTATION_AUTH");
}

export function topologyReadPlaneContractRoutes(nodes: TopologyNode[]): TopologyNode[] {
  return topologyContractRouteNodes(nodes).filter((n) => n.safety_class === "READ_PLANE");
}

export function topologyExportContractRoutes(nodes: TopologyNode[]): TopologyNode[] {
  return topologyContractRouteNodes(nodes).filter((n) => n.safety_class === "EXPORT");
}

export function topologyMetadataContractRoutes(nodes: TopologyNode[]): TopologyNode[] {
  return topologyContractRouteNodes(nodes).filter((n) => n.safety_class === "METADATA");
}

/** When a pane is degraded, return curated inspect hints (non-diagnostic). */
export function topologyDegradedHints(paneKey: string): string | undefined {
  return COCKPIT_HOME_PANE_LINKS.find((p) => p.pane_key === paneKey)?.degraded_hint;
}

/** Redact values that must never appear in topology UI (defense in depth). */
export function redactTopologyRaw(raw: Record<string, unknown> | undefined): Record<string, unknown> {
  if (!raw) return {};
  const out: Record<string, unknown> = { ...raw };
  for (const k of Object.keys(out)) {
    if (/token|secret|password|apikey|api_key|authorization|bearer/i.test(k)) {
      out[k] = "[REDACTED]";
    }
  }
  return out;
}

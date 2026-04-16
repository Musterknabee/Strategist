export type WorkItem = {
  work_item_key: string;
  queue_key: string;
  review_target: string;
  priority_band: string;
  review_due_by_utc: string;
  review_sort_key: string;
  action_owner_lane: string;
  claim_operability: string;
  dispatch_posture: string;
  urgency: string;
  score: number;
  summary_line: string;
  recommended_actions: string[];
};

export type WorkboardQueue = {
  schema_version: string;
  board_label: string;
  queue_key: string;
  review_target: string;
  priority_band: string;
  review_due_by_utc: string;
  review_sort_key: string;
  work_item_count: number;
  summary_line: string;
  queue_summary_line: string;
  recommended_next_actions: string[];
  entries: WorkItem[];
};

export type WorkbenchItem = {
  pack_kind: string;
  trust_status: string | null;
  summary_line: string | null;
  generated_at_utc: string | null;
  manifest_path: string;
  pack_root: string;
  primary_output_artifact_path: string | null;
  output_artifact_labels: string[];
  output_artifact_paths: string[];
};

export type WorkbenchColumn = {
  pack_kind: string;
  item_count: number;
  latest_generated_at_utc: string | null;
  trust_statuses: string[];
  items: WorkbenchItem[];
};

export type Workbench = {
  schema_version: string;
  search_root: string;
  total_item_count: number;
  column_count: number;
  columns: WorkbenchColumn[];
};

export type UiWorkboardDashboard = {
  schema_version: string;
  generated_at_utc: string;
  board_label: string;
  queue: WorkboardQueue;
  pack_workbench: Workbench;
  transition_policy: Record<string, unknown>;
  stats: {
    active_count: number;
    escalated_count: number;
    pack_item_count: number;
    pack_column_count: number;
  };
};


export type MetricProvenance = {
  source_label: string;
  artifact_count: number;
  artifact_paths: string[];
  projection_family: string;
  verification_label: string;
};

export type BurnInMetricsPayload = {
  cpcvCoverage: Array<{ fold: string; coverage: number }>;
  calibrationCurve: Array<{ bucket: string; predicted: number; realized: number }>;
  incrementality: {
    pValue: number;
    coefficient: number;
    significant: boolean;
  };
  realism: {
    slippageBps: number;
    borrowCostBps: number;
    marketHoursCompliance: number;
    capacityStress: number;
    liquidityIntegrity: number;
  };
  providerPaths: Array<{ provider: string; status: string; path: string }>;
  dsrPbo: {
    deflatedSharpeRatio: number;
    probabilityOfBacktestOverfitting: number;
    overfitRisk: string;
    promotionPosture: string;
  };
  pathStability: Array<{ window: string; stability: number; dispersion: number }>;
  realismConstraints: Array<{
    name: string;
    value: number;
    target: number;
    unit: string;
    status: string;
    summary_line: string;
  }>;
  forensicSummary: {
    promotion_posture: string;
    overfit_risk: string;
    primary_warning: string;
    forensic_notes: string[];
  };
  metricProvenance: Record<string, MetricProvenance>;
};

export type UiBurnInDashboard = {
  schema_version: string;
  generated_at_utc: string;
  artifact_paths: string[];
  artifact_summary: {
    artifact_count: number;
    total_round_count: number;
    total_fallback_count: number;
    total_stale_count: number;
    artifacts: Array<Record<string, unknown>>;
  };
  metrics: BurnInMetricsPayload;
};

export type UiPackSection = {
  item_count?: number;
  items?: Array<Record<string, unknown>>;
  [key: string]: unknown;
};

export type UiPackDetail = {
  schema_version: string;
  generated_at_utc: string;
  pack: WorkbenchItem | null;
  navigation: UiPackSection;
  timeline: UiPackSection;
  assignment: UiPackSection;
  claim_lease: UiPackSection;
  claim_lifecycle: UiPackSection;
  escalation: UiPackSection;
  command_hints: string[];
};

export type UiOperatorCommandReceipt = {
  schema_version: string;
  generated_at_utc: string;
  command_id: string;
  action: string;
  accepted: boolean;
  operator_id: string;
  execution_mode: string;
  requires_projection_refresh: boolean;
  target: {
    work_item_key?: string | null;
    review_target?: string | null;
    pack_kind?: string | null;
    manifest_path?: string | null;
  };
  summary_line: string;
  operator_message: string;
};


export type UiTribunalGraphNode = {
  id: string;
  label: string;
  kind: string;
};

export type UiTribunalGraphEdge = {
  source: string;
  target: string;
  relation: string;
};

export type UiTribunalWorkspace = {
  doctrine_stats: {
    active_doctrine_count: number;
    sealed_history_count: number;
    falsification_enforced_count: number;
    graph_density_label: string;
  };
  section_provenance: Record<string, MetricProvenance>;
  schema_version: string;
  generated_at_utc: string;
  blindness: {
    mode: string;
    quantitative_payloads_present: boolean;
    forbidden_metric_families: string[];
    operator_message: string;
  };
  agent_workflows: Record<string, {
    stage: string;
    status: string;
    summary_line: string;
    prompt_law: string;
  }>;
  prompt_evaluations: Array<{
    evaluation_id: string;
    stage: string;
    status: string;
    constraint: string;
    summary_line: string;
  }>;
  falsification_checks: Array<{
    check_id: string;
    status: string;
    summary_line: string;
  }>;
  sealed_history: Array<{
    event_id: string;
    forensic_status: string;
    summary_line: string;
  }>;
  doctrine_memory: Array<{
    doctrine_key: string;
    adaptation_status: string;
    summary_line: string;
  }>;
  thesis_graph: {
    nodes: UiTribunalGraphNode[];
    edges: UiTribunalGraphEdge[];
  };
  operator_lines: string[];
};


export type UiEvidenceDashboard = {
  section_provenance: Record<string, MetricProvenance>;
  schema_version: string;
  generated_at_utc: string;
  search_root: string;
  registry: {
    schema_version: string;
    projection_label: string;
    projection_family: string;
    projection_version: string;
    source_artifact_count: number;
    output_artifact_count: number;
    projection_digest_sha256: string;
    source_artifacts: Array<{
      artifact_label: string;
      path: string;
      exists: boolean;
      sha256?: string;
      size_bytes?: number;
      modified_at_utc?: string;
      schema_version?: string;
    }>;
  };
  verification: {
    projection_snapshot_verified: boolean;
    trust_status: string;
    lineage_reason: string;
    seal_status: string;
    completeness_percent: number;
    integrity_warnings: string[];
  };
  host_fingerprint: null | {
    host_kind?: string | null;
    host_label?: string | null;
    runtime_mode?: string | null;
    config_fingerprint?: string | null;
    git_commit?: string | null;
    git_tag?: string | null;
    interface_freeze_id?: string | null;
    present_env_keys: string[];
    env_hash_count: number;
  };
  daily_checklist: Record<string, unknown>;
  runtime_review: Record<string, unknown>;
  lineage: {
    summary_line: string;
    layers: Array<{ layer: string; count: number; sample_paths: string[] }>;
    warnings: string[];
  };
  registry_table: Array<Record<string, unknown>>;
  operator_lines: string[];
};


export type UiRuntimeStatus = {
  schema_version: string;
  generated_at_utc: string;
  environment: string;
  persona: {
    active_role: "operator" | "validator" | "tribunal";
    active_label: string;
    available_roles: Array<"operator" | "validator" | "tribunal">;
    default_route: string;
  };
  policy: {
    allowed_domains: string[];
    redacted_domains: string[];
    allowed_actions: string[];
  };
  read_plane: {
    status: string;
    freshness_status: string;
    operator_message: string;
  };
  backend: {
    status: string;
    base_mode: string;
    operator_message: string;
  };
  blindness: {
    tribunal_mode: string;
    operator_message: string;
  };
  providers: {
    enabled_count: number;
    items: Array<{ provider: string; status: string; path: string }>;
  };
  command_bar: {
    allowed_actions: string[];
    operator_hint: string;
  };
};

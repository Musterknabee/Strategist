"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Timestamp } from "@/components/operator/Timestamp";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useProbeApiRoot } from "@/hooks/useProbeApiRoot";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiFacade } from "@/hooks/useUiFacade";
import { useUiResearchCompute } from "@/hooks/useUiResearchCompute";
import { useUiRuntime } from "@/hooks/useUiRuntime";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asNumber, asRecord, asString } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

export default function RuntimePage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const runtime = useUiRuntime("operator");
  const facade = useUiFacade();
  const researchCompute = useUiResearchCompute();
  const apiRoot = useProbeApiRoot();

  const r = runtime.data != null ? asRecord(runtime.data) : null;
  const persona = r ? asRecord(r.persona) : null;
  const readPlane = r ? asRecord(r.read_plane) : null;
  const backend = r ? asRecord(r.backend) : null;
  const providers = r ? asRecord(r.providers) : null;
  const rootBanner = apiRoot.data != null ? asRecord(apiRoot.data) : null;
  const links = rootBanner?.links != null ? asRecord(rootBanner.links) : null;
  const rc = researchCompute.data != null ? asRecord(researchCompute.data) : null;
  const rcProbe = rc?.gpu_probe != null ? asRecord(rc.gpu_probe) : null;
  const rcBench = rc?.last_benchmark != null ? asRecord(rc.last_benchmark) : null;

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "rt",
        severity: "info",
        text: `runtime ${r ? asString(r.schema_version)?.slice(0, 8) ?? "?" : "—"} · facade ${facade.data?.schema_version ?? "—"}`,
      },
      {
        id: "rc",
        severity: asString(rc?.research_compute_readiness) === "GPU_ACCELERATION_READY" ? "ok" : "warn",
        text: `rc ${asString(rc?.research_compute_readiness) ?? "UNKNOWN"}`,
      },
    ],
    [r, facade.data?.schema_version, rc],
  );

  const ticker = useMemo(
    () => [
      {
        severity: "neutral" as const,
        text: `RP ${asString(readPlane?.status) ?? "?"}`,
      },
    ],
    [readPlane],
  );

  useTerminalPageBind(tape, ticker);

  if (!config.ok) {
    return (
      <div className="term-page">
        <h1 className="term-page__title">RUNTIME</h1>
        <p className="muted">{config.error.message}</p>
      </div>
    );
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">RUNTIME · SYSINFO</h1>
      <p className="muted" style={{ fontSize: "10px" }}>
        GET /ui/runtime?role=operator · /ui/facade · GET / (banner) — advisory read-plane; not live process logs.
      </p>
      {runtime.isLoading && <p className="muted">Loading…</p>}
      {runtime.isError && (
        <p className="term-page__banner" style={{ color: "#f85149" }}>
          {runtime.error instanceof Error ? runtime.error.message : String(runtime.error)}
        </p>
      )}

      {r && (
        <PaneGrid cols={2}>
          <Pane
            title="Process / read-plane"
            dense
            onInspect={() => openInspector({ title: "Runtime payload", rawJson: r })}
          >
            <TermKV
              rows={[
                { k: "schema", v: asString(r.schema_version) ?? "—" },
                {
                  k: "gen",
                  v: <Timestamp iso={asString(r.generated_at_utc)} />,
                },
                { k: "env", v: asString(r.environment) ?? "—" },
                {
                  k: "persona",
                  v: (
                    <>
                      {asString(persona?.active_label) ?? "—"}{" "}
                      <code className="muted">{asString(persona?.active_role) ?? "—"}</code>
                    </>
                  ),
                },
                {
                  k: "read_plane",
                  v: <StatusBadge raw={asString(readPlane?.status)} />,
                },
                { k: "freshness", v: asString(readPlane?.freshness_status) ?? "UNKNOWN" },
                {
                  k: "backend",
                  v: <StatusBadge raw={asString(backend?.status)} />,
                },
                { k: "base_mode", v: asString(backend?.base_mode) ?? "—" },
              ]}
            />
            {asString(readPlane?.operator_message) && (
              <p className="muted" style={{ marginTop: "4px", fontSize: "10px" }}>
                {asString(readPlane?.operator_message)}
              </p>
            )}
          </Pane>

          <Pane
            title="Providers (runtime slice)"
            dense
            onInspect={() => openInspector({ title: "Providers slice", rawJson: providers ?? {} })}
          >
            {providers ? (
              <TermKV rows={[{ k: "enabled", v: String(asNumber(providers.enabled_count) ?? "—") }]} />
            ) : (
              <span className="muted">—</span>
            )}
          </Pane>

          <Pane
            title="Facade inventory"
            dense
            onInspect={() =>
              openInspector({
                title: "/ui/facade",
                body: (
                  <p className="muted" style={{ fontSize: "10px" }}>
                    <code>frontend_package_present</code> = API process sees expected Next package on its filesystem — not
                    browser deployment.
                  </p>
                ),
                rawJson: facade.data ?? { error: "facade not loaded" },
              })
            }
          >
            {facade.isLoading && <span className="muted">Loading…</span>}
            {facade.isError && <span className="muted">Facade unavailable</span>}
            {facade.data && (
              <TermKV
                rows={[
                  { k: "schema", v: facade.data.schema_version },
                  { k: "surface", v: facade.data.surface },
                  { k: "routes", v: String(facade.data.routes?.length ?? 0) },
                  { k: "read_plane_only", v: String(facade.data.read_plane_only) },
                  {
                    k: "fe_pkg_present",
                    v: String(facade.data.frontend_package_present),
                  },
                  {
                    k: "fe_expected",
                    v: facade.data.frontend_expected_package,
                  },
                  {
                    k: "fe_readiness_claimed",
                    v: String(facade.data.frontend_readiness_claimed),
                  },
                  {
                    k: "fe_runtime_reach",
                    v:
                      facade.data.frontend_runtime_reachable === null ||
                      facade.data.frontend_runtime_reachable === undefined
                        ? "null (API does not probe browser)"
                        : String(facade.data.frontend_runtime_reachable),
                  },
                ]}
              />
            )}
            {facade.data?.frontend_operator_console_hint && (
              <p className="muted" style={{ marginTop: "4px", fontSize: "10px" }}>
                {facade.data.frontend_operator_console_hint}
              </p>
            )}
          </Pane>

          <Pane
            title="API root banner"
            dense
            onInspect={() => openInspector({ title: "GET /", rawJson: rootBanner ?? apiRoot.data ?? {} })}
          >
            {apiRoot.isLoading && <span className="muted">Loading…</span>}
            {apiRoot.isError && (
              <span className="muted">{apiRoot.error instanceof Error ? apiRoot.error.message : String(apiRoot.error)}</span>
            )}
            {rootBanner && (
              <>
                <TermKV
                  rows={[
                    { k: "service", v: asString(rootBanner.service) ?? "—" },
                    { k: "schema", v: asString(rootBanner.schema_version) ?? "—" },
                  ]}
                />
                {links && (
                  <ul className="term-link-list" style={{ margin: "6px 0 0", paddingLeft: "1rem", fontSize: "10px" }}>
                    {Object.entries(links).map(([k, v]) => {
                      const path = typeof v === "string" ? v : "";
                      const href = path ? new URL(path, `${config.baseUrl}/`).toString() : "#";
                      return (
                        <li key={k}>
                          <a href={href} rel="noreferrer" target="_blank">
                            {k}
                          </a>{" "}
                          <code className="muted">{path}</code>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </>
            )}
          </Pane>

          <Pane
            title="Research compute (optional GPU advisory)"
            dense
            onInspect={() =>
              openInspector({
                title: "/ui/research-compute",
                rawJson: rc ?? researchCompute.data ?? {},
              })
            }
          >
            {researchCompute.isLoading && <span className="muted">Loading…</span>}
            {researchCompute.isError && <span className="muted">Unavailable</span>}
            {rc && (
              <TermKV
                rows={[
                  {
                    k: "readiness",
                    v: asString(rc.research_compute_readiness) ?? "UNKNOWN",
                  },
                  {
                    k: "gpu_available",
                    v: String(rcProbe?.gpu_available ?? "UNKNOWN"),
                  },
                  {
                    k: "torch_available",
                    v: String(rcProbe?.torch_available ?? "UNKNOWN"),
                  },
                  {
                    k: "cuda_available",
                    v: String(rcProbe?.cuda_available ?? "UNKNOWN"),
                  },
                  {
                    k: "fallback_reason",
                    v: asString(rc.fallback_reason) ?? "—",
                  },
                  {
                    k: "benchmark_gpu",
                    v: rcBench ? String(rcBench.gpu_available ?? "UNKNOWN") : "NOT_RUN",
                  },
                  {
                    k: "benchmark_digest",
                    v: asString(rcBench?.evidence_digest)?.slice(0, 16) ?? "—",
                  },
                  {
                    k: "bench_process_workers",
                    v: rcBench?.process_pool_workers != null ? String(rcBench.process_pool_workers) : "—",
                  },
                  {
                    k: "bench_cpu_ms",
                    v: rcBench?.cpu_duration_ms != null ? String(rcBench.cpu_duration_ms) : "—",
                  },
                  {
                    k: "bench_pool_ms",
                    v: rcBench?.process_pool_duration_ms != null ? String(rcBench.process_pool_duration_ms) : "—",
                  },
                ]}
              />
            )}
          </Pane>
        </PaneGrid>
      )}

      {runtime.data && <JsonDetails summary="Drilldown: /ui/runtime JSON" data={runtime.data} />}
    </div>
  );
}

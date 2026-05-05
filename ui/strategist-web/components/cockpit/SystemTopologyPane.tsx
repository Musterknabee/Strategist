"use client";

import type { ReactNode } from "react";
import { useMemo, useState } from "react";
import type { UiFacadeRoute } from "@/lib/api/types";
import { Pane } from "@/components/terminal/Pane";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import {
  COCKPIT_HOME_PANE_LINKS,
  type TopologyNode,
  buildSystemTopology,
  redactTopologyRaw,
  topologyContractRouteNodes,
  topologyDegradedHints,
  topologyExportContractRoutes,
  topologyMetadataContractRoutes,
  topologyMutationRoutes,
  topologyReadPlaneContractRoutes,
} from "@/lib/operator/system-topology-model";
import { inspectBody } from "./cockpit-utils";

export type SystemTopologyPaneProps = {
  topologyNodes: TopologyNode[];
  facadeReadPlaneOnly: boolean | null;
  mutationRouteLabel: string | null;
  openInspector: (p: InspectorPayload) => void;
};

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <details className="topology-section" open>
      <summary className="topology-section__summary">{title}</summary>
      <div className="topology-section__body">{children}</div>
    </details>
  );
}

function NodeLine({
  n,
  onSelect,
  selected,
}: {
  n: TopologyNode;
  onSelect: (n: TopologyNode) => void;
  selected: boolean;
}) {
  return (
    <button
      type="button"
      className={`topology-line${selected ? " topology-line--selected" : ""}`}
      onClick={() => onSelect(n)}
    >
      <span className="topology-line__type">{n.node_type}</span>
      <span className="topology-line__label">{n.label}</span>
      <span className="topology-line__status">{n.status}</span>
      <span className="topology-line__safety">{n.safety_class}</span>
    </button>
  );
}

export function SystemTopologyPane({
  topologyNodes,
  facadeReadPlaneOnly,
  mutationRouteLabel,
  openInspector,
}: SystemTopologyPaneProps) {
  const [selected, setSelected] = useState<TopologyNode | null>(null);

  const contractRoutes = useMemo(() => topologyContractRouteNodes(topologyNodes), [topologyNodes]);
  const mutations = useMemo(() => topologyMutationRoutes(topologyNodes), [topologyNodes]);
  const readPlane = useMemo(() => topologyReadPlaneContractRoutes(topologyNodes), [topologyNodes]);
  const exports = useMemo(() => topologyExportContractRoutes(topologyNodes), [topologyNodes]);
  const metadata = useMemo(() => topologyMetadataContractRoutes(topologyNodes), [topologyNodes]);
  const panes = useMemo(() => topologyNodes.filter((n) => n.node_type === "FRONTEND_PANE"), [topologyNodes]);
  const builders = useMemo(() => topologyNodes.filter((n) => n.node_type === "APPLICATION_BUILDER"), [topologyNodes]);
  const cli = useMemo(() => topologyNodes.filter((n) => n.node_type === "CLI_COMMAND"), [topologyNodes]);
  const ciGates = useMemo(() => topologyNodes.filter((n) => n.node_type === "CI_GATE"), [topologyNodes]);
  const boundaries = useMemo(() => topologyNodes.filter((n) => n.node_type === "AUTHORITY_BOUNDARY"), [topologyNodes]);
  const snapshots = useMemo(() => topologyNodes.filter((n) => n.node_type === "SNAPSHOT"), [topologyNodes]);

  return (
    <div className="cockpit-topology-wrap" data-testid="cockpit-system-topology-pane">
    <Pane
      title="System topology / dependency map"
      dense
      onInspect={() =>
        openInspector({
          title: "Topology inspector",
          subtitle: "Read-only map from contracts + registry",
          body: inspectBody({
            status: snapshots.find((s) => s.node_id === "snapshot:facade-contract")?.status ?? "UNKNOWN",
            summary:
              "Pane → hook → endpoint links are curated in system-topology-model. Contract routes come from ui-facade-routes.json. CLI/evidence from local-ops-command-registry.json. No browser execution.",
            details: [
              { k: "read_plane_only (facade)", v: String(facadeReadPlaneOnly ?? "UNKNOWN") },
              { k: "mutation_route (facade)", v: mutationRouteLabel ?? "UNKNOWN" },
              { k: "contract_route_count", v: String(contractRoutes.length) },
            ],
          }),
          rawJson: { nodes: topologyNodes.length },
        })
      }
    >
      <div className="topology-banner">
        <span>READ-PLANE MAP</span>
        <span>·</span>
        <span>no browser execution</span>
        <span>·</span>
        <span>facade read_plane_only: {facadeReadPlaneOnly === null ? "UNKNOWN" : String(facadeReadPlaneOnly)}</span>
        <span>·</span>
        <span>mutation route: {mutationRouteLabel ?? "UNKNOWN"}</span>
      </div>

      <Section title="Authority boundaries">
        <ul className="topology-list">
          {boundaries.map((b) => (
            <li key={b.node_id}>
              <strong>{b.label}</strong> — {b.source_file_or_endpoint}
              <div className="topology-muted">{(b.raw?.summary as string) ?? ""}</div>
            </li>
          ))}
        </ul>
      </Section>

      <Section title="Contract snapshots">
        <ul className="topology-list">
          {snapshots.map((s) => (
            <li key={s.node_id}>
              {s.label}: {s.status} · digest {s.evidence_digest_prefix}
            </li>
          ))}
        </ul>
      </Section>

      <Section title="Route safety (from ui-facade-routes.json)">
        <p className="topology-muted">
          Mutations: POST routes with `kind: mutation` (auth_required from contract). Read-plane: GET read routes. Export:
          GET/HEAD export routes. Metadata: OPTIONS/GET facade inventory.
        </p>
        <div className="topology-columns">
          <div>
            <h4 className="topology-subhead">Mutation routes</h4>
            {mutations.length === 0 ? (
              <p className="topology-muted">UNKNOWN / no contract</p>
            ) : (
              <ul className="topology-list">
                {mutations.map((r) => {
                  const rows = Array.isArray(r.raw?.routes) ? (r.raw?.routes as UiFacadeRoute[]) : [];
                  const mut = rows.filter((x) => x.kind === "mutation");
                  const authed = mut.length > 0 && mut.every((x) => x.auth_required);
                  return (
                    <li key={r.node_id}>
                      {r.source_file_or_endpoint} · auth gate: {authed ? "auth_required (contract)" : "UNKNOWN"}
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
          <div>
            <h4 className="topology-subhead">Read-plane (sample)</h4>
            <ul className="topology-list">
              {readPlane.slice(0, 10).map((r) => (
                <li key={r.node_id}>{r.label}</li>
              ))}
              {readPlane.length > 10 ? <li className="topology-muted">… {readPlane.length - 10} more</li> : null}
            </ul>
            <h4 className="topology-subhead">Export / metadata (counts)</h4>
            <p className="topology-muted">
              export routes: {exports.length} · metadata routes: {metadata.length}
            </p>
          </div>
        </div>
      </Section>

      <Section title="Frontend pane → hook → endpoint (curated)">
        <ul className="topology-list">
          {COCKPIT_HOME_PANE_LINKS.map((p) => {
            const degraded = panes.find((x) => x.node_id === `pane:${p.pane_key}`)?.status === "DEGRADED";
            return (
              <li key={p.pane_key}>
                <strong>{p.title}</strong> {degraded ? <em className="topology-warn">DEGRADED</em> : null}
                <div className="topology-muted">Hooks: {p.hooks.slice(0, 4).join(", ")}{p.hooks.length > 4 ? "…" : ""}</div>
                <div className="topology-muted">Endpoints: {p.endpoints.join(", ")}</div>
                {degraded ? <div className="topology-hint">Inspect: {topologyDegradedHints(p.pane_key)}</div> : null}
              </li>
            );
          })}
        </ul>
      </Section>

      <Section title="Endpoint → application builder (payload_schema hints only)">
        <ul className="topology-list">
          {builders.length === 0 ? (
            <li className="topology-muted">No builder hints for current contract slice (UNKNOWN).</li>
          ) : (
            builders.map((b) => (
              <li key={b.node_id}>
                <code>{b.label}</code> → {b.source_file_or_endpoint}
              </li>
            ))
          )}
        </ul>
      </Section>

      <Section title="CLI command → evidence → cockpit pane (registry)">
        <ul className="topology-list topology-list--compact">
          {cli.slice(0, 14).map((c) => (
            <li key={c.node_id}>
              <strong>{c.label}</strong> — {c.source_file_or_endpoint}
              <div className="topology-muted">{(c.raw?.cockpitPane as string) ?? ""}</div>
            </li>
          ))}
        </ul>
        {cli.length > 14 ? <p className="topology-muted">… {cli.length - 14} more commands in registry</p> : null}
      </Section>

      <Section title="Provider → readiness / evidence surface">
        <ul className="topology-list">
          <li>
            <strong>Provider surface node</strong> links contract GET routes for /ui/provider-setup and /ui/provider-health
            when present.
          </li>
        </ul>
      </Section>

      <Section title="CI gate → invariant (curated scripts)">
        <ul className="topology-list">
          {ciGates.map((g) => (
            <li key={g.node_id}>
              <strong>{g.label}</strong> — <code>{g.source_file_or_endpoint}</code>
              <div className="topology-muted">{(g.raw?.invariant as string) ?? ""}</div>
            </li>
          ))}
        </ul>
      </Section>

      <Section title="Node inspector (selected)">
        <p className="topology-muted">Select a node below to preview redacted raw fields. This view performs no API calls.</p>
        <div className="topology-picker">
          {topologyNodes.slice(0, 80).map((n) => (
            <NodeLine key={n.node_id} n={n} selected={selected?.node_id === n.node_id} onSelect={setSelected} />
          ))}
          {topologyNodes.length > 80 ? (
            <p className="topology-muted">… {topologyNodes.length - 80} nodes omitted in picker (use repo search for full list)</p>
          ) : null}
        </div>
        {selected ? (
          <pre className="topology-pre">{JSON.stringify(redactTopologyRaw(selected.raw), null, 2)}</pre>
        ) : (
          <p className="topology-muted">PENDING · no selection</p>
        )}
      </Section>
    </Pane>
    </div>
  );
}

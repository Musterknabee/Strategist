import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import { asString } from "@/lib/operator/payload-utils";
import type { UiFacadePayload } from "@/lib/api/types";
import { UNKNOWN, inspectBody, value } from "./cockpit-utils";

export type RuntimePaneProps = {
  facadeData: UiFacadePayload | null | undefined;
  runtimeBody: Record<string, unknown> | null;
  readPlane: Record<string, unknown> | null;
  backend: Record<string, unknown> | null;
  gpuProbe: Record<string, unknown> | null;
  gpuHardware: Record<string, unknown> | null;
  researchBody: Record<string, unknown> | null;
  apiRootData: unknown;
  runtimeData: unknown;
  researchComputeData: unknown;
  openInspector: (s: InspectorPayload) => void;
};

export function RuntimePane({
  facadeData,
  runtimeBody,
  readPlane,
  backend,
  gpuProbe,
  gpuHardware,
  researchBody,
  apiRootData,
  runtimeData,
  researchComputeData,
  openInspector,
}: RuntimePaneProps) {
  return (
    <Pane
      title="Runtime"
      dense
      onInspect={() =>
        openInspector({
          title: "Runtime / Facade",
          body: inspectBody({
            status: asString(readPlane?.status) ?? UNKNOWN,
            summary:
              "Backend package detection does not mean browser frontend is absent. Frontend readiness remains not claimed. Read-plane mode remains active. GPU hardware detection is separate from CUDA acceleration readiness.",
            details: [
              { k: "routes", v: String(facadeData?.routes?.length ?? UNKNOWN) },
              { k: "frontend_readiness_claimed", v: String(facadeData?.frontend_readiness_claimed ?? false) },
              { k: "gpu_hardware_detected", v: String(gpuProbe?.gpu_hardware_detected ?? UNKNOWN) },
              { k: "gpu_acceleration_ready", v: String(researchBody?.gpu_available ?? false) },
            ],
          }),
          rawJson: { runtime: runtimeData, facade: facadeData, root: apiRootData, research_compute: researchComputeData },
        })
      }
    >
      <TermKV
        rows={[
          { k: "schema_read", v: asString(runtimeBody?.schema_version) ?? UNKNOWN },
          { k: "schema_write", v: "NO_MUTATIONS" },
          { k: "facade_routes", v: String(facadeData?.routes?.length ?? UNKNOWN) },
          { k: "read_plane_only", v: String(facadeData?.read_plane_only ?? UNKNOWN) },
          { k: "frontend_readiness_claimed", v: String(facadeData?.frontend_readiness_claimed ?? false) },
          {
            k: "frontend_package_detected_by_backend",
            v: String(
              facadeData?.frontend_package_detected_by_backend ??
                facadeData?.frontend_package_present ??
                UNKNOWN,
            ),
          },
          { k: "runtime_mode", v: asString(runtimeBody?.environment) ?? asString(backend?.base_mode) ?? UNKNOWN },
          { k: "gpu_hardware_detected", v: String(gpuProbe?.gpu_hardware_detected ?? UNKNOWN) },
          { k: "gpu_name", v: asString(gpuHardware?.name) ?? "UNKNOWN" },
          { k: "gpu_memory_mib", v: value(gpuHardware?.memory_total_mib, "UNKNOWN") },
          { k: "gpu_acceleration_ready", v: String(researchBody?.gpu_available ?? false) },
          { k: "cuda_available", v: String(gpuProbe?.cuda_available ?? UNKNOWN) },
          { k: "compute_backend", v: asString(gpuProbe?.backend) ?? UNKNOWN },
          { k: "uptime", v: asString(runtimeBody?.uptime) ?? "PENDING" },
        ]}
      />
      <p className="runtime-note">
        backend package detection does not mean browser frontend is absent; frontend readiness remains not claimed;
        read-plane mode remains active
      </p>
    </Pane>
  );
}

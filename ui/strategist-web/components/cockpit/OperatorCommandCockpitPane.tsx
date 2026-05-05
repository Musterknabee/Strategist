"use client";

import { OperatorCommandPanel } from "@/components/operator/OperatorCommandPanel";
import type { UiMutationSafetyStatus, UiWorkboardQueueEntry } from "@/lib/api/types";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";

export type OperatorCommandCockpitPaneProps = {
  selectedWorkTarget: UiWorkboardQueueEntry | null;
  mutationSafety: UiMutationSafetyStatus | null;
  mutationRoute: string | null;
  readPlaneOnly: boolean | null;
  runtimeEnvironment: string | null;
  openInspector: (p: InspectorPayload) => void;
};

export function OperatorCommandCockpitPane({
  selectedWorkTarget,
  mutationSafety,
  mutationRoute,
  readPlaneOnly,
  runtimeEnvironment,
  openInspector,
}: OperatorCommandCockpitPaneProps) {
  return (
    <div className="cockpit-command-row" data-testid="cockpit-operator-command">
      <OperatorCommandPanel
        target={selectedWorkTarget}
        boardLabel="operator"
        title="Operator commands (mutation)"
        mutationSafety={mutationSafety}
        mutationRoute={mutationRoute}
        readPlaneOnly={readPlaneOnly}
        runtimeEnvironment={runtimeEnvironment}
        onInspectPosture={openInspector}
        onInspectReceipt={openInspector}
      />
    </div>
  );
}

"use client";

import type { UiOperatorCommandReceipt, UiPackDetail, WorkItem, WorkbenchItem } from "@/lib/contracts/ui";
import { PackDetailPanel } from "@/features/control-plane/components/pack-detail-panel";

export function PackDetailDrawer({
  selected,
  pack,
  detail,
  receipt,
  onCommand,
  actionsFrozen = false,
}: {
  selected: WorkItem | null;
  pack?: WorkbenchItem | null;
  detail?: UiPackDetail;
  receipt?: UiOperatorCommandReceipt | null;
  onCommand: (action: string) => void;
  actionsFrozen?: boolean;
}) {
  return (
    <PackDetailPanel
      selected={selected}
      pack={pack}
      detail={detail}
      receipt={receipt}
      onCommand={onCommand}
      actionsFrozen={actionsFrozen}
      embedded
    />
  );
}

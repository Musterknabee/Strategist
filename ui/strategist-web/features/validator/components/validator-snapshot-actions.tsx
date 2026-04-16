"use client";

import { ExportSnapshotActions } from "@/features/shared/components/export-snapshot-actions";

export function ValidatorSnapshotActions({
  payload,
  fileStem,
}: {
  payload: unknown;
  fileStem: string;
}) {
  return <ExportSnapshotActions payload={payload} fileStem={fileStem} />;
}

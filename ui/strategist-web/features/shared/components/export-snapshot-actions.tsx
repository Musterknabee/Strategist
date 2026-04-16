"use client";

import { useState } from "react";
import { Check, Download } from "lucide-react";

import { Button } from "@/components/ui/button";

export function ExportSnapshotActions({
  payload,
  fileStem,
  label = "Export snapshot",
}: {
  payload: unknown;
  fileStem: string;
  label?: string;
}) {
  const [saved, setSaved] = useState(false);

  const onDownload = () => {
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${fileStem}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    setSaved(true);
    window.setTimeout(() => setSaved(false), 1800);
  };

  return (
    <Button variant="outline" className="gap-2" onClick={onDownload}>
      {saved ? <Check className="h-4 w-4" /> : <Download className="h-4 w-4" />}
      {saved ? "Snapshot downloaded" : label}
    </Button>
  );
}

"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";

export function CopyCommandBlock({
  command,
  description,
  label,
}: {
  command: string;
  description?: string;
  label?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4">
      {label ? <div className="text-sm font-medium text-zinc-100">{label}</div> : null}
      {description ? <p className="mt-1 text-sm text-zinc-400">{description}</p> : null}
      <div className="mt-3 flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <code className="block flex-1 overflow-x-auto rounded-xl bg-zinc-950 px-3 py-2 text-sm text-zinc-100">
          {command}
        </code>
        <Button
          type="button"
          variant="outline"
          onClick={handleCopy}
          className="rounded-xl border-zinc-700 bg-transparent text-zinc-200 hover:bg-zinc-900"
        >
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>
    </div>
  );
}

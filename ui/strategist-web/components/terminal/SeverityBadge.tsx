import type { ReactNode } from "react";
import type { TapeSeverity } from "@/lib/terminal/cockpit-context";

const MAP: Record<TapeSeverity, string> = {
  ok: "sev sev--ok",
  warn: "sev sev--warn",
  bad: "sev sev--bad",
  info: "sev sev--info",
  neutral: "sev sev--neutral",
};

export function SeverityBadge({ severity, children }: { severity: TapeSeverity; children: ReactNode }) {
  return <span className={MAP[severity] ?? MAP.neutral}>{children}</span>;
}

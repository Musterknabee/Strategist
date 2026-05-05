"use client";

import { isStrategistDemoModeEnabled } from "@/lib/config/public-config";

export function DemoModeBanner() {
  if (!isStrategistDemoModeEnabled()) return null;
  return (
    <div className="demo-mode-banner" role="status" aria-label="Demo mode safety banner">
      <strong>DEMO MODE</strong>
      <span>Synthetic read-plane data only</span>
      <span>No backend readiness claim</span>
      <span>No provider credentials</span>
      <span>No deployment approval</span>
      <span>No operator signoff</span>
      <span>No live trading or broker orders</span>
      <span>No profitability claim</span>
    </div>
  );
}

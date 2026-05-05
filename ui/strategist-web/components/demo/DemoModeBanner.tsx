"use client";

import { isStrategistDemoModeEnabled } from "@/lib/config/public-config";

export function DemoModeBanner() {
  if (!isStrategistDemoModeEnabled()) return null;
  return (
    <div className="demo-mode-banner" role="status" aria-label="Demo mode safety banner">
      <strong>DEMO MODE</strong>
      <span>No real backend evidence</span>
      <span>No deployment approval</span>
      <span>No live execution</span>
      <span>Synthetic data only</span>
    </div>
  );
}

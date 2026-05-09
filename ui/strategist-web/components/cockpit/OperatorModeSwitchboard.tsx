"use client";

import type { OperatorModeDefinition, OperatorModeId } from "@/lib/operator/operator-modes";
import { OPERATOR_MODE_IDS } from "@/lib/operator/operator-modes";

export type OperatorModeSwitchboardProps = {
  mode: OperatorModeId;
  onChange: (mode: OperatorModeId) => void;
  definition: OperatorModeDefinition;
  nextFocusLines: readonly string[];
  /** Post-grid section order for the active mode (for transparency). */
  postGridOrderPreview: readonly string[];
};

export function OperatorModeSwitchboard({
  mode,
  onChange,
  definition,
  nextFocusLines,
  postGridOrderPreview,
}: OperatorModeSwitchboardProps) {
  const commandCapable = definition.safety === "COMMAND_CAPABLE";

  return (
    <section className="operator-mode-switchboard" data-testid="cockpit-mode-switchboard" aria-label="Operator mode">
      <header className="operator-mode-switchboard__head">
        <span className="operator-mode-switchboard__title">Operator mode</span>
        <span className="operator-mode-switchboard__current" data-testid="cockpit-mode-current-label">
          {definition.label}
        </span>
      </header>

      <div className="operator-mode-switchboard__toolbar">
        {OPERATOR_MODE_IDS.map((id) => (
          <button
            key={id}
            type="button"
            className={`operator-mode-chip${id === mode ? " operator-mode-chip--active" : ""}`}
            data-testid={`cockpit-mode-select-${id}`}
            onClick={() => onChange(id)}
          >
            {id.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      <p className="operator-mode-switchboard__purpose">{definition.purpose}</p>

      {commandCapable && definition.command_warning ? (
        <div className="operator-mode-switchboard__banner operator-mode-switchboard__banner--warn" data-testid="cockpit-mode-command-banner">
          <strong>Command-capable mode</strong> — {definition.command_warning}
        </div>
      ) : (
        <div className="operator-mode-switchboard__banner operator-mode-switchboard__banner--muted" data-testid="cockpit-mode-readonly-banner">
          <strong>Read-plane mode</strong> — operator command cockpit hidden; no shell execution from browser.
        </div>
      )}

      <div className="operator-mode-switchboard__columns">
        <div>
          <h3 className="operator-mode-switchboard__sub">Primary panes (intent)</h3>
          <ul className="operator-mode-switchboard__list" data-testid="cockpit-mode-primary-panes">
            {definition.primary_panes.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="operator-mode-switchboard__sub">Secondary panes</h3>
          <ul className="operator-mode-switchboard__list" data-testid="cockpit-mode-secondary-panes">
            {definition.secondary_panes.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="operator-mode-switchboard__focus">
        <h3 className="operator-mode-switchboard__sub">Next review focus (derived, not approval)</h3>
        <p className="operator-mode-switchboard__meta">Source: {definition.recommended_next_action_source}</p>
        <ul className="operator-mode-switchboard__list" data-testid="cockpit-mode-next-focus">
          {nextFocusLines.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </div>

      <details className="operator-mode-switchboard__details">
        <summary>Post–seven-pane render order (UI only)</summary>
        <code className="operator-mode-switchboard__order-preview">{postGridOrderPreview.join(" → ")}</code>
      </details>
    </section>
  );
}

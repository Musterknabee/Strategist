# Next Slice Ledger — Paper Evidence-Chain Export Handoff Manifest

## Slice

Add a read-only paper evidence-chain export handoff manifest after closure verification.

## Operator value

Closure verification proves the final review packet and its referenced artifacts still hash-match. The export handoff manifest turns that verified chain into a deterministic retention inventory so an operator can move or retain the paper evidence package outside the repo while preserving digest accountability.

## Boundaries preserved

- No broker orders are submitted.
- No live-trading authority is introduced.
- No browser/API order controls are introduced.
- No validator ledger mutation or promotion authority is introduced.
- The export command writes only a manifest; it does not copy retained artifacts.

## Main implementation points

- `strategy_validator/application/paper_execution_evidence_bundle_export.py`
- `PaperExecutionEvidenceBundleExportEntry`
- `PaperExecutionEvidenceBundleExportManifestArtifact`
- `PaperExecutionEvidenceBundleExportManifestView`
- CLI command: `strategy-validator-paper-broker export-evidence-bundle-chain`
- `/ui/paper-execution/latest` payload now surfaces export handoff status and latest manifest.
- Daily operator-run summary includes export handoff counters.
- Frontend paper execution cockpit shows export handoff status, digest index, retained entry counts, and blockers/warnings.

## Validation

- New app tests cover ready export and tampered retained artifact blocking.
- New CLI test covers manifest creation through `strategy-validator-paper-broker export-evidence-bundle-chain`.
- Existing closure-verification, cockpit, daily operator-run, and paper bundle tests were run in focused groups.

import type { QueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/lib/query/keys";

const OPERATOR_BOARD = "operator";
const RUNTIME_ROLE = "operator";

function normalizePath(pathname: string): string {
  const t = pathname.trim();
  if (!t || t === "/") return "/";
  return t.replace(/\/+$/, "") || "/";
}

/**
 * Invalidate TanStack Query caches for hooks used by the given App Router path.
 * Unknown paths fall back to full strategist invalidation.
 */
export function invalidateQueriesForRoute(client: QueryClient, pathname: string): void {
  const p = normalizePath(pathname);
  const inv = (key: readonly unknown[]) => {
    void client.invalidateQueries({ queryKey: [...key] });
  };

  switch (p) {
    case "/":
      inv(queryKeys.uiFacade);
      inv(queryKeys.probeApiRoot);
      inv(queryKeys.probeHealthz);
      inv(queryKeys.probeReadyz);
      inv(queryKeys.uiHealth);
      inv(queryKeys.uiWorkboard(OPERATOR_BOARD));
      inv(queryKeys.uiProviderHealth);
      inv(queryKeys.uiEvidence(undefined));
      inv(queryKeys.uiOperatorActions);
      break;
    case "/workboard":
      inv(queryKeys.uiFacade);
      inv(queryKeys.uiWorkboard(OPERATOR_BOARD));
      break;
    case "/readiness":
      inv(queryKeys.probeHealthz);
      inv(queryKeys.probeLivez);
      inv(queryKeys.probeReadyz);
      inv(queryKeys.uiHealth);
      break;
    case "/evidence":
      inv(queryKeys.uiEvidence(undefined));
      break;
    case "/evidence-chain":
      inv(queryKeys.uiEvidenceChain);
      break;
    case "/evidence-bundles":
      inv(queryKeys.uiEvidenceBundles);
      break;
    case "/operator-packs":
      inv(queryKeys.uiOperatorPackWorkbench);
      break;
    case "/operator-actions":
      inv(queryKeys.uiOperatorActions);
      break;
    case "/operator-command-policy":
      inv(queryKeys.uiOperatorCommandPolicy({}));
      break;
    case "/ledger":
      inv(queryKeys.uiOperatorActions);
      break;
    case "/tribunal":
      inv(queryKeys.uiTribunal);
      break;
    case "/providers":
      inv(queryKeys.uiProviderHealth);
      break;
    case "/market-data-integrity":
      inv(queryKeys.uiMarketDataIntegrity);
      break;
    case "/backtest-forensics":
      inv(queryKeys.uiBacktestForensicsLatest);
      break;
    case "/promotion-review":
      inv(queryKeys.uiPromotionReview);
      break;
    case "/runtime":
      inv(queryKeys.uiRuntime(RUNTIME_ROLE));
      inv(queryKeys.uiFacade);
      inv(queryKeys.uiResearchCompute);
      inv(queryKeys.probeApiRoot);
      break;
    case "/research-compute":
      inv(queryKeys.uiResearchCompute);
      break;
    case "/projection-registry":
      inv(queryKeys.uiProjectionRegistry);
      break;
    case "/semantic-release":
      inv(queryKeys.uiSemanticRelease);
      break;
    case "/semantic-validator-handoff":
      inv(queryKeys.uiSemanticValidatorHandoff);
      break;
    case "/semantic-validator-handoff-lineage":
      inv(queryKeys.uiSemanticValidatorHandoffLineage);
      break;
    case "/semantic-validator-handoff-remediation":
      inv(queryKeys.uiSemanticValidatorHandoffRemediation);
      break;
    case "/semantic-validator-handoff-review":
      inv(queryKeys.uiSemanticValidatorHandoffReview);
      break;
    case "/semantic-validator-handoff-decision":
      inv(queryKeys.uiSemanticValidatorHandoffDecision);
      break;
    case "/semantic-validator-handoff-signoff":
      inv(queryKeys.uiSemanticValidatorHandoffSignoff);
      break;
    case "/semantic-validator-handoff-custody":
      inv(queryKeys.uiSemanticValidatorHandoffCustody);
      break;
    case "/semantic-validator-handoff-archive":
      inv(queryKeys.uiSemanticValidatorHandoffArchive);
      break;
    case "/semantic-validator-handoff-closure":
      inv(queryKeys.uiSemanticValidatorHandoffClosure);
      break;
    case "/semantic-validator-handoff-continuity":
      inv(queryKeys.uiSemanticValidatorHandoffContinuity);
      break;
    case "/semantic-validator-handoff-runbook":
      inv(queryKeys.uiSemanticValidatorHandoffRunbook);
      break;
    case "/semantic-validator-handoff-exceptions":
      inv(queryKeys.uiSemanticValidatorHandoffExceptions);
      break;
    case "/semantic-validator-handoff-timeline":
      inv(queryKeys.uiSemanticValidatorHandoffTimeline);
      break;
    case "/semantic-validator-handoff-evidence-gaps":
      inv(queryKeys.uiSemanticValidatorHandoffEvidenceGaps);
      break;
    case "/semantic-validator-handoff-audit-packet":
      inv(queryKeys.uiSemanticValidatorHandoffAuditPacket);
      break;
    case "/semantic-validator-handoff-action-queue":
      inv(queryKeys.uiSemanticValidatorHandoffActionQueue);
      break;
    case "/semantic-validator-handoff-escalation-board":
      inv(queryKeys.uiSemanticValidatorHandoffEscalationBoard);
      break;
    case "/semantic-validator-handoff-resolution-plan":
      inv(queryKeys.uiSemanticValidatorHandoffResolutionPlan);
      break;
    case "/semantic-validator-handoff-clearance-gate":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceGate);
      break;
    case "/semantic-validator-handoff-clearance-dossier":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceDossier);
      break;
    case "/semantic-validator-handoff-clearance-checklist":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceChecklist);
      break;
    case "/semantic-validator-handoff-clearance-evidence-matrix":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceEvidenceMatrix);
      break;
    case "/semantic-validator-handoff-clearance-coverage-board":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceCoverageBoard);
      break;
    case "/semantic-validator-handoff-clearance-operations-board":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceOperationsBoard);
      break;
    case "/semantic-validator-handoff-clearance-action-register":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceActionRegister);
      break;
    case "/semantic-validator-handoff-clearance-resolution-plan":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceResolutionPlan);
      break;
    case "/semantic-validator-handoff-clearance-verification-board":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceVerificationBoard);
      break;
    case "/semantic-validator-handoff-clearance-closeout-board":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceCloseoutBoard);
      break;
    case "/semantic-validator-handoff-clearance-review-docket":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceReviewDocket);
      break;
    case "/semantic-validator-handoff-clearance-signoff-packet":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceSignoffPacket);
      break;
    case "/semantic-validator-handoff-clearance-acceptance-board":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceAcceptanceBoard);
      break;
    case "/semantic-validator-handoff-clearance-release-readiness-board":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceReleaseReadinessBoard);
      break;
    case "/semantic-validator-handoff-clearance-release-packet":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceReleasePacket);
      break;
    case "/semantic-validator-handoff-clearance-release-handoff-board":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceReleaseHandoffBoard);
      break;
    case "/semantic-validator-handoff-clearance-release-custody-board":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceReleaseCustodyBoard);
      break;
    case "/semantic-validator-handoff-clearance-release-receipt-board":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceReleaseReceiptBoard);
      break;
    case "/semantic-validator-handoff-clearance-release-acknowledgment-board":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceReleaseAcknowledgmentBoard);
      break;
    case "/semantic-validator-handoff-clearance-release-confirmation-board":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceReleaseConfirmationBoard);
      break;
    case "/semantic-validator-handoff-clearance-release-completion-board":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceReleaseCompletionBoard);
      break;
    case "/semantic-validator-handoff-clearance-release-closure-board":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceReleaseClosureBoard);
      break;
    case "/semantic-validator-handoff-clearance-release-archive-board":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceReleaseArchiveBoard);
      break;
    case "/semantic-validator-handoff-clearance-release-retention-board":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceReleaseRetentionBoard);
      break;
    case "/semantic-validator-handoff-clearance-release-disposition-board":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceReleaseDispositionBoard);
      break;
    case "/semantic-validator-handoff-clearance-release-disposal-board":
      inv(queryKeys.uiSemanticValidatorHandoffClearanceReleaseDisposalBoard);
      break;
    case "/strategy-lab":
      inv(queryKeys.uiStrategyBatchesLatest);
      inv(queryKeys.uiStrategyBatchesList);
      inv(queryKeys.uiBacktestForensicsLatest);
      break;
    case "/paper-tracking":
      inv(queryKeys.uiPaperTrackingLatest);
      break;
    default:
      void client.invalidateQueries({
        predicate: (q) => Array.isArray(q.queryKey) && q.queryKey[0] === "strategist",
      });
  }
}

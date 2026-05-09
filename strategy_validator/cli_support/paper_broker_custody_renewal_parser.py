"""Retention custody renewal parser registration for the paper broker CLI."""
from __future__ import annotations

import argparse
from pathlib import Path


def register_custody_renewal_parsers(sub: argparse._SubParsersAction) -> None:
    s_renew_retention_custody = sub.add_parser(
        "renew-evidence-bundle-retention-custody",
        help="Write a read-only renewal certificate for a verified paper evidence-chain retention custody review.",
    )
    s_renew_retention_custody.add_argument(
        "--retention-custody-review-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_review_verification.json path. Defaults to latest custody review verification.",
    )
    s_renew_retention_custody.add_argument("--renewed-by", default="operator", help="Operator identity recorded in the custody renewal.")
    s_renew_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody renewal.")
    s_renew_retention_custody.add_argument("--renewal-interval-days", type=int, default=30, help="Number of days until the next custody renewal is due.")
    s_renew_retention_custody.add_argument("--renewal-note", default="", help="Optional short custody renewal note.")
    s_renew_retention_custody.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody renewal evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention_custody_renewal = sub.add_parser(
        "verify-evidence-bundle-retention-custody-renewal",
        help="Verify a paper evidence-chain retention custody renewal artifact.",
    )
    s_verify_retention_custody_renewal.add_argument(
        "--retention-custody-renewal-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_renewal.json path. Defaults to latest custody renewal.",
    )
    s_verify_retention_custody_renewal.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody renewal verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_schedule_retention_custody = sub.add_parser(
        "schedule-evidence-bundle-retention-custody-renewal",
        help="Write a read-only schedule for the next verified paper evidence-chain retention custody renewal.",
    )
    s_schedule_retention_custody.add_argument(
        "--retention-custody-renewal-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_renewal_verification.json path. Defaults to latest custody renewal verification.",
    )
    s_schedule_retention_custody.add_argument("--scheduled-by", default="operator", help="Operator identity recorded in the custody renewal schedule.")
    s_schedule_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody renewal schedule.")
    s_schedule_retention_custody.add_argument("--reminder-days-before-due", type=int, default=7, help="Reminder lead time before the next custody renewal due date.")
    s_schedule_retention_custody.add_argument("--schedule-note", default="", help="Optional short custody schedule note.")
    s_schedule_retention_custody.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody schedule evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention_custody_schedule = sub.add_parser(
        "verify-evidence-bundle-retention-custody-schedule",
        help="Verify a paper evidence-chain retention custody renewal schedule artifact.",
    )
    s_verify_retention_custody_schedule.add_argument(
        "--retention-custody-schedule-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_schedule.json path. Defaults to latest custody renewal schedule.",
    )
    s_verify_retention_custody_schedule.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody schedule verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_notice_retention_custody = sub.add_parser(
        "notice-evidence-bundle-retention-custody-renewal",
        help="Write a read-only operator notice for a verified paper evidence-chain retention custody renewal schedule.",
    )
    s_notice_retention_custody.add_argument(
        "--retention-custody-schedule-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_schedule_verification.json path. Defaults to latest custody renewal schedule verification.",
    )
    s_notice_retention_custody.add_argument("--notified-by", default="operator", help="Operator identity recorded in the custody renewal notice.")
    s_notice_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody renewal notice.")
    s_notice_retention_custody.add_argument("--notice-note", default="", help="Optional short custody renewal notice note.")
    s_notice_retention_custody.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody notice evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention_custody_notice = sub.add_parser(
        "verify-evidence-bundle-retention-custody-notice",
        help="Verify a paper evidence-chain retention custody renewal notice artifact.",
    )
    s_verify_retention_custody_notice.add_argument(
        "--retention-custody-notice-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_notice.json path. Defaults to latest custody renewal notice.",
    )
    s_verify_retention_custody_notice.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody notice verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_ack_retention_custody_notice = sub.add_parser(
        "acknowledge-evidence-bundle-retention-custody-notice",
        help="Write a read-only operator acknowledgment for a verified paper evidence-chain retention custody renewal notice.",
    )
    s_ack_retention_custody_notice.add_argument(
        "--retention-custody-notice-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_notice_verification.json path. Defaults to latest custody renewal notice verification.",
    )
    s_ack_retention_custody_notice.add_argument("--acknowledged-by", default="operator", help="Operator identity recorded in the custody renewal notice acknowledgment.")
    s_ack_retention_custody_notice.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody renewal notice acknowledgment.")
    s_ack_retention_custody_notice.add_argument("--acknowledgment-note", default="", help="Optional short custody renewal notice acknowledgment note.")
    s_ack_retention_custody_notice.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody acknowledgment evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention_custody_acknowledgment = sub.add_parser(
        "verify-evidence-bundle-retention-custody-acknowledgment",
        help="Verify a paper evidence-chain retention custody renewal notice acknowledgment artifact.",
    )
    s_verify_retention_custody_acknowledgment.add_argument(
        "--retention-custody-acknowledgment-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_acknowledgment.json path. Defaults to latest custody renewal notice acknowledgment.",
    )
    s_verify_retention_custody_acknowledgment.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody acknowledgment verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_complete_retention_custody_renewal = sub.add_parser(
        "complete-evidence-bundle-retention-custody-renewal",
        help="Write a read-only completion record for an acknowledged paper evidence-chain retention custody renewal.",
    )
    s_complete_retention_custody_renewal.add_argument(
        "--retention-custody-acknowledgment-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_acknowledgment_verification.json path. Defaults to latest custody acknowledgment verification.",
    )
    s_complete_retention_custody_renewal.add_argument("--completed-by", default="operator", help="Operator identity recorded in the custody renewal completion.")
    s_complete_retention_custody_renewal.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody renewal completion.")
    s_complete_retention_custody_renewal.add_argument("--completion-note", default="", help="Optional short custody renewal completion note.")
    s_complete_retention_custody_renewal.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody completion evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention_custody_completion = sub.add_parser(
        "verify-evidence-bundle-retention-custody-completion",
        help="Verify a paper evidence-chain retention custody completion artifact.",
    )
    s_verify_retention_custody_completion.add_argument(
        "--retention-custody-completion-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_completion.json path. Defaults to latest custody completion.",
    )
    s_verify_retention_custody_completion.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody completion verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_closeout_retention_custody = sub.add_parser(
        "closeout-evidence-bundle-retention-custody-renewal",
        help="Write a read-only closeout record for a verified paper evidence-chain retention custody renewal completion.",
    )
    s_closeout_retention_custody.add_argument(
        "--retention-custody-completion-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_completion_verification.json path. Defaults to latest custody completion verification.",
    )
    s_closeout_retention_custody.add_argument("--closed-out-by", default="operator", help="Operator identity recorded in the custody closeout.")
    s_closeout_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody closeout.")
    s_closeout_retention_custody.add_argument("--closeout-note", default="", help="Optional short custody closeout note.")
    s_closeout_retention_custody.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody closeout evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention_custody_closeout = sub.add_parser(
        "verify-evidence-bundle-retention-custody-closeout",
        help="Verify a paper evidence-chain retention custody closeout artifact.",
    )
    s_verify_retention_custody_closeout.add_argument(
        "--retention-custody-closeout-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_closeout.json path. Defaults to latest custody closeout.",
    )
    s_verify_retention_custody_closeout.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody closeout verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

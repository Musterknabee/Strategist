from __future__ import annotations


def classify_review_state(*, approval_needed: bool = False, approval_status: str | None = None, supervisor_required: bool = False) -> str:
    status = (approval_status or '').strip().upper()
    if status in {'APPROVED', 'DECLINED', 'REJECTED'}:
        return status
    if supervisor_required:
        return 'SUPERVISOR_REVIEW_REQUIRED'
    if approval_needed:
        return 'APPROVAL_NEEDED'
    return 'NO_REVIEW_REQUIRED'



def requires_supervisor_review(*, approval_needed: bool = False, approval_status: str | None = None, supervisor_required: bool = False) -> bool:
    return classify_review_state(
        approval_needed=approval_needed,
        approval_status=approval_status,
        supervisor_required=supervisor_required,
    ) == 'SUPERVISOR_REVIEW_REQUIRED'

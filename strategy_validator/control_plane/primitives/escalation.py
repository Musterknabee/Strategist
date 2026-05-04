from __future__ import annotations


def _normalize(value: str | None, default: str = '') -> str:
    return (value or default).strip().upper()


PRIORITY_ORDER = {
    'CRITICAL': 4,
    'HIGH': 3,
    'MEDIUM': 2,
    'LOW': 1,
    'INFO': 0,
}



def classify_priority_band(priority_band: str | None) -> str:
    normalized = _normalize(priority_band, 'MEDIUM')
    if normalized in PRIORITY_ORDER:
        return normalized
    if normalized.startswith('P0'):
        return 'CRITICAL'
    if normalized.startswith('P1'):
        return 'HIGH'
    if normalized.startswith('P2'):
        return 'MEDIUM'
    if normalized.startswith('P3'):
        return 'LOW'
    return 'MEDIUM'



def is_escalated_status(status: str | None) -> bool:
    normalized = _normalize(status)
    return 'ESCALAT' in normalized or normalized in {'BREACHED', 'ATTENTION_REQUIRED', 'SUPERVISOR_REVIEW'}



def summarize_escalation_posture(priority_band: str | None, status: str | None) -> str:
    priority = classify_priority_band(priority_band)
    if is_escalated_status(status):
        return f'ESCALATED_{priority}'
    return f'ROUTED_{priority}'

from __future__ import annotations

from typing import Any

from strategy_validator.application.research_integrity_common import _sha256_payload
from strategy_validator.contracts.semantic_validator_handoff import (
    SemanticValidatorHandoffPacketIngressCertificate,
)


def _validator_handoff_packet_ingress_certificate_checksum_payload(
    certificate: SemanticValidatorHandoffPacketIngressCertificate,
) -> dict[str, Any]:
    """Return the canonical certificate payload excluding its self-checksum."""

    payload = certificate.model_dump(mode="json")
    payload.pop("payload_checksum", None)
    return payload


def _validator_handoff_packet_ingress_certificate_payload_checksum(
    certificate: SemanticValidatorHandoffPacketIngressCertificate,
) -> str:
    """Compute the canonical payload checksum for a validator-ingress certificate."""

    return _sha256_payload(_validator_handoff_packet_ingress_certificate_checksum_payload(certificate))


__all__ = [
    "_validator_handoff_packet_ingress_certificate_checksum_payload",
    "_validator_handoff_packet_ingress_certificate_payload_checksum",
]

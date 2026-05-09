from __future__ import annotations

from typing import Any, Mapping

from strategy_validator.application.ui_workboard_intelligence_foundations import (
    _unique_nonempty_paths,
)

def _build_action_provenance(
    *,
    entry: Mapping[str, Any],
    linked_pack: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if linked_pack is None:
        empty_targets = [
            {
                'action': action,
                'anchor_kind': 'UNLINKED',
                'target_label': 'lineage unavailable',
                'target_path': None,
                'supporting_paths': [],
                'rationale': 'No linked pack/publication is indexed yet, so this command has no evidence anchor path.',
            }
            for action in ('claim-item', 'acknowledge-reentry', 'renew-lease')
        ]
        return {
            'summary_line': 'No linked pack/publication is available, so command provenance remains unresolved.',
            'linkage_basis_line': 'The current queue item has not yet been matched to an indexed pack lineage.',
            'matched_terms': [],
            'evidence_anchor_count': 0,
            'anchor_paths': [],
            'anchor_labels': [],
            'pack_root': None,
            'pack_manifest_path': None,
            'primary_publication_path': None,
            'command_targets': empty_targets,
        }

    manifest_path = str(linked_pack.get('manifest_path') or '') or None
    primary_publication_path = str(linked_pack.get('primary_output_artifact_path') or '') or None
    pack_root = str(linked_pack.get('pack_root') or '') or None
    matched_terms = [str(token) for token in (linked_pack.get('linkage_basis', {}) or {}).get('matched_terms', []) or []]
    direct_phrase = bool((linked_pack.get('linkage_basis', {}) or {}).get('direct_phrase'))
    pack_kind = str(linked_pack.get('pack_kind') or 'operator_pack')
    review_target = str(entry.get('review_target') or 'work item')
    anchor_paths = _unique_nonempty_paths(
        manifest_path,
        primary_publication_path,
        extra_paths=[str(path) for path in linked_pack.get('output_artifact_paths', []) or []],
    )
    anchor_labels = ['manifest', 'primary_publication']
    for label in [str(label) for label in linked_pack.get('output_artifact_labels', []) or []]:
        if label and label not in anchor_labels:
            anchor_labels.append(label)

    if matched_terms:
        linkage_basis_line = (
            f"Queue target '{review_target}' maps to {pack_kind} via token overlap on: {', '.join(matched_terms)}."
        )
    elif direct_phrase:
        linkage_basis_line = f"Queue target '{review_target}' directly names the {pack_kind} lineage."
    else:
        linkage_basis_line = f"Queue target '{review_target}' is attached to the best available {pack_kind} lineage."

    summary_line = (
        f"Commands on this item will anchor to {pack_kind} evidence rooted at "
        f"{primary_publication_path or manifest_path or 'the indexed pack lineage'}."
    )

    command_targets = [
        {
            'action': 'claim-item',
            'anchor_kind': 'PACK_MANIFEST',
            'target_label': 'pack manifest',
            'target_path': manifest_path,
            'supporting_paths': anchor_paths,
            'rationale': 'Claiming should attach operator ownership to the current pack manifest and its supporting evidence chain.',
        },
        {
            'action': 'acknowledge-reentry',
            'anchor_kind': 'PUBLICATION_ARTIFACT' if primary_publication_path else 'PACK_MANIFEST',
            'target_label': 'primary publication' if primary_publication_path else 'pack manifest',
            'target_path': primary_publication_path or manifest_path,
            'supporting_paths': anchor_paths,
            'rationale': 'Re-entry acknowledgement should point at the operator-visible publication that reflects the current posture.',
        },
        {
            'action': 'renew-lease',
            'anchor_kind': 'EVIDENCE_CHAIN',
            'target_label': 'lease evidence chain',
            'target_path': primary_publication_path or manifest_path,
            'supporting_paths': anchor_paths,
            'rationale': 'Lease renewal should stay anchored to the current publication and supporting evidence artifacts.',
        },
    ]

    return {
        'summary_line': summary_line,
        'linkage_basis_line': linkage_basis_line,
        'matched_terms': matched_terms,
        'evidence_anchor_count': len(anchor_paths),
        'anchor_paths': anchor_paths,
        'anchor_labels': anchor_labels,
        'pack_root': pack_root,
        'pack_manifest_path': manifest_path,
        'primary_publication_path': primary_publication_path,
        'command_targets': command_targets,
    }


__all__ = [
    '_build_action_provenance',
]

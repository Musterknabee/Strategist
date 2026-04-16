from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

from strategy_validator.cli.oracle_temporal_runners import cmd_summarize_temporal_lane
from strategy_validator.contracts.oracle_temporal import (
    TemporalCanonicalizationBatchResult,
    TemporalEventLogAppendBatchResult,
    TemporalLaneStatus,
    TemporalSemanticBatchManifest,
    TemporalSemanticBatchVerification,
    TemporalSemanticDay,
)
from strategy_validator.contracts.oracle import OracleSensorRawSemanticInput
from strategy_validator.validator.oracle_diagnostics_builders import _build_oracle_status_pack_impl


def _manifest() -> TemporalSemanticBatchManifest:
    semantic = OracleSensorRawSemanticInput(
        hawkish_document_ratio=0.55,
        dovish_document_ratio=0.45,
        geopolitical_headline_share=0.2,
        contradiction_count=1,
        belief_conflict_score=0.3,
    )
    return TemporalSemanticBatchManifest(
        provider_kind='NVIDIA_NIM',
        provider_id='nvidia_nim',
        model_name='minimaxai/minimax-m2.7',
        batch_start_date=date(2026, 1, 5),
        batch_end_date=date(2026, 1, 6),
        days=[
            TemporalSemanticDay(
                point_in_time_date=date(2026, 1, 5),
                trading_session_id='2026-01-05',
                semantic_raw=semantic,
                allowed_prefix_digest_sha256='a'*64,
            ),
            TemporalSemanticDay(
                point_in_time_date=date(2026, 1, 6),
                trading_session_id='2026-01-06',
                semantic_raw=semantic,
                allowed_prefix_digest_sha256='b'*64,
            ),
        ],
    )


def test_cli_summarize_temporal_lane_writes_standard_artifact(tmp_path: Path) -> None:
    manifest = _manifest()
    verification = TemporalSemanticBatchVerification(
        provider_id=manifest.provider_id,
        model_name=manifest.model_name,
        batch_start_date=manifest.batch_start_date,
        batch_end_date=manifest.batch_end_date,
        status='VERIFIED',
        accepted_dates=[date(2026, 1, 5), date(2026, 1, 6)],
        rejected_dates=[],
    )
    canonicalization = TemporalCanonicalizationBatchResult(
        provider_id=manifest.provider_id,
        model_name=manifest.model_name,
        universe_label='macro-us',
        output_root=str(tmp_path / 'canonical'),
        verification_status='VERIFIED',
        canonicalized_dates=[date(2026, 1, 5), date(2026, 1, 6)],
        skipped_dates=[],
    )
    append_report = TemporalEventLogAppendBatchResult(
        provider_id=manifest.provider_id,
        model_name=manifest.model_name,
        universe_label='macro-us',
        lane_path=str(tmp_path / 'ORACLE_EVENT_LOG.jsonl'),
        canonicalization_output_root=str(tmp_path / 'canonical'),
        canonicalization_verification_status='VERIFIED',
        appended_dates=[date(2026, 1, 5), date(2026, 1, 6)],
        skipped_dates=[],
        summary_line='ok',
    )
    paths = {
        'manifest': tmp_path / 'manifest.json',
        'verification': tmp_path / 'verification.json',
        'canonicalization': tmp_path / 'canonicalization.json',
        'append': tmp_path / 'append.json',
        'output': tmp_path / 'status_payload.json',
        'artifact_root': tmp_path / 'artifacts',
    }
    paths['manifest'].write_text(json.dumps(manifest.model_dump(mode='json')), encoding='utf-8')
    paths['verification'].write_text(json.dumps(verification.model_dump(mode='json')), encoding='utf-8')
    paths['canonicalization'].write_text(json.dumps(canonicalization.model_dump(mode='json')), encoding='utf-8')
    paths['append'].write_text(json.dumps(append_report.model_dump(mode='json')), encoding='utf-8')

    class NS:
        manifest = str(paths['manifest'])
        universe_label = 'macro-us'
        verification = str(paths['verification'])
        canonicalization = str(paths['canonicalization'])
        append_report = str(paths['append'])
        output = str(paths['output'])
        artifact_root = str(paths['artifact_root'])

    assert cmd_summarize_temporal_lane(NS()) == 0
    artifact_path = paths['artifact_root'] / 'ORACLE_TEMPORAL_LANE_STATUS.json'
    status = TemporalLaneStatus.model_validate(json.loads(artifact_path.read_text(encoding='utf-8')))
    assert status.appended_days == 2
    assert status.verification_status == 'VERIFIED'


def test_status_pack_impl_embeds_temporal_lane_section(tmp_path: Path) -> None:
    temporal_status = TemporalLaneStatus(
        provider_id='nvidia_nim',
        model_name='minimaxai/minimax-m2.7',
        universe_label='macro-us',
        batch_start_date=date(2026, 1, 5),
        batch_end_date=date(2026, 1, 6),
        extraction_days=2,
        verified_days=2,
        rejected_days=0,
        canonicalized_days=2,
        canonicalization_skipped_days=0,
        appended_days=2,
        append_skipped_days=0,
        verification_status='VERIFIED',
        canonicalization_verification_status='VERIFIED',
        append_lane_path=str(tmp_path / 'ORACLE_EVENT_LOG.jsonl'),
        summary_line='Temporal lane healthy.',
        operator_lines=['Temporal lane healthy.', 'Verification status: VERIFIED.'],
        generated_at_utc=datetime.now(timezone.utc),
    )
    search_root = tmp_path / 'artifacts'
    search_root.mkdir()
    temporal_path = search_root / 'ORACLE_TEMPORAL_LANE_STATUS.json'
    temporal_path.write_text(json.dumps(temporal_status.model_dump(mode='json')), encoding='utf-8')

    report = _build_oracle_status_pack_impl(repo_root=tmp_path, search_root=search_root)
    section = next((section for section in report.sections if section.section_id == 'temporal_lane'), None)
    assert section is not None
    assert section.summary_line == 'Temporal lane healthy.'
    assert any('provider_id=nvidia_nim' == fact for fact in section.facts)
    assert any('Verification status: VERIFIED.' == action for action in section.operator_actions)
    assert 'Verification status: VERIFIED.' in report.operator_actions

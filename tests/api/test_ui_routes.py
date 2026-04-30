from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import app


def test_ui_workboard_route_uses_service(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_payload',
        lambda **_: {'schema_version': 'ui_workboard_dashboard/v1', 'board_label': 'operator', 'stats': {'active_count': 3}},
    )
    client = TestClient(app)
    response = client.get('/ui/workboard')
    assert response.status_code == 200
    payload = response.json()
    assert payload['schema_version'] == 'ui_workboard_dashboard/v1'
    assert payload['stats']['active_count'] == 3


def test_ui_workboard_export_route_uses_service(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_payload',
        lambda **_: {
            'schema_version': 'oracle_operator_board_export_payload/v1',
            'export_state': 'EXPORT_READY',
            'verification_state': 'VERIFIABLE',
            'payload_keys': ['board_governance_digest'],
        },
    )
    client = TestClient(app)
    response = client.get('/ui/workboard/export')
    assert response.status_code == 200
    payload = response.json()
    assert payload['schema_version'] == 'oracle_operator_board_export_payload/v1'
    assert payload['export_state'] == 'EXPORT_READY'
    assert payload['verification_state'] == 'VERIFIABLE'
    assert payload['payload_keys'] == ['board_governance_digest']

def test_ui_workboard_export_index_route_uses_service(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_index',
        lambda **_: {
            'schema_version': 'oracle_operator_board_export_index/v1',
            'verification_state': 'VERIFIABLE',
            'export_state': 'EXPORT_READY',
            'export_completeness_state': 'FULLY_EMBEDDED',
            'relative_document_path': 'generated/publications/operator/governance-main/board_export_payload.json',
            'published_relative_document_path': 'published/publications/operator/governance-main/board_export_payload.json',
            'document_sha256': 'c' * 64,
            'bundle_fingerprint_sha256': 'd' * 64,
            'document_byte_count': 101,
            'document_line_count': 5,
            'member_count': 4,
        },
    )
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_index_headers',
        lambda payload: {
            'ETag': '"sha256:' + str(payload['document_sha256']) + '"',
            'Digest': 'sha-256=indexstub',
            'X-Board-Export-Index-Route': '/ui/workboard/export/index',
            'X-Board-Export-Document-Route': '/ui/workboard/export/document',
            'Cache-Control': 'no-cache',
            'Last-Modified': 'Thu, 16 Apr 2026 12:00:00 GMT',
            'X-Board-Export-Generated-At': '2026-04-16T12:00:00+00:00',
            'X-Board-Export-Freshness-State': 'CURRENT',
            'X-Board-Export-Freshness-Basis': 'generated_at_utc',
            'X-Board-Export-Document-SHA256': str(payload['document_sha256']),
            'X-Board-Export-Bundle-Fingerprint-SHA256': str(payload['bundle_fingerprint_sha256']),
            'X-Board-Export-Relative-Path': str(payload['relative_document_path']),
            'X-Board-Export-Published-Relative-Path': str(payload['published_relative_document_path']),
            'X-Board-Export-State': str(payload['export_state']),
            'X-Board-Export-Completeness': str(payload['export_completeness_state']),
            'X-Board-Export-Verification': str(payload['verification_state']),
            'X-Board-Export-Byte-Count': str(payload['document_byte_count']),
            'X-Board-Export-Line-Count': str(payload['document_line_count']),
            'Link': '</ui/workboard/export/document>; rel="describedby", </ui/workboard/export/index>; rel="self"',
        },
    )
    client = TestClient(app)
    response = client.get('/ui/workboard/export/index')
    assert response.status_code == 200
    payload = response.json()
    assert payload['schema_version'] == 'oracle_operator_board_export_index/v1'
    assert payload['verification_state'] == 'VERIFIABLE'
    assert payload['relative_document_path'] == 'generated/publications/operator/governance-main/board_export_payload.json'
    assert payload['member_count'] == 4
    assert response.headers['etag'] == '"sha256:' + ('c' * 64) + '"'
    assert response.headers['digest'] == 'sha-256=indexstub'
    assert response.headers['x-board-export-index-route'] == '/ui/workboard/export/index'
    assert response.headers['x-board-export-document-route'] == '/ui/workboard/export/document'
    assert response.headers['cache-control'] == 'no-cache'
    assert response.headers['last-modified'] == 'Thu, 16 Apr 2026 12:00:00 GMT'
    assert response.headers['x-board-export-generated-at'] == '2026-04-16T12:00:00+00:00'
    assert response.headers['x-board-export-freshness-state'] == 'CURRENT'
    assert response.headers['x-board-export-freshness-basis'] == 'generated_at_utc'
    assert response.headers['x-board-export-document-sha256'] == 'c' * 64
    assert response.headers['x-board-export-bundle-fingerprint-sha256'] == 'd' * 64
    assert response.headers['x-board-export-relative-path'] == 'generated/publications/operator/governance-main/board_export_payload.json'
    assert response.headers['x-board-export-published-relative-path'] == 'published/publications/operator/governance-main/board_export_payload.json'
    assert response.headers['x-board-export-index-route'] == '/ui/workboard/export/index'
    assert response.headers['x-board-export-document-route'] == '/ui/workboard/export/document'
    assert response.headers['link'].startswith('</ui/workboard/export/document>; rel="describedby", </ui/workboard/export/index>; rel="self"')
    assert 'rel="profile"' in response.headers['link']
    assert response.headers['x-board-export-state'] == 'EXPORT_READY'
    assert response.headers['x-board-export-completeness'] == 'FULLY_EMBEDDED'
    assert response.headers['x-board-export-verification'] == 'VERIFIABLE'
    assert response.headers['x-board-export-byte-count'] == '101'
    assert response.headers['x-board-export-line-count'] == '5'
    assert response.headers['allow'] == 'GET, HEAD, OPTIONS'
    assert response.headers['x-board-export-allow'] == 'GET, HEAD, OPTIONS'
    assert response.headers['x-board-export-response-class'] == 'INDEX_DOCUMENT'
    assert response.headers['x-board-export-body-role'] == 'EXPORT_CATALOG'
    assert response.headers['link'].startswith('</ui/workboard/export/document>; rel="describedby", </ui/workboard/export/index>; rel="self"')
    assert 'rel="profile"' in response.headers['link']




def test_ui_workboard_export_index_head_route_returns_headers_without_body(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_index',
        lambda **_: {
            'schema_version': 'oracle_operator_board_export_index/v1',
            'generated_at_utc': '2026-04-16T12:00:00+00:00',
        },
    )
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_index_headers',
        lambda payload: {
            'ETag': '"sha256:' + ('c' * 64) + '"',
            'Cache-Control': 'no-cache',
            'Last-Modified': 'Thu, 16 Apr 2026 12:00:00 GMT',
            'X-Board-Export-Generated-At': '2026-04-16T12:00:00+00:00',
            'X-Board-Export-Freshness-State': 'CURRENT',
            'X-Board-Export-Freshness-Basis': 'generated_at_utc',
            'X-Board-Export-Document-SHA256': 'c' * 64,
            'X-Board-Export-Bundle-Fingerprint-SHA256': 'd' * 64,
            'X-Board-Export-Relative-Path': 'generated/publications/operator/governance-main/board_export_payload.json',
            'X-Board-Export-Published-Relative-Path': 'published/publications/operator/governance-main/board_export_payload.json',
            'X-Board-Export-Index-Route': '/ui/workboard/export/index',
            'X-Board-Export-Document-Route': '/ui/workboard/export/document',
            'X-Board-Export-State': 'EXPORT_READY',
            'X-Board-Export-Completeness': 'FULLY_EMBEDDED',
            'X-Board-Export-Verification': 'VERIFIABLE',
            'X-Board-Export-Byte-Count': '101',
            'X-Board-Export-Line-Count': '5',
            'Link': '</ui/workboard/export/document>; rel="describedby", </ui/workboard/export/index>; rel="self"',
        },
    )
    client = TestClient(app)
    response = client.head('/ui/workboard/export/index')
    assert response.status_code == 200
    assert response.text == ''
    assert response.headers['etag'] == '"sha256:' + ('c' * 64) + '"'
    assert response.headers['last-modified'] == 'Thu, 16 Apr 2026 12:00:00 GMT'
    assert response.headers['x-board-export-index-route'] == '/ui/workboard/export/index'
    assert response.headers['x-board-export-document-route'] == '/ui/workboard/export/document'
    assert response.headers['allow'] == 'GET, HEAD, OPTIONS'
    assert response.headers['x-board-export-allow'] == 'GET, HEAD, OPTIONS'
    assert response.headers['x-board-export-response-class'] == 'INDEX_DOCUMENT'
    assert response.headers['x-board-export-body-role'] == 'EXPORT_CATALOG'


def test_ui_workboard_export_document_head_route_returns_headers_without_body(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_document',
        lambda **_: {
            'schema_version': 'oracle_operator_board_export_document/v1',
            'canonical_json': '{\n  "schema_version": "oracle_operator_board_export_payload/v1"\n}\n',
            'document_sha256': 'a' * 64,
            'relative_document_path': 'generated/publications/operator/governance-main/board_export_payload.json',
            'published_relative_document_path': 'published/publications/operator/governance-main/board_export_payload.json',
            'export_state': 'EXPORT_READY',
            'export_completeness_state': 'FULLY_EMBEDDED',
            'verification_state': 'VERIFIABLE',
            'byte_count': 95,
            'line_count': 4,
            'canonical_payload': {'bundle_fingerprint_sha256': 'b' * 64},
        },
    )
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_document_headers',
        lambda document: {
            'ETag': '"sha256:' + str(document['document_sha256']) + '"',
            'Cache-Control': 'no-cache',
            'Last-Modified': 'Thu, 16 Apr 2026 12:00:00 GMT',
            'X-Board-Export-Generated-At': '2026-04-16T12:00:00+00:00',
            'X-Board-Export-Freshness-State': 'CURRENT',
            'X-Board-Export-Freshness-Basis': 'generated_at_utc',
            'X-Board-Export-Document-SHA256': str(document['document_sha256']),
            'X-Board-Export-Bundle-Fingerprint-SHA256': str(document['canonical_payload']['bundle_fingerprint_sha256']),
            'X-Board-Export-Relative-Path': str(document['relative_document_path']),
            'X-Board-Export-Published-Relative-Path': str(document['published_relative_document_path']),
            'X-Board-Export-Index-Route': '/ui/workboard/export/index',
            'X-Board-Export-Document-Route': '/ui/workboard/export/document',
            'X-Board-Export-State': str(document['export_state']),
            'X-Board-Export-Completeness': str(document['export_completeness_state']),
            'X-Board-Export-Verification': str(document['verification_state']),
            'X-Board-Export-Byte-Count': str(document['byte_count']),
            'X-Board-Export-Line-Count': str(document['line_count']),
            'Digest': 'sha-256=stubbed',
            'Link': '</ui/workboard/export/index>; rel="index", </ui/workboard/export/document>; rel="self"',
        },
    )
    client = TestClient(app)
    response = client.head('/ui/workboard/export/document')
    assert response.status_code == 200
    assert response.text == ''
    assert response.headers['etag'] == '"sha256:' + ('a' * 64) + '"'
    assert response.headers['last-modified'] == 'Thu, 16 Apr 2026 12:00:00 GMT'
    assert response.headers['x-board-export-index-route'] == '/ui/workboard/export/index'
    assert response.headers['x-board-export-document-route'] == '/ui/workboard/export/document'
    assert response.headers['allow'] == 'GET, HEAD, OPTIONS'
    assert response.headers['x-board-export-allow'] == 'GET, HEAD, OPTIONS'
    assert response.headers['x-board-export-response-class'] == 'CANONICAL_EXPORT_DOCUMENT'
    assert response.headers['x-board-export-body-role'] == 'EXPORT_PAYLOAD'


def test_ui_workboard_export_document_head_route_returns_304_when_etag_matches(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_document',
        lambda **_: {'schema_version': 'oracle_operator_board_export_document/v1', 'document_sha256': 'a' * 64},
    )
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_document_headers',
        lambda _: {
            'ETag': '"sha256:' + ('a' * 64) + '"',
            'Last-Modified': 'Thu, 16 Apr 2026 12:00:00 GMT',
            'X-Board-Export-Index-Route': '/ui/workboard/export/index',
            'X-Board-Export-Document-Route': '/ui/workboard/export/document',
            'Link': '</ui/workboard/export/index>; rel="index", </ui/workboard/export/document>; rel="self"',
        },
    )
    client = TestClient(app)
    response = client.head('/ui/workboard/export/document', headers={'If-None-Match': '"sha256:' + ('a' * 64) + '"'})
    assert response.status_code == 304
    assert response.text == ''
    assert response.headers['etag'] == '"sha256:' + ('a' * 64) + '"'

def test_ui_workboard_export_document_options_route_returns_allow_headers(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_document',
        lambda **_: {'schema_version': 'oracle_operator_board_export_document/v1', 'document_sha256': 'a' * 64},
    )
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_document_headers',
        lambda _: {
            'ETag': '"sha256:' + ('a' * 64) + '"',
            'X-Board-Export-Index-Route': '/ui/workboard/export/index',
            'X-Board-Export-Document-Route': '/ui/workboard/export/document',
            'Link': '</ui/workboard/export/index>; rel="index", </ui/workboard/export/document>; rel="self"',
        },
    )
    client = TestClient(app)
    response = client.options('/ui/workboard/export/document')
    assert response.status_code == 204
    assert response.text == ''
    assert response.headers['allow'] == 'GET, HEAD, OPTIONS'
    assert response.headers['x-board-export-allow'] == 'GET, HEAD, OPTIONS'
    assert response.headers['x-board-export-index-route'] == '/ui/workboard/export/index'
    assert response.headers['x-board-export-document-route'] == '/ui/workboard/export/document'
    assert response.headers['x-board-export-response-class'] == 'CANONICAL_EXPORT_DOCUMENT'
    assert response.headers['x-board-export-body-role'] == 'EXPORT_PAYLOAD'


def test_ui_workboard_export_index_options_route_returns_allow_headers(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_index',
        lambda **_: {'schema_version': 'oracle_operator_board_export_index/v1', 'document_sha256': 'c' * 64},
    )
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_index_headers',
        lambda _: {
            'ETag': '"sha256:' + ('c' * 64) + '"',
            'X-Board-Export-Index-Route': '/ui/workboard/export/index',
            'X-Board-Export-Document-Route': '/ui/workboard/export/document',
            'Link': '</ui/workboard/export/document>; rel="describedby", </ui/workboard/export/index>; rel="self"',
        },
    )
    client = TestClient(app)
    response = client.options('/ui/workboard/export/index')
    assert response.status_code == 204
    assert response.text == ''
    assert response.headers['allow'] == 'GET, HEAD, OPTIONS'
    assert response.headers['x-board-export-allow'] == 'GET, HEAD, OPTIONS'
    assert response.headers['x-board-export-index-route'] == '/ui/workboard/export/index'
    assert response.headers['x-board-export-document-route'] == '/ui/workboard/export/document'
    assert response.headers['x-board-export-response-class'] == 'INDEX_DOCUMENT'
    assert response.headers['x-board-export-body-role'] == 'EXPORT_CATALOG'


def test_ui_workboard_export_document_route_returns_canonical_json(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_document',
        lambda **_: {
            'schema_version': 'oracle_operator_board_export_document/v1',
            'canonical_json': '{\n  "schema_version": "oracle_operator_board_export_payload/v1",\n  "export_state": "EXPORT_READY"\n}\n',
            'document_sha256': 'a' * 64,
            'relative_document_path': 'generated/publications/operator/governance-main/board_export_payload.json',
            'published_relative_document_path': 'published/publications/operator/governance-main/board_export_payload.json',
            'export_state': 'EXPORT_READY',
            'export_completeness_state': 'FULLY_EMBEDDED',
            'verification_state': 'VERIFIABLE',
            'byte_count': 95,
            'line_count': 4,
            'canonical_payload': {'bundle_fingerprint_sha256': 'b' * 64},
        },
    )
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_document_headers',
        lambda document: {
            'ETag': '"sha256:' + str(document['document_sha256']) + '"',
            'Cache-Control': 'no-cache',
            'Last-Modified': 'Thu, 16 Apr 2026 12:00:00 GMT',
            'X-Board-Export-Generated-At': '2026-04-16T12:00:00+00:00',
            'X-Board-Export-Freshness-State': 'CURRENT',
            'X-Board-Export-Freshness-Basis': 'generated_at_utc',
            'X-Board-Export-Document-SHA256': str(document['document_sha256']),
            'X-Board-Export-Bundle-Fingerprint-SHA256': str(document['canonical_payload']['bundle_fingerprint_sha256']),
            'X-Board-Export-Relative-Path': str(document['relative_document_path']),
            'X-Board-Export-Published-Relative-Path': str(document['published_relative_document_path']),
            'X-Board-Export-Index-Route': '/ui/workboard/export/index',
            'X-Board-Export-Document-Route': '/ui/workboard/export/document',
            'X-Board-Export-State': str(document['export_state']),
            'X-Board-Export-Completeness': str(document['export_completeness_state']),
            'X-Board-Export-Verification': str(document['verification_state']),
            'X-Board-Export-Byte-Count': str(document['byte_count']),
            'X-Board-Export-Line-Count': str(document['line_count']),
            'Digest': 'sha-256=stubbed',
            'Link': '</ui/workboard/export/index>; rel="index", </ui/workboard/export/document>; rel="self"',
        },
    )
    client = TestClient(app)
    response = client.get('/ui/workboard/export/document')
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('application/json')
    assert response.headers['etag'] == '"sha256:' + ('a' * 64) + '"'
    assert response.headers['cache-control'] == 'no-cache'
    assert response.headers['last-modified'] == 'Thu, 16 Apr 2026 12:00:00 GMT'
    assert response.headers['x-board-export-generated-at'] == '2026-04-16T12:00:00+00:00'
    assert response.headers['x-board-export-freshness-state'] == 'CURRENT'
    assert response.headers['x-board-export-freshness-basis'] == 'generated_at_utc'
    assert response.headers['x-board-export-document-sha256'] == 'a' * 64
    assert response.headers['x-board-export-bundle-fingerprint-sha256'] == 'b' * 64
    assert response.headers['x-board-export-relative-path'] == 'generated/publications/operator/governance-main/board_export_payload.json'
    assert response.headers['x-board-export-published-relative-path'] == 'published/publications/operator/governance-main/board_export_payload.json'
    assert response.headers['x-board-export-index-route'] == '/ui/workboard/export/index'
    assert response.headers['x-board-export-document-route'] == '/ui/workboard/export/document'
    assert response.headers['link'].startswith('</ui/workboard/export/index>; rel="index", </ui/workboard/export/document>; rel="self"')
    assert 'rel="profile"' in response.headers['link']
    assert response.headers['x-board-export-state'] == 'EXPORT_READY'
    assert response.headers['x-board-export-completeness'] == 'FULLY_EMBEDDED'
    assert response.headers['x-board-export-verification'] == 'VERIFIABLE'
    assert response.headers['x-board-export-byte-count'] == '95'
    assert response.headers['x-board-export-line-count'] == '4'
    assert response.headers['digest'] == 'sha-256=stubbed'
    payload = response.json()
    assert payload['schema_version'] == 'oracle_operator_board_export_payload/v1'
    assert payload['export_state'] == 'EXPORT_READY'



def test_ui_burnin_route_uses_service(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_burnin_payload',
        lambda **_: {'schema_version': 'ui_burnin_dashboard/v1', 'metrics': {'providerPaths': []}},
    )
    client = TestClient(app)
    response = client.get('/ui/burnin')
    assert response.status_code == 200
    payload = response.json()
    assert payload['schema_version'] == 'ui_burnin_dashboard/v1'
    assert payload['metrics']['providerPaths'] == []


def test_ui_pack_detail_route_uses_service(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_pack_detail_payload',
        lambda **_: {'schema_version': 'ui_pack_detail/v1', 'pack': {'pack_kind': 'status_pack'}},
    )
    client = TestClient(app)
    response = client.get('/ui/packs/detail')
    assert response.status_code == 200
    payload = response.json()
    assert payload['schema_version'] == 'ui_pack_detail/v1'
    assert payload['pack']['pack_kind'] == 'status_pack'


def test_ui_command_route_returns_receipt(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.execute_ui_operator_command',
        lambda **_: {'schema_version': 'ui_operator_command_receipt/v1', 'accepted': True, 'action': 'claim-item'},
    )
    client = TestClient(app)
    response = client.post('/ui/commands/claim-item', json={'operator_id': 'jp', 'work_item_key': 'w1'})
    assert response.status_code == 200
    payload = response.json()
    assert payload['schema_version'] == 'ui_operator_command_receipt/v1'
    assert payload['accepted'] is True
    assert payload['action'] == 'claim-item'


def test_ui_command_route_returns_journaled_receipt(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))
    client = TestClient(app)
    response = client.post('/ui/commands/claim-item', json={'operator_id': 'jp', 'work_item_key': 'w1'})
    assert response.status_code == 200
    payload = response.json()
    assert payload['execution_mode'] == 'JOURNALED_RECEIPT'
    assert payload['journal_family'] == 'operator_action_events'
    assert payload['target']['work_item_key'] == 'w1'


def test_ui_tribunal_route_is_blindness_safe(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_tribunal_payload',
        lambda **_: {
            'schema_version': 'ui_tribunal_workspace/v1',
            'blindness': {'quantitative_payloads_present': False},
            'doctrine_stats': {'active_doctrine_count': 2},
            'section_provenance': {'thesis_graph': {'projection_family': 'tribunal'}},
            'prompt_evaluations': [],
            'falsification_checks': [],
            'operator_lines': ['Validator quantitative metrics are intentionally excluded.'],
        },
    )
    client = TestClient(app)
    response = client.get('/ui/tribunal')
    assert response.status_code == 200
    payload = response.json()
    assert payload['schema_version'] == 'ui_tribunal_workspace/v1'
    assert payload['blindness']['quantitative_payloads_present'] is False
    serialized = str(payload).lower()
    for forbidden in ('cpcv', 'slippagebps', 'borrowcostbps', 'calibrationcurve'):
        assert forbidden not in serialized


def test_ui_evidence_route_uses_service(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_evidence_payload',
        lambda **_: {'schema_version': 'ui_evidence_dashboard/v1', 'verification': {'trust_status': 'TRUST_RESTRICTED'}, 'registry': {'source_artifact_count': 2}, 'section_provenance': {'registry': {'projection_family': 'ui'}}},
    )
    client = TestClient(app)
    response = client.get('/ui/evidence')
    assert response.status_code == 200
    payload = response.json()
    assert payload['schema_version'] == 'ui_evidence_dashboard/v1'
    assert payload['verification']['trust_status'] == 'TRUST_RESTRICTED'
    assert payload['registry']['source_artifact_count'] == 2


def test_ui_runtime_route_uses_service(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_runtime_status_payload',
        lambda **_: {'schema_version': 'ui_runtime_status/v1', 'environment': 'TEST', 'backend': {'status': 'CONFIGURED'}},
    )
    client = TestClient(app)
    response = client.get('/ui/runtime')
    assert response.status_code == 200
    payload = response.json()
    assert payload['schema_version'] == 'ui_runtime_status/v1'
    assert payload['environment'] == 'TEST'
    assert payload['backend']['status'] == 'CONFIGURED'


def test_ui_runtime_route_honors_role_query(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_runtime_status_payload',
        lambda **kwargs: {'schema_version': 'ui_runtime_status/v1', 'persona': {'active_role': kwargs.get('role', 'operator')}, 'policy': {'allowed_domains': ['tribunal'], 'allowed_actions': []}},
    )
    client = TestClient(app)
    response = client.get('/ui/runtime?role=tribunal')
    assert response.status_code == 200
    payload = response.json()
    assert payload['persona']['active_role'] == 'tribunal'
    assert payload['policy']['allowed_domains'] == ['tribunal']


def test_ui_workboard_export_index_route_returns_304_when_etag_matches(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_index',
        lambda **_: {'schema_version': 'oracle_operator_board_export_index/v1'},
    )
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_index_headers',
        lambda _: {
            'ETag': '"sha256:idx123"',
            'Cache-Control': 'no-cache',
            'Last-Modified': 'Thu, 16 Apr 2026 12:00:00 GMT',
            'X-Board-Export-Generated-At': '2026-04-16T12:00:00+00:00',
            'X-Board-Export-Freshness-State': 'CURRENT',
            'X-Board-Export-Freshness-Basis': 'generated_at_utc',
            'X-Board-Export-Index-Route': '/ui/workboard/export/index',
            'X-Board-Export-Document-Route': '/ui/workboard/export/document',
            'Link': '</ui/workboard/export/document>; rel="describedby", </ui/workboard/export/index>; rel="self"',
        },
    )
    client = TestClient(app)
    response = client.get('/ui/workboard/export/index', headers={'If-None-Match': '"sha256:idx123"'})
    assert response.status_code == 304
    assert response.text == ''
    assert response.headers['etag'] == '"sha256:idx123"'
    assert response.headers['cache-control'] == 'no-cache'
    assert response.headers['last-modified'] == 'Thu, 16 Apr 2026 12:00:00 GMT'
    assert response.headers['x-board-export-generated-at'] == '2026-04-16T12:00:00+00:00'
    assert response.headers['x-board-export-freshness-state'] == 'CURRENT'
    assert response.headers['x-board-export-freshness-basis'] == 'generated_at_utc'
    assert response.headers['x-board-export-index-route'] == '/ui/workboard/export/index'
    assert response.headers['x-board-export-document-route'] == '/ui/workboard/export/document'
    assert response.headers['link'].startswith('</ui/workboard/export/document>; rel="describedby", </ui/workboard/export/index>; rel="self"')
    assert 'rel="profile"' in response.headers['link']


def test_ui_workboard_export_document_route_returns_304_when_etag_matches(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_document',
        lambda **_: {'schema_version': 'oracle_operator_board_export_document/v1', 'canonical_json': '{\"ok\":true}\n'},
    )
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_document_headers',
        lambda _: {
            'ETag': '"sha256:doc123"',
            'Cache-Control': 'no-cache',
            'Last-Modified': 'Thu, 16 Apr 2026 12:00:00 GMT',
            'X-Board-Export-Generated-At': '2026-04-16T12:00:00+00:00',
            'X-Board-Export-Freshness-State': 'CURRENT',
            'X-Board-Export-Freshness-Basis': 'generated_at_utc',
            'X-Board-Export-Index-Route': '/ui/workboard/export/index',
            'X-Board-Export-Document-Route': '/ui/workboard/export/document',
            'Link': '</ui/workboard/export/index>; rel="index", </ui/workboard/export/document>; rel="self"',
        },
    )
    client = TestClient(app)
    response = client.get('/ui/workboard/export/document', headers={'If-None-Match': '"sha256:doc123"'})
    assert response.status_code == 304
    assert response.text == ''
    assert response.headers['etag'] == '"sha256:doc123"'
    assert response.headers['cache-control'] == 'no-cache'
    assert response.headers['last-modified'] == 'Thu, 16 Apr 2026 12:00:00 GMT'
    assert response.headers['x-board-export-generated-at'] == '2026-04-16T12:00:00+00:00'
    assert response.headers['x-board-export-freshness-state'] == 'CURRENT'
    assert response.headers['x-board-export-freshness-basis'] == 'generated_at_utc'
    assert response.headers['x-board-export-index-route'] == '/ui/workboard/export/index'
    assert response.headers['x-board-export-document-route'] == '/ui/workboard/export/document'
    assert response.headers['link'].startswith('</ui/workboard/export/index>; rel="index", </ui/workboard/export/document>; rel="self"')
    assert 'rel="profile"' in response.headers['link']


def test_ui_workboard_export_index_route_returns_304_when_last_modified_matches(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_index',
        lambda **_: {'schema_version': 'oracle_operator_board_export_index/v1'},
    )
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_index_headers',
        lambda _: {
            'ETag': '"sha256:idx123"',
            'Cache-Control': 'no-cache',
            'Last-Modified': 'Thu, 16 Apr 2026 12:00:00 GMT',
            'X-Board-Export-Generated-At': '2026-04-16T12:00:00+00:00',
            'X-Board-Export-Freshness-State': 'CURRENT',
            'X-Board-Export-Freshness-Basis': 'generated_at_utc',
            'X-Board-Export-Index-Route': '/ui/workboard/export/index',
            'X-Board-Export-Document-Route': '/ui/workboard/export/document',
            'Link': '</ui/workboard/export/document>; rel="describedby", </ui/workboard/export/index>; rel="self"',
        },
    )
    client = TestClient(app)
    response = client.get('/ui/workboard/export/index', headers={'If-Modified-Since': 'Thu, 16 Apr 2026 12:00:00 GMT'})
    assert response.status_code == 304
    assert response.text == ''
    assert response.headers['last-modified'] == 'Thu, 16 Apr 2026 12:00:00 GMT'
    assert response.headers['cache-control'] == 'no-cache'
    assert response.headers['x-board-export-generated-at'] == '2026-04-16T12:00:00+00:00'
    assert response.headers['x-board-export-freshness-state'] == 'CURRENT'
    assert response.headers['x-board-export-freshness-basis'] == 'generated_at_utc'


def test_ui_workboard_export_document_route_returns_304_when_last_modified_matches(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_document',
        lambda **_: {'schema_version': 'oracle_operator_board_export_document/v1', 'canonical_json': '{\"ok\":true}\n'},
    )
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_document_headers',
        lambda _: {
            'ETag': '"sha256:doc123"',
            'Cache-Control': 'no-cache',
            'Last-Modified': 'Thu, 16 Apr 2026 12:00:00 GMT',
            'X-Board-Export-Generated-At': '2026-04-16T12:00:00+00:00',
            'X-Board-Export-Freshness-State': 'CURRENT',
            'X-Board-Export-Freshness-Basis': 'generated_at_utc',
            'X-Board-Export-Index-Route': '/ui/workboard/export/index',
            'X-Board-Export-Document-Route': '/ui/workboard/export/document',
            'Link': '</ui/workboard/export/index>; rel="index", </ui/workboard/export/document>; rel="self"',
        },
    )
    client = TestClient(app)
    response = client.get('/ui/workboard/export/document', headers={'If-Modified-Since': 'Thu, 16 Apr 2026 12:00:00 GMT'})
    assert response.status_code == 304
    assert response.text == ''
    assert response.headers['last-modified'] == 'Thu, 16 Apr 2026 12:00:00 GMT'
    assert response.headers['cache-control'] == 'no-cache'
    assert response.headers['x-board-export-generated-at'] == '2026-04-16T12:00:00+00:00'
    assert response.headers['x-board-export-freshness-state'] == 'CURRENT'
    assert response.headers['x-board-export-freshness-basis'] == 'generated_at_utc'


def test_ui_workboard_export_index_route_advertises_canonical_json_and_schema_profile(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_index',
        lambda **_: {
            'schema_version': 'oracle_operator_board_export_index/v1',
            'generated_at_utc': '2026-04-16T12:00:00+00:00',
            'document_sha256': 'c' * 64,
            'bundle_fingerprint_sha256': 'd' * 64,
            'relative_document_path': 'generated/publications/operator/governance-main/board_export_payload.json',
            'published_relative_document_path': 'published/publications/operator/governance-main/board_export_payload.json',
            'export_state': 'EXPORT_READY',
            'export_completeness_state': 'FULLY_EMBEDDED',
            'verification_state': 'VERIFIABLE',
            'document_byte_count': 101,
            'document_line_count': 5,
        },
    )
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_index_headers',
        lambda payload: {
            'ETag': '"sha256:' + ('c' * 64) + '"',
            'Cache-Control': 'no-cache',
            'Last-Modified': 'Thu, 16 Apr 2026 12:00:00 GMT',
            'Allow': 'GET, HEAD, OPTIONS',
            'X-Board-Export-Allow': 'GET, HEAD, OPTIONS',
            'X-Board-Export-Index-Route': '/ui/workboard/export/index',
            'X-Board-Export-Document-Route': '/ui/workboard/export/document',
            'Link': '</ui/workboard/export/document>; rel="describedby", </ui/workboard/export/index>; rel="self"',
        },
    )
    client = TestClient(app)
    response = client.get('/ui/workboard/export/index')
    assert response.status_code == 200
    assert response.headers['vary'] == 'Accept, If-None-Match, If-Modified-Since'
    assert response.headers['x-board-export-accept'] == 'application/json'
    assert response.headers['x-board-export-representation'] == 'application/json'
    assert response.headers['x-board-export-negotiation-state'] == 'CANONICAL_JSON_ONLY'
    assert response.headers['x-board-export-schema-version'] == 'oracle_operator_board_export_index/v1'
    assert response.headers['x-board-export-schema-family'] == 'oracle_operator_board_export_index'
    assert response.headers['x-board-export-schema-revision'] == 'v1'
    assert response.headers['x-board-export-profile'] == 'urn:strategy-validator:schema:oracle_operator_board_export_index:v1'
    assert response.headers['x-board-export-profile-state'] == 'DECLARED'
    assert 'rel="profile"' in response.headers['link']
    assert response.headers['content-location'] == 'generated/publications/operator/governance-main/board_export_payload.json'
    assert response.headers['x-board-export-canonical-relative-path'] == 'generated/publications/operator/governance-main/board_export_payload.json'
    assert response.headers['x-board-export-published-canonical-relative-path'] == 'published/publications/operator/governance-main/board_export_payload.json'
    assert response.headers['x-board-export-location-state'] == 'DECLARED'
    assert response.headers['x-board-export-published-location-state'] == 'DECLARED'
    assert 'rel="canonical"' in response.headers['link']
    assert response.headers['content-disposition'] == 'inline; filename="board_export_index.json"'
    assert response.headers['x-board-export-disposition-state'] == 'INLINE_INSPECTION'
    assert response.headers['x-board-export-attachment-disposition'] == 'attachment; filename="board_export_index.json"'
    assert response.headers['x-board-export-export-intent'] == 'INSPECT_INLINE_OR_DOWNLOAD'


def test_ui_workboard_export_document_route_advertises_canonical_json_and_schema_profile(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_document',
        lambda **_: {
            'schema_version': 'oracle_operator_board_export_document/v1',
            'canonical_json': '{\n  "schema_version": "oracle_operator_board_export_payload/v1"\n}\n',
            'document_sha256': 'a' * 64,
            'relative_document_path': 'generated/publications/operator/governance-main/board_export_payload.json',
            'published_relative_document_path': 'published/publications/operator/governance-main/board_export_payload.json',
            'export_state': 'EXPORT_READY',
            'export_completeness_state': 'FULLY_EMBEDDED',
            'verification_state': 'VERIFIABLE',
            'byte_count': 95,
            'line_count': 4,
            'canonical_payload': {'bundle_fingerprint_sha256': 'b' * 64},
        },
    )
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_export_document_headers',
        lambda document: {
            'ETag': '"sha256:' + ('a' * 64) + '"',
            'Cache-Control': 'no-cache',
            'Last-Modified': 'Thu, 16 Apr 2026 12:00:00 GMT',
            'Allow': 'GET, HEAD, OPTIONS',
            'X-Board-Export-Allow': 'GET, HEAD, OPTIONS',
            'X-Board-Export-Index-Route': '/ui/workboard/export/index',
            'X-Board-Export-Document-Route': '/ui/workboard/export/document',
            'Link': '</ui/workboard/export/index>; rel="index", </ui/workboard/export/document>; rel="self"',
        },
    )
    client = TestClient(app)
    response = client.get('/ui/workboard/export/document')
    assert response.status_code == 200
    assert response.headers['vary'] == 'Accept, If-None-Match, If-Modified-Since'
    assert response.headers['x-board-export-accept'] == 'application/json'
    assert response.headers['x-board-export-representation'] == 'application/json'
    assert response.headers['x-board-export-negotiation-state'] == 'CANONICAL_JSON_ONLY'
    assert response.headers['x-board-export-schema-version'] == 'oracle_operator_board_export_document/v1'
    assert response.headers['x-board-export-schema-family'] == 'oracle_operator_board_export_document'
    assert response.headers['x-board-export-schema-revision'] == 'v1'
    assert response.headers['x-board-export-profile'] == 'urn:strategy-validator:schema:oracle_operator_board_export_document:v1'
    assert response.headers['x-board-export-profile-state'] == 'DECLARED'
    assert 'rel="profile"' in response.headers['link']
    assert response.headers['content-location'] == 'generated/publications/operator/governance-main/board_export_payload.json'
    assert response.headers['x-board-export-canonical-relative-path'] == 'generated/publications/operator/governance-main/board_export_payload.json'
    assert response.headers['x-board-export-published-canonical-relative-path'] == 'published/publications/operator/governance-main/board_export_payload.json'
    assert response.headers['x-board-export-location-state'] == 'DECLARED'
    assert response.headers['x-board-export-published-location-state'] == 'DECLARED'
    assert 'rel="canonical"' in response.headers['link']
    assert response.headers['content-disposition'] == 'inline; filename="board_export_payload.json"'
    assert response.headers['x-board-export-disposition-state'] == 'INLINE_INSPECTION'
    assert response.headers['x-board-export-attachment-disposition'] == 'attachment; filename="board_export_payload.json"'
    assert response.headers['x-board-export-export-intent'] == 'INSPECT_INLINE_OR_DOWNLOAD'

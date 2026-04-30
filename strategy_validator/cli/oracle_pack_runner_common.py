from __future__ import annotations

import argparse
import json
from pathlib import Path

from strategy_validator.application.operator_pack_assembly import (
    build_pack_assignment_payload,
    build_pack_claim_lease_payload,
    build_pack_claim_lifecycle_payload,
    build_pack_claim_operability_payload,
    build_pack_escalation_payload,
)
from strategy_validator.application.operator_pack_queries import (
    build_operator_pack_navigation_payload,
    build_operator_pack_query_payload,
    build_operator_pack_timeline_payload,
    build_operator_pack_workbench_payload,
    publish_operator_terminal_record_payload,
)
from strategy_validator.cli.control_plane_pack_surfaces import (
    build_operator_pack_assignment_request,
    build_operator_pack_claim_lease_request,
    build_operator_pack_claim_lifecycle_request,
    build_operator_pack_claim_operability_request,
    build_operator_pack_lease_governance_request,
    build_operator_pack_execution_readiness_request,
    build_operator_pack_dispatch_permission_request,
    build_operator_pack_dispatch_outcome_request,
    build_operator_pack_execution_exception_request,
    build_operator_pack_approval_needed_request,
    build_operator_pack_approval_disposition_request,
    build_operator_pack_execution_authorization_request,
    build_operator_pack_execution_force_request,
    build_operator_pack_execution_finality_request,
    build_operator_pack_terminal_resolution_request,
    build_operator_pack_terminal_closure_request,
    build_operator_pack_terminal_archive_request,
    build_operator_pack_terminal_record_request,
    build_operator_pack_handoff_request,
    build_operator_pack_comparison_request,
    build_operator_pack_escalation_request,
    build_operator_pack_drift_request,
    build_operator_pack_dashboard_request,
    build_operator_pack_timeline_request,
    build_operator_pack_navigation_request,
    build_operator_pack_workbench_request,
    materialize_operator_pack_assignment,
    materialize_operator_pack_claim_lease,
    materialize_operator_pack_claim_lifecycle,
    materialize_operator_pack_claim_operability,
    materialize_operator_pack_lease_governance,
    materialize_operator_pack_execution_readiness,
    materialize_operator_pack_dispatch_permission,
    materialize_operator_pack_dispatch_outcome,
    materialize_operator_pack_execution_exception,
    materialize_operator_pack_approval_needed,
    materialize_operator_pack_approval_disposition,
    materialize_operator_pack_execution_authorization,
    materialize_operator_pack_execution_force,
    materialize_operator_pack_execution_finality,
    materialize_operator_pack_terminal_resolution,
    materialize_operator_pack_terminal_closure,
    materialize_operator_pack_terminal_archive,
    materialize_operator_pack_terminal_record,
    materialize_operator_pack_handoff,
    materialize_operator_pack_comparison,
    materialize_operator_pack_escalation,
    materialize_operator_pack_drift,
    materialize_operator_pack_dashboard,
    materialize_operator_pack_timeline,
    materialize_operator_pack_navigation,
    materialize_operator_pack_workbench,
)



def _emit_payload(payload: dict, output: str) -> int:
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    else:
        print(json.dumps(payload, indent=2))
    return 0


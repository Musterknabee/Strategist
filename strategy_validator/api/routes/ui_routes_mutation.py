from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from strategy_validator.api.routes import ui as ui_root

router = APIRouter()


@router.post('/commands/{action}')
def post_ui_command(
    action: str,
    request: ui_root.UiOperatorCommandRequest,
    auth_context: ui_root.UiMutationAuthContext = Depends(ui_root.require_mutation_auth),
) -> dict[str, object]:
    try:
        return ui_root.execute_ui_operator_command(action=action, request=request, auth_context=auth_context)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/strategy-intake')
def post_ui_strategy_intake(
    request: ui_root.StrategyIntakeRequest,
    auth_context: ui_root.UiMutationAuthContext = Depends(ui_root.require_mutation_auth),
) -> dict[str, object]:
    try:
        return ui_root.submit_ui_strategy_intake(request=request, auth_context=auth_context)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

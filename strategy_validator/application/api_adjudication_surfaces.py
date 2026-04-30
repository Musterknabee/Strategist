"""Bounded application entrypoints for adjudication-facing API routes."""

from __future__ import annotations

from strategy_validator.application.adjudication import run_oracle_adjudication

__all__ = ['run_oracle_adjudication']

from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_telemetry_metrics_file_surface_is_present_for_e2e_wiring():
    assert (ROOT/"strategy_validator/validator/observability.py").exists() or (ROOT/"strategy_validator/application/readiness.py").exists()

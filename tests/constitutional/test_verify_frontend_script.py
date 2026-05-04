from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_verify_frontend_script_and_ci_local_flag_exist() -> None:
    verify = ROOT / "scripts" / "verify_frontend.py"
    ci_local = ROOT / "scripts" / "ci_local_verify.py"
    assert verify.exists()
    vtext = verify.read_text(encoding="utf-8")
    for item in [
        "verify_frontend/v1",
        "STRATEGIST_SMOKE_API_BASE_URL",
        "npm_lint",
        '"lint"',
        '"typecheck"',
        '"build"',
    ]:
        assert item in vtext
    ctext = ci_local.read_text(encoding="utf-8")
    assert "--include-frontend" in ctext
    assert "verify_frontend.py" in ctext
    workflow = ROOT / ".github" / "workflows" / "ci.yml"
    wtext = workflow.read_text(encoding="utf-8")
    assert "strategist-web" in wtext
    assert "npm run lint" in wtext or "npm run certify" in wtext

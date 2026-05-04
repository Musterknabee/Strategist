from __future__ import annotations

import importlib.util
import json
import os
import stat
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_module(name: str, relative: str) -> ModuleType:
    path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _payload(stderr: str) -> dict[str, object]:
    return json.loads(stderr.strip().splitlines()[-1])


def _script_root(tmp_path: Path, script_name: str) -> Path:
    scripts = tmp_path / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    script = scripts / script_name
    script.write_text("# test shim\n", encoding="utf-8")
    return script


def _patch_setup_module(mod: ModuleType, repo_root: Path) -> None:
    web = repo_root / "ui" / "strategist-web"
    web.mkdir(parents=True, exist_ok=True)
    mod.REPO_ROOT = repo_root
    mod.DEPLOYMENT_ENV = repo_root / "deployment.env"
    mod.WEB_ENV_EXAMPLE = web / ".env.example"
    mod.WEB_ENV_LOCAL = web / ".env.local"


def test_setup_local_deployment_rejects_symlinked_deployment_env(tmp_path: Path, capsys) -> None:  # noqa: ANN001
    mod = _load_module("_setup_local_deployment_env_symlink", "scripts/setup_local_deployment.py")
    _patch_setup_module(mod, tmp_path)
    real_env = tmp_path / "real-deployment.env"
    real_env.write_text("do-not-overwrite\n", encoding="utf-8")
    (tmp_path / "deployment.env").symlink_to(real_env)

    rc = mod.main(["--dev", "--force", "--skip-migrate"])

    assert rc == 2
    assert _payload(capsys.readouterr().err)["code"] == "SETUP_LOCAL_DEPLOYMENT_ENV_FILE_IS_SYMLINK"
    assert real_env.read_text(encoding="utf-8") == "do-not-overwrite\n"


def test_setup_local_deployment_rejects_symlinked_local_output_root(tmp_path: Path, capsys) -> None:  # noqa: ANN001
    mod = _load_module("_setup_local_deployment_output_symlink", "scripts/setup_local_deployment.py")
    _patch_setup_module(mod, tmp_path)
    real_local = tmp_path / "real-local"
    real_local.mkdir()
    (tmp_path / ".local").symlink_to(real_local, target_is_directory=True)

    rc = mod.main(["--dev", "--force", "--skip-migrate"])

    assert rc == 2
    assert _payload(capsys.readouterr().err)["code"] == "SETUP_LOCAL_DEPLOYMENT_OUTPUT_DIR_IS_SYMLINK"
    assert not (tmp_path / "deployment.env").exists()


def test_setup_local_deployment_rejects_symlinked_frontend_env_output(tmp_path: Path, capsys) -> None:  # noqa: ANN001
    mod = _load_module("_setup_local_deployment_web_env_symlink", "scripts/setup_local_deployment.py")
    _patch_setup_module(mod, tmp_path)
    real_web_env = tmp_path / "real-web.env"
    real_web_env.write_text("NEXT_PUBLIC_STRATEGIST_API_BASE_URL=http://safe.example\n", encoding="utf-8")
    mod.WEB_ENV_LOCAL.symlink_to(real_web_env)

    rc = mod.main(["--dev", "--force", "--skip-migrate"])

    assert rc == 2
    assert _payload(capsys.readouterr().err)["code"] == "SETUP_LOCAL_DEPLOYMENT_WEB_ENV_LOCAL_IS_SYMLINK"
    assert real_web_env.read_text(encoding="utf-8") == "NEXT_PUBLIC_STRATEGIST_API_BASE_URL=http://safe.example\n"


def test_setup_local_deployment_rejects_symlinked_frontend_env_example(tmp_path: Path, capsys) -> None:  # noqa: ANN001
    mod = _load_module("_setup_local_deployment_web_example_symlink", "scripts/setup_local_deployment.py")
    _patch_setup_module(mod, tmp_path)
    real_example = tmp_path / "real-example.env"
    real_example.write_text("NEXT_PUBLIC_STRATEGIST_API_BASE_URL=http://safe.example\n", encoding="utf-8")
    mod.WEB_ENV_EXAMPLE.symlink_to(real_example)

    rc = mod.main(["--dev", "--force", "--skip-migrate"])

    assert rc == 2
    assert _payload(capsys.readouterr().err)["code"] == "SETUP_LOCAL_DEPLOYMENT_WEB_ENV_EXAMPLE_IS_SYMLINK"
    assert not mod.WEB_ENV_LOCAL.exists()


def test_setup_local_deployment_writes_secret_env_with_owner_only_permissions(tmp_path: Path) -> None:
    mod = _load_module("_setup_local_deployment_env_permissions", "scripts/setup_local_deployment.py")
    _patch_setup_module(mod, tmp_path)

    rc = mod.main(["--dev", "--force", "--skip-migrate"])

    assert rc == 0
    env_path = tmp_path / "deployment.env"
    assert env_path.is_file()
    if os.name != "nt":
        mode = stat.S_IMODE(env_path.stat().st_mode)
        assert mode & (stat.S_IRWXG | stat.S_IRWXO) == 0


def test_run_local_api_rejects_symlinked_deployment_env(tmp_path: Path, capsys) -> None:  # noqa: ANN001
    mod = _load_module("_run_local_api_env_symlink", "scripts/run_local_api_with_deployment_env.py")
    script = _script_root(tmp_path, "run_local_api_with_deployment_env.py")
    mod.__file__ = str(script)
    real_env = tmp_path / "real.env"
    real_env.write_text("STRATEGY_VALIDATOR_API_TOKEN=secret\n", encoding="utf-8")
    (tmp_path / "deployment.env").symlink_to(real_env)

    rc = mod.main()

    assert rc == 2
    assert _payload(capsys.readouterr().err)["code"] == "RUN_LOCAL_API_ENV_FILE_IS_SYMLINK"


def test_run_preflight_rejects_symlinked_deployment_env(tmp_path: Path, capsys) -> None:  # noqa: ANN001
    mod = _load_module("_run_preflight_env_symlink", "scripts/run_preflight_with_deployment_env.py")
    script = _script_root(tmp_path, "run_preflight_with_deployment_env.py")
    mod.__file__ = str(script)
    real_env = tmp_path / "real.env"
    real_env.write_text("STRATEGY_VALIDATOR_API_TOKEN=secret\n", encoding="utf-8")
    (tmp_path / "deployment.env").symlink_to(real_env)

    rc = mod.main()

    assert rc == 2
    assert _payload(capsys.readouterr().err)["code"] == "RUN_PREFLIGHT_ENV_FILE_IS_SYMLINK"

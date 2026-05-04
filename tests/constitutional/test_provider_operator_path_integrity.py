from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_module(name: str, relative: str) -> object:
    path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _payload(stdout: str) -> dict[str, object]:
    return json.loads(stdout.strip().splitlines()[-1])


def test_check_provider_keys_rejects_symlinked_env_file(tmp_path: Path, capsys) -> None:  # noqa: ANN001
    mod = _load_module("_check_provider_keys_path_integrity", "scripts/check_provider_keys.py")
    real_env = tmp_path / "real.env"
    real_env.write_text("FRED_API_KEY=secret-token\n", encoding="utf-8")
    linked_env = tmp_path / "linked.env"
    linked_env.symlink_to(real_env)

    rc = mod.main(["--env-file", str(linked_env), "--json"])

    assert rc == 2
    payload = _payload(capsys.readouterr().out)
    assert payload["code"] == "CHECK_PROVIDER_KEYS_ENV_FILE_IS_SYMLINK"


def test_retrieve_provider_samples_rejects_symlinked_output_dir(tmp_path: Path, capsys) -> None:  # noqa: ANN001
    mod = _load_module("_retrieve_provider_samples_path_integrity", "scripts/retrieve_provider_samples.py")
    real_output = tmp_path / "real-output"
    real_output.mkdir()
    linked_output = tmp_path / "linked-output"
    linked_output.symlink_to(real_output, target_is_directory=True)

    rc = mod.main(
        [
            "--public-only",
            "--no-network",
            "--output-dir",
            str(linked_output),
            "--manifest-json",
            "--max-samples",
            "1",
        ]
    )

    assert rc == 2
    payload = _payload(capsys.readouterr().out)
    assert payload["code"] == "RETRIEVE_PROVIDER_OUTPUT_DIR_IS_SYMLINK"
    assert not (real_output / "manifest.json").exists()


def test_retrieve_provider_samples_rejects_env_under_symlinked_parent(tmp_path: Path, capsys) -> None:  # noqa: ANN001
    mod = _load_module("_retrieve_provider_samples_env_parent", "scripts/retrieve_provider_samples.py")
    real_env_dir = tmp_path / "real-env"
    real_env_dir.mkdir()
    env_file = real_env_dir / "provider.env"
    env_file.write_text("FRED_API_KEY=secret-token\n", encoding="utf-8")
    linked_env_dir = tmp_path / "linked-env"
    linked_env_dir.symlink_to(real_env_dir, target_is_directory=True)

    rc = mod.main(
        [
            "--providers",
            "fred",
            "--no-network",
            "--env-file",
            str(linked_env_dir / "provider.env"),
            "--output-dir",
            str(tmp_path / "samples"),
            "--manifest-json",
        ]
    )

    assert rc == 2
    payload = _payload(capsys.readouterr().out)
    assert payload["code"] == "RETRIEVE_PROVIDER_ENV_FILE_PARENT_IS_SYMLINK"


def test_provider_health_rejects_symlinked_manifest(tmp_path: Path, capsys) -> None:  # noqa: ANN001
    mod = _load_module("_provider_health_path_integrity", "scripts/provider_health_check.py")
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"schema_version":"provider_samples_manifest/v1","entries":[]}\n', encoding="utf-8")
    linked_manifest = tmp_path / "linked-manifest.json"
    linked_manifest.symlink_to(manifest)

    rc = mod.main(["--manifest", str(linked_manifest), "--json"])

    assert rc == 2
    payload = _payload(capsys.readouterr().out)
    assert payload["code"] == "PROVIDER_HEALTH_MANIFEST_IS_SYMLINK"


def test_provider_evidence_rejects_output_under_symlinked_parent(tmp_path: Path, capsys) -> None:  # noqa: ANN001
    mod = _load_module("_provider_evidence_path_integrity", "scripts/build_provider_evidence_manifest.py")
    samples = tmp_path / "samples_manifest.json"
    samples.write_text('{"schema_version":"provider_samples_manifest/v1","entries":[]}\n', encoding="utf-8")
    real_output_dir = tmp_path / "real-output"
    real_output_dir.mkdir()
    linked_output_dir = tmp_path / "linked-output"
    linked_output_dir.symlink_to(real_output_dir, target_is_directory=True)

    rc = mod.main(["--samples", str(samples), "--output", str(linked_output_dir / "provider_evidence.json")])

    assert rc == 2
    payload = _payload(capsys.readouterr().out)
    assert payload["code"] == "PROVIDER_EVIDENCE_OUTPUT_PARENT_IS_SYMLINK"
    assert not (real_output_dir / "provider_evidence.json").exists()


def test_provider_evidence_rejects_symlinked_normalized_records(tmp_path: Path, capsys) -> None:  # noqa: ANN001
    mod = _load_module("_provider_evidence_normalized_path_integrity", "scripts/build_provider_evidence_manifest.py")
    samples = tmp_path / "samples_manifest.json"
    samples.write_text('{"schema_version":"provider_samples_manifest/v1","entries":[]}\n', encoding="utf-8")
    normalized = tmp_path / "normalized.json"
    normalized.write_text("[]\n", encoding="utf-8")
    linked_normalized = tmp_path / "linked-normalized.json"
    linked_normalized.symlink_to(normalized)

    rc = mod.main(
        [
            "--samples",
            str(samples),
            "--normalized",
            str(linked_normalized),
            "--output",
            str(tmp_path / "provider_evidence.json"),
        ]
    )

    assert rc == 2
    payload = _payload(capsys.readouterr().out)
    assert payload["code"] == "PROVIDER_EVIDENCE_NORMALIZED_IS_SYMLINK"


def test_normalize_provider_samples_rejects_symlinked_samples_dir(tmp_path: Path, capsys) -> None:  # noqa: ANN001
    mod = _load_module("_normalize_provider_samples_path_integrity", "scripts/normalize_provider_samples.py")
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"schema_version":"provider_samples_manifest/v1","entries":[]}\n', encoding="utf-8")
    real_samples = tmp_path / "real-samples"
    real_samples.mkdir()
    linked_samples = tmp_path / "linked-samples"
    linked_samples.symlink_to(real_samples, target_is_directory=True)

    rc = mod.main(
        [
            "--manifest",
            str(manifest),
            "--samples-dir",
            str(linked_samples),
            "--output",
            str(tmp_path / "normalized.json"),
        ]
    )

    assert rc == 2
    payload = _payload(capsys.readouterr().out)
    assert payload["code"] == "NORMALIZE_PROVIDER_SAMPLES_DIR_IS_SYMLINK"


def test_normalize_provider_samples_rejects_symlinked_output(tmp_path: Path, capsys) -> None:  # noqa: ANN001
    mod = _load_module("_normalize_provider_samples_output_path_integrity", "scripts/normalize_provider_samples.py")
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"schema_version":"provider_samples_manifest/v1","entries":[]}\n', encoding="utf-8")
    real_output = tmp_path / "normalized.json"
    real_output.write_text("placeholder\n", encoding="utf-8")
    linked_output = tmp_path / "linked-normalized.json"
    linked_output.symlink_to(real_output)

    rc = mod.main(["--manifest", str(manifest), "--output", str(linked_output)])

    assert rc == 2
    payload = _payload(capsys.readouterr().out)
    assert payload["code"] == "NORMALIZE_PROVIDER_OUTPUT_IS_SYMLINK"
    assert real_output.read_text(encoding="utf-8") == "placeholder\n"

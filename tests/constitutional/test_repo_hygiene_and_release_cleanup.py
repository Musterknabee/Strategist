from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_clean_archive_and_release_cleanup_filter_runtime_transients():
    package=(ROOT/"scripts/package_repo.py").read_text(); release=(ROOT/"strategy_validator/cli/release_candidate_cleanup.py").read_text()
    for item in ["EXCLUDED_TOP_LEVEL",'"artifacts"', '"scratch"', '".db-wal"', '".jsonl"']:
        assert item in package
    assert 'rm_tree(Path(".pytest_cache"))' in release
    assert 'rm_tree(Path(".import_linter_cache"))' in release

from __future__ import annotations

import json
from pathlib import Path


def test_strategist_web_package_manifest_pins_top_level_dependencies() -> None:
    package_json = json.loads(Path('ui/strategist-web/package.json').read_text(encoding='utf-8'))

    for section in ('dependencies', 'devDependencies'):
        entries = package_json.get(section, {})
        assert entries, f'{section} should not be empty'
        assert all(str(version).strip().lower() != 'latest' for version in entries.values())

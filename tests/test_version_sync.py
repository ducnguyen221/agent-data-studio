"""Một số phiên bản cho mọi manifest phát hành.

Bump version phải đổi đủ năm chỗ cùng lúc và có mục tương ứng ở đầu `docs/CHANGELOG.md`;
lệch một chỗ thì marketplace, gói Python và ghi chú phát hành nói ba phiên bản khác nhau.
"""

import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(rel: str) -> str:
    with open(os.path.join(REPO, rel.replace("/", os.sep)), encoding="utf-8") as fh:
        return fh.read()


def manifest_versions() -> dict[str, str]:
    found = {}
    pyproject = re.search(r'^version\s*=\s*"([^"]+)"', read("pyproject.toml"), re.MULTILINE)
    found["pyproject.toml"] = pyproject.group(1) if pyproject else None
    init = re.search(r'^__version__\s*=\s*"([^"]+)"', read("powerbi_agent/__init__.py"), re.MULTILINE)
    found["powerbi_agent/__init__.py"] = init.group(1) if init else None
    found[".claude-plugin/plugin.json"] = json.loads(read(".claude-plugin/plugin.json")).get("version")
    found[".codex-plugin/plugin.json"] = json.loads(read(".codex-plugin/plugin.json")).get("version")
    market = json.loads(read(".claude-plugin/marketplace.json"))
    for plugin in market.get("plugins", []):
        found[f".claude-plugin/marketplace.json#{plugin.get('name')}"] = plugin.get("version")
    return found


def test_all_manifests_share_one_version():
    versions = manifest_versions()
    assert None not in versions.values(), f"Thiếu trường version: {versions}"
    assert len(set(versions.values())) == 1, f"Version lệch giữa các manifest: {versions}"
    assert re.fullmatch(r"\d+\.\d+\.\d+", next(iter(versions.values())))


def test_changelog_leads_with_current_version():
    version = next(iter(manifest_versions().values()))
    first = re.search(r"^## (\S+)", read("docs/CHANGELOG.md"), re.MULTILINE)
    assert first and first.group(1) == version, (
        f"Mục đầu docs/CHANGELOG.md phải là {version}, đang là {first.group(1) if first else None}"
    )

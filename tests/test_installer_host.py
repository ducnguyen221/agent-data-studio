"""Host configuration regressions against the real installer in an isolated profile."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib

import pytest

from test_installer import source_fixture  # noqa: F401 (shared synthetic source fixture)


def _install(source: Path, home: Path, *hosts: str) -> subprocess.CompletedProcess[str]:
    home.mkdir(exist_ok=True)
    env = os.environ.copy()
    for name in (
        "ADS_DATA", "POWERBI_PROJECT_DIR", "POWERBI_POLICY_FILE", "POWERBI_AUDIT_DIR",
        "ADS_SECRETS_FILE",
    ):
        env.pop(name, None)
    env["USERPROFILE"] = str(home)
    env["POWERBI_INSTALL_PYTHON"] = sys.executable
    # Force the Claude JSON fallback without invoking a real CLI or touching its profile.
    powershell = shutil.which("powershell")
    assert powershell is not None
    env["PATH"] = os.pathsep.join(
        [str(Path(powershell).parent), str(Path(sys.executable).parent),
         str(Path(os.environ["SystemRoot"]) / "System32")]
    )
    return subprocess.run(
        [powershell, "-NoProfile", "-File", str(source / "install.ps1"),
         "-SkipVenv", "-Hosts", *hosts],
        cwd=source, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=90,
    )


def _assert_ok(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, result.stdout[-1800:] + result.stderr[-1800:]


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
def test_codex_foreign_sections_preserved_and_own_block_idempotent(source_fixture):
    source = source_fixture
    home = source.parent / "fakehome"
    config = home / ".codex" / "config.toml"
    config.parent.mkdir(parents=True)
    config.write_text(
        'model = "user-model"\n\n'
        '[mcp_servers.foreign]\ncommand = "foreign-tool"\n'
        '[mcp_servers.foreign.env]\nKEEP = "yes"\n',
        encoding="utf-8",
    )
    _assert_ok(_install(source, home, "codex"))
    first = config.read_bytes()
    data = tomllib.loads(first.decode("utf-8"))
    assert data["model"] == "user-model"
    assert data["mcp_servers"]["foreign"] == {
        "command": "foreign-tool", "env": {"KEEP": "yes"},
    }
    owned = data["mcp_servers"]["powerbi-mcp-bridge"]
    assert Path(owned["args"][1]) == source / "mcp_server_powerbi.py"
    assert owned["env"] == {"PYTHONUNBUFFERED": "1"}
    _assert_ok(_install(source, home, "codex"))
    assert config.read_bytes() == first
    assert not (home / ".claude.json").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
def test_claude_nested_json_and_other_servers_preserved(source_fixture):
    source = source_fixture
    home = source.parent / "fakehome"
    home.mkdir()
    config = home / ".claude.json"
    original = {
        "": {"nested": [{"message": "giữ nguyên", "level": [1, {"deep": True}]}]},
        "mcpServers": {"foreign": {"command": "other", "env": {"KEEP": "yes"}}},
        "otherSetting": [1, {"inner": [2, 3]}],
    }
    config.write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8")
    _assert_ok(_install(source, home, "claude"))
    first = json.loads(config.read_text(encoding="utf-8"))
    assert first[""] == original[""]
    assert first["otherSetting"] == original["otherSetting"]
    assert first["mcpServers"]["foreign"] == original["mcpServers"]["foreign"]
    assert Path(first["mcpServers"]["powerbi-mcp-bridge"]["args"][1]) == (
        source / "mcp_server_powerbi.py"
    )
    _assert_ok(_install(source, home, "claude"))
    assert json.loads(config.read_text(encoding="utf-8")) == first
    assert not (home / ".codex" / "config.toml").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
def test_invalid_claude_json_keeps_original_and_reports_failure(source_fixture):
    source = source_fixture
    home = source.parent / "fakehome"
    home.mkdir()
    config = home / ".claude.json"
    invalid = b"{invalid fixture JSON"
    config.write_bytes(invalid)
    result = _install(source, home, "claude")
    assert result.returncode != 0
    assert config.read_bytes() == invalid
    assert not (home / ".codex" / "config.toml").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
@pytest.mark.parametrize(
    ("host", "relative_config"),
    [
        ("codex", Path(".codex/config.toml")),
        ("claude", Path(".claude.json")),
        ("antigravity", Path(".gemini/antigravity/mcp_config.json")),
    ],
)
def test_same_name_foreign_server_is_refused_without_overwrite(
    source_fixture, host, relative_config
):
    source = source_fixture
    home = source.parent / "fakehome"
    config = home / relative_config
    config.parent.mkdir(parents=True)
    if host == "codex":
        original = (
            '[mcp_servers.powerbi-mcp-bridge]\ncommand = "foreign-tool"\n'
            'args = ["--user-owned"]\n'
        ).encode("utf-8")
    else:
        original = json.dumps(
            {"mcpServers": {"powerbi-mcp-bridge": {
                "command": "foreign-tool", "args": ["--user-owned"]
            }}},
            indent=2,
        ).encode("utf-8")
    config.write_bytes(original)
    result = _install(source, home, host)
    assert result.returncode != 0, result.stdout[-1800:] + result.stderr[-1800:]
    assert config.read_bytes() == original


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
def test_invalid_existing_codex_toml_keeps_original(source_fixture):
    source = source_fixture
    home = source.parent / "fakehome"
    config = home / ".codex" / "config.toml"
    config.parent.mkdir(parents=True)
    invalid = b'[broken\nvalue = "fixture"\n'
    config.write_bytes(invalid)
    result = _install(source, home, "codex")
    assert result.returncode != 0, result.stdout[-1800:] + result.stderr[-1800:]
    assert config.read_bytes() == invalid


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
def test_selected_host_does_not_modify_other_existing_configs(source_fixture):
    source = source_fixture
    home = source.parent / "fakehome"
    codex = home / ".codex" / "config.toml"
    claude = home / ".claude.json"
    antigravity = home / ".gemini" / "antigravity" / "mcp_config.json"
    for config in (codex, claude, antigravity):
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text("untouched fixture", encoding="utf-8")
    codex.write_text('model = "fixture"\n', encoding="utf-8")
    before_claude = claude.read_bytes()
    before_antigravity = antigravity.read_bytes()
    _assert_ok(_install(source, home, "codex"))
    assert claude.read_bytes() == before_claude
    assert antigravity.read_bytes() == before_antigravity
    assert "powerbi-mcp-bridge" in codex.read_text(encoding="utf-8")


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
@pytest.mark.parametrize(
    ("host", "relative_config"),
    [
        ("codex", Path(".codex/config.toml")),
        ("claude", Path(".claude.json")),
        ("antigravity", Path(".gemini/antigravity/mcp_config.json")),
    ],
)
def test_owned_entry_preserves_user_customizations(source_fixture, host, relative_config):
    source = source_fixture
    home = source.parent / "fakehome"
    config = home / relative_config
    config.parent.mkdir(parents=True)
    server = str(source / "mcp_server_powerbi.py")
    if host == "codex":
        original = (
            "[mcp_servers.powerbi-mcp-bridge]\n"
            f"command = {json.dumps(sys.executable)}\n"
            f"args = [\"-u\", {json.dumps(server)}]\n"
            "enabled = false\n"
            "[mcp_servers.powerbi-mcp-bridge.env]\n"
            "ADS_DATA = \"D:/user-station\"\n"
        ).encode("utf-8")
    else:
        original = json.dumps({"mcpServers": {"powerbi-mcp-bridge": {
            "command": sys.executable,
            "args": ["-u", server],
            "env": {"ADS_DATA": "D:/user-station"},
            "enabled": False,
        }}}, indent=2).encode("utf-8")
    config.write_bytes(original)
    _assert_ok(_install(source, home, host))
    assert config.read_bytes() == original


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
def test_existing_unowned_venv_is_not_adopted(source_fixture):
    source = source_fixture
    venv = source / ".venv"
    venv.mkdir()
    canary = venv / "keep.txt"
    canary.write_text("user venv", encoding="utf-8")
    env = os.environ.copy()
    env.pop("ADS_DATA", None)
    env["USERPROFILE"] = str(source.parent / "fakehome")
    result = subprocess.run(
        ["powershell", "-NoProfile", "-File", str(source / "install.ps1"), "-SkipHosts"],
        cwd=source, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=90,
    )
    assert result.returncode != 0
    assert canary.read_text(encoding="utf-8") == "user venv"
    assert not (venv / ".ads-venv-owned").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
def test_failed_dependency_install_can_retry_owned_venv(source_fixture):
    source = source_fixture
    env = os.environ.copy()
    env.pop("ADS_DATA", None)
    env["USERPROFILE"] = str(source.parent / "fakehome")
    env["PIP_NO_INDEX"] = "1"
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    command = ["powershell", "-NoProfile", "-File", str(source / "install.ps1"), "-SkipHosts"]
    first = subprocess.run(command, cwd=source, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
    assert first.returncode != 0
    marker = source / ".venv" / ".ads-venv-owned"
    assert marker.read_text(encoding="utf-8").strip() == str(source)
    second = subprocess.run(command, cwd=source, env=env, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=120)
    assert second.returncode != 0
    assert "chưa có dấu sở hữu" not in second.stdout
    assert marker.read_text(encoding="utf-8").strip() == str(source)

"""WP-04-fix — lỗi thấp của installer tìm thấy ở rehearsal G39, chạy installer thật trên source giả.

Không cài gì vào Python hệ thống: ca override dùng một "python" giả (.cmd ghi lại lời gọi).
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from test_installer import run_install, source_fixture  # noqa: F401 (fixture dùng chung)
from test_installer_host import _install

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")


def test_python_override_without_skipvenv_is_refused_before_write(source_fixture):
    source = source_fixture
    fake = source.parent / "fake python" / "python.cmd"
    fake.parent.mkdir()
    calls = fake.parent / "calls.txt"
    fake.write_text(f'@echo %*>>"{calls}"\r\n@exit /b 0\r\n', encoding="ascii")
    env = os.environ.copy()
    env.pop("ADS_DATA", None)
    env["USERPROFILE"] = str(source.parent / "fakehome")
    env["POWERBI_INSTALL_PYTHON"] = str(fake)
    result = subprocess.run(
        ["powershell", "-NoProfile", "-File", str(source / "install.ps1"), "-SkipHosts"],
        cwd=source, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=120,
    )
    assert result.returncode == 1, result.stdout[-1500:] + result.stderr[-1500:]
    # stdout PowerShell 5.1 không phải UTF-8 khi bị chuyển hướng: chỉ so phần ASCII của thông điệp.
    assert "POWERBI_INSTALL_PYTHON" in result.stdout and "-SkipVenv (CI/test)" in result.stdout
    # Không pip install vào Python chỉ định, không dựng trạm, không coi nó là venv.
    assert not calls.exists(), calls.read_text(encoding="ascii", errors="replace")
    assert not (source / "workspace").exists()
    assert not (source / ".venv").exists()


def test_reinstall_with_unchanged_config_leaves_no_new_backup(source_fixture):
    source = source_fixture
    home = source.parent / "fakehome"
    codex = home / ".codex" / "config.toml"
    codex.parent.mkdir(parents=True)
    codex.write_text('model = "user-model"\n', encoding="utf-8")
    claude = home / ".claude.json"
    claude.write_text('{"mcpServers": {}}\n', encoding="utf-8")
    for host in ("codex", "claude"):
        first = _install(source, home, host)
        assert first.returncode == 0, first.stdout[-1800:] + first.stderr[-1800:]
    backups = sorted(p.name for p in home.rglob("*.bak.*"))
    assert len(backups) == 2, backups  # lần đầu đổi cả hai file: mỗi file đúng một bản sao lưu
    for host in ("codex", "claude"):
        second = _install(source, home, host)
        assert second.returncode == 0, second.stdout[-1800:] + second.stderr[-1800:]
    assert sorted(p.name for p in home.rglob("*.bak.*")) == backups


def test_foreign_same_name_entry_prints_next_step(source_fixture):
    source = source_fixture
    home = source.parent / "fakehome"
    config = home / ".codex" / "config.toml"
    config.parent.mkdir(parents=True)
    original = b'[mcp_servers.powerbi-mcp-bridge]\ncommand = "foreign-tool"\nargs = ["--user-owned"]\n'
    config.write_bytes(original)
    result = _install(source, home, "codex")
    assert result.returncode != 0
    assert config.read_bytes() == original
    assert "uninstall.ps1" in result.stdout, result.stdout[-1800:]


def test_switch_from_workspace_with_data_to_external_station_warns(source_fixture):
    source = source_fixture
    first = run_install(source)
    assert first.returncode == 0, first.stdout[-1500:] + first.stderr[-1500:]
    keep = source / "workspace" / "projects" / "keep.txt"
    keep.write_text("user data", encoding="utf-8")
    station = source.parent / "station"
    second = run_install(source, ads_data=str(station))
    assert second.returncode == 0, second.stdout[-1500:] + second.stderr[-1500:]
    assert "[!] workspace/" in second.stdout, second.stdout[-1500:]
    assert keep.read_text(encoding="utf-8") == "user data"  # không di chuyển dữ liệu
    assert not (station / "projects" / "keep.txt").exists()
    assert Path(station / "config.env").is_file()

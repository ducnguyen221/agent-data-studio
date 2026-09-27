"""Regression checks for local Power BI diagnostics without real credentials."""

import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from powerbi_agent import discovery


REPO = Path(__file__).resolve().parents[1]


def test_port_discovery_uses_bounded_argument_list():
    assert Path(discovery.__file__).resolve() == (REPO / "powerbi_agent" / "discovery.py").resolve()
    result = subprocess.CompletedProcess([], 0, stdout="54321\n", stderr="")
    with patch.object(discovery.sys, "platform", "win32"), patch(
        "subprocess.run", return_value=result
    ) as run:
        instances = discovery.find_active_pbi_ports()

    assert instances == [{"port": "54321", "workspace_id": "tcp_54321"}]
    calls = [call for call in run.call_args_list if isinstance(call.args[0], list)]
    assert len(calls) == 1
    args, kwargs = calls[0].args, calls[0].kwargs
    assert args[0][:3] == ["powershell", "-NoProfile", "-Command"]
    assert kwargs["timeout"] == 10
    assert "shell" not in kwargs


def test_connection_diagnostic_does_not_print_exception_detail(tmp_path):
    source = tmp_path / "checkout"
    (source / "scripts").mkdir(parents=True)
    (source / "powerbi_agent").mkdir()
    shutil.copy2(REPO / "scripts" / "test_mcp_local.py", source / "scripts" / "test_mcp_local.py")
    (source / "mcp_server_powerbi.py").write_text(
        "def find_active_pbi_ports():\n"
        "    return [{'port': '0', 'workspace_id': 'invalid'}, "
        "{'port': '54321', 'workspace_id': 'synthetic'}]\n",
        encoding="utf-8",
    )
    (source / "powerbi_agent" / "__init__.py").write_text("", encoding="utf-8")
    shutil.copy2(REPO / "powerbi_agent" / "connection.py", source / "powerbi_agent" / "connection.py")
    (source / "pyadomd.py").write_text(
        "class Pyadomd:\n"
        "    def __init__(self, connection):\n"
        "        raise RuntimeError('SYNTHETIC_PRIVATE_CANARY')\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(source / "scripts" / "test_mcp_local.py")],
        cwd=source, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20,
    )
    assert result.returncode == 1
    assert "Lỗi khi kết nối ADOMD tới cổng 0." in result.stdout
    assert "Lỗi khi kết nối ADOMD tới cổng 54321." in result.stdout
    assert "SYNTHETIC_PRIVATE_CANARY" not in result.stdout + result.stderr

    (source / "pyadomd.py").write_text(
        "class Cursor:\n"
        "    def __enter__(self): return self\n"
        "    def __exit__(self, *args): return False\n"
        "    def execute(self, query): self.query = query; return self\n"
        "    def fetchall(self):\n"
        "        return [('SYNTHETIC_MODEL',)] if 'CATALOG' in self.query else [('SyntheticTable',)]\n"
        "class Pyadomd:\n"
        "    def __init__(self, connection): pass\n"
        "    def __enter__(self): return self\n"
        "    def __exit__(self, *args): return False\n"
        "    def cursor(self): return Cursor()\n",
        encoding="utf-8",
    )
    success = subprocess.run(
        [sys.executable, str(source / "scripts" / "test_mcp_local.py")],
        cwd=source, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20,
    )
    assert success.returncode == 0, success.stdout + success.stderr
    assert "Lỗi khi kết nối ADOMD tới cổng 0." in success.stdout
    assert "Kết nối thành công!" in success.stdout
    assert "SYNTHETIC_MODEL" in success.stdout

    (source / "mcp_server_powerbi.py").write_text(
        "raise ImportError('SYNTHETIC_PRIVATE_CANARY')\n", encoding="utf-8"
    )
    missing_dependency = subprocess.run(
        [sys.executable, str(source / "scripts" / "test_mcp_local.py")],
        cwd=source, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20,
    )
    assert missing_dependency.returncode == 1
    assert "Thiếu thư viện hoặc file mcp_server_powerbi.py; kiểm tra bộ cài." in missing_dependency.stdout
    assert "SYNTHETIC_PRIVATE_CANARY" not in missing_dependency.stdout + missing_dependency.stderr

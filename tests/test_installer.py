"""Regression test cho install.ps1/uninstall.ps1 — chạy bộ ca PowerShell end-to-end
với USERPROFILE GIẢ (không đụng config thật của máy).

Ra đời từ audit 2026-07-15 (sự cố Codex chết vì TOML duplicate key). Bộ ca cover:
fuzz 9 config Codex (rỗng/thiếu/CRLF/EOF/orphan sub-table/BOM/prefix-name/duplicate hỏng thật)
× chạy 2 lần (heal + idempotent) + validate parse sau ghi; merge JSON Claude/Antigravity
qua Python (fixture có KEY RỖNG — thứ làm ConvertFrom-Json PS 5.1 crash); chu trình
install→uninstall→install; skill-copy mirror (không drift); uninstall đối xứng.
"""

import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUITE = os.path.join(REPO, "tests", "installer", "installer.tests.ps1")


@pytest.mark.skipif(sys.platform != "win32", reason="installer là PowerShell/Windows")
def test_installer_config_suite():
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", SUITE,
         "-RepoRoot", REPO, "-PythonExe", sys.executable],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600,
    )
    out = proc.stdout + proc.stderr
    # Harness da tu exit 1 khi co ca do — phai KIEM ma tra ve, khong chi doc stdout,
    # neu khong thi mot lan refactor lam mat exit code se troi qua im lang.
    assert proc.returncode == 0, f"harness exit {proc.returncode}:\n{out[-3000:]}"
    lines = [line for line in out.splitlines() if line.startswith(("PASS", "FAIL"))]
    assert lines, f"suite không chạy ra ca nào:\n{out[-2000:]}"
    fails = [line for line in lines if line.startswith("FAIL")]
    assert not fails, "Có ca FAIL:\n" + "\n".join(fails) + f"\n--- full ---\n{out[-3000:]}"
    assert len(lines) >= 26, f"thiếu ca (được {len(lines)}/26):\n" + "\n".join(lines)

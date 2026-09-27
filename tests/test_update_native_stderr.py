"""update.ps1: stderr của git không được làm script chết im; lỗi thật vẫn in [FAIL] và exit 1.

Windows PowerShell 5.1 với ErrorActionPreference=Stop biến stderr của lệnh native thành lỗi dừng
khi stderr bị chuyển hướng (`2>$null` trong script, hoặc người gọi gom `*>&1`/`2>&1`). `git fetch`
luôn ghi "From …" ra stderr. Repo git tạm + bare remote, không đụng mạng.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
# Windows PowerShell 5.1 là shell mục tiêu (T15); pwsh chỉ là đường lùi khi máy không có nó.
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")
GIT = shutil.which("git")
IDENTITY = ("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid")


def run(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False, timeout=120)


def _commit(upstream: Path, message: str) -> None:
    run(GIT, "add", ".", cwd=upstream)
    assert run(GIT, *IDENTITY, "commit", "-m", message, cwd=upstream).returncode == 0


@pytest.fixture
def checkout(tmp_path):
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    run(GIT, "init", "-b", "main", str(upstream))
    for name in ("install.ps1", "uninstall.ps1", "doctor.ps1"):
        (upstream / name).write_text("Write-Host 'fixture'\n", encoding="utf-8")
    shutil.copy2(REPO / "update.ps1", upstream / "update.ps1")
    (upstream / "scripts").mkdir()
    shutil.copy2(REPO / "scripts" / "update_release.py", upstream / "scripts" / "update_release.py")
    (upstream / "requirements.txt").write_text("packaging==25.0\n", encoding="utf-8")
    (upstream / "mcp_server_powerbi.py").write_text("pass\n", encoding="utf-8")
    (upstream / "sample.py").write_text("value = 1\n", encoding="utf-8")
    _commit(upstream, "seed")
    bare = tmp_path / "remote.git"
    assert run(GIT, "clone", "--bare", str(upstream), str(bare)).returncode == 0
    clone = tmp_path / "checkout"
    assert run(GIT, "clone", str(bare), str(clone)).returncode == 0
    (upstream / "sample.py").write_text("value = 2\n", encoding="utf-8")
    _commit(upstream, "candidate")
    assert run(GIT, "push", str(bare), "main", cwd=upstream).returncode == 0
    return clone


def _update(clone: Path, redirect: str):
    script = str(clone / "update.ps1")
    if not redirect:
        return run(POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, cwd=clone)
    # Người gọi gom output vào biến (cách một agent/CI thường gọi): đây là dạng làm PS 5.1
    # bọc stderr native thành lỗi; `& script *>&1` in thẳng ra console thì không tái hiện.
    command = (f"$out = & '{script}' {redirect}; $code = $LASTEXITCODE; "
               "$out | Out-String; exit $code")
    return run(POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command, cwd=clone)


@pytest.mark.skipif(not POWERSHELL or not GIT, reason="PowerShell and Git required")
@pytest.mark.parametrize("redirect", ["", "*>&1", "2>&1"])
def test_update_preview_survives_git_fetch_stderr(checkout, redirect):
    result = _update(checkout, redirect)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "READY_FOR_REVIEW" in result.stdout


@pytest.mark.skipif(not POWERSHELL or not GIT, reason="PowerShell and Git required")
@pytest.mark.parametrize("redirect", ["", "*>&1"])
def test_update_fetch_failure_prints_fail(checkout, redirect):
    missing = checkout.parent / "missing.git"
    assert run(GIT, "remote", "set-url", "origin", str(missing), cwd=checkout).returncode == 0
    result = _update(checkout, redirect)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "[FAIL] Fetch failed" in result.stdout


@pytest.mark.skipif(not POWERSHELL or not GIT, reason="PowerShell and Git required")
@pytest.mark.parametrize("redirect", ["", "*>&1"])
def test_update_missing_upstream_prints_fail(checkout, redirect):
    assert run(GIT, "branch", "--unset-upstream", cwd=checkout).returncode == 0
    result = _update(checkout, redirect)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "[FAIL] Branch upstream unavailable." in result.stdout


def _short_path(path: Path) -> str:
    import ctypes

    buffer = ctypes.create_unicode_buffer(32768)
    ctypes.windll.kernel32.GetShortPathNameW(str(path.resolve()), buffer, len(buffer))
    return buffer.value or str(path.resolve())


def _update_with_python_argument(clone: Path, argument: str):
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", argument],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        return _update(clone, "")
    finally:
        child.kill()
        child.wait(timeout=10)


@pytest.mark.skipif(not POWERSHELL or not GIT or sys.platform != "win32", reason="Windows PowerShell and Git required")
@pytest.mark.parametrize("form", ["long", "short", "root"])
def test_update_refuses_when_python_uses_checkout_by_short_path(checkout, form):
    """CIM trả CommandLine đúng dạng lúc khởi chạy (dài, 8.3, hoặc gốc làm đối số cuối): phải từ chối."""
    script = checkout / "sample.py"
    if form == "short" and _short_path(script).lower() == str(script.resolve()).lower():
        pytest.skip("Ổ đĩa này tắt tên ngắn 8.3: dạng ngắn trùng dạng dài, không có gì để so.")
    argument = {"long": str(script.resolve()), "short": _short_path(script),
                "root": str(checkout.resolve())}[form]
    result = _update_with_python_argument(checkout, argument)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "[FAIL] A Python process is using this checkout." in result.stdout


@pytest.mark.skipif(not POWERSHELL or not GIT or sys.platform != "win32", reason="Windows PowerShell and Git required")
@pytest.mark.parametrize("suffix", ["2", "-old"])
def test_update_ignores_python_in_sibling_clone_with_same_prefix(checkout, suffix):
    """Clone anh em `<gốc>2`, `<gốc>-old` chung tiền tố nhưng không phải checkout này -> vẫn preview."""
    sibling = checkout.parent / (checkout.name + suffix)
    sibling.mkdir()
    (sibling / "sample.py").write_text("value = 1\n", encoding="utf-8")
    result = _update_with_python_argument(checkout, str((sibling / "sample.py").resolve()))
    assert result.returncode == 2, result.stdout + result.stderr
    assert "READY_FOR_REVIEW" in result.stdout


@pytest.mark.skipif(not POWERSHELL or not GIT or sys.platform != "win32", reason="Windows PowerShell and Git required")
def test_update_reports_path_forms_overflow(checkout):
    """Quá 1024 dạng đường 8.3 -> [FAIL] với mã riêng, exit 1, không coi là rảnh."""
    deep = checkout.parent
    for _ in range(11):
        deep = deep / "a b"
    deep.parent.mkdir(parents=True)
    if _short_path(deep.parent).lower() == str(deep.parent.resolve()).lower():
        pytest.skip("Ổ đĩa này tắt tên ngắn 8.3: chỉ có một dạng đường.")
    assert run(GIT, "clone", str(checkout.parent / "remote.git"), str(deep)).returncode == 0
    result = _update(deep, "")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "[FAIL] PATH_FORMS_OVERFLOW:" in result.stdout

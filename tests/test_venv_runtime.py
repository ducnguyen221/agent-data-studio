"""SPR-61 TK7 — venv MCP Power BI nằm ở runtime OpcOS (R\\mcp\\agent-data-studio\\powerbi), không phải .venv.

Mọi test chạy trong cây giả ở thư mục tạm: HOME/USERPROFILE/APPDATA giả, gốc runtime giả, CLI
`opcos-runtime.ps1` giả (ghi lại tham số, không cài gì thật). Không test nào chạm runtime hay cấu hình host
thật của máy.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from test_installer import source_fixture  # noqa: F401 (nguồn giả dùng chung)

REPO = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")
pytestmark = pytest.mark.skipif(
    sys.platform != "win32" or not POWERSHELL, reason="installer chạy trên Windows PowerShell"
)

TARGET_REL = Path("mcp") / "agent-data-studio" / "powerbi"

# Véc-tơ VT1-VT4 chép nguyên văn từ hợp đồng runtime-resource-v1.json (khối `vectors`), chỉ giữ phần đường gốc:
# `/r` `/o` `/h` là gốc giả (map sang thư mục tạm). Hợp đồng gọi với category venvs; data đặt ở category mcp,
# nên phần đuôi so sánh là mcp\agent-data-studio\powerbi (cùng quy tắc "R/<category>/<repoKey>/<resourceKey>").
# `expect` là đường gốc R (không kèm đuôi); None = không có OpcOS.
VECTORS = [
    {"id": "VT1", "env": {"OPCOS_RUNTIME": "/r", "OPCOS_ROOT": "/o"}, "paths_json": True, "expect": ["/r"]},
    {"id": "VT2", "env": {"OPCOS_ROOT": "/o"}, "paths_json": False, "expect": ["/o", "runtime"]},
    {"id": "VT3", "env": {}, "paths_json": True, "expect": ["/h", "OpcOS", "runtime"]},
    {"id": "VT4", "env": {}, "paths_json": False, "expect": None},
]

FAKE_CLI = r'''
# CLI opcos-runtime giả cho test: ghi tham số, không cài gì thật ngoài venv rỗng khi `ensure`.
$log = $env:ADS_FAKE_CLI_LOG
if ($log) { Add-Content -LiteralPath $log -Value ($args -join '|') -Encoding UTF8 }
$cmd = [string]$args[0]
$target = Join-Path $env:OPCOS_RUNTIME 'mcp\agent-data-studio\powerbi'
$manifestFile = Join-Path $target '.opcos-resource.json'
if ($cmd -eq 'ensure') {
    & $env:ADS_FAKE_PY -m venv --without-pip $target
    $m = @{ schema = 'opcos-resource/1'; category = 'mcp'; repoKey = 'agent-data-studio'; resourceKey = 'powerbi';
            installed_by = 'agent-data-studio'; consumers = @('agent-data-studio'); status = 'complete' }
    [System.IO.File]::WriteAllText($manifestFile, ($m | ConvertTo-Json -Depth 5), (New-Object System.Text.UTF8Encoding($false)))
    Write-Output "RT_CREATED $target"
    exit 0
}
if ($cmd -eq 'release') {
    $repo = $args[[array]::IndexOf($args, '--repo') + 1]
    if (Test-Path -LiteralPath $manifestFile) {
        $m = Get-Content -LiteralPath $manifestFile -Raw -Encoding UTF8 | ConvertFrom-Json
        $m.consumers = @($m.consumers | Where-Object { $_ -ne $repo })
        [System.IO.File]::WriteAllText($manifestFile, ($m | ConvertTo-Json -Depth 5), (New-Object System.Text.UTF8Encoding($false)))
        Write-Output "RT_CONSUMER_REMOVED $target"
    }
    exit 0
}
exit 0
'''


def _clean_env(home: Path) -> dict[str, str]:
    env = os.environ.copy()
    for name in ("OPCOS_RUNTIME", "OPCOS_ROOT", "ADS_DATA", "POWERBI_PROJECT_DIR", "POWERBI_POLICY_FILE",
                 "POWERBI_AUDIT_DIR", "ADS_SECRETS_FILE", "POWERBI_INSTALL_PYTHON"):
        env.pop(name, None)
    home.mkdir(parents=True, exist_ok=True)
    env["USERPROFILE"] = str(home)
    env["HOME"] = str(home)
    env["APPDATA"] = str(home / "AppData" / "Roaming")
    env["LOCALAPPDATA"] = str(home / "AppData" / "Local")
    return env


def _ps(*args: str, env: dict[str, str], cwd: Path | None = None,
        timeout: int = 150) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", *args],
        cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
    )


def _fake_opcos(base: Path, env: dict[str, str]) -> tuple[Path, Path, Path]:
    """Dựng `<base>\\system\\operations\\runtime\\opcos-runtime.ps1` giả + R = `<base>\\runtime`; trả (R, đích, log)."""
    cli = base / "system" / "operations" / "runtime" / "opcos-runtime.ps1"
    cli.parent.mkdir(parents=True)
    cli.write_text("﻿" + FAKE_CLI, encoding="utf-8")
    runtime = base / "runtime"
    runtime.mkdir()
    log = base / "cli.log"
    env["OPCOS_RUNTIME"] = str(runtime)
    env["ADS_FAKE_CLI_LOG"] = str(log)
    env["ADS_FAKE_PY"] = sys.executable
    return runtime, runtime / TARGET_REL, log


def _manifest(target: Path, repo_key: str = "agent-data-studio", consumers=("agent-data-studio",)) -> None:
    target.mkdir(parents=True, exist_ok=True)
    (target / "pyvenv.cfg").write_text("home = fixture\n", encoding="utf-8")
    (target / ".opcos-resource.json").write_text(json.dumps({
        "schema": "opcos-resource/1", "category": "mcp", "repoKey": repo_key, "resourceKey": "powerbi",
        "installed_by": repo_key, "consumers": list(consumers), "status": "complete",
    }), encoding="utf-8")


def _calls(log: Path) -> list[str]:
    return log.read_text(encoding="utf-8-sig").splitlines() if log.exists() else []


def _uninstall_checkout(base: Path) -> Path:
    source = base / "checkout"
    (source / "scripts").mkdir(parents=True)
    shutil.copy2(REPO / "uninstall.ps1", source / "uninstall.ps1")
    shutil.copy2(REPO / "scripts" / "ads-venv.ps1", source / "scripts" / "ads-venv.ps1")
    (source / "mcp_server_powerbi.py").write_text("# fixture\n", encoding="utf-8")
    return source


def _norm(path: str) -> str:
    return os.path.normcase(os.path.normpath(path))


# ---------------------------------------------------------------- véc-tơ đường gốc
@pytest.mark.parametrize("vector", VECTORS, ids=[v["id"] for v in VECTORS])
def test_resolve_root_vectors(vector, tmp_path):
    base = tmp_path / "t"
    mapping = {"/r": base / "r", "/o": base / "o", "/h": base / "h"}
    home = mapping["/h"]
    env = _clean_env(home)
    for name, value in vector["env"].items():
        env[name] = str(mapping[value])
    if vector["paths_json"]:
        (home / "OpcOS").mkdir(parents=True)
        (home / "OpcOS" / "paths.json").write_text("{}", encoding="utf-8")
    root = tmp_path / "checkout"
    root.mkdir()
    if vector["expect"] is None:
        expected = root / ".venv"
    else:
        first, *rest = vector["expect"]
        expected = mapping[first].joinpath(*rest) / TARGET_REL
    result = _ps("-File", str(REPO / "scripts" / "ads-venv.ps1"), "--print", str(root), env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert _norm(result.stdout.strip()) == _norm(str(expected)), vector["id"]
    # Bản Python của updater phải ra cùng đáp số (một hợp đồng, hai ngôn ngữ).
    sys.path.insert(0, str(REPO))
    try:
        from scripts import update_release
    finally:
        sys.path.remove(str(REPO))
    assert _norm(str(update_release.venv_root(root, env))) == _norm(str(expected)), vector["id"]


# ---------------------------------------------------------------- cài
def test_install_refuses_foreign_manifest(source_fixture):
    source = source_fixture
    base = source.parent
    env = _clean_env(base / "fakehome")
    _, target, log = _fake_opcos(base / "opcos", env)
    _manifest(target, repo_key="agent-video-studio", consumers=("agent-video-studio",))
    canary = target / "keep.txt"
    canary.write_text("của repo khác", encoding="utf-8")
    result = _ps("-File", str(source / "install.ps1"), "-SkipHosts", env=env, cwd=source)
    assert result.returncode == 1, result.stdout[-1800:] + result.stderr[-1800:]
    # Console OEM làm hỏng dấu tiếng Việt: chỉ so phần ASCII của thông báo từ chối.
    assert "repoKey=agent-video-studio" in result.stdout
    assert canary.read_text(encoding="utf-8") == "của repo khác"
    assert _calls(log) == [], "không được gọi ensure khi tệp khai sinh thuộc repo khác"
    assert not (target / ".ads-venv-owned").exists()


def test_install_calls_ensure_in_unicode_space_root(source_fixture, tmp_path):
    parent = tmp_path / "Đức Ng"
    parent.mkdir()
    source = parent / "source"
    shutil.copytree(source_fixture, source)
    env = _clean_env(parent / "fakehome")
    _, target, log = _fake_opcos(parent / "opcos", env)
    first = _ps("-File", str(source / "install.ps1"), "-SkipHosts", env=env, cwd=source)
    assert first.returncode == 0, first.stdout[-2000:] + first.stderr[-1500:]
    calls = _calls(log)
    assert calls[0] == f"ensure|--repo-dir|{source}|--only|mcp/powerbi", calls
    assert (target / "Scripts" / "python.exe").is_file()
    assert (target / ".ads-venv-owned").read_text(encoding="utf-8").strip() == str(source)
    # Idempotent: chạy lần hai vẫn xanh (tệp khai sinh còn chủ cũ, không bị từ chối).
    second = _ps("-File", str(source / "install.ps1"), "-SkipHosts", env=env, cwd=source)
    assert second.returncode == 0, second.stdout[-2000:] + second.stderr[-1500:]


def test_skip_hosts_writes_no_host_config(source_fixture):
    source = source_fixture
    home = source.parent / "fakehome"
    env = _clean_env(home)
    _fake_opcos(source.parent / "opcos", env)
    env["POWERBI_INSTALL_PYTHON"] = sys.executable
    result = _ps("-File", str(source / "install.ps1"), "-SkipVenv", "-SkipHosts", env=env, cwd=source)
    assert result.returncode == 0, result.stdout[-1800:] + result.stderr[-1800:]
    leaked = [
        p for p in home.rglob("*")
        if any(part.lower().startswith((".claude", ".codex", ".gemini")) or part == "Claude"
               for part in p.relative_to(home).parts)
    ]
    assert leaked == []


# ---------------------------------------------------------------- gỡ
def _uninstall(source: Path, env: dict[str, str], *extra: str):
    return _ps("-File", str(source / "uninstall.ps1"), "-Hosts", "codex", *extra, env=env, cwd=source)


def test_uninstall_calls_release(tmp_path):
    base = tmp_path / "Đức Ng"
    source = _uninstall_checkout(base)
    env = _clean_env(base / "profile")
    env["POWERBI_INSTALL_PYTHON"] = sys.executable
    _, target, log = _fake_opcos(base / "opcos", env)
    _manifest(target)
    # Không -RemoveVenv: vẫn release, venv ở nguyên.
    plain = _uninstall(source, env)
    assert plain.returncode == 0, plain.stdout + plain.stderr
    assert _calls(log) == ["release|--repo|agent-data-studio"]
    assert target.exists()
    # Có -RemoveVenv: consumers rỗng sau release -> xoá đúng đích runtime.
    _manifest(target)
    removed = _uninstall(source, env, "-RemoveVenv")
    assert removed.returncode == 0, removed.stdout + removed.stderr
    assert not target.exists()
    assert (source / "mcp_server_powerbi.py").exists()


def test_uninstall_keeps_when_other_consumers(tmp_path):
    base = tmp_path / "t"
    source = _uninstall_checkout(base)
    env = _clean_env(base / "profile")
    env["POWERBI_INSTALL_PYTHON"] = sys.executable
    _, target, _ = _fake_opcos(base / "opcos", env)
    _manifest(target, consumers=("agent-data-studio", "agent-marketing-team"))
    result = _uninstall(source, env, "-RemoveVenv")
    assert result.returncode == 0, result.stdout + result.stderr
    assert target.exists(), "còn repo khác dùng -> phải giữ venv"
    assert "other consumers" in (result.stdout + result.stderr)
    data = json.loads((target / ".opcos-resource.json").read_text(encoding="utf-8-sig"))
    assert data["consumers"] == ["agent-marketing-team"]


def test_uninstall_refuses_foreign_runtime_manifest(tmp_path):
    base = tmp_path / "t"
    source = _uninstall_checkout(base)
    env = _clean_env(base / "profile")
    env["POWERBI_INSTALL_PYTHON"] = sys.executable
    _, target, _ = _fake_opcos(base / "opcos", env)
    _manifest(target, repo_key="agent-video-studio", consumers=())
    result = _uninstall(source, env, "-RemoveVenv")
    assert result.returncode == 1
    assert target.exists()


# ---------------------------------------------------------------- .mcp.json
def test_mcp_json_points_runtime():
    data = json.loads((REPO / ".mcp.json").read_text(encoding="utf-8"))
    server = data["mcpServers"]["powerbi-mcp-bridge"]
    assert server["command"] == "${OPCOS_RUNTIME}\\mcp\\agent-data-studio\\powerbi\\Scripts\\python.exe"
    assert server["args"] == ["${CLAUDE_PLUGIN_ROOT}\\mcp_server_powerbi.py"]
    assert server["env"] == {"ADS_DATA": "${OPCOS_WORKSPACES}\\data", "PYTHONUNBUFFERED": "1"}


# ---------------------------------------------------------------- khai báo nhu cầu
def test_needs_file_declares_one_own_mcp_resource():
    needs = json.loads((REPO / "opcos-runtime.json").read_text(encoding="utf-8"))
    assert needs["schema"] == "opcos-runtime-needs/1" and needs["repoKey"] == "agent-data-studio"
    assert len(needs["needs"]) == 1
    need = needs["needs"][0]
    assert (need["scope"], need["category"], need["key"]) == ("own", "mcp", "powerbi")
    assert need["install"]["requirements"] == ["requirements.txt"]
    assert need["install"]["constraints"] == {"windows": ["locks/powerbi-windows.txt"]}
    lock = [line for line in (REPO / "locks" / "powerbi-windows.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")]
    assert lock and all("==" in line for line in lock)
    assert not any(line.split("==")[0] in {"pip", "setuptools", "wheel"} for line in lock)
    pins = {line.split("==")[0].lower(): line.split("==")[1] for line in lock}
    for line in (REPO / "requirements.txt").read_text(encoding="utf-8").splitlines():
        if "==" in line:
            name, version = line.strip().split("==")
            assert pins.get(name.lower(), version) == version, f"lock mâu thuẫn với requirements: {name}"

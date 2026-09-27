"""Áp bản Git đã duyệt khi dependency không đổi; giữ journal và rollback an toàn.

Được gọi bởi update.ps1 sau preflight. Không xử lý version làm đổi requirements.txt.
"""

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True


class UpdateError(RuntimeError):
    """Lỗi update có thông báo an toàn để đưa cho người dùng."""


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=False, timeout=60,
    )
    if check and result.returncode:
        raise UpdateError(f"Git thất bại ở bước {args[0]} (exit {result.returncode}).")
    return result


def _clean(repo: Path) -> bool:
    return not _git(repo, "status", "--porcelain=v1", "--untracked-files=all").stdout.strip()


def _head(repo: Path) -> str:
    return _git(repo, "rev-parse", "--verify", "HEAD").stdout.strip()


def _candidate_paths_safe(repo: Path, old: str, target: str) -> bool:
    names = [name for name in _git(repo, "ls-tree", "-r", "-z", "--name-only", target).stdout.split("\0") if name]
    changed = [name for name in _git(repo, "diff", "--no-renames", "--name-only", "-z", old, target).stdout.split("\0") if name]
    if any(name.lower() == ".gitignore" or name.lower().endswith("/.gitignore") for name in changed):
        return False
    private_roots = {"workspace", ".venv", "lab", "out", "audit"}
    private_files = {".ads-binding.json", "config.env", "secrets.env", "policy.json", "knowledge.config.json"}
    for name in names:
        parts = name.replace("\\", "/").lower().split("/")
        if (parts[0] in private_roots or name.lower() in private_files
                or parts[0].startswith(".env") and name != ".env.example"
                or parts[:2] == ["docs", "internal"]):
            return False
    result = subprocess.run(
        ["git", "-C", str(repo), "check-ignore", "--no-index", "-z", "--stdin"],
        input="\0".join(names) + "\0", capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=False, timeout=60,
    )
    if result.returncode not in (0, 1):
        raise UpdateError("Không kiểm được ranh giới file riêng của candidate.")
    return result.returncode == 1


def _is_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    if is_junction is not None and is_junction():
        return True
    return bool(getattr(os.lstat(path), "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _station(repo: Path) -> Path:
    sys.path.insert(0, str(repo))
    from powerbi_agent._env import data_dir

    station = Path(data_dir()).resolve()
    if not station.is_dir():
        raise UpdateError("Trạm đã đăng ký chưa tồn tại; chạy installer trước khi update.")
    state = station / "state"
    if state.exists() and (_is_link(state) or not state.is_dir()):
        raise UpdateError("Thư mục state của trạm là link hoặc không phải thư mục.")
    return station


def _journal(station: Path, entry: dict) -> None:
    state = station / "state"
    state.mkdir(exist_ok=True)
    if _is_link(state) or not state.resolve().is_relative_to(station):
        raise UpdateError("Thư mục state trỏ ra ngoài trạm.")
    target = state / "update-journal.jsonl"
    if (target.is_symlink() or target.exists()) and (_is_link(target) or not target.is_file()):
        raise UpdateError("Sổ update là link hoặc không phải file.")
    line = json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n"
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


_PROBE = """
import os, sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root))
from powerbi_agent import app
manager = getattr(app.mcp, '_tool_manager', None)
tools = manager.list_tools() if manager is not None else []
if len(tools) < 16:
    raise SystemExit(3)
print('STARTUP_PASS')
"""


def _smoke(root: Path, python: Path, station_path: Path | None = None) -> None:
    with tempfile.TemporaryDirectory(prefix="ads-update-station-") as station:
        env = {name: os.environ[name] for name in (
            "SystemRoot", "WINDIR", "PATH", "TEMP", "TMP",
        ) if name in os.environ}
        env.update({
            "ADS_DATA": str(station_path or station),
            "USERPROFILE": station,
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
        })
        try:
            result = subprocess.run(
                [str(python), "-I", "-B", "-c", _PROBE, str(root)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=40, env=env, check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise UpdateError("Candidate startup quá thời gian 40 giây.") from exc
        if result.returncode != 0 or result.stdout.strip() != "STARTUP_PASS":
            raise UpdateError("Candidate không khởi động đủ 16 MCP tool trong trạm cô lập.")


def _rollback(repo: Path, old: str, target: str) -> bool:
    current = _head(repo)
    if current == old:
        return _clean(repo)
    if current != target or not _clean(repo):
        return False
    result = _git(repo, "reset", "--keep", old, check=False)
    return result.returncode == 0 and _head(repo) == old and _clean(repo)


def _try_rollback(repo: Path, old: str, target: str, applied: bool) -> bool:
    try:
        return _rollback(repo, old, target) if applied or _head(repo) != old else _clean(repo)
    except Exception:
        return False


def _runtime_busy(repo: Path) -> bool:
    """Kiểm lại process ngay trước khi đổi source; lỗi truy vấn thì dừng."""
    shell = shutil.which("powershell") or shutil.which("pwsh")
    if os.name != "nt" or shell is None:
        raise UpdateError("Không kiểm được phiên Python đang dùng source trên Windows.")
    script = r'''
$ErrorActionPreference = 'Stop'
$sourceRoot = $env:ADS_UPDATE_ROOT.TrimEnd('\', '/')
$ownedRuntime = Join-Path $sourceRoot '.venv'
$ownerProcess = [int]$env:ADS_UPDATE_PID
# CIM trả CommandLine/ExecutablePath đúng dạng lúc khởi chạy, kể cả tên ngắn 8.3 (DUCNGU~1) và dạng
# trộn ngắn-dài từng đoạn -> so với mọi dạng của đường. Ổ tắt 8.3 thì ShortName = tên dài (1 dạng).
function Get-PathForms([string] $path) {
    $fso = New-Object -ComObject Scripting.FileSystemObject
    $parts = $path.TrimEnd('\').Split('\')
    $forms = @($parts[0])
    $prefix = $parts[0]
    for ($i = 1; $i -lt $parts.Count; $i++) {
        $part = $parts[$i]
        $prefix = $prefix + '\' + $part
        $short = if (Test-Path -LiteralPath $prefix -PathType Container) { $fso.GetFolder($prefix).ShortName } else { '' }
        $forms = @(foreach ($form in $forms) {
            $form + '\' + $part
            if ($short -and $short -ne $part) { $form + '\' + $short }
        })
        if ($forms.Count -gt 1024) { throw 'PATH_FORMS_OVERFLOW' }
    }
    return $forms
}
# Gốc phải dừng ở biên đoạn (\ hoặc / sau gốc, nháy, khoảng trắng, hết chuỗi): clone anh em có tiền
# tố giống (checkout2, checkout-old) không phải source này; gốc làm cwd/đối số cuối vẫn tính.
function Test-Contains([string] $text, [string[]] $forms) {
    foreach ($form in $forms) {
        if ([regex]::IsMatch($text, [regex]::Escape($form) + '(?=[\\/"\s]|$)', 'IgnoreCase, CultureInvariant')) { return $true }
    }
    return $false
}
function Test-Under([string] $path, [string[]] $forms) {
    foreach ($form in $forms) { if ($path.StartsWith($form + '\',[StringComparison]::OrdinalIgnoreCase)) { return $true } }
    return $false
}
$sourceForms = Get-PathForms $sourceRoot
$runtimeForms = Get-PathForms $ownedRuntime
$pythons = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'")
# Launcher .venv\Scripts\python.exe trên Windows sinh Python con với đúng đối số của nó: loại
# chuỗi cha Python chạy cùng đối số với updater, không loại tiến trình Python nào khác.
function Get-ArgumentTail([string] $commandLine) {
    if (-not $commandLine) { return '' }
    $text = $commandLine.TrimStart()
    if ($text.StartsWith('"')) { $end = $text.IndexOf('"', 1) } else { $end = $text.IndexOf(' ') }
    if ($end -lt 0) { return '' }
    return $text.Substring($end + 1).Trim()
}
$excluded = @($ownerProcess)
$self = $pythons | Where-Object { $_.ProcessId -eq $ownerProcess } | Select-Object -First 1
$ownArguments = if ($self) { Get-ArgumentTail $self.CommandLine } else { '' }
$current = $self
while ($ownArguments -and $current -and $excluded.Count -lt 8) {
    $parentId = $current.ParentProcessId
    $current = $pythons | Where-Object {
        $_.ProcessId -eq $parentId -and $_.ProcessId -notin $excluded -and
        (Get-ArgumentTail $_.CommandLine) -ceq $ownArguments
    } | Select-Object -First 1
    if ($current) { $excluded += $current.ProcessId }
}
$running = @($pythons |
    Where-Object {
        $_.ProcessId -notin $excluded -and (
            ($_.CommandLine -and (Test-Contains $_.CommandLine $sourceForms)) -or
            ($_.ExecutablePath -and (Test-Under $_.ExecutablePath $runtimeForms))
        )
    })
[Console]::Write($running.Count)
'''
    # Env đầy đủ trừ PSModulePath: env rút gọn (thiếu hồ sơ người dùng, LOCALAPPDATA...) làm Windows
    # PowerShell 5.1 quá hạn trên runner CI; PSModulePath thừa hưởng từ pwsh 7 làm 5.1 nạp nhầm module
    # bản Core -> bỏ khoá để 5.1 tự dựng đường mặc định. CIM lần đầu có thể chậm: hạn 45s, lỗi vẫn dừng.
    env = {name: value for name, value in os.environ.items() if name.upper() != "PSMODULEPATH"}
    env["ADS_UPDATE_ROOT"] = str(repo)
    env["ADS_UPDATE_PID"] = str(os.getpid())
    try:
        result = subprocess.run(
            [shell, "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env, check=False, timeout=45,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise UpdateError("Không kiểm được phiên Python đang dùng source.") from exc
    if result.returncode and "PATH_FORMS_OVERFLOW" in result.stderr:
        raise UpdateError("PATH_FORMS_OVERFLOW: quá nhiều dạng đường 8.3; không kiểm được phiên Python đang dùng source.")
    if result.returncode or not result.stdout.strip().isdecimal():
        raise UpdateError("Không kiểm được phiên Python đang dùng source.")
    return int(result.stdout.strip()) > 0


def _remove_owned_candidate(path: Path, repo: Path, station: Path) -> bool:
    """Dọn đúng candidate tạm do lượt này tạo, không đi qua link/junction."""
    try:
        resolved = path.resolve()
        temp_root = Path(tempfile.gettempdir()).resolve()
        if (not path.name.startswith("ads-update-candidate-")
                or not resolved.is_relative_to(temp_root)
                or resolved == temp_root
                or resolved.is_relative_to(repo)
                or resolved.is_relative_to(station)
                or _is_link(path)):
            return False
        shutil.rmtree(path)
        return not path.exists()
    except (OSError, ValueError):
        return False


def apply(repo: Path, old: str, target: str, python: Path) -> int:
    repo = repo.resolve()
    python = python.resolve()
    if _head(repo) != old or not _clean(repo):
        raise UpdateError("Checkout đã đổi sau preflight; không áp update.")
    if _git(repo, "merge-base", "--is-ancestor", old, target, check=False).returncode:
        raise UpdateError("Target không còn là fast-forward của checkout.")
    if not _candidate_paths_safe(repo, old, target):
        raise UpdateError("Candidate chứa đường dẫn dữ liệu riêng hoặc file bị ignore; không áp update.")
    station = _station(repo)
    operation = uuid.uuid4().hex
    base = {"operation": operation, "repo": str(repo), "old": old, "target": target}
    _journal(station, {**base, "event": "start", "at": datetime.now(timezone.utc).isoformat()})
    worktree = None
    applied = False
    cleanup_pending = False
    try:
        worktree = Path(tempfile.mkdtemp(prefix="ads-update-candidate-"))
        _git(repo, "worktree", "add", "--detach", str(worktree), target)
        _smoke(worktree, python)
        if _head(repo) != old or not _clean(repo):
            raise UpdateError("Checkout đổi trong lúc kiểm candidate.")
        if _runtime_busy(repo):
            raise UpdateError("Một phiên Python còn dùng source; đóng host rồi thử lại.")
        result = _git(repo, "merge", "--ff-only", target, check=False)
        if result.returncode or _head(repo) != target:
            raise UpdateError("Git không áp được fast-forward; đang kiểm rollback.")
        applied = True
        _smoke(repo, python, station if (repo / ".ads-binding.json").exists() else None)
        _journal(station, {**base, "event": "end", "status": "pending_host_restart",
                           "at": datetime.now(timezone.utc).isoformat()})
        print("[PASS] SOURCE_APPLIED candidate and checkout startup passed.")
        print("[NOT_CHECKED] Host restart and Power BI Desktop live connection.")
        return 0
    except Exception as exc:
        restored = _try_rollback(repo, old, target, applied)
        try:
            _journal(station, {**base, "event": "aborted" if restored else "partial",
                               "reason": type(exc).__name__, "at": datetime.now(timezone.utc).isoformat()})
        except Exception:
            print("[WARN] JOURNAL_WRITE_FAILED: inspect checkout and station state.")
        if restored:
            print(f"[FAIL] Update not applied; checkout is at {old} ({type(exc).__name__}).")
        else:
            print("[FAIL] PARTIAL_UPDATE: rollback unverified; inspect checkout and journal.")
        return 1
    finally:
        if worktree is not None:
            try:
                result = _git(repo, "worktree", "remove", "--force", str(worktree), check=False)
                cleanup_pending = result.returncode != 0
            except Exception:
                cleanup_pending = True
        if worktree is not None and worktree.exists():
            try:
                if any(worktree.iterdir()):
                    cleanup_pending = not _remove_owned_candidate(worktree, repo, station) or cleanup_pending
                else:
                    worktree.rmdir()
            except OSError:
                cleanup_pending = True
        if cleanup_pending:
            print("[WARN] Candidate worktree cleanup pending; inspect git worktree list.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--old", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--runtime-python", type=Path, required=True)
    args = parser.parse_args()
    try:
        return apply(args.repo, args.old, args.target, args.runtime_python)
    except (UpdateError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"[FAIL] Update preflight stopped: {type(exc).__name__}.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

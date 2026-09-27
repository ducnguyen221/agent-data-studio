# Removes only MCP registrations pointing at this checkout.
[CmdletBinding()]
param(
    [ValidateSet('claude', 'codex', 'antigravity')]
    [string[]] $Hosts = @('codex'),
    [switch] $RemoveVenv
)
$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$serverPath = Join-Path $repoRoot 'mcp_server_powerbi.py'
$python = if ($env:POWERBI_INSTALL_PYTHON) { $env:POWERBI_INSTALL_PYTHON } else { Join-Path $repoRoot '.venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) { $python = $pythonCmd.Source }
}
$helper = @'
import json
import os
import re
import shutil
import sys
import tempfile
import tomllib
import uuid
from pathlib import Path

kind, filename, server = sys.argv[1:4]
path = Path(filename)
if kind == "scan":
    profile = path
    for relative, format_name in (
        (".claude.json", "json"),
        (".codex/config.toml", "toml"),
        (".gemini/antigravity/mcp_config.json", "json"),
    ):
        config = profile / relative
        if not config.exists():
            continue
        try:
            raw_config = config.read_text(encoding="utf-8-sig")
            data = (json.loads(raw_config) if format_name == "json" else tomllib.loads(raw_config)) if raw_config.strip() else {}
            entries = data.get("mcpServers" if format_name == "json" else "mcp_servers", {})
            entry = entries.get("powerbi-mcp-bridge") if isinstance(entries, dict) else None
            if isinstance(entry, dict) and (
                any(isinstance(a, str) and os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(server))
                    for a in entry.get("args", []))
                or (isinstance(entry.get("command"), str)
                    and os.path.normcase(os.path.realpath(entry["command"])) == os.path.normcase(os.path.realpath(sys.argv[4])))
            ):
                print("BUSY")
                sys.exit(0)
        except Exception:
            print("INVALID")
            sys.exit(0)
    print("CLEAR")
    sys.exit(0)
if not path.exists():
    print("ABSENT")
    sys.exit(0)

def same_path(candidate):
    return isinstance(candidate, str) and os.path.normcase(os.path.realpath(candidate)) == os.path.normcase(os.path.realpath(server))

def owned(entry):
    return isinstance(entry, dict) and isinstance(entry.get("args"), list) and any(same_path(a) for a in entry["args"])

def save(content):
    backup = path.with_name(path.name + ".bak-agent-data-studio-" + uuid.uuid4().hex)
    shutil.copy2(path, backup)
    fd, temp = tempfile.mkstemp(prefix=path.name + ".ads-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

raw = path.read_text(encoding="utf-8-sig")
if not raw.strip():
    print("ABSENT")
    sys.exit(0)
name = "powerbi-mcp-bridge"
if kind == "json":
    data = json.loads(raw)
    entries = data.get("mcpServers") if isinstance(data, dict) else None
    entry = entries.get(name) if isinstance(entries, dict) else None
    if entry is None:
        print("ABSENT")
    elif not owned(entry):
        print("FOREIGN")
    else:
        del entries[name]
        result = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        json.loads(result)
        save(result)
        print("REMOVED")
elif kind == "toml":
    data = tomllib.loads(raw)
    entries = data.get("mcp_servers") if isinstance(data, dict) else None
    entry = entries.get(name) if isinstance(entries, dict) else None
    if entry is None:
        print("ABSENT")
    elif not owned(entry):
        print("FOREIGN")
    else:
        heading = re.compile(r"(?m)^\[([^\]\r\n]+)\][^\S\r\n]*(?:\r?\n|$)")
        matches = list(heading.finditer(raw))
        spans = []
        for i, match in enumerate(matches):
            table = match.group(1)
            if table == "mcp_servers." + name or table.startswith("mcp_servers." + name + "."):
                end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
                spans.append((match.start(), end))
        if not spans:
            raise ValueError("Owned entry exists but table boundaries could not be found")
        result = raw
        for start, end in reversed(spans):
            result = result[:start] + result[end:]
        parsed = tomllib.loads(result)
        if parsed.get("mcp_servers", {}).get(name) is not None:
            raise ValueError("Owned entry remained after removal")
        save(result)
        print("REMOVED")
else:
    raise ValueError("Unsupported configuration format")
'@
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    Write-Error 'Python 3.11+ is required to inspect MCP configuration safely.'
    exit 1
}
$tempHelper = Join-Path ([System.IO.Path]::GetTempPath()) ('ads-uninstall-' + [guid]::NewGuid().ToString('N') + '.py')
[System.IO.File]::WriteAllText($tempHelper, $helper, (New-Object System.Text.UTF8Encoding($false)))
$failed = $false
try {
    foreach ($hostName in $Hosts) {
        $config = switch ($hostName) {
            'claude' { Join-Path $env:USERPROFILE '.claude.json' }
            'codex' { Join-Path $env:USERPROFILE '.codex\config.toml' }
            'antigravity' { Join-Path $env:USERPROFILE '.gemini\antigravity\mcp_config.json' }
        }
        $kind = if ($hostName -eq 'codex') { 'toml' } else { 'json' }
        $oldPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            $result = & $python $tempHelper $kind $config $serverPath 2>&1
            $exitCode = $LASTEXITCODE
        } finally { $ErrorActionPreference = $oldPreference }
        $status = (@($result) | ForEach-Object { "$_" }) -join "`n"
        if ($exitCode -ne 0) {
            Write-Warning "$hostName`: configuration could not be inspected; no changes were made."
            $failed = $true
        } elseif ($status -match '(?m)^REMOVED\s*$') {
            Write-Host "$hostName`: removed repository-owned MCP entry."
        } elseif ($status -match '(?m)^FOREIGN\s*$') {
            Write-Host "$hostName`: same-name MCP entry belongs to another checkout; retained."
        } elseif ($status -match '(?m)^ABSENT\s*$') {
            Write-Host "$hostName`: no repository-owned MCP entry."
        } else {
            Write-Warning "$hostName`: helper returned an unknown status."
            $failed = $true
        }
    }
} catch {
    Remove-Item -LiteralPath $tempHelper -Force -ErrorAction SilentlyContinue
    throw
}
try {
if ($RemoveVenv -and $failed) {
    Write-Warning 'Skipping .venv removal because MCP configuration could not be fully inspected.'
}
if ($RemoveVenv -and -not $failed) {
    $venv = Join-Path $repoRoot '.venv'
    $resolvedRepo = [System.IO.Path]::GetFullPath($repoRoot).TrimEnd('\', '/')
    $resolvedVenv = [System.IO.Path]::GetFullPath($venv).TrimEnd('\', '/')
    if (-not $resolvedVenv.StartsWith($resolvedRepo + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase) -or
        [System.IO.Path]::GetFileName($resolvedVenv) -ne '.venv') {
        Write-Warning 'Refusing to remove virtual environment outside this checkout.'
        $failed = $true
    } elseif (Test-Path -LiteralPath $venv) {
        $item = Get-Item -LiteralPath $venv -Force
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            Write-Warning 'Refusing to remove a linked virtual environment.'
            $failed = $true
        } else {
            $marker = Join-Path $venv '.ads-venv-owned'
            $expected = [IO.Path]::GetFullPath($repoRoot).TrimEnd('\', '/')
            if (-not (Test-Path -LiteralPath $marker -PathType Leaf) -or
                (Get-Content -LiteralPath $marker -Raw -Encoding UTF8).Trim() -ne $expected) {
                Write-Warning 'Refusing .venv removal without an ownership marker for this checkout.'
                $failed = $true
            } elseif (-not (Test-Path -LiteralPath (Join-Path $venv 'pyvenv.cfg') -PathType Leaf)) {
                Write-Warning 'Refusing .venv removal without pyvenv.cfg.'
                $failed = $true
            } else {
                $prev = $ErrorActionPreference
                $ErrorActionPreference = 'Continue'
                try {
                    $scan = & $python $tempHelper scan $env:USERPROFILE $serverPath (Join-Path $venv 'Scripts\python.exe') 2>&1
                    $scanExit = $LASTEXITCODE
                } finally { $ErrorActionPreference = $prev }
                if ($scanExit -ne 0 -or (@($scan) -join [Environment]::NewLine) -notmatch '(?m)^CLEAR\s*$') {
                    Write-Warning 'Refusing .venv removal: another host still uses it or host config cannot be inspected.'
                    $failed = $true
                } else {
                    try {
                        $active = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" -ErrorAction Stop |
                            Where-Object { $_.CommandLine -and $_.CommandLine.IndexOf($resolvedVenv, [StringComparison]::OrdinalIgnoreCase) -ge 0 })
                        if ($active.Count -gt 0) { throw 'busy' }
                        Remove-Item -LiteralPath $venv -Recurse -Force
                        Write-Host 'Removed checkout .venv by explicit request.'
                    } catch {
                        Write-Warning 'Refusing .venv removal because it is busy or process state could not be verified.'
                        $failed = $true
                    }
                }
            }
        }
    }
}
} finally {
    Remove-Item -LiteralPath $tempHelper -Force -ErrorAction SilentlyContinue
}
if ($failed) { exit 1 }
Write-Host 'Uninstall complete. Restart selected hosts to refresh MCP connections.'

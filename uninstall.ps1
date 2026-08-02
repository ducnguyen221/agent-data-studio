<#
.SYNOPSIS
  Gỡ Power BI MCP Bridge khỏi các host. (Chạy ngay trong thư mục cài.)
.EXAMPLE
  .\uninstall.ps1                # gỡ khỏi 3 host + xoá skill/lệnh đã copy. GIỮ file & .venv & .env.
  .\uninstall.ps1 -RemoveVenv    # gỡ như trên + xoá .venv (giải phóng dung lượng).
#>
[CmdletBinding()]
param(
    [string[]] $Hosts = @("claude", "codex", "antigravity"),
    [switch]   $RemoveVenv
)
$ErrorActionPreference = "Stop"
$Root  = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$venvPy = Join-Path $Root ".venv\Scripts\python.exe"
# Override cho CI/test (không có venv): dùng python chỉ định để merge/validate config
if (-not (Test-Path $venvPy) -and $env:POWERBI_INSTALL_PYTHON) { $venvPy = $env:POWERBI_INSTALL_PYTHON }
function Info($m){Write-Host "[i] $m" -ForegroundColor Cyan}
function Ok($m){Write-Host "[OK] $m" -ForegroundColor Green}
function Warn($m){Write-Host "[!] $m" -ForegroundColor Yellow}
function Backup-File($p){ if(Test-Path $p){ Copy-Item $p "$p.bak.$Stamp" -Force; Info "Backup: $p.bak.$Stamp" } }
function Write-Utf8NoBom($Path,$Text){ [System.IO.File]::WriteAllText($Path,$Text,(New-Object System.Text.UTF8Encoding($false)))}
$name = "powerbi-mcp-bridge"

function Remove-FromJson($Path){
    # BẪY ĐÃ TÁI HIỆN: KHÔNG round-trip JSON host bằng PS 5.1 (key rỗng trong ~/.claude.json
    # làm ConvertFrom-Json crash; ConvertTo-Json cắt cụt tầng sâu). Gỡ bằng Python + atomic + validate.
    if (-not (Test-Path $Path)) { return }
    if (-not (Test-Path $venvPy)) { Warn "Không có venv để sửa JSON an toàn -> bỏ qua $Path (gỡ tay entry '$name')."; return }
    Backup-File $Path
    $py = @'
import json, os, sys
path, name = sys.argv[1], sys.argv[2]
data = json.load(open(path, encoding="utf-8-sig"))
if isinstance(data, dict) and isinstance(data.get("mcpServers"), dict) and name in data["mcpServers"]:
    del data["mcpServers"][name]
    out = json.dumps(data, ensure_ascii=False, indent=2)
    json.loads(out)
    tmp = path + ".powerbi-tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(out + "\n")
    json.load(open(tmp, encoding="utf-8"))
    os.replace(tmp, path)
    json.load(open(path, encoding="utf-8"))
    print("REMOVED")
else:
    print("ABSENT")
'@
    $tmpPy = Join-Path $env:TEMP "powerbi-remove-mcp.py"
    Write-Utf8NoBom $tmpPy $py
    $out = & $venvPy $tmpPy $Path $name 2>&1
    Remove-Item $tmpPy -Force -ErrorAction SilentlyContinue
    if ("$out" -match "REMOVED") { Ok "Đã gỡ '$name' khỏi $Path (validate OK)" }
    elseif ("$out" -match "ABSENT") { Info "$Path không chứa '$name'." }
    else { Warn "Không gỡ được khỏi $Path ($out) — file gốc còn nguyên (.bak.$Stamp)." }
}

if ($Hosts -contains "claude") {
    if (Get-Command claude -ErrorAction SilentlyContinue) {
        # LƯU Ý PS 5.1: không redirect stderr của native command phía PowerShell khi
        # $ErrorActionPreference=Stop (NativeCommandError terminating) — gộp trong cmd /c.
        & cmd /c "claude mcp remove $name -s user 2>&1" | Out-Null
        Ok "Claude: remove qua CLI."
    }
    else { Remove-FromJson (Join-Path $env:USERPROFILE ".claude.json") }
}
if ($Hosts -contains "antigravity") { Remove-FromJson (Join-Path $env:USERPROFILE ".gemini\antigravity\mcp_config.json") }
if ($Hosts -contains "codex") {
    $cfg = Join-Path $env:USERPROFILE ".codex\config.toml"
    if (Test-Path $cfg) {
        Backup-File $cfg
        $text = Get-Content $cfg -Raw -Encoding UTF8
        if ($null -eq $text) { $text = '' }
        # Phải khớp CẢ sub-table ([mcp_servers.powerbi-mcp-bridge.env]): nếu chỉ xóa block cha,
        # sub-table còn lại vẫn ngầm tạo server không có `command` -> Codex lỗi config.
        # Lookahead `^\[` (ngoặc ĐẦU DÒNG), KHÔNG dùng [^\[]*: dòng `args = ["-u", ...]`
        # có `[` giữa dòng, sẽ cắt cụt block và làm hỏng file.
        $new = [regex]::Replace($text, '(?ms)^\[mcp_servers\.powerbi-mcp-bridge(?:\.[^\]\r\n]+)?\].*?(?=^\[|\z)', '')
        Write-Utf8NoBom $cfg ($new.TrimEnd() + "`n")
        # validate parse sau khi ghi (tiêu chí audit: MỌI nhánh ghi config đều validate)
        if (Test-Path $venvPy) {
            & $venvPy -c "import tomllib,sys; tomllib.load(open(sys.argv[1],'rb'))" $cfg 2>$null
            if ($LASTEXITCODE -ne 0) { Warn "config.toml KHÔNG parse được sau khi gỡ — khôi phục từ .bak.$Stamp!" }
            else { Ok "Đã gỡ block khỏi $cfg (validate OK)" }
        } else { Ok "Đã gỡ block khỏi $cfg" }
    }
}

# Gỡ MỌI skill + lệnh mà installer đã copy (đối xứng với Install-Skill — lấy danh sách từ nguồn)
$skillBase = Join-Path $Root "plugins\powerbi-agent\skills"
if (-not (Test-Path $skillBase)) { $skillBase = Join-Path $Root "skill" }
$skillNames = @()
if (Test-Path $skillBase) { $skillNames = (Get-ChildItem $skillBase -Directory).Name }
$hostSkillRoots = @()
if ($Hosts -contains "claude")      { $hostSkillRoots += (Join-Path $env:USERPROFILE ".claude\skills") }
if ($Hosts -contains "codex")       { $hostSkillRoots += (Join-Path $env:USERPROFILE ".codex\skills") }
if ($Hosts -contains "antigravity") { $hostSkillRoots += (Join-Path $env:USERPROFILE ".gemini\antigravity\skills") }
# KHÔNG đặt tên biến lặp là $root: PowerShell không phân biệt hoa/thường nên nó GHI ĐÈ $Root
# (thư mục repo) và mọi Join-Path $Root phía dưới sẽ trỏ vào ...\.gemini\antigravity\skills\...
foreach ($skRoot in $hostSkillRoots) {
    foreach ($n in $skillNames) {
        $p = Join-Path $skRoot $n
        if (Test-Path $p) { Remove-Item $p -Recurse -Force; Info "Xoá skill: $p" }
    }
}
# Gỡ ĐỐI XỨNG với bước 4 của installer. Installer ghi vào 3 nơi (Claude commands+agents,
# Codex prompts, và trong skill Antigravity); gỡ mà chỉ dọn Claude thì Codex giữ nguyên 8 lệnh
# sống nhăn sau khi user tưởng đã gỡ sạch. (Antigravity tự sạch vì lệnh nằm trong skill folder
# đã bị xoá đệ quy ở trên.)
function Remove-InstalledFrom([string]$Dir, [string]$SrcDir, [string[]]$Legacy, [string]$What) {
    if (-not (Test-Path $Dir)) { return }
    $own = if (Test-Path $SrcDir) { @(Get-ChildItem $SrcDir -Filter "*.md" | ForEach-Object { $_.Name }) } else { @() }
    $ledger = Join-Path $Dir ".powerbi-agent-installed.txt"
    $prev = if (Test-Path $ledger) { @(Get-Content $ledger | Where-Object { $_ -match '\S' }) } else { @() }
    foreach ($nm in ($prev + $own + $Legacy | Sort-Object -Unique)) {
        # Cùng lý do như installer: sổ ghi là file user ghi được, coi nội dung là KHÔNG tin cậy.
        if ([string]::IsNullOrWhiteSpace($nm)) { continue }
        if ($nm -ne [System.IO.Path]::GetFileName($nm) -or $nm -match '[\*\?\[\]]') {
            Warn "Bỏ qua mục sổ ghi không hợp lệ: $nm"; continue
        }
        try {
            $p = Join-Path $Dir $nm
            if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force; Info "Xoá ${What}: $nm" }
        } catch { Warn "Bỏ qua mục sổ ghi không xử lý được: $nm" }
    }
    if (Test-Path $ledger) { Remove-Item $ledger -Force }
}

# Lấy lại gốc repo từ $PSScriptRoot chứ KHÔNG dùng $Root: các vòng lặp phía trên có thể đã ghi đè
# $Root (PowerShell không phân biệt hoa/thường với tên biến), và lỗi đó im lặng — $own rỗng thì
# hàm gỡ vẫn chạy, chỉ là không xoá gì.
$RepoDir     = $PSScriptRoot
$cmdSrcDir   = Join-Path $RepoDir "plugins\powerbi-agent\commands"
$agentSrcDir = Join-Path $RepoDir "plugins\powerbi-agent\agents"
if (-not (Test-Path $agentSrcDir)) { Warn "Không thấy $agentSrcDir — bỏ qua gỡ agent." }
$legacyCmds = @("pbi-setup.md","pbi-new.md","pbi-scan.md","pbi-done.md","pbi-pack.md","pbi-recall.md")

if ($Hosts -contains "codex") {
    Remove-InstalledFrom (Join-Path $env:USERPROFILE ".codex\prompts") $cmdSrcDir $legacyCmds "lệnh"
}
if ($Hosts -contains "claude") {
    # Gỡ agent bằng danh sách tên tường minh — chỉ có đúng 1 agent, và cách này không phụ thuộc
    # vào việc suy tên từ thư mục repo (đã có lần hỏng im lặng vì biến gốc repo bị ghi đè).
    $agentDst = Join-Path $env:USERPROFILE ".claude\agents"
    if (Test-Path $agentDst) {
        foreach ($nm in @("powerbi-knowledge-curator.md", "pbi-knowledge-curator.md")) {
            $p = Join-Path $agentDst $nm
            if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force; Info "Xoá agent: $nm" }
        }
        $agLedger = Join-Path $agentDst ".powerbi-agent-installed.txt"
        if (Test-Path $agLedger) { Remove-Item $agLedger -Force }
    }
    $cmdDst = Join-Path $env:USERPROFILE ".claude\commands"
    if (Test-Path $cmdDst) {
        Remove-InstalledFrom $cmdDst $cmdSrcDir $legacyCmds "lệnh"
    }
}
if ($RemoveVenv) {
    $venv = Join-Path $Root ".venv"
    if (Test-Path $venv) { Remove-Item $venv -Recurse -Force; Ok "Đã xoá .venv" }
}
Ok "Gỡ cài hoàn tất. Khởi động lại host để áp dụng. (Thư mục mã nguồn giữ nguyên.)"

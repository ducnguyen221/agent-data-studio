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
foreach ($root in $hostSkillRoots) {
    foreach ($n in $skillNames) {
        $p = Join-Path $root $n
        if (Test-Path $p) { Remove-Item $p -Recurse -Force; Info "Xoá skill: $p" }
    }
}
if ($Hosts -contains "claude") {
    $cmdDst = Join-Path $env:USERPROFILE ".claude\commands"
    if (Test-Path $cmdDst) {
        # Gỡ đối xứng với installer: chỉ những file THUỘC repo (suy từ manifest) + họ tên cũ
        # trước v0.5.0. KHÔNG wildcard "powerbi-*.md" — sẽ xoá luôn lệnh riêng của user.
        $cmdSrc = Join-Path $Root "plugins\powerbi-agent\commands"
        $own = if (Test-Path $cmdSrc) { @(Get-ChildItem $cmdSrc -Filter "*.md" | ForEach-Object { $_.Name }) } else { @() }
        $legacy = @("pbi-setup.md","pbi-new.md","pbi-scan.md","pbi-done.md","pbi-pack.md","pbi-recall.md")
        $ledger = Join-Path $cmdDst ".powerbi-agent-installed.txt"
        $prev = if (Test-Path $ledger) { @(Get-Content $ledger | Where-Object { $_ -match '\S' }) } else { @() }
        foreach ($nm in ($prev + $own + $legacy | Sort-Object -Unique)) {
            $p = Join-Path $cmdDst $nm
            if (Test-Path $p) { Remove-Item $p -Force; Info "Xoá lệnh: $nm" }
        }
        if (Test-Path $ledger) { Remove-Item $ledger -Force }
    }
}
if ($RemoveVenv) {
    $venv = Join-Path $Root ".venv"
    if (Test-Path $venv) { Remove-Item $venv -Recurse -Force; Ok "Đã xoá .venv" }
}
Ok "Gỡ cài hoàn tất. Khởi động lại host để áp dụng. (Thư mục mã nguồn giữ nguyên.)"

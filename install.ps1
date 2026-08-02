<#
.SYNOPSIS
  Bộ cài "một phát chạy ngay" cho Power BI MCP Bridge — IN-PLACE.
  Thư mục này VỪA là bản đang chạy, VỪA là bộ cài mang sang máy khác.

.DESCRIPTION
  Cài đặt NGAY TẠI thư mục chứa file này (không sao chép đi đâu khác):
    - Tạo / kiểm tra venv Python + cài dependencies.
    - Dò ADOMD.NET (đa phiên bản).
    - Đăng ký MCP vào Claude Code / Codex / Antigravity, trỏ về CHÍNH thư mục này
      (merge vào cấu hình có sẵn, có backup .bak, không xoá server khác).
    - Copy skill cho từng host.
  KHÔNG bao giờ đụng .env (secrets). Chạy lại nhiều lần an toàn (idempotent).

.EXAMPLE
  # Cách dùng chuẩn — mở PowerShell tại thư mục này rồi chạy:
  powershell -ExecutionPolicy Bypass -File .\install.ps1

.EXAMPLE
  # Mang sang máy mới: copy CẢ thư mục (bỏ .venv và .env) tới
  # %USERPROFILE%\.mcp\powerbi-mcp rồi chạy lại lệnh trên. venv tự dựng lại.

.PARAMETER Hosts
  Host cần đăng ký: claude, codex, antigravity. Mặc định cả ba.
.PARAMETER SkipVenv
  Bỏ qua tạo venv / cài pip (chỉ cập nhật cấu hình host).
.PARAMETER SkipHosts
  Chỉ dựng venv, không đụng cấu hình host nào.
#>
[CmdletBinding()]
param(
    [string[]] $Hosts = @("claude", "codex", "antigravity"),
    [switch]   $SkipVenv,
    [switch]   $SkipHosts
)

$ErrorActionPreference = "Stop"
$Root  = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"

function Info($m)  { Write-Host "[i] $m" -ForegroundColor Cyan }
function Ok($m)    { Write-Host "[OK] $m" -ForegroundColor Green }
function Warn($m)  { Write-Host "[!] $m" -ForegroundColor Yellow }
function Err($m)   { Write-Host "[X] $m" -ForegroundColor Red }
function Step($m)  { Write-Host "`n=== $m ===" -ForegroundColor Magenta }

# Ghi file UTF-8 KHÔNG BOM (an toàn cho JSON/TOML)
function Write-Utf8NoBom([string]$Path, [string]$Text) {
    [System.IO.File]::WriteAllText($Path, $Text, (New-Object System.Text.UTF8Encoding($false)))
}
function Backup-File([string]$Path) {
    if (Test-Path $Path) { Copy-Item $Path "$Path.bak.$Stamp" -Force; Info "Đã sao lưu: $Path.bak.$Stamp" }
}

Write-Host @"

  ____                        ____ ___   __  __  ____ ____
 |  _ \ _____      _____ _ __| __ )_ _| |  \/  |/ ___|  _ \
 | |_) / _ \ \ /\ / / _ \ '__|  _ \| |  | |\/| | |   | |_) |
 |  __/ (_) \ V  V /  __/ |  | |_) | |  | |  | | |___|  __/
 |_|   \___/ \_/\_/ \___|_|  |____/___| |_|  |_|\____|_|

  Power BI MCP Bridge - Installer (in-place)
"@ -ForegroundColor Blue

Info "Thư mục cài (= vị trí MCP server): $Root"
Info "Host đăng ký: $($Hosts -join ', ')"

$serverPath = Join-Path $Root "mcp_server_powerbi.py"
if (-not (Test-Path $serverPath)) { Err "Không thấy mcp_server_powerbi.py cạnh install.ps1. Dừng."; exit 1 }

# ---- .env: tạo từ mẫu nếu chưa có, KHÔNG ghi đè (giữ secrets) ----
$envFile = Join-Path $Root ".env"
$envEx   = Join-Path $Root ".env.example"
if ((-not (Test-Path $envFile)) -and (Test-Path $envEx)) {
    Copy-Item $envEx $envFile -Force
    Warn ".env chưa có -> tạo từ mẫu. Điền vào nếu cần Power BI Service (Cloud): $envFile"
}

# ============================================================
# 1) PYTHON VENV + DEPENDENCIES
# ============================================================
$venvPy = Join-Path $Root ".venv\Scripts\python.exe"
# Override cho CI/test (không có venv): dùng python chỉ định để merge/validate config
if (-not (Test-Path $venvPy) -and $env:POWERBI_INSTALL_PYTHON) { $venvPy = $env:POWERBI_INSTALL_PYTHON }

if ($SkipVenv) {
    Warn "Bỏ qua venv/pip (-SkipVenv)."
} else {
    Step "1/3 Python venv + dependencies"

    function Get-Python {
        foreach ($c in @(@("py",@("-3.12")),@("py",@("-3.11")),@("py",@("-3")),@("python",@()),@("python3",@()))) {
            $exe=$c[0]; $pre=$c[1]
            if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
            try {
                $ver = & $exe @pre -c "import sys;print('%d.%d'%sys.version_info[:2])" 2>$null
                if ($ver -match '^(\d+)\.(\d+)$' -and [int]$Matches[1] -eq 3 -and [int]$Matches[2] -ge 11) {
                    return ,@($exe,$pre,$ver)
                }
            } catch {}
        }
        return $null
    }

    # venv có sẵn nhưng HỎNG (copy từ máy khác) -> dựng lại
    $needBuild = $true
    if (Test-Path $venvPy) {
        & $venvPy --version *> $null
        if ($LASTEXITCODE -eq 0) { $needBuild = $false; Info "venv hợp lệ -> tái sử dụng." }
        else { Warn "venv không chạy được (có thể copy từ máy khác) -> dựng lại."; Remove-Item (Join-Path $Root ".venv") -Recurse -Force }
    }

    if ($needBuild) {
        $py = Get-Python
        if (-not $py) { Err "Không thấy Python >= 3.11. Cài từ https://www.python.org/downloads/ (tick 'Add to PATH') rồi chạy lại."; exit 1 }
        Ok "Dùng Python $($py[2])"
        & $py[0] @($py[1]) -m venv (Join-Path $Root ".venv")
        if ($LASTEXITCODE -ne 0) { Err "Tạo venv thất bại."; exit 1 }
    }

    Info "Nâng cấp pip..."
    & $venvPy -m pip install --upgrade pip --quiet

    $req   = Join-Path $Root "requirements.txt"
    $loose = Join-Path $Root "requirements.loose.txt"
    Info "Cài dependencies (requirements.txt)..."
    & $venvPy -m pip install -r $req --quiet
    if ($LASTEXITCODE -ne 0 -and (Test-Path $loose)) {
        Warn "Bản pin lỗi -> thử requirements.loose.txt."
        & $venvPy -m pip install -r $loose --quiet
    }
    if ($LASTEXITCODE -ne 0) { Err "Cài dependencies thất bại."; exit 1 }
    Ok "Dependencies sẵn sàng."
}

# ============================================================
# 2) KIỂM TRA ADOMD.NET
# ============================================================
Step "2/3 Kiểm tra ADOMD.NET"
$adomdDll = "Microsoft.AnalysisServices.AdomdClient.dll"
$pf = ${env:ProgramFiles}; if (-not $pf) { $pf="C:\Program Files" }
$pf86 = ${env:ProgramFiles(x86)}; if (-not $pf86) { $pf86="C:\Program Files (x86)" }
$globs = @(
    (Join-Path $pf   "Microsoft SQL Server Management Studio*\*\Common7\IDE"),
    (Join-Path $pf   "Microsoft SQL Server Management Studio*\Common7\IDE"),
    (Join-Path $pf86 "Microsoft SQL Server Management Studio*\Common7\IDE"),
    (Join-Path $pf   "Microsoft.NET\ADOMD.NET\*"),
    (Join-Path $pf86 "Microsoft.NET\ADOMD.NET\*"),
    (Join-Path $pf   "Microsoft SQL Server\*\SDK\Assemblies")
)
$found = $null
foreach ($g in $globs) {
    $hit = Get-ChildItem -Path $g -Filter $adomdDll -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hit) { $found = $hit.FullName; break }
}
if ($found) { Ok "Tìm thấy ADOMD.NET: $found" }
else {
    Warn "KHÔNG thấy ADOMD.NET. Tool Cloud vẫn chạy; tool LOCAL sẽ lỗi tới khi cài."
    Warn "  Cài 'Analysis Services client libraries': https://learn.microsoft.com/analysis-services/client-libraries"
    Warn "  Hoặc đặt ADOMD_LIB_DIR trong $envFile tới thư mục chứa $adomdDll."
}

# ============================================================
# 3) ĐĂNG KÝ MCP VÀO HOST (trỏ về CHÍNH thư mục này)
# ============================================================
$pyJson  = $venvPy.Replace('\','/')
$srvJson = $serverPath.Replace('\','/')

function Merge-McpJson([string]$Path) {
    # BẪY ĐÃ TÁI HIỆN (audit 2026-07-15): KHÔNG round-trip JSON của host bằng PS 5.1.
    #   (1) ~/.claude.json thật chứa key rỗng "" -> ConvertFrom-Json PS 5.1 CRASH luôn
    #       ("value of argument name is not valid") -> nhánh fallback này chưa bao giờ chạy nổi.
    #   (2) ConvertTo-Json quá -Depth thì ÂM THẦM biến tầng sâu hơn thành chuỗi '@{n=}' (mất dữ liệu).
    # => Merge bằng Python của venv (json chuẩn: không depth limit, không sợ key rỗng,
    #    ensure_ascii=False giữ tiếng Việt) + VALIDATE parse lại sau khi ghi.
    if (-not (Test-Path $Path)) {
        $dir = Split-Path -Parent $Path
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        Write-Utf8NoBom $Path "{`n  `"mcpServers`": {}`n}"
        Info "Tạo mới $Path"
    }
    if (-not (Test-Path $venvPy)) {
        Warn "Không có venv Python ($venvPy) để merge JSON an toàn -> BỎ QUA $Path."
        Warn "  Chạy lại install.ps1 KHÔNG kèm -SkipVenv, hoặc thêm tay block powerbi-mcp-bridge (xem hosts/)."
        return
    }
    Backup-File $Path
    $mergePy = @'
import json, sys
path, py, srv = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, encoding="utf-8-sig") as f:
    raw = f.read().strip()
data = json.loads(raw) if raw else {}
if not isinstance(data, dict):
    sys.exit("root JSON khong phai object")
data.setdefault("mcpServers", {})["powerbi-mcp-bridge"] = {
    "type": "stdio", "command": py, "args": ["-u", srv],
    "env": {"PYTHONUNBUFFERED": "1"},
}
out = json.dumps(data, ensure_ascii=False, indent=2)
json.loads(out)  # validate truoc khi ghi
import os
tmp = path + ".pbi-tmp"
with open(tmp, "w", encoding="utf-8", newline="\n") as f:
    f.write(out + "\n")
json.load(open(tmp, encoding="utf-8"))  # validate ban tam
os.replace(tmp, path)                    # thay the ATOMIC — khong co trang thai nua vời
json.load(open(path, encoding="utf-8"))  # validate sau khi ghi
print("MERGE_OK")
'@
    $tmpPy = Join-Path $env:TEMP "pbi-merge-mcp.py"
    Write-Utf8NoBom $tmpPy $mergePy
    $out = & $venvPy $tmpPy $Path $pyJson $srvJson 2>&1
    Remove-Item $tmpPy -Force -ErrorAction SilentlyContinue
    if ("$out" -match "MERGE_OK") { Ok "Đã ghi + validate cấu hình MCP trong $Path" }
    else { Err "Merge JSON thất bại ($out). File gốc còn nguyên trong .bak.$Stamp — KHÔNG ghi đè."; }
}

function Register-Claude {
    Info "Claude Code..."
    if (Get-Command claude -ErrorAction SilentlyContinue) {
        # BẪY ĐÃ TRẢ GIÁ: (1) KHÔNG thêm cờ `-u` sau `--` — parser của claude CLI nuốt nó
        # và lệnh add FAIL (PYTHONUNBUFFERED=1 đã đủ unbuffered). (2) Gọi qua cmd /c để
        # PowerShell không can thiệp token `--`. (3) CHỈ remove sau khi chắc chắn add được
        # -> add trước với tên tạm? Không cần: add đè cùng tên sẽ lỗi "already exists",
        # nên thử add trước; nếu "already exists" thì remove rồi add lại.
        # LƯU Ý PS 5.1: KHÔNG dùng `2>&1` ở phía PowerShell với native command khi
        # $ErrorActionPreference=Stop — stderr bị bọc thành NativeCommandError TERMINATING
        # và script chết giữa chừng. Redirect BÊN TRONG chuỗi cmd để cmd.exe tự gộp.
        $addCmd = "claude mcp add powerbi-mcp-bridge -s user -e PYTHONUNBUFFERED=1 -- ""$venvPy"" ""$serverPath"""
        $out = & cmd /c "$addCmd 2>&1"
        if ($LASTEXITCODE -ne 0 -and "$out" -match "already exists") {
            & cmd /c "claude mcp remove powerbi-mcp-bridge -s user 2>&1" | Out-Null
            $out = & cmd /c "$addCmd 2>&1"
        }
        if ($LASTEXITCODE -eq 0) { Ok "Claude: đăng ký qua 'claude mcp add' (scope user)."; return }
        Warn "claude CLI lỗi ($out) -> sửa .claude.json trực tiếp."
    } else { Warn "Không thấy 'claude' CLI -> sửa .claude.json trực tiếp." }
    Merge-McpJson (Join-Path $env:USERPROFILE ".claude.json")
}
function Register-Antigravity { Info "Antigravity..."; Merge-McpJson (Join-Path $env:USERPROFILE ".gemini\antigravity\mcp_config.json") }
function Register-Codex {
    Info "Codex..."
    $cfg = Join-Path $env:USERPROFILE ".codex\config.toml"
    $dir = Split-Path -Parent $cfg
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    # env ghi dạng SUB-TABLE, không dùng inline `env = {...}`: Codex tự ghi lại config
    # theo dạng sub-table, nên nếu ta ghi inline thì hai dạng cùng tồn tại -> TOML
    # "duplicate key" -> Codex không parse nổi config -> app chết ngay lúc khởi động.
    $block = @"
[mcp_servers.powerbi-mcp-bridge]
command = "$pyJson"
args = ["-u", "$srvJson"]

[mcp_servers.powerbi-mcp-bridge.env]
PYTHONUNBUFFERED = "1"
"@
    # File chưa có / RỖNG đi chung một đường với file có sẵn (thống nhất format => idempotent
    # ngay từ lần đầu; và Get-Content -Raw file rỗng trả $null -> .TrimEnd() nổ NullReference).
    Backup-File $cfg
    $text = ''
    if (Test-Path $cfg) { $text = Get-Content $cfg -Raw -Encoding UTF8 }
    if ($null -eq $text) { $text = '' }
    # Phải xóa CẢ sub-table ([mcp_servers.powerbi-mcp-bridge.env]) chứ không chỉ block cha:
    # regex cũ chỉ khớp block cha nên bỏ sót sub-table -> nó thành mồ côi và trùng key.
    # Kết thúc match bằng lookahead `^\[` (ngoặc ĐẦU DÒNG), KHÔNG dùng [^\[]* —
    # giá trị `args = ["-u", ...]` có `[` giữa dòng, sẽ cắt cụt block và làm hỏng file.
    $pattern = '(?ms)^\[mcp_servers\.powerbi-mcp-bridge(?:\.[^\]\r\n]+)?\].*?(?=^\[|\z)'
    $had = $text -match '(?m)^\[mcp_servers\.powerbi-mcp-bridge(?:\.[^\]\r\n]+)?\]'
    $text = [regex]::Replace($text, $pattern, '')
    $body = $text.TrimEnd()
    if ($body) { $body += "`n`n" }
    Write-Utf8NoBom $cfg ($body + $block + "`n")
    if ($had) { Ok "Cập nhật block MCP trong $cfg" } else { Ok "Đã thêm block MCP vào $cfg" }

    # Chốt an toàn: config.toml hỏng = Codex không mở được. Verify parse ngay sau khi ghi.
    if (Test-Path $venvPy) {
        & $venvPy -c "import tomllib,sys; tomllib.load(open(sys.argv[1],'rb'))" $cfg 2>$null
        if ($LASTEXITCODE -ne 0) {
            Err "config.toml KHÔNG parse được sau khi ghi. Khôi phục từ bản .bak gần nhất!"
        } else { Info "config.toml parse OK." }
    }
}
function Install-Skill([string]$SkillRoot) {
    # Copy MỌI skill (powerbi-mcp, pbi-pipeline, kpim-analysis, ...) — nguồn duy nhất:
    # plugins\powerbi-agent\skills\ (fallback layout cũ skill\ cho bản clone cũ).
    # Copy CẢ thư mục: SKILL.md + references\ + document-templates\ + scripts\ + assets\
    $skillBase = Join-Path $Root "plugins\powerbi-agent\skills"
    if (-not (Test-Path $skillBase)) { $skillBase = Join-Path $Root "skill" }
    if (-not (Test-Path $skillBase)) { return }
    Get-ChildItem -Path $skillBase -Directory | ForEach-Object {
        $src = Join-Path $_.FullName "SKILL.md"
        if (Test-Path $src) {
            $dst = Join-Path $SkillRoot $_.Name
            # MIRROR, không phải merge: xóa bản đích cũ trước khi copy — file đã bị xóa/đổi tên
            # ở nguồn sẽ không thành "xác sống" drift ở host (đã tái hiện bằng harness audit).
            if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
            New-Item -ItemType Directory -Path $dst -Force | Out-Null
            # copy toàn bộ nội dung skill (bỏ __pycache__ và out/ tạm)
            Copy-Item (Join-Path $_.FullName "*") $dst -Recurse -Force `
                -Exclude "__pycache__","out" -ErrorAction SilentlyContinue
            Info "Skill $($_.Name) (full) -> $dst"
        }
    }

    # Claude: copy thêm 6 lệnh /pbi-* vào ~/.claude/commands (host khác dùng skill pbi-knowledge)
    if ($SkillRoot -like "*\.claude\skills") {
        $cmdSrc = Join-Path $Root "plugins\powerbi-agent\commands"
        $cmdDst = Join-Path (Split-Path -Parent $SkillRoot) "commands"
        if (Test-Path $cmdSrc) {
            if (-not (Test-Path $cmdDst)) { New-Item -ItemType Directory -Path $cmdDst -Force | Out-Null }
            # mirror phần lệnh pbi-* (lệnh khác của user giữ nguyên)
            Get-ChildItem $cmdDst -Filter "pbi-*.md" -ErrorAction SilentlyContinue | Remove-Item -Force
            Copy-Item (Join-Path $cmdSrc "*.md") $cmdDst -Force
            Info "Commands /pbi-* -> $cmdDst"
        }
    }
}

if ($SkipHosts) {
    Step "3/3 Đăng ký host"; Warn "Bỏ qua đăng ký host (-SkipHosts)."
} else {
    Step "3/3 Đăng ký MCP vào host"
    if ($Hosts -contains "claude")      { Register-Claude;      Install-Skill (Join-Path $env:USERPROFILE ".claude\skills") }
    if ($Hosts -contains "codex")       { Register-Codex;       Install-Skill (Join-Path $env:USERPROFILE ".codex\skills") }
    if ($Hosts -contains "antigravity") { Register-Antigravity; Install-Skill (Join-Path $env:USERPROFILE ".gemini\antigravity\skills") }
}

# ---- Smoke test ----
if ((-not $SkipVenv) -and (Test-Path $venvPy)) {
    Step "Kiểm thử nhanh (import)"
    $probe = "import importlib;[importlib.import_module(m) for m in ('mcp.server.fastmcp','pyadomd','pandas','msal','dotenv','tabulate')];print('IMPORTS_OK')"
    $out = & $venvPy -c $probe 2>&1
    if ($out -match "IMPORTS_OK") { Ok "Thư viện import OK. Server sẵn sàng." } else { Warn "Import có vấn đề:"; Write-Host $out }
}

Write-Host "`n=============================================" -ForegroundColor Green
Ok "HOÀN TẤT."
Write-Host @"

Bước cuối: KHỞI ĐỘNG LẠI host để nạp MCP (Claude: 'claude mcp list' để kiểm).
Server tại : $Root
Gỡ cài     : .\uninstall.ps1
"@ -ForegroundColor Gray

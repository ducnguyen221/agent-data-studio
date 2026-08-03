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
.PARAMETER Only
  Chỉ chạy MỘT bước: "plugin" = chỉ cài skill + lệnh + agent (bước 4), không đụng venv/MCP.
  Dùng khi đã cài rồi và chỉ muốn cập nhật phần quy trình.
#>
[CmdletBinding()]
param(
    [string[]] $Hosts = @("claude", "codex", "antigravity"),
    [switch]   $SkipVenv,
    [switch]   $SkipHosts,
    [ValidateSet("plugin")]
    [string]   $Only
)

# -Only plugin: bỏ qua venv + đăng ký MCP, chỉ chạy bước 4 (skill/lệnh/agent).
# KHÔNG overload $SkipHosts: -SkipHosts có hợp đồng riêng ("không đụng thư mục host nào"),
# nếu dùng chung cờ thì -SkipHosts sẽ vẫn ghi skill/lệnh vào host — sai tài liệu.
$SkipMcp    = $SkipHosts
$RunPlugin  = -not $SkipHosts
if ($Only -eq "plugin") { $SkipVenv = $true; $SkipMcp = $true; $RunPlugin = $true }

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
tmp = path + ".powerbi-tmp"
with open(tmp, "w", encoding="utf-8", newline="\n") as f:
    f.write(out + "\n")
json.load(open(tmp, encoding="utf-8"))  # validate ban tam
os.replace(tmp, path)                    # thay the ATOMIC — khong co trang thai nua vời
json.load(open(path, encoding="utf-8"))  # validate sau khi ghi
print("MERGE_OK")
'@
    $tmpPy = Join-Path $env:TEMP "powerbi-merge-mcp.py"
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
    # Copy MỌI skill (powerbi-mcp, powerbi-pipeline, kpim-analysis, ...) — nguồn duy nhất:
    # plugins\powerbi-agent\skills\ (fallback layout cũ skill\ cho bản clone cũ).
    # Copy CẢ thư mục: SKILL.md + references\ + document-templates\ + scripts\ + assets\
    $skillBase = Join-Path $Root "plugins\powerbi-agent\skills"
    if (-not (Test-Path $skillBase)) { $skillBase = Join-Path $Root "skill" }
    if (-not (Test-Path $skillBase)) { return }
    # Skill ĐỔI TÊN ở v0.5.0: mirror chỉ xử lý skill CÓ trong nguồn, nên bản cũ nằm lại thành
    # xác sống. Tệ hơn nhiều so với rác thường: pbi-knowledge/SKILL.md chứa nguyên bảng định tuyến
    # bảo agent chạy /pbi-setup, /pbi-new... — đúng những lệnh mà chính installer vừa xoá.
    foreach ($old in @("pbi-pipeline", "pbi-knowledge")) {
        $p = Join-Path $SkillRoot $old
        if (Test-Path $p) { Remove-Item $p -Recurse -Force; Info "Xoá skill cũ (<0.5.0): $old" }
    }
    Get-ChildItem -Path $skillBase -Directory | ForEach-Object {
        $src = Join-Path $_.FullName "SKILL.md"
        if (Test-Path $src) {
            $dst = Join-Path $SkillRoot $_.Name
            # MIRROR, không phải merge: xóa bản đích cũ trước khi copy — file đã bị xóa/đổi tên
            # ở nguồn sẽ không thành "xác sống" drift ở host (đã tái hiện bằng harness audit).
            # Dựng ở thư mục TẠM cạnh đích rồi mới tráo vào: bản cũ chỉ bị xoá khi bản mới
            # đã copy xong và kiểm được. Trước đây xoá đích TRƯỚC rồi copy với
            # -ErrorAction SilentlyContinue và luôn in "thành công" — lỗi quyền/đường dẫn quá dài
            # là user mất luôn skill đang chạy tốt mà installer vẫn báo OK.
            $stage = "$dst.__new"
            if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
            New-Item -ItemType Directory -Path $stage -Force | Out-Null
            Copy-Item (Join-Path $_.FullName "*") $stage -Recurse -Force -Exclude "__pycache__","out"
            if (-not (Test-Path (Join-Path $stage "SKILL.md"))) {
                Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
                Err "Skill $($_.Name): copy hỏng (thiếu SKILL.md) — GIỮ NGUYÊN bản cũ ở $dst"
                return
            }
            # Skill goc cua repo cung phai ton trong so huu: user co the co skill rieng
            # trung ten (vd powerbi-knowledge). Nhan dien ban CUA TA bang frontmatter name:.
            if (Test-Path $dst) {
                $mine = Test-Path (Join-Path $dst ".powerbi-agent-generated")
                if (-not $mine) {
                    $skf = Join-Path $dst "SKILL.md"
                    if (Test-Path $skf) {
                        $h = (Get-Content $skf -TotalCount 5 -ErrorAction SilentlyContinue) -join "`n"
                        if ($h -match "(?m)^name:\s*$([regex]::Escape($_.Name))\s*$") { $mine = $true }
                    } else { $mine = $true }   # thu muc rong/rac -> coi la cua ta
                }
                if (-not $mine) {
                    Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
                    Warn "Bo qua skill '$($_.Name)': da co skill CUNG TEN khong phai do powerbi-agent tao."
                    return
                }
                Remove-Item $dst -Recurse -Force
            }
            Move-Item $stage $dst
            Info "Skill $($_.Name) (full) -> $dst"
        }
    }

}

# Mirror thư mục lệnh: dọn CẢ họ tên cũ "pbi-*" (trước v0.5.0) lẫn họ mới "powerbi-*" rồi copy lại.
# Nếu chỉ dọn họ mới thì người nâng cấp giữ 6 lệnh cũ mồ côi -> thấy 12 lệnh, gọi nhầm bản cũ.
# -Filter "pbi-*.md" KHÔNG khớp "powerbi-*.md" (wildcard khớp từ ĐẦU tên) nên phải duyệt cả hai.
# Lệnh khác của user trong cùng thư mục KHÔNG bị đụng.
# Xoá MỘT mục theo sổ ghi, an toàn trước sổ ghi rác.
# Sổ ghi là file text nằm trong thư mục user ghi được, nên phải coi nội dung là KHÔNG tin cậy:
#  - "powerbi-*.md" đi qua Join-Path vẫn là wildcard hợp lệ -> Remove-Item xoá luôn lệnh riêng
#    của user, tái tạo đúng cái bug mà sổ ghi sinh ra để chống;
#  - "..\..\x.md" resolve ra NGOÀI thư mục đích;
#  - ký tự lạ (tab, "<") làm Test-Path NÉM lỗi, mà $ErrorActionPreference='Stop' -> chết installer.
function Remove-LedgerEntry([string]$Dir, [string]$Name) {
    if ([string]::IsNullOrWhiteSpace($Name)) { return }
    if ($Name -ne [System.IO.Path]::GetFileName($Name) -or $Name -match '[\*\?\[\]]') {
        Warn "Bỏ qua mục sổ ghi không hợp lệ: $Name"; return
    }
    try {
        $p = Join-Path $Dir $Name
        if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force }
    } catch { Warn "Bỏ qua mục sổ ghi không xử lý được: $Name" }
}

function Install-Commands([string]$CmdDst, [string]$Label) {
    $cmdSrc = Join-Path $Root "plugins\powerbi-agent\commands"
    if (-not (Test-Path $cmdSrc)) { return }
    if (-not (Test-Path $CmdDst)) { New-Item -ItemType Directory -Path $CmdDst -Force | Out-Null }
    # Xoá theo SỔ GHI những gì LẦN TRƯỚC ta đã cài, không dùng wildcard.
    #  - wildcard "powerbi-*.md" sẽ nuốt cả lệnh riêng của user (vd powerbi-cua-toi.md)
    #    và chiếm namespace mà repo không sở hữu;
    #  - chỉ suy từ manifest hiện tại thì lệnh ĐÃ BỊ BỎ khỏi repo sẽ thành xác sống ở host.
    # Sổ ghi giải quyết cả hai: xoá đúng thứ ta từng đặt vào, không hơn không kém.
    $ownNames    = @(Get-ChildItem $cmdSrc -Filter "*.md" | ForEach-Object { $_.Name })
    $ledger      = Join-Path $CmdDst ".powerbi-agent-installed.txt"
    $prev        = if (Test-Path $ledger) { @(Get-Content $ledger | Where-Object { $_ -match '\S' }) } else { @() }
    $legacyNames = @("pbi-setup.md","pbi-new.md","pbi-scan.md","pbi-done.md","pbi-pack.md","pbi-recall.md")
    foreach ($nm in ($prev + $ownNames + $legacyNames | Sort-Object -Unique)) {
        Remove-LedgerEntry $CmdDst $nm
    }
    Copy-Item (Join-Path $cmdSrc "*.md") $CmdDst -Force
    Set-Content -Path $ledger -Value $ownNames -Encoding UTF8
    Info "$($ownNames.Count) lệnh /powerbi-* -> $CmdDst ($Label)"
}

# Codex KHÔNG có slash-command tự do như Claude: file trong ~/.codex/prompts/ được gọi bằng
# `/prompts:<tên>`, không phải `/<tên>` — nên đặt ở đó thì tên lệnh lệch hẳn so với Claude, mà
# installer vẫn báo thành công và test vẫn xanh (test chỉ đếm file ở nơi CHÍNH NÓ vừa ghi vào).
# Cách đúng theo hướng hiện tại của Codex: mỗi lệnh thành MỘT SKILL, agent gọi theo tên.
# Nguồn vẫn là commands/ — không nhân bản nội dung, chỉ bọc thêm frontmatter skill.
function Install-CommandsAsSkills([string]$SkillRoot) {
    $cmdSrc = Join-Path $Root "plugins\powerbi-agent\commands"
    if (-not (Test-Path $cmdSrc)) { return }
    $n = 0
    $generated = @()
    foreach ($f in Get-ChildItem $cmdSrc -Filter "*.md") {
        $name = [System.IO.Path]::GetFileNameWithoutExtension($f.Name)
        $raw  = Get-Content $f.FullName -Raw -Encoding UTF8

        # Lấy description trong frontmatter của command để làm description của skill.
        $desc = "Quy trình powerbi-agent: $name"
        if ($raw -match '(?ms)\A---\s*\r?\n(.*?)\r?\n---\s*\r?\n') {
            $fm = $Matches[1]
            if ($fm -match '(?m)^description:\s*(.+)$') { $desc = $Matches[1].Trim() }
            $body = $raw.Substring($Matches[0].Length)
        } else { $body = $raw }

        # $ARGUMENTS là cú pháp slash-command của Claude — Codex không thay thế nó.
        $body = $body -replace '\$ARGUMENTS', '(tham số user đưa vào khi gọi quy trình này)'

        $dst = Join-Path $SkillRoot $name
        # KHONG xoa bua thu muc trung ten: nguoi dung co the co skill rieng ten powerbi-help.
        # Chi ghi de thu MINH TUNG TAO (co file danh dau). Trung ten ma khong phai cua minh
        # thi BAO va bo qua, khong pha do cua ho.
        $marker = Join-Path $dst ".powerbi-agent-generated"
        if (Test-Path $dst) {
            $owned = Test-Path $marker
            if (-not $owned) {
                # Ban truoc v0.6 sinh skill nay MA CHUA co marker. Neu doi hoi marker tuyet doi
                # thi nguoi nang cap vua khong cap nhat duoc, vua khong go duoc — ket vinh vien.
                # Nhan dien theo DAU VET SINH RA: frontmatter `name: <ten lenh>` do chinh ta ghi.
                $sk = Join-Path $dst "SKILL.md"
                if (Test-Path $sk) {
                    $head = Get-Content $sk -TotalCount 5 -ErrorAction SilentlyContinue
                    if (($head -join "`n") -match "(?m)^name:\s*$([regex]::Escape($name))\s*$") { $owned = $true }
                }
            }
            if (-not $owned) {
                Warn "Bo qua '$name': da co skill CUNG TEN khong phai do powerbi-agent tao ($dst)."
                continue
            }
            Remove-Item $dst -Recurse -Force
        }
        New-Item -ItemType Directory -Path $dst -Force | Out-Null
        $head = "---`nname: $name`ndescription: >`n  $desc`n  Gọi khi user nói `"chạy $name`" hoặc mô tả việc khớp mô tả trên.`n---`n`n"
        Write-Utf8NoBom (Join-Path $dst "SKILL.md") ($head + $body)
        # Marker ghi SAU CUNG: SKILL.md loi thi khong de lai thu muc co marker ma rong.
        Write-Utf8NoBom $marker "powerbi-agent sinh tu plugins/powerbi-agent/commands/$name.md`n"
        $generated += $name
        $n++
    }
    $ledger = Join-Path $SkillRoot ".powerbi-agent-skills.txt"
    # Lenh bi XOA khoi repo phai bien mat o host. Khong co so ghi thi no nam lai
    # vinh vien — va gio con mang marker nen trong nhu hang chinh chu.
    if (Test-Path $ledger) {
        foreach ($old in (Get-Content $ledger | Where-Object { $_ -match '\S' })) {
            if ($generated -contains $old) { continue }
            if ($old -ne [System.IO.Path]::GetFileName($old) -or $old -match '[\*\?\[\]]') { continue }
            $p = Join-Path $SkillRoot $old
            if ((Test-Path (Join-Path $p ".powerbi-agent-generated"))) {
                Remove-Item $p -Recurse -Force; Info "Xoa skill-lenh da bo: $old"
            }
        }
    }
    Set-Content -Path $ledger -Value $generated -Encoding UTF8
    Info "$n lệnh -> skill Codex tại $SkillRoot (gọi theo tên, vd `"chạy powerbi-help`")"
}

# Agent phụ (powerbi-knowledge-curator). Chỉ Claude Code có thư mục agents/ chuẩn;
# host khác vẫn có nội dung đó qua skill powerbi-knowledge nên không mất năng lực.
function Install-Agents([string]$AgentDst) {
    $src = Join-Path $Root "plugins\powerbi-agent\agents"
    if (-not (Test-Path $src)) { return }
    if (-not (Test-Path $AgentDst)) { New-Item -ItemType Directory -Path $AgentDst -Force | Out-Null }
    foreach ($nm in (@(Get-ChildItem $src -Filter "*.md" | ForEach-Object { $_.Name }) + @("pbi-knowledge-curator.md"))) {
        Remove-LedgerEntry $AgentDst $nm
    }
    Copy-Item (Join-Path $src "*.md") $AgentDst -Force
    Info "Agent powerbi-knowledge-curator -> $AgentDst"
}

Step "3/4 Đăng ký MCP vào host"
if ($SkipMcp) {
    if ($Only -eq "plugin") { Info "Bỏ qua đăng ký MCP (-Only plugin)." }
    else                    { Warn "Bỏ qua đăng ký host (-SkipHosts)." }
} else {
    if ($Hosts -contains "claude")      { Register-Claude }
    if ($Hosts -contains "codex")       { Register-Codex }
    if ($Hosts -contains "antigravity") { Register-Antigravity }
}

# ---- Bước 4: skill + lệnh + agent (chạy độc lập được: install.ps1 -Only plugin) ----
Step "4/4 Cài quy trình (skill + lệnh + agent)"
if (-not $RunPlugin) {
    Warn "Bỏ qua cài quy trình (-SkipHosts): không đụng thư mục host nào."
} else {
if ($Hosts -contains "claude") {
    $h = Join-Path $env:USERPROFILE ".claude"
    Install-Skill    (Join-Path $h "skills")
    Install-Commands (Join-Path $h "commands") "slash-command"
    Install-Agents   (Join-Path $h "agents")
}
if ($Hosts -contains "codex") {
    $h = Join-Path $env:USERPROFILE ".codex"
    Install-Skill          (Join-Path $h "skills")
    Install-CommandsAsSkills (Join-Path $h "skills")
}
if ($Hosts -contains "antigravity") {
    $h = Join-Path $env:USERPROFILE ".gemini\antigravity"
    Install-Skill (Join-Path $h "skills")
    # Antigravity KHÔNG có cơ chế slash-command (xem hosts/antigravity/README.md). Đặt bộ lệnh
    # ngay trong skill powerbi-knowledge để agent vẫn đọc được quy trình và gọi theo tên.
    $kn = Join-Path $h "skills\powerbi-knowledge"
    if (Test-Path $kn) { Install-Commands (Join-Path $kn "commands") "tham chiếu trong skill" }
    else {
        # Im lặng ở đây là tệ nhất: Antigravity không có slash-command nên user không có cách
        # nào tự phát hiện mình đang thiếu TOÀN BỘ bộ lệnh.
        Warn "Không thấy skill powerbi-knowledge -> Antigravity KHÔNG nhận được bộ lệnh."
        Warn "  Chạy lại install.ps1 đầy đủ (không -Only) từ thư mục repo còn nguyên vẹn."
    }
}
}

# ---- Smoke test ----
# Không chỉ kiểm import: kiểm luôn 2 năng lực người dùng đụng vào đầu tiên (kit + Knowledge Dir),
# để câu "việc cần làm tiếp" bên dưới nói đúng trạng thái THẬT của máy này thay vì đoán.
$knowledgeReady = $false
if ((-not $SkipVenv) -and (Test-Path $venvPy)) {
    Step "Kiểm thử nhanh"
    $probe = "import importlib;[importlib.import_module(m) for m in ('mcp.server.fastmcp','pyadomd','pandas','msal','dotenv','tabulate')];print('IMPORTS_OK')"
    $out = & $venvPy -c $probe 2>&1
    if ($out -match "IMPORTS_OK") { Ok "Thư viện import OK. Server sẵn sàng." } else { Warn "Import có vấn đề:"; Write-Host $out }

    # KHÔNG nội suy $Root vào literal Python: đường dẫn có dấu nháy đơn (vd thư mục tên "Anh's PC")
    # hoặc kết thúc bằng "\" sẽ tạo SyntaxError, probe im lặng thất bại và installer khuyên SAI.
    # Truyền đường dẫn qua argv thay vì ghép chuỗi.
    $probe2 = @'
import sys
sys.path.insert(0, sys.argv[1])
from powerbi_agent.tools_template import _load_kits
from powerbi_agent.knowledge import resolve_root
print('KITS=%d' % len(_load_kits()))
print('KNOWLEDGE=%s' % ('yes' if resolve_root() else 'no'))
'@
    $out2 = & $venvPy -c $probe2 $Root 2>&1
    $probeOk = "$out2" -match "KITS=(\d+)"
    if ($probeOk) { Ok "Kit báo cáo dùng được: $($Matches[1])" }
    else { Warn "Không kiểm được kho kit / Knowledge Dir (probe lỗi): $out2" }
    if ($probeOk) {
        if ("$out2" -match "KNOWLEDGE=yes") { $knowledgeReady = $true; Ok "Knowledge Dir đã thiết lập." }
        else { Info "Knowledge Dir CHƯA thiết lập (bình thường ở máy mới)." }
    }
}

Write-Host "`n=============================================" -ForegroundColor Green
Ok "HOÀN TẤT."
$nextSetup = if ($knowledgeReady) { "(đã xong — bỏ qua)" } else { "/powerbi-setup   -> chỉ định Knowledge Dir (làm 1 lần)" }
Write-Host @"

VIỆC CẦN LÀM TIẾP — 3 bước:
  1. KHỞI ĐỘNG LẠI host để nạp MCP (Claude: 'claude mcp list' để kiểm).
  2. $nextSetup
  3. /powerbi-help    -> agent tự liệt kê năng lực và định tuyến việc của bạn.

Server tại : $Root
Cập nhật riêng phần quy trình (không đụng venv/MCP): .\install.ps1 -Only plugin
Gỡ cài     : .\uninstall.ps1
"@ -ForegroundColor Gray

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
# Đối xứng với install.ps1: gỡ hụt mà vẫn exit 0 thì script gọi (hoặc CI) tưởng đã sạch.
$script:HadError = $false
function Err($m){$script:HadError = $true; Write-Host "[X] $m" -ForegroundColor Red}
function Backup-File($p){ if(Test-Path $p){ Copy-Item $p "$p.bak.$Stamp" -Force; Info "Backup: $p.bak.$Stamp" } }
function Write-Utf8NoBom($Path,$Text){ [System.IO.File]::WriteAllText($Path,$Text,(New-Object System.Text.UTF8Encoding($false)))}
$name = "powerbi-mcp-bridge"
# Co user tu dat de noi "thu muc nay la CUA TOI, dung dung" (xem install.ps1).
$KeepFile = ".powerbi-agent-keep"

function Remove-FromJson($Path){
    # BẪY ĐÃ TÁI HIỆN: KHÔNG round-trip JSON host bằng PS 5.1 (key rỗng trong ~/.claude.json
    # làm ConvertFrom-Json crash; ConvertTo-Json cắt cụt tầng sâu). Gỡ bằng Python + atomic + validate.
    if (-not (Test-Path $Path)) { return }
    if (-not (Test-Path $venvPy)) { Warn "Không có venv để sửa JSON an toàn -> bỏ qua $Path (gỡ tay entry '$name')."; return }
    Backup-File $Path
    $py = @'
import json, os, sys
path, name = sys.argv[1], sys.argv[2]
# File RONG khong phai loi: khong co gi de go. json.load() se nem JSONDecodeError,
# gio Err -> exit 1, bao "GO CHUA SACH" cho mot trang thai hoan toan vo hai.
# (Helper merge ben install.ps1 da xu ly file rong theo dung cach nay.)
with open(path, encoding="utf-8-sig") as f:
    raw = f.read().strip()
if not raw:
    print("ABSENT")
    sys.exit(0)
data = json.loads(raw)
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
    # Ten DUY NHAT theo tien trinh: ten co dinh thi hai lan chay song song (pytest goi
    # harness, harness goi installer) xoa file cua nhau giua chung -> "can't open file".
    $tmpPy = Join-Path $env:TEMP ("powerbi-remove-mcp-$PID-" + [guid]::NewGuid().ToString("N") + ".py")
    Write-Utf8NoBom $tmpPy $py
    # KHONG dung `2>&1` phia PowerShell voi native command khi $ErrorActionPreference=Stop:
    # stderr bi boc thanh NativeCommandError TERMINATING -> script chet TRUOC khi toi nhanh
    # xu ly loi ben duoi, va installer dung o giua (buoc 4 khong chay).
    # Cung KHONG boc qua cmd /c: tham so o day la JSON co dau nhay, cmd se lam hong.
    # Cach an toan: ha ErrorActionPreference dung quanh loi goi roi tra lai.
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $helperExit = 1
    try     { $out = & $venvPy $tmpPy $Path $name 2>&1; $helperExit = $LASTEXITCODE }
    finally { $ErrorActionPreference = $prevEap
              # Dọn trong finally: ném giữa chừng mà dọn ở ngoài thì mỗi lần chạy để lại
              # một file tạm TÊN DUY NHẤT -> rác tích tụ trong %TEMP% thay vì bị ghi đè.
              Remove-Item $tmpPy -Force -ErrorAction SilentlyContinue }
    # PHAI doc $LASTEXITCODE, va khop NEO DONG. Truoc day chi tim chuoi con trong
    # stdout+stderr da gop: helper in "REMOVED" roi exit 1, hoac traceback tinh co
    # chua chuoi do, deu lam installer bao dang ky THANH CONG trong khi khong co gi xay ra.
    # `"$out"` nối MẢNG bằng DẤU CÁCH chứ không phải newline -> neo `(?m)^...$` chỉ khớp khi
    # REMOVED là TOÀN BỘ output. Một dòng warning bất kỳ của Python là gỡ THÀNH CÔNG mà
    # script báo thất bại. Phải tự nối bằng LF trước khi khớp.
    $outText = (@($out) | ForEach-Object { "$_" }) -join "`n"
    if ($helperExit -eq 0 -and $outText -match "(?m)^REMOVED\s*$") { Ok "Đã gỡ '$name' khỏi $Path (validate OK)" }
    elseif ($outText -match "(?m)^ABSENT\s*$") { Info "$Path không chứa '$name'." }
    else { Err "Không gỡ được khỏi $Path ($outText) — file gốc còn nguyên (.bak.$Stamp)." }
}

if ($Hosts -contains "claude") {
    if (Get-Command claude -ErrorAction SilentlyContinue) {
        # LƯU Ý PS 5.1: không redirect stderr của native command phía PowerShell khi
        # $ErrorActionPreference=Stop (NativeCommandError terminating) — gộp trong cmd /c.
        $rmOut = & cmd /c "claude mcp remove $name -s user 2>&1"
        # Trước đây báo "đã gỡ" vô điều kiện: CLI lỗi thì user tưởng sạch
        # nhưng entry MCP vẫn sống trong config.
        if ($LASTEXITCODE -eq 0) { Ok "Claude: remove qua CLI." }
        else {
            Warn "claude CLI không gỡ được ($rmOut) -> gỡ trực tiếp trong .claude.json"
            Remove-FromJson (Join-Path $env:USERPROFILE ".claude.json")
        }
    }
    else { Remove-FromJson (Join-Path $env:USERPROFILE ".claude.json") }
}
if ($Hosts -contains "antigravity") { Remove-FromJson (Join-Path $env:USERPROFILE ".gemini\antigravity\mcp_config.json") }
if ($Hosts -contains "codex") {
    $cfg = Join-Path $env:USERPROFILE ".codex\config.toml"
    if (Test-Path $cfg) {
        $text = Get-Content $cfg -Raw -Encoding UTF8
        if ($null -eq $text) { $text = '' }
        # File KHÔNG chứa block của ta -> không có gì để gỡ, và KHÔNG đụng vào file (kể cả
        # backup). Trước đây vẫn TrimEnd+ghi đè rồi validate: một config.toml vốn đã hỏng sẵn
        # (không phải lỗi ta) làm uninstall exit 1 kèm thông điệp đổ lỗi cho bước gỡ và khuyên
        # khôi phục từ .bak — trong khi bản .bak vừa tạo hỏng y hệt.
        # Phải ĐÓNG NGOẶC: prefix trần còn khớp `[mcp_servers.powerbi-mcp-bridge-v2]` — server RIÊNG
        # của user — nên ta tưởng có block của mình rồi ghi đè + báo "đã gỡ" trong khi không gỡ gì.
        # (install.ps1 kiểm `$had` đã đóng ngoặc đúng từ đầu — copy sang cho khớp.)
        if ($text -notmatch '(?m)^\[mcp_servers\.powerbi-mcp-bridge(?:\]|\.)') {
            Info "$cfg không chứa '$name' -> không đụng vào file."
        } else {
            Backup-File $cfg
            # Phải khớp CẢ sub-table ([mcp_servers.powerbi-mcp-bridge.env]): nếu chỉ xóa block cha,
            # sub-table còn lại vẫn ngầm tạo server không có `command` -> Codex lỗi config.
            # Lookahead `^\[` (ngoặc ĐẦU DÒNG), KHÔNG dùng [^\[]*: dòng `args = ["-u", ...]`
            # có `[` giữa dòng, sẽ cắt cụt block và làm hỏng file.
            $new = [regex]::Replace($text, '(?ms)^\[mcp_servers\.powerbi-mcp-bridge(?:\.[^\]\r\n]+)?\].*?(?=^\[|\z)', '')
            Write-Utf8NoBom $cfg ($new.TrimEnd() + "`n")
            # validate parse sau khi ghi (tiêu chí audit: MỌI nhánh ghi config đều validate)
            if (Test-Path $venvPy) {
                & $venvPy -c "import tomllib,sys; tomllib.load(open(sys.argv[1],'rb'))" $cfg 2>$null
                if ($LASTEXITCODE -ne 0) { Err "config.toml KHÔNG parse được sau khi gỡ — khôi phục từ .bak.$Stamp!" }
                else { Ok "Đã gỡ block khỏi $cfg (validate OK)" }
            } else { Ok "Đã gỡ block khỏi $cfg" }
        }
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
$RepoDir = $PSScriptRoot
$skillNames += @("pbi-pipeline", "pbi-knowledge")   # tên trước v0.5.0 — gỡ cả bản cũ
# Codex nhận MỖI LỆNH là MỘT SKILL (xem Install-CommandsAsSkills). Không gỡ chúng thì
# sau khi user gỡ cài, Codex vẫn còn 8 skill sống nhăn gọi tool đã biến mất.
$cmdDirForSkills = Join-Path $RepoDir "plugins\powerbi-agent\commands"
if (Test-Path $cmdDirForSkills) {
    $skillNames += @(Get-ChildItem $cmdDirForSkills -Filter "*.md" |
        ForEach-Object { [System.IO.Path]::GetFileNameWithoutExtension($_.Name) })
}
foreach ($skRoot in $hostSkillRoots) {
    foreach ($n in $skillNames) {
        $p = Join-Path $skRoot $n
        if (-not (Test-Path $p)) { continue }
        # Skill-lenh (sinh tu commands/) co file danh dau. Skill goc cua repo thi khong,
        # nen chi ap luat "phai co marker" cho nhom sinh ra - tranh xoa skill rieng cua user
        # chi vi no trung ten voi mot lenh.
        # Cờ user đặt thắng mọi suy đoán (đối xứng với install.ps1).
        if (Test-Path (Join-Path $p $KeepFile)) {
            Info "Giữ nguyên '$p' (có $KeepFile)."
            continue
        }
        $mine = (Test-Path (Join-Path $p ".powerbi-agent-generated"))
        if (-not $mine) {
            # Ban cai truoc v0.6 chua co marker -> nhan dien bang frontmatter `name:` do ta ghi.
            # Khong co buoc nay thi nguoi nang cap khong bao gio go duoc skill cu.
            $skf = Join-Path $p "SKILL.md"
            $nameOk = $false
            if (Test-Path $skf) {
                # Đọc 40 dòng đầu — đủ vì `name:`/`x-generated-by:` luôn nằm ngay đầu frontmatter.
                $h = (Get-Content $skf -TotalCount 40 -Encoding UTF8 -ErrorAction SilentlyContinue) -join "`n"
                $nameOk = $h -match "(?m)^name:\s*$([regex]::Escape($n))\s*$"
                # Dau hieu ASCII la chinh. Van xuoi tieng Viet CHI dung cho skill-lenh doi
                # v0.5.x, va phai la CA CUM co ten lenh — cum ngan la cau noi thong thuong,
                # skill tieng Viet nao cung co the chua, va da tai hien duoc canh mat du lieu.
                $prov = ($h -match "(?m)^x-generated-by:\s*powerbi-agent\s*$") -or
                        ($h -match ([regex]::Escape("Gọi khi user nói `"chạy $n`"")))
                if ($nameOk -and $prov) { $mine = $true }
            }
            # Thu muc KHONG co SKILL.md: khong bao gio coi la cua ta (co the la thu muc
            # ghi chu/asset cua user). install.ps1 da theo luat nay, uninstall phai giong.
        }
        if (-not $mine) {
            Warn "Giữ lại '$p': không mang dấu sở hữu của powerbi-agent."
            if ($nameOk) {
                # Bản cài trước khi có marker: `name:` là của ta nhưng thiếu dấu hiệu thứ hai để
                # chắc chắn. Không đoán mò rồi xoá — chỉ nói rõ đường xử lý, vì đoán sai là mất
                # dữ liệu không hoàn tác được, còn giữ lại thì cùng lắm là thừa một thư mục.
                Warn "  Là bản cài cũ? -> chạy install.ps1 MỘT lần (nó tự dời bản cũ sang backup và"
                Warn "     cài bản có dấu sở hữu), rồi chạy lại uninstall.ps1. Hoặc xoá tay: $p"
            }
            continue
        }
        Remove-Item $p -Recurse -Force; Info "Xoá skill: $p"
    }
}
# Gỡ ĐỐI XỨNG với bước 4 của installer: Claude commands + agents, và `.codex\prompts` của
# bản CŨ (từ restructure, lệnh Codex được sinh thành SKILL chứ không còn là prompt — nhánh
# prompts giữ lại chỉ để dọn bản cũ). Gỡ mà chỉ dọn Claude thì người nâng cấp giữ nguyên 8
# lệnh sống nhăn sau khi tưởng đã gỡ sạch. (Antigravity tự sạch vì lệnh nằm trong skill folder
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
    # Sổ ghi skill-lệnh do Install-CommandsAsSkills tạo. Không xoá thì gỡ xong vẫn còn file
    # mồ côi, và lần cài sau nó là "sổ ghi của bản cài đã biến mất" — sai nguồn sự thật.
    $cxLedger = Join-Path $env:USERPROFILE ".codex\skills\.powerbi-agent-skills.txt"
    if (Test-Path $cxLedger) { Remove-Item $cxLedger -Force; Info "Xoá sổ ghi skill-lệnh: $cxLedger" }
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
# Backup do install.ps1 dọi sang KHÔNG bị xóa — có thể là dữ liệu của user. Nhưng "gỡ cài
# hoàn tất" mà để lại thư mục mang tên powerbi-agent không một lời nào thì user tưởng máy đã sạch.
foreach ($skRoot in $hostSkillRoots) {
    $bkParent = Split-Path $skRoot -Parent
    if (-not (Test-Path $bkParent)) { continue }
    foreach ($bk in @(Get-ChildItem $bkParent -Directory -Filter "powerbi-agent-backup-*" -ErrorAction SilentlyContinue)) {
        Info "Còn bản backup cũ: $($bk.FullName) — xem lại rồi tự xoá nếu không cần."
    }
}

if ($script:HadError) {
    Err "GỠ CHƯA SẠCH — xem các dòng [X] ở trên. Cấu hình gốc còn nguyên trong bản .bak.$Stamp."
    exit 1
}
Ok "Gỡ cài hoàn tất. Khởi động lại host để áp dụng. (Thư mục mã nguồn giữ nguyên.)"

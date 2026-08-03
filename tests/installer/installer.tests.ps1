# AUDIT HARNESS — chạy installer/uninstaller THẬT với USERPROFILE GIẢ.
# An toàn: mọi ghi đều vào $FakeHome; KHÔNG đụng config thật.
param(
  [string]$RepoRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
  [string]$PythonExe = ''
)
$ErrorActionPreference = 'Continue'
$S = Split-Path -Parent $MyInvocation.MyCommand.Path
# Duy nhat theo tien trinh: pytest cung goi harness nay, chay song song ma dung chung
# mot duong dan co dinh thi hai lan chay pha state cua nhau -> FAIL gia, rat kho truy.
$FakeHome = Join-Path $S "fakehome-$PID"
$venvPy = if ($PythonExe) { $PythonExe } else { Join-Path $RepoRoot '.venv\Scripts\python.exe' }
if (-not (Test-Path $venvPy)) { $venvPy = 'python' }
$results = @()

function Reset-Home {
    if (Test-Path $FakeHome) { Remove-Item $FakeHome -Recurse -Force }
    New-Item -ItemType Directory -Path (Join-Path $FakeHome '.codex') -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $FakeHome '.gemini\antigravity') -Force | Out-Null
}
function Run-Install([string]$HostsArg) {
    # PATH tối giản: KHÔNG có claude/codex CLI -> ép nhánh fallback; python/git vẫn cần? installer -SkipVenv không cần
    $env:USERPROFILE = $FakeHome
    & powershell -NoProfile -ExecutionPolicy Bypass -Command "
        `$env:USERPROFILE='$FakeHome';
        `$env:Path='C:\Windows\System32;C:\Windows'; `$env:POWERBI_INSTALL_PYTHON='$venvPy';
        & '$RepoRoot\install.ps1' -SkipVenv -Hosts $HostsArg" *>&1 | Out-String
}
function Run-Uninstall([string]$HostsArg) {
    & powershell -NoProfile -ExecutionPolicy Bypass -Command "
        `$env:USERPROFILE='$FakeHome';
        `$env:Path='C:\Windows\System32;C:\Windows'; `$env:POWERBI_INSTALL_PYTHON='$venvPy';
        & '$RepoRoot\uninstall.ps1' -Hosts $HostsArg" *>&1 | Out-String
}
function Toml-Valid([string]$p) {
    if (-not (Test-Path $p)) { return $false }
    & $venvPy -c "import tomllib,sys; tomllib.load(open(sys.argv[1],'rb'))" $p 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}
function Json-Valid([string]$p) {
    & $venvPy -c "import json,sys; json.load(open(sys.argv[1],encoding='utf-8-sig'))" $p 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}
function Add-Result([string]$case,[bool]$pass,[string]$note){
    $script:results += [pscustomobject]@{case=$case; pass=$pass; note=$note}
    Write-Host ("{0} {1} - {2}" -f ($(if($pass){'PASS'}else{'FAIL'}), $case, $note))
}

# ============ B. CODEX FUZZ — 8 ca, mỗi ca install 2 lần + tomllib + idempotent ============
$cfgPath = Join-Path $FakeHome '.codex\config.toml'
$cases = [ordered]@{
  'B1-empty'        = ''
  'B2-missing'      = $null   # không tạo file
  'B3-lf-only'      = "[model]`nname = `"x`"`n[mcp_servers.other]`ncommand = `"o`"`n"
  'B4-crlf'         = "[model]`r`nname = `"x`"`r`n[mcp_servers.other]`r`ncommand = `"o`"`r`n"
  'B5-block-cuoi-file' = "[model]`nname = `"x`"`n`n[mcp_servers.powerbi-mcp-bridge]`ncommand = `"OLD`"`nargs = [`"-u`", `"OLD.py`"]`n`n[mcp_servers.powerbi-mcp-bridge.env]`nPYTHONUNBUFFERED = `"1`""
  'B6-orphan-subtable' = "[model]`nname = `"x`"`n`n[mcp_servers.powerbi-mcp-bridge.env]`nPYTHONUNBUFFERED = `"1`"`n`n[tools]`nweb = true`n"
  'B7-bom'          = "BOM" # xử lý riêng
  'B8-prefix-v2'    = "[mcp_servers.powerbi-mcp-bridge-v2]`ncommand = `"KEEPME`"`nargs = [`"-u`", `"keep.py`"]`n`n[mcp_servers.powerbi-mcp-bridge]`ncommand = `"OLD`"`n`n[mcp_servers.powerbi-mcp-bridge.env]`nPYTHONUNBUFFERED = `"1`"`n`n[[profiles]]`nname = `"p1`"`n"
  'B9-duplicate-hong-that' = "[model]`nname = `"x`"`n`n[mcp_servers.powerbi-mcp-bridge]`ncommand = `"OLD`"`nenv = { PYTHONUNBUFFERED = `"1`" }`n`n[mcp_servers.powerbi-mcp-bridge.env]`nPYTHONUNBUFFERED = `"1`"`n"
}
foreach($k in $cases.Keys){
  Reset-Home
  if ($k -eq 'B2-missing') { Remove-Item $cfgPath -ErrorAction SilentlyContinue }
  elseif ($k -eq 'B7-bom') { [System.IO.File]::WriteAllText($cfgPath, "[model]`nname = `"x`"`n", (New-Object System.Text.UTF8Encoding($true))) }
  else { [System.IO.File]::WriteAllText($cfgPath, $cases[$k], (New-Object System.Text.UTF8Encoding($false))) }

  $null = Run-Install 'codex'
  $v1 = Toml-Valid $cfgPath
  $t1 = if(Test-Path $cfgPath){ Get-Content $cfgPath -Raw } else { '' }
  $null = Run-Install 'codex'
  $v2 = Toml-Valid $cfgPath
  $t2 = Get-Content $cfgPath -Raw
  $idem = ($t1 -eq $t2)
  $foreignOk = $true
  if ($k -in @('B3-lf-only','B4-crlf'))   { $foreignOk = ($t2 -match '\[mcp_servers\.other\]') -and ($t2 -match '\[model\]') }
  if ($k -eq 'B5-block-cuoi-file')        { $foreignOk = ($t2 -match '\[model\]') -and ($t2 -notmatch 'OLD') }
  if ($k -eq 'B6-orphan-subtable')        { $foreignOk = ($t2 -match '\[tools\]') }
  if ($k -eq 'B8-prefix-v2')              { $foreignOk = ($t2 -match 'KEEPME') -and ($t2 -match '\[\[profiles\]\]') -and ($t2 -notmatch '"OLD"') }
  if ($k -eq 'B9-duplicate-hong-that')    { $foreignOk = ($t2 -match '\[model\]') -and ($t2 -notmatch 'OLD') }
  # block ta phải đúng dạng sub-table, không inline env
  $blockOk = ($t2 -match '\[mcp_servers\.powerbi-mcp-bridge\]') -and ($t2 -match '\[mcp_servers\.powerbi-mcp-bridge\.env\]') -and ($t2 -notmatch 'env\s*=\s*\{')
  Add-Result $k ($v1 -and $v2 -and $idem -and $foreignOk -and $blockOk) "parse1=$v1 parse2=$v2 idem=$idem foreign=$foreignOk block=$blockOk"
}

# ============ B10: install -> uninstall -> install (codex) ============
Reset-Home
[System.IO.File]::WriteAllText($cfgPath, $cases['B8-prefix-v2'], (New-Object System.Text.UTF8Encoding($false)))
$null = Run-Install 'codex'; $null = Run-Uninstall 'codex'
$tU = Get-Content $cfgPath -Raw
$vU = Toml-Valid $cfgPath
$goneOk = ($tU -notmatch '\[mcp_servers\.powerbi-mcp-bridge\]') -and ($tU -notmatch 'powerbi-mcp-bridge\.env') -and ($tU -match 'KEEPME')
$null = Run-Install 'codex'
$vR = Toml-Valid $cfgPath
Add-Result 'B10-cycle' ($vU -and $goneOk -and $vR) "uninstallParse=$vU gone+keepV2=$goneOk reinstallParse=$vR"

# ============ A. CLAUDE fallback + ANTIGRAVITY merge (python-based, file THẬT copy) ============
Reset-Home
# fixture mô phỏng ~/.claude.json THẬT: có KEY RỖNG "" (làm ConvertFrom-Json PS 5.1 crash),
# tiếng Việt, mảng 1 phần tử — mọi thứ phải SỐNG SÓT nguyên vẹn sau merge
$claudeFx = '{"clientDataCacheSlots":{"slot":{"":"empty-key-must-survive","vi":"Tiếng Việt ơi"}},"oneItem":["only"],"mcpServers":{"other":{"command":"keep"}}}'
[System.IO.File]::WriteAllText((Join-Path $FakeHome '.claude.json'), $claudeFx, (New-Object System.Text.UTF8Encoding($false)))
$agFx = '{"mcpServers":{"other":{"command":"keep","args":["one"]}}}'
[System.IO.File]::WriteAllText((Join-Path $FakeHome '.gemini\antigravity\mcp_config.json'), $agFx, (New-Object System.Text.UTF8Encoding($false)))
$out1 = Run-Install 'claude,antigravity'
$cj = Join-Path $FakeHome '.claude.json'; $ag = Join-Path $FakeHome '.gemini\antigravity\mcp_config.json'
$cjV = Json-Valid $cj; $agV = Json-Valid $ag
$h1 = (Get-FileHash $cj).Hash + (Get-FileHash $ag).Hash
$null = Run-Install 'claude,antigravity'
$h2 = (Get-FileHash $cj).Hash + (Get-FileHash $ag).Hash
# python structural check: entry đúng + dữ liệu cũ còn (empty key survive!)
$chk = & $venvPy -c @"
import json,sys
cj=json.load(open(r'$cj',encoding='utf-8'))
ag=json.load(open(r'$ag',encoding='utf-8'))
e=cj['mcpServers']['powerbi-mcp-bridge']
assert e['type']=='stdio' and e['args'][0]=='-u' and e['env']['PYTHONUNBUFFERED']=='1', 'schema claude sai'
assert ag['mcpServers']['powerbi-mcp-bridge']['command'], 'schema ag sai'
def fek(o):
    if isinstance(o,dict):
        return any(k=='' for k in o)+sum(fek(v) for v in o.values())
    if isinstance(o,list): return sum(fek(v) for v in o)
    return 0
assert fek(cj)>0, 'empty key BIEN MAT -> mat du lieu'
assert 'clientDataCacheSlots' in cj, 'section cu mat'
print('STRUCT_OK')
"@ 2>&1
Add-Result 'A-merge-python' ($cjV -and $agV -and ($h1 -eq $h2) -and ("$chk" -match 'STRUCT_OK')) "jsonValid=$cjV/$agV idem=$($h1 -eq $h2) struct=$chk"

# ============ C. SKILL COPY drift + uninstall đối xứng ============
Reset-Home
$null = Run-Install 'claude'
$sk = Join-Path $FakeHome '.claude\skills'
$n1 = (Get-ChildItem $sk -Directory).Count
$stale = Join-Path $sk 'powerbi-mcp\STALE-OLD-FILE.md'
'old' | Set-Content $stale
$null = Run-Install 'claude'
$staleSurvives = Test-Path $stale
# Suy số lệnh kỳ vọng TỪ NGUỒN, không hardcode: thêm/bớt lệnh không được làm test đỏ giả.
$cmdSrcDir  = Join-Path $RepoRoot 'plugins\powerbi-agent\commands'
$expectCmds = @(Get-ChildItem $cmdSrcDir -Filter '*.md').Count
$cmds = (Get-ChildItem (Join-Path $FakeHome '.claude\commands') -Filter 'powerbi-*.md' -ErrorAction SilentlyContinue).Count
Add-Result 'C-skill-copy' ($n1 -eq 4 -and $cmds -eq $expectCmds -and -not $staleSurvives) "skills=$n1/4 cmds=$cmds/$expectCmds staleSauLan2=$staleSurvives (true=DRIFT)"
# Nội dung skill, không chỉ số lượng: mẫu tài liệu (trụ 4) phải đi theo skill sang host.
# Thiếu assertion này thì đổi tên document-templates/ có thể hỏng mà test vẫn xanh.
$kpim    = Join-Path $sk 'kpim-analysis'
$docTpl  = Join-Path $kpim 'document-templates\PROJECT.md'
$oldTpl  = Join-Path $kpim 'templates'
Add-Result 'C-skill-content' ((Test-Path $docTpl) -and -not (Test-Path $oldTpl)) `
    "document-templates/PROJECT.md=$(Test-Path $docTpl) folderCu_templates=$(Test-Path $oldTpl) (true=CHUA_DOI_TEN)"
# Nâng cấp từ bản < 0.5.0: lệnh cũ họ "pbi-*" phải bị dọn, không được để lại 12 lệnh mồ côi.
$cmdDir = Join-Path $FakeHome '.claude\commands'
'legacy' | Set-Content (Join-Path $cmdDir 'pbi-new.md')
'legacy' | Set-Content (Join-Path $cmdDir 'pbi-setup.md')
$null = Run-Install 'claude'
# Xác sống chiều ngược lại: lệnh ta TỪNG cài rồi bị bỏ khỏi repo phải biến mất khỏi host.
# Giả lập bằng cách thêm 1 tên lạ vào sổ ghi + tạo file tương ứng.
'powerbi-da-bo.md' | Add-Content (Join-Path $cmdDir '.powerbi-agent-installed.txt')
'stale' | Set-Content (Join-Path $cmdDir 'powerbi-da-bo.md')
# Lệnh RIÊNG của user cùng tiền tố powerbi- KHÔNG được đụng tới.
'cua toi' | Set-Content (Join-Path $cmdDir 'powerbi-cua-toi.md')
$null = Run-Install 'claude'
$driftGone = -not (Test-Path (Join-Path $cmdDir 'powerbi-da-bo.md'))
$userKept  = Test-Path (Join-Path $cmdDir 'powerbi-cua-toi.md')
# -Filter 'pbi-*.md' KHÔNG khớp 'powerbi-*.md' (wildcard khớp từ đầu tên) — đã kiểm nghiệm.
$legacyLeft = @(Get-ChildItem $cmdDir -Filter 'pbi-*.md' -ErrorAction SilentlyContinue).Count
Add-Result 'C-cmd-drift-and-user-files' ($driftGone -and $userKept) `
    "lenhDaBo_bienMat=$driftGone lenhRiengCuaUser_conNguyen=$userKept"
Remove-Item (Join-Path $cmdDir 'powerbi-cua-toi.md') -Force -ErrorAction SilentlyContinue
$newCount = @(Get-ChildItem $cmdDir -Filter 'powerbi-*.md' -ErrorAction SilentlyContinue).Count
Add-Result 'C-legacy-cmd-cleanup' ($legacyLeft -eq 0 -and $newCount -eq $expectCmds) `
    "lenhCu_pbi_conLai=$legacyLeft (phai=0) lenhMoi=$newCount/$expectCmds"

# Bước 4 mới: lệnh phải tới CẢ 3 host, không chỉ Claude (yêu cầu #5/#6).
Reset-Home
$null = Run-Install 'codex'
# Codex: moi lenh la MOT SKILL (khong phai prompts/ - o do phai goi /prompts:<ten>).
$codexDir    = Join-Path $FakeHome '.codex\skills'
$codexAll    = @(Get-ChildItem $codexDir -Directory -ErrorAction SilentlyContinue)
$codexCmdSk  = @($codexAll | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } |
                 Where-Object { (Get-Content (Join-Path $_.FullName 'SKILL.md') -Raw) -match '(?m)^name:\s*powerbi-' })
$codexNoPrompts = -not (Test-Path (Join-Path $FakeHome '.codex\prompts'))
Add-Result 'D-codex-commands' ($codexAll.Count -eq (4 + $expectCmds) -and $codexNoPrompts) `
    "skillTong=$($codexAll.Count)/$(4 + $expectCmds) khongDungPrompts=$codexNoPrompts"

Reset-Home
$null = Run-Install 'antigravity'
$agCmds = @(Get-ChildItem (Join-Path $FakeHome '.gemini\antigravity\skills\powerbi-knowledge\commands') -Filter 'powerbi-*.md' -ErrorAction SilentlyContinue).Count
Add-Result 'D-antigravity-commands' ($agCmds -eq $expectCmds) "lenhTrongSkill=$agCmds/$expectCmds"

# -Only plugin: cài lại phần quy trình mà KHÔNG đụng venv/MCP config.
Reset-Home
$null = Run-Install 'claude'
$cfgBefore = Get-Content (Join-Path $FakeHome '.claude.json') -Raw -ErrorAction SilentlyContinue
$bakBefore = @(Get-ChildItem $FakeHome -Filter '.claude.json.bak.*' -Force -ErrorAction SilentlyContinue).Count
Remove-Item (Join-Path $FakeHome '.claude\commands\powerbi-help.md') -Force -ErrorAction SilentlyContinue
$null = & powershell -NoProfile -ExecutionPolicy Bypass -Command "
    `$env:USERPROFILE='$FakeHome'; `$env:POWERBI_INSTALL_PYTHON='$venvPy';
    & '$RepoRoot\install.ps1' -Hosts claude -Only plugin" *>&1
$restored = Test-Path (Join-Path $FakeHome '.claude\commands\powerbi-help.md')
$cfgAfter = Get-Content (Join-Path $FakeHome '.claude.json') -Raw -ErrorAction SilentlyContinue
# So sánh nội dung config là VÔ NGHĨA ở đây: đăng ký MCP vốn idempotent (ca A-merge-python đã
# chứng minh), nên dù -Only plugin có chạy nhầm Register-Claude thì file vẫn y hệt. Bằng chứng
# thật là KHÔNG có file .bak mới — Backup-File đóng dấu mỗi lần đăng ký.
$bakAfter = @(Get-ChildItem $FakeHome -Filter '.claude.json.bak.*' -Force -ErrorAction SilentlyContinue).Count
Add-Result 'D-only-plugin' ($restored -and $bakAfter -eq $bakBefore -and $cfgBefore -eq $cfgAfter) `
    "lenhDuocPhucHoi=$restored soBanBak=$bakBefore->$bakAfter (phai bang nhau: tang = da dang ky lai MCP)"

# Nâng cấp từ <0.5.0: skill mang tên cũ phải BIẾN MẤT, không được nằm lại thành xác sống —
# bản cũ chứa bảng định tuyến trỏ tới các lệnh mà chính installer vừa xoá.
Reset-Home
$skDir = Join-Path $FakeHome '.claude\skills'
foreach ($old in @('pbi-pipeline','pbi-knowledge')) {
    New-Item -ItemType Directory -Path (Join-Path $skDir $old) -Force | Out-Null
    'legacy' | Set-Content (Join-Path $skDir "$old\SKILL.md")
}
$null = Run-Install 'claude'
$zombies = @(Get-ChildItem $skDir -Directory -EA SilentlyContinue | Where-Object { $_.Name -like 'pbi-*' -and $_.Name -notlike 'powerbi-*' }).Count
$total   = @(Get-ChildItem $skDir -Directory -EA SilentlyContinue).Count
Add-Result 'D-upgrade-no-zombie-skill' ($zombies -eq 0 -and $total -eq 4) `
    "skillCu_conLai=$zombies (phai=0) tongSkill=$total/4"

# Nang cap tu ban CHUA CO marker: skill-lenh cu phai duoc cap nhat VA go duoc.
# Neu doi hoi marker tuyet doi thi nguoi nang cap ket vinh vien (khong update, khong go).
Reset-Home
$cx = Join-Path $FakeHome '.codex\skills\powerbi-help'
New-Item -ItemType Directory -Path $cx -Force | Out-Null
Set-Content (Join-Path $cx 'SKILL.md') "---`nname: powerbi-help`ndescription: ban cu`n---`nNOI DUNG CU"
$null = Run-Install 'codex'
$updated = -not ((Get-Content (Join-Path $cx 'SKILL.md') -Raw) -match 'NOI DUNG CU')
$hasMarker = Test-Path (Join-Path $cx '.powerbi-agent-generated')
$null = Run-Uninstall 'codex'
$removed = -not (Test-Path $cx)
Add-Result 'D-upgrade-marker-migration' ($updated -and $hasMarker -and $removed) `
    "capNhat=$updated coMarker=$hasMarker goDuoc=$removed"

# Skill RIENG cua user trung ten: khong duoc dung toi, ca luc cai lan luc go.
Reset-Home
$mine = Join-Path $FakeHome '.codex\skills\powerbi-help'
New-Item -ItemType Directory -Path $mine -Force | Out-Null
Set-Content (Join-Path $mine 'SKILL.md') "---`nname: skill-rieng-cua-toi`n---`nCUA TOI"
$null = Run-Install 'codex'
$keptOnInstall = (Get-Content (Join-Path $mine 'SKILL.md') -Raw) -match 'CUA TOI'
$null = Run-Uninstall 'codex'
$keptOnUninstall = Test-Path (Join-Path $mine 'SKILL.md')
Add-Result 'D-respects-user-skill' ($keptOnInstall -and $keptOnUninstall) `
    "conNguyenSauCai=$keptOnInstall conNguyenSauGo=$keptOnUninstall"

# -SkipHosts phải giữ đúng hợp đồng: KHÔNG đụng thư mục host nào (kể cả bước 4).
# Gọi trực tiếp nên PHẢI tự set env — Run-Install mới là chỗ set USERPROFILE giả.
Reset-Home
$env:USERPROFILE = $FakeHome
$null = & powershell -NoProfile -ExecutionPolicy Bypass -Command "
    `$env:USERPROFILE='$FakeHome'; `$env:POWERBI_INSTALL_PYTHON='$venvPy';
    & '$RepoRoot\install.ps1' -Hosts claude -SkipVenv -SkipHosts" *>&1
$touched = (Test-Path (Join-Path $FakeHome '.claude\skills')) -or (Test-Path (Join-Path $FakeHome '.claude\commands'))
Add-Result 'D-skiphosts-contract' (-not $touched) "daDungThuMucHost=$touched (phai=False)"

# Gỡ phải ĐỐI XỨNG: Codex prompts + Claude agents cũng phải sạch, không chỉ Claude commands.
Reset-Home
$null = Run-Install 'claude'
$null = Run-Install 'codex'
$null = Run-Uninstall 'claude'
$null = Run-Uninstall 'codex'
$leftPrompts = @(Get-ChildItem (Join-Path $FakeHome '.codex\skills') -Directory -ErrorAction SilentlyContinue).Count
$leftAgents  = @(Get-ChildItem (Join-Path $FakeHome '.claude\agents') -Filter 'powerbi-*.md' -ErrorAction SilentlyContinue).Count
Add-Result 'D-uninstall-all-hosts' ($leftPrompts -eq 0 -and $leftAgents -eq 0) `
    "codexSkillConLai=$leftPrompts claudeAgentsConLai=$leftAgents (deu phai=0)"

# Sổ ghi rác không được xoá lệnh riêng của user, cũng không được giết installer.
Reset-Home
$null = Run-Install 'claude'
$cd = Join-Path $FakeHome '.claude\commands'
'cua toi' | Set-Content (Join-Path $cd 'powerbi-rieng.md')
Set-Content (Join-Path $cd '.powerbi-agent-installed.txt') -Value @('powerbi-*.md', '..\..\ngoai-thu-muc.md', 'powerbi-help.md')
'ngoai' | Set-Content (Join-Path $FakeHome 'ngoai-thu-muc.md')
$null = Run-Install 'claude'
$userSafe = Test-Path (Join-Path $cd 'powerbi-rieng.md')
$outsideSafe = Test-Path (Join-Path $FakeHome 'ngoai-thu-muc.md')
$stillInstalled = @(Get-ChildItem $cd -Filter 'powerbi-*.md' -ErrorAction SilentlyContinue).Count
Add-Result 'D-ledger-hostile' ($userSafe -and $outsideSafe -and $stillInstalled -ge $expectCmds) `
    "lenhRieng=$userSafe fileNgoaiThuMuc=$outsideSafe daCaiLai=$stillInstalled"

# Các ca ở trên cố tình để lại state bẩn (sổ ghi rác, lệnh riêng của user). Dựng lại sạch
# trước ca gỡ cuối, nếu không nó đo nhầm state của ca trước và đỏ giả.
Reset-Home
$null = Run-Install 'claude'
$null = Run-Uninstall 'claude'
$left = @(Get-ChildItem $sk -Directory -ErrorAction SilentlyContinue).Name -join ','
$cmdsLeft = @(Get-ChildItem (Join-Path $FakeHome '.claude\commands') -Filter 'powerbi-*.md' -ErrorAction SilentlyContinue).Count
Add-Result 'C-uninstall-symmetric' ($left -eq '' -and $cmdsLeft -eq 0) "skillsConLai='$left' cmdsConLai=$cmdsLeft"

if (Test-Path $FakeHome) { Remove-Item $FakeHome -Recurse -Force }  # tự dọn residue
Write-Host "`n===== TONG KET ====="
$results | Format-Table -AutoSize | Out-String | Write-Host

# Exit code PHAI phan anh ket qua. Truoc day in ca bang roi luon exit 0 -> chay doc lap
# (hoac trong CI khong qua pytest) thay 20 FAIL ma van bao thanh cong.
$failed = @($results | Where-Object { -not $_.pass })
if ($failed.Count -gt 0) {
    Write-Host "FAILED: $($failed.Count)/$($results.Count) ca" -ForegroundColor Red
    exit 1
}
Write-Host "OK: $($results.Count)/$($results.Count) ca" -ForegroundColor Green
exit 0

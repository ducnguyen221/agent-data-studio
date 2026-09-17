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
function FileHash([string]$p) {
    # KHONG dung Get-FileHash: tren runner CI cmdlet nay khong resolve duoc
    # ("CommandNotFoundException") -> harness chet giua chung. .NET thuan luon co.
    if (-not (Test-Path $p)) { return '' }
    $md5 = [System.Security.Cryptography.MD5]::Create()
    return [System.BitConverter]::ToString($md5.ComputeHash([System.IO.File]::ReadAllBytes($p)))
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
$h1 = (FileHash $cj) + (FileHash $ag)
$null = Run-Install 'claude,antigravity'
$h2 = (FileHash $cj) + (FileHash $ag)
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
$stale = Join-Path $sk 'pbi-analysis\STALE-OLD-FILE.md'
'old' | Set-Content $stale
$null = Run-Install 'claude'
$staleSurvives = Test-Path $stale
# Suy số lệnh kỳ vọng TỪ NGUỒN, không hardcode: thêm/bớt lệnh không được làm test đỏ giả.
$cmdSrcDir  = Join-Path $RepoRoot 'commands'
$expectCmds = @(Get-ChildItem $cmdSrcDir -Filter '*.md').Count
# Suy CA so skill tu nguon: them 1 skill vao repo khong duoc lam 3 ca do gia.
# Chi dem thu muc CO SKILL.md — installer chi cai dung nhom do (skill dang viet do dang thi bo qua).
$expectSkills = @(Get-ChildItem (Join-Path $RepoRoot 'skills') -Directory |
                  Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') }).Count
$cmds = (Get-ChildItem (Join-Path $FakeHome '.claude\commands') -Filter 'pbi-*.md' -ErrorAction SilentlyContinue).Count
Add-Result 'C-skill-copy' ($n1 -eq $expectSkills -and $cmds -eq $expectCmds -and -not $staleSurvives) "skills=$n1/$expectSkills cmds=$cmds/$expectCmds staleSauLan2=$staleSurvives (true=DRIFT)"
# Nội dung skill, không chỉ số lượng: CẢ thư mục skill (scripts\...) phải sang host, không chỉ SKILL.md.
# Mẫu tài liệu nay ở templates\documents\ gốc repo, KHÔNG còn đi theo skill -> không được lọt vào skill.
$disc    = Join-Path $sk 'data-discovery'
$script1 = Join-Path $disc 'scripts\generate_mindmap_html.py'
$oldTpl  = Join-Path $disc 'document-templates'
Add-Result 'C-skill-content' ((Test-Path $script1) -and -not (Test-Path $oldTpl)) `
    "data-discovery/scripts/generate_mindmap_html.py=$(Test-Path $script1) document-templatesTrongSkill=$(Test-Path $oldTpl) (phai=False)"
# Nâng cấp từ bản < 0.7: lệnh cũ họ "powerbi-*" phải bị dọn, không được để lại 16 lệnh mồ côi.
$cmdDir = Join-Path $FakeHome '.claude\commands'
'legacy' | Set-Content (Join-Path $cmdDir 'powerbi-new.md')
'legacy' | Set-Content (Join-Path $cmdDir 'powerbi-setup.md')
$null = Run-Install 'claude'
# Xác sống chiều ngược lại: lệnh ta TỪNG cài rồi bị bỏ khỏi repo phải biến mất khỏi host.
# Giả lập bằng cách thêm 1 tên lạ vào sổ ghi + tạo file tương ứng.
'pbi-da-bo.md' | Add-Content (Join-Path $cmdDir '.powerbi-agent-installed.txt')
'stale' | Set-Content (Join-Path $cmdDir 'pbi-da-bo.md')
# Lệnh RIÊNG của user cùng tiền tố pbi- KHÔNG được đụng tới.
'cua toi' | Set-Content (Join-Path $cmdDir 'pbi-cua-toi.md')
$null = Run-Install 'claude'
$driftGone = -not (Test-Path (Join-Path $cmdDir 'pbi-da-bo.md'))
$userKept  = Test-Path (Join-Path $cmdDir 'pbi-cua-toi.md')
# -Filter 'pbi-*.md' KHÔNG khớp 'powerbi-*.md' (wildcard khớp từ đầu tên) — đã kiểm nghiệm.
$legacyLeft = @(Get-ChildItem $cmdDir -Filter 'powerbi-*.md' -ErrorAction SilentlyContinue).Count
Add-Result 'C-cmd-drift-and-user-files' ($driftGone -and $userKept) `
    "lenhDaBo_bienMat=$driftGone lenhRiengCuaUser_conNguyen=$userKept"
Remove-Item (Join-Path $cmdDir 'pbi-cua-toi.md') -Force -ErrorAction SilentlyContinue
$newCount = @(Get-ChildItem $cmdDir -Filter 'pbi-*.md' -ErrorAction SilentlyContinue).Count
Add-Result 'C-legacy-cmd-cleanup' ($legacyLeft -eq 0 -and $newCount -eq $expectCmds) `
    "lenhCu_powerbi_conLai=$legacyLeft (phai=0) lenhMoi=$newCount/$expectCmds"

# Bước 4 mới: lệnh phải tới CẢ 3 host, không chỉ Claude (yêu cầu #5/#6).
Reset-Home
$null = Run-Install 'codex'
# Codex: moi lenh la MOT SKILL (khong phai prompts/ - o do phai goi /prompts:<ten>).
$codexDir    = Join-Path $FakeHome '.codex\skills'
$codexAll    = @(Get-ChildItem $codexDir -Directory -ErrorAction SilentlyContinue)
$codexCmdSk  = @($codexAll | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } |
                 Where-Object { (Get-Content (Join-Path $_.FullName 'SKILL.md') -Raw) -match '(?m)^name:\s*pbi-' })
$codexNoPrompts = -not (Test-Path (Join-Path $FakeHome '.codex\prompts'))
Add-Result 'D-codex-commands' ($codexAll.Count -eq ($expectSkills + $expectCmds) -and $codexNoPrompts) `
    "skillTong=$($codexAll.Count)/$($expectSkills + $expectCmds) khongDungPrompts=$codexNoPrompts"

Reset-Home
$null = Run-Install 'antigravity'
$agCmds = @(Get-ChildItem (Join-Path $FakeHome '.gemini\antigravity\skills\pbi-knowledge\commands') -Filter 'pbi-*.md' -ErrorAction SilentlyContinue).Count
Add-Result 'D-antigravity-commands' ($agCmds -eq $expectCmds) "lenhTrongSkill=$agCmds/$expectCmds"

# -Only plugin: cài lại phần quy trình mà KHÔNG đụng venv/MCP config.
Reset-Home
$null = Run-Install 'claude'
$cfgBefore = Get-Content (Join-Path $FakeHome '.claude.json') -Raw -ErrorAction SilentlyContinue
$bakBefore = @(Get-ChildItem $FakeHome -Filter '.claude.json.bak.*' -Force -ErrorAction SilentlyContinue).Count
Remove-Item (Join-Path $FakeHome '.claude\commands\pbi-help.md') -Force -ErrorAction SilentlyContinue
$null = & powershell -NoProfile -ExecutionPolicy Bypass -Command "
    `$env:USERPROFILE='$FakeHome'; `$env:POWERBI_INSTALL_PYTHON='$venvPy';
    & '$RepoRoot\install.ps1' -Hosts claude -Only plugin" *>&1
$restored = Test-Path (Join-Path $FakeHome '.claude\commands\pbi-help.md')
$cfgAfter = Get-Content (Join-Path $FakeHome '.claude.json') -Raw -ErrorAction SilentlyContinue
# So sánh nội dung config là VÔ NGHĨA ở đây: đăng ký MCP vốn idempotent (ca A-merge-python đã
# chứng minh), nên dù -Only plugin có chạy nhầm Register-Claude thì file vẫn y hệt. Bằng chứng
# thật là KHÔNG có file .bak mới — Backup-File đóng dấu mỗi lần đăng ký.
$bakAfter = @(Get-ChildItem $FakeHome -Filter '.claude.json.bak.*' -Force -ErrorAction SilentlyContinue).Count
Add-Result 'D-only-plugin' ($restored -and $bakAfter -eq $bakBefore -and $cfgBefore -eq $cfgAfter) `
    "lenhDuocPhucHoi=$restored soBanBak=$bakBefore->$bakAfter (phai bang nhau: tang = da dang ky lai MCP)"

# Nâng cấp từ bản < 0.7: skill mang tên cũ phải BIẾN MẤT khỏi skills\, không được nằm lại thành
# xác sống — bản cũ chứa bảng định tuyến trỏ tới các lệnh/skill mà chính installer vừa đổi tên.
# Bản do ta sinh (có marker) -> xoá; bản không rõ chủ (pbi-pipeline, không marker) -> dời sang bên.
Reset-Home
$skDir = Join-Path $FakeHome '.claude\skills'
$oldNames = @('powerbi-mcp','kpim-analysis','pbi-pipeline')
foreach ($old in $oldNames) {
    New-Item -ItemType Directory -Path (Join-Path $skDir $old) -Force | Out-Null
    'legacy' | Set-Content (Join-Path $skDir "$old\SKILL.md")
    if ($old -ne 'pbi-pipeline') { 'powerbi-agent' | Set-Content (Join-Path $skDir "$old\.powerbi-agent-generated") }
}
$null = Run-Install 'claude'
$zombies = @(Get-ChildItem $skDir -Directory -EA SilentlyContinue | Where-Object { $oldNames -contains $_.Name }).Count
$total   = @(Get-ChildItem $skDir -Directory -EA SilentlyContinue).Count
Add-Result 'D-upgrade-no-zombie-skill' ($zombies -eq 0 -and $total -eq $expectSkills) `
    "skillCu_conLai=$zombies (phai=0) tongSkill=$total/$expectSkills"
# Tên HIỆN HÀNH (pbi-knowledge) không được nằm trong danh sách dọn: cài lần 2 phải không dời gì.
$bkBefore = @(Get-ChildItem (Join-Path $FakeHome '.claude') -Directory -Filter 'powerbi-agent-backup-*' -EA SilentlyContinue).Count
$null = Run-Install 'claude'
$bkAfter  = @(Get-ChildItem (Join-Path $FakeHome '.claude') -Directory -Filter 'powerbi-agent-backup-*' -EA SilentlyContinue).Count
$knStill  = Test-Path (Join-Path $skDir 'pbi-knowledge\.powerbi-agent-generated')
Add-Result 'D-reinstall-keeps-current-skills' ($bkAfter -eq $bkBefore -and $knStill) `
    "soBackup=$bkBefore->$bkAfter (phai bang nhau) pbiKnowledgeConNguyen=$knStill"

# Lệnh + agent họ tên cũ do ta sinh (powerbi-*) phải biến mất sau khi cài bản mới.
Reset-Home
$cxOld = Join-Path $FakeHome '.codex\skills\powerbi-help'
New-Item -ItemType Directory -Path $cxOld -Force | Out-Null
"---`nname: powerbi-help`nx-generated-by: powerbi-agent`n---`nCU" | Set-Content (Join-Path $cxOld 'SKILL.md')
'powerbi-agent' | Set-Content (Join-Path $cxOld '.powerbi-agent-generated')
$agDir = Join-Path $FakeHome '.claude\agents'
New-Item -ItemType Directory -Path $agDir -Force | Out-Null
'cu' | Set-Content (Join-Path $agDir 'powerbi-knowledge-curator.md')
$null = Run-Install 'codex'
$null = Run-Install 'claude'
$cxGone = -not (Test-Path $cxOld)
$agGone = -not (Test-Path (Join-Path $agDir 'powerbi-knowledge-curator.md'))
$agNew  = Test-Path (Join-Path $agDir 'pbi-knowledge-curator.md')
Add-Result 'D-legacy-command-skill-and-agent-renamed' ($cxGone -and $agGone -and $agNew) `
    "skillLenhCu_bienMat=$cxGone agentCu_bienMat=$agGone agentMoi=$agNew"

# Nang cap tu ban CHUA CO marker: skill-lenh cu phai duoc cap nhat VA go duoc.
# Neu doi hoi marker tuyet doi thi nguoi nang cap ket vinh vien (khong update, khong go).
Reset-Home
$cx = Join-Path $FakeHome '.codex\skills\pbi-help'
New-Item -ItemType Directory -Path $cx -Force | Out-Null
# Fixture phai giong HET thu ban v0.5.x SINH RA — ke ca dong mo ta dac trung,
# vi do la dau van thu hai dung de nhan dien quyen so huu.
# Ghi UTF-8 TUONG MINH: Set-Content mac dinh ANSI tren PS 5.1, tieng Viet se lech.
[System.IO.File]::WriteAllText((Join-Path $cx 'SKILL.md'),
  "---`nname: pbi-help`ndescription: >`n  ban cu`n  Gọi khi user nói `"chạy pbi-help`" abc.`n---`nNOI DUNG CU",
  (New-Object System.Text.UTF8Encoding($false)))
$null = Run-Install 'codex'
$updated = -not ((Get-Content (Join-Path $cx 'SKILL.md') -Raw) -match 'NOI DUNG CU')
$hasMarker = Test-Path (Join-Path $cx '.powerbi-agent-generated')
$null = Run-Uninstall 'codex'
$removed = -not (Test-Path $cx)
Add-Result 'D-upgrade-marker-migration' ($updated -and $hasMarker -and $removed) `
    "capNhat=$updated coMarker=$hasMarker goDuoc=$removed"

# Skill user trung CA TEN (name: pbi-help) nhung khong phai ban ta sinh ra.
# Chi doi moi dong `name:` la khong du — day la ca lam mat du lieu user.
Reset-Home
$same = Join-Path $FakeHome '.codex\skills\pbi-help'
New-Item -ItemType Directory -Path $same -Force | Out-Null
Set-Content (Join-Path $same 'SKILL.md') "---`nname: pbi-help`ndescription: ban TU VIET cua toi`n---`nGHI CHU RIENG"
Set-Content (Join-Path $same 'ghi-chu.md') "tai lieu rieng cua user"
$null = Run-Install 'codex'
$bodyKept = (Get-Content (Join-Path $same 'SKILL.md') -Raw) -match 'GHI CHU RIENG'
$sideKept = Test-Path (Join-Path $same 'ghi-chu.md')
Add-Result 'D-same-name-user-skill-safe' ($bodyKept -and $sideKept) `
    "noiDungConNguyen=$bodyKept fileKemConNguyen=$sideKept"

# Skill RIENG cua user trung ten: khong duoc dung toi, ca luc cai lan luc go.
Reset-Home
$mine = Join-Path $FakeHome '.codex\skills\pbi-help'
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

# Config chi chua server KHAC co ten BAT DAU BANG ten cua ta (powerbi-mcp-bridge-v2):
# prefix-match khong dong ngoac lam uninstall tuong co block cua minh -> ghi de + bao gia "da go".
Reset-Home
$onlyV2 = "[mcp_servers.powerbi-mcp-bridge-v2]`ncommand = `"KEEPME`"`nargs = [`"-u`", `"keep.py`"]`n"
[System.IO.File]::WriteAllText($cfgPath, $onlyV2, (New-Object System.Text.UTF8Encoding($false)))
$hashTruoc = (FileHash $cfgPath)
$null = Run-Uninstall 'codex'
$khongDungFile = ((FileHash $cfgPath) -eq $hashTruoc)
$khongTaoBak   = @(Get-ChildItem (Split-Path $cfgPath -Parent) -Filter 'config.toml.bak.*').Count -eq 0
Add-Result 'D-uninstall-leaves-lookalike-alone' ($khongDungFile -and $khongTaoBak) `
    "fileNguyenVen=$khongDungFile khongTaoBakThua=$khongTaoBak"

# So ghi skill-lenh Codex phai bien mat cung voi skill (truoc day mo coi lai sau khi go).
Reset-Home
$null = Run-Install 'codex'
$null = Run-Uninstall 'codex'
$soGhiConLai = Test-Path (Join-Path $FakeHome '.codex\skills\.powerbi-agent-skills.txt')
Add-Result 'D-uninstall-removes-skill-ledger' (-not $soGhiConLai) "soGhiConLai=$soGhiConLai (phai=False)"

# Gỡ phải ĐỐI XỨNG: Codex prompts + Claude agents cũng phải sạch, không chỉ Claude commands.
Reset-Home
$null = Run-Install 'claude'
$null = Run-Install 'codex'
$null = Run-Uninstall 'claude'
$null = Run-Uninstall 'codex'
$leftPrompts = @(Get-ChildItem (Join-Path $FakeHome '.codex\skills') -Directory -ErrorAction SilentlyContinue).Count
$leftAgents  = @(Get-ChildItem (Join-Path $FakeHome '.claude\agents') -Filter '*.md' -ErrorAction SilentlyContinue).Count
Add-Result 'D-uninstall-all-hosts' ($leftPrompts -eq 0 -and $leftAgents -eq 0) `
    "codexSkillConLai=$leftPrompts claudeAgentsConLai=$leftAgents (deu phai=0)"

# Sổ ghi rác không được xoá lệnh riêng của user, cũng không được giết installer.
Reset-Home
$null = Run-Install 'claude'
$cd = Join-Path $FakeHome '.claude\commands'
'cua toi' | Set-Content (Join-Path $cd 'pbi-rieng.md')
Set-Content (Join-Path $cd '.powerbi-agent-installed.txt') -Value @('pbi-*.md', '..\..\ngoai-thu-muc.md', 'pbi-help.md')
'ngoai' | Set-Content (Join-Path $FakeHome 'ngoai-thu-muc.md')
$null = Run-Install 'claude'
$userSafe = Test-Path (Join-Path $cd 'pbi-rieng.md')
$outsideSafe = Test-Path (Join-Path $FakeHome 'ngoai-thu-muc.md')
$stillInstalled = @(Get-ChildItem $cd -Filter 'pbi-*.md' -ErrorAction SilentlyContinue).Count
Add-Result 'D-ledger-hostile' ($userSafe -and $outsideSafe -and $stillInstalled -ge $expectCmds) `
    "lenhRieng=$userSafe fileNgoaiThuMuc=$outsideSafe daCaiLai=$stillInstalled"

# Các ca ở trên cố tình để lại state bẩn (sổ ghi rác, lệnh riêng của user). Dựng lại sạch
# trước ca gỡ cuối, nếu không nó đo nhầm state của ca trước và đỏ giả.
Reset-Home
$null = Run-Install 'claude'
$null = Run-Uninstall 'claude'
$left = @(Get-ChildItem $sk -Directory -ErrorAction SilentlyContinue).Name -join ','
$cmdsLeft = @(Get-ChildItem (Join-Path $FakeHome '.claude\commands') -Filter 'pbi-*.md' -ErrorAction SilentlyContinue).Count
Add-Result 'C-uninstall-symmetric' ($left -eq '' -and $cmdsLeft -eq 0) "skillsConLai='$left' cmdsConLai=$cmdsLeft"

# Nâng cấp từ bản cài THẬT trước khi có dấu sở hữu (SKILL.md của cb94d27: có `name:` do ta ghi,
# KHÔNG có `x-generated-by`, KHÔNG có file marker — Install-Skill xưa nay không hề ghi marker).
# Không có ca này thì luật two-signal làm skill gốc kẹt vĩnh viễn: install bỏ qua, uninstall giữ lại.
# Từ v0.7 skill đó đổi tên powerbi-knowledge -> pbi-knowledge: bản cũ (không marker) phải bị dời
# sang bên, bản mới được cài ở tên mới.
Reset-Home
$legacySkill = Join-Path $FakeHome '.codex\skills\powerbi-knowledge'
$newSkill    = Join-Path $FakeHome '.codex\skills\pbi-knowledge'
New-Item -ItemType Directory -Path $legacySkill -Force | Out-Null
$legacyBody = & git -C $RepoRoot show 'cb94d27:plugins/powerbi-agent/skills/powerbi-knowledge/SKILL.md' 2>$null
if (-not $legacyBody) { $legacyBody = @("---","name: powerbi-knowledge","description: ban cu","---","NOI DUNG CU") }
Set-Content (Join-Path $legacySkill 'SKILL.md') ($legacyBody -join "`n") -Encoding UTF8
$null = Run-Install 'codex'
$skRootC = Join-Path $FakeHome '.codex\skills'
# "Cập nhật" = bản mới ở tên mới có ĐÚNG nội dung nguồn (không khớp trường frontmatter cụ thể:
# người viết skill đổi frontmatter không được làm ca này đỏ giả).
$nowHasProv = (-not (Test-Path $legacySkill)) -and
              ((FileHash (Join-Path $newSkill 'SKILL.md')) -eq (FileHash (Join-Path $RepoRoot 'skills\pbi-knowledge\SKILL.md')))
$hasMarkerNow = Test-Path (Join-Path $newSkill '.powerbi-agent-generated')
# Bản cũ phải được GIỮ (không xoá mất dữ liệu) nhưng nằm NGOÀI skills/ — trong skills/ thì
# host vẫn nạp nó như một skill xác sống, đúng cái bug đang muốn diệt.
$bkOutside = @(Get-ChildItem (Join-Path $FakeHome '.codex') -Directory -Filter 'powerbi-agent-backup-*' -ErrorAction SilentlyContinue).Count
$expectSkillDirs = $expectSkills + $expectCmds
$skillDirs = @(Get-ChildItem $skRootC -Directory -ErrorAction SilentlyContinue | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') }).Count
$null = Run-Uninstall 'codex'
$goneNow = -not (Test-Path $newSkill)
Add-Result 'D-upgrade-repo-skill-no-marker' ($nowHasProv -and $hasMarkerNow -and $bkOutside -eq 1 -and $skillDirs -eq $expectSkillDirs -and $goneNow) `
    "capNhat=$nowHasProv marker=$hasMarkerNow backupNgoaiSkills=$bkOutside skillTrongSkills=$skillDirs/$expectSkillDirs goDuoc=$goneNow"

# Bước lỗi phải làm install exit 1. Trước đây 3 chỗ gọi Err rồi chạy tiếp -> vẫn in HOÀN TẤT + exit 0.
Reset-Home
Set-Content (Join-Path $FakeHome '.claude.json') '[1,2,3]' -Encoding UTF8   # root khong phai object -> helper sys.exit
$null = Run-Install 'claude'
$installExit = $LASTEXITCODE
$cfgUntouched = (Get-Content (Join-Path $FakeHome '.claude.json') -Raw) -match '\[\s*1'
Add-Result 'D-install-exits-1-on-failure' ($installExit -eq 1 -and $cfgUntouched) `
    "exitCode=$installExit (phai=1) fileGocConNguyen=$cfgUntouched"

# M1 vong 5: user đặt cờ .powerbi-agent-keep -> installer PHẢI để yên, chạy BAO NHIÊU LẦN cũng vậy.
# Không có cờ này thì skill riêng trùng `name:` bị dời đi mỗi lần cài, không có trạng thái ổn định.
Reset-Home
$keepDir = Join-Path $FakeHome '.codex\skills\pbi-knowledge'
New-Item -ItemType Directory -Path $keepDir -Force | Out-Null
Set-Content (Join-Path $keepDir 'SKILL.md') "---`nname: pbi-knowledge`n---`nSKILL RIENG CUA TOI" -Encoding UTF8
Set-Content (Join-Path $keepDir '.powerbi-agent-keep') '' -Encoding UTF8
$null = Run-Install 'codex'
$null = Run-Install 'codex'
$keptBody = (Get-Content (Join-Path $keepDir 'SKILL.md') -Raw -Encoding UTF8) -match 'SKILL RIENG CUA TOI'
$noBackup = @(Get-ChildItem (Join-Path $FakeHome '.codex') -Directory -Filter 'powerbi-agent-backup-*' -ErrorAction SilentlyContinue).Count
$null = Run-Uninstall 'codex'
$keptAfterUninstall = Test-Path (Join-Path $keepDir 'SKILL.md')
Add-Result 'D-keep-flag-is-honoured' ($keptBody -and $noBackup -eq 0 -and $keptAfterUninstall) `
    "conNguyenSau2LanCai=$keptBody soBackup=$noBackup (phai=0) conSauKhiGo=$keptAfterUninstall"

# MAJOR-1 vong 6: co keep phai duoc ton trong CA o Install-CommandsAsSkills (skill-lenh Codex).
# D-keep-flag-is-honoured chi dung ten skill GOC nen khong cham duong nay — ma chinh duong nay
# xoa luon file keep, lam mat ca la chan ben uninstall.
Reset-Home
$null = Run-Install 'codex'
$cmdSkill = Join-Path $FakeHome '.codex\skills\pbi-help'
Set-Content (Join-Path $cmdSkill 'SKILL.md') "---`nname: pbi-help`nx-generated-by: powerbi-agent`n---`nTUY BIEN CUA TOI" -Encoding UTF8
Set-Content (Join-Path $cmdSkill 'ghi-chu.md') 'ghi chu rieng' -Encoding UTF8
Set-Content (Join-Path $cmdSkill '.powerbi-agent-keep') '' -Encoding UTF8
$null = Run-Install 'codex'
$cmdKept  = (Get-Content (Join-Path $cmdSkill 'SKILL.md') -Raw -Encoding UTF8) -match 'TUY BIEN CUA TOI'
$cmdSide  = Test-Path (Join-Path $cmdSkill 'ghi-chu.md')
$cmdFlag  = Test-Path (Join-Path $cmdSkill '.powerbi-agent-keep')
$null = Run-Uninstall 'codex'
$cmdAfter = Test-Path (Join-Path $cmdSkill 'SKILL.md')
Add-Result 'D-keep-flag-on-command-skill' ($cmdKept -and $cmdSide -and $cmdFlag -and $cmdAfter) `
    "noiDungConNguyen=$cmdKept fileKemConNguyen=$cmdSide coKeepConNguyen=$cmdFlag conSauKhiGo=$cmdAfter"

# m2 vong 5: helper in thêm dòng noise ra stderr (PYTHONWARNINGS, sitecustomize...).
# "$out" nối mảng bằng DẤU CÁCH nên neo (?m)^MERGE_OK$ không bao giờ khớp -> merge THÀNH CÔNG
# mà installer báo thất bại (và từ vòng 3 là exit 1). Không có ca này thì bản vá join-LF không được khóa.
Reset-Home
$noisy = Join-Path $FakeHome "noisy-python.cmd"   # trong FakeHome: da gitignore + bi don cuong buc
$sentinel = Join-Path $FakeHome "wrapper-da-chay.txt"
Set-Content $noisy "@echo off`r`necho da chay> `"$sentinel`"`r`necho canh bao gia lap 1>&2`r`n`"$venvPy`" %*" -Encoding ASCII
$null = & powershell -NoProfile -ExecutionPolicy Bypass -Command "
    `$env:USERPROFILE='$FakeHome';
    `$env:Path='C:\Windows\System32;C:\Windows'; `$env:POWERBI_INSTALL_PYTHON='$noisy';
    & '$RepoRoot\install.ps1' -SkipVenv -Hosts claude" *>&1 | Out-String
$noisyExit = $LASTEXITCODE
$cfgJson = Join-Path $FakeHome '.claude.json'
$registered = (Test-Path $cfgJson) -and ((Get-Content $cfgJson -Raw) -match 'powerbi-mcp-bridge')
# SENTINEL bat buoc: neu installer bo qua POWERBI_INSTALL_PYTHON (vi repo co .venv) thi
# wrapper khong he chay, ca test do chinh no vo nghia ma van XANH — dung lop loi
# "verify khong verify" ma chuoi review nay dang san.
$wrapperRan = Test-Path $sentinel
Remove-Item $noisy -Force -ErrorAction SilentlyContinue
Add-Result 'D-merge-ok-despite-stderr-noise' ($noisyExit -eq 0 -and $registered -and $wrapperRan) `
    "exitCode=$noisyExit (phai=0) daDangKy=$registered wrapperDaChay=$wrapperRan (phai=True)"

# Gate exit-1 của uninstall cũng phải có ca khóa (đối xứng với D-install-exits-1-on-failure).
Reset-Home
$null = Run-Install 'claude'
# JSON HONG (khong parse duoc) — khac '[1,2,3]': mang o goc chi la "khong co entry nao"
# nen ABSENT/exit 0 moi dung. Hong that thi khong biet entry con hay khong -> phai bao that bai.
Set-Content (Join-Path $FakeHome '.claude.json') '{"mcpServers": {' -Encoding UTF8
$null = Run-Uninstall 'claude'
$unExit = $LASTEXITCODE
Add-Result 'D-uninstall-exits-1-on-failure' ($unExit -eq 1) "exitCode=$unExit (phai=1)"

# Config RỖNG là vô hại ("không có gì để gỡ"), KHÔNG được thành fail cứng.
Reset-Home
Set-Content (Join-Path $FakeHome '.claude.json') '' -Encoding ASCII -NoNewline
$null = Run-Uninstall 'claude'
$emptyExit = $LASTEXITCODE
Add-Result 'D-uninstall-empty-config-ok' ($emptyExit -eq 0) "exitCode=$emptyExit (phai=0)"

# pack.ps1 la cong cu DUY NHAT dong goi mang di, ma khong mot ca pytest/harness nao chay no.
# Hai luat song con: (a) khong duoc ghi zip vao TRONG repo, (b) zip chi chua file tracked.
$packOut = Join-Path $env:TEMP "pbi-pack-$PID"
if (Test-Path $packOut) { Remove-Item $packOut -Recurse -Force }
$null = & powershell -NoProfile -ExecutionPolicy Bypass -Command "
    & '$RepoRoot\pack.ps1' -OutDir '$RepoRoot\zip-tam-$PID'" *>&1 | Out-String
$packExit = $LASTEXITCODE
# KHONG khop van xuoi tieng Viet trong output: khi harness bi goi TU PYTEST (subprocess),
# console encoding lech nen chuoi 'TU CHOI' khong khop -> ca test DO GIA. Da tai hien:
# chay harness truc tiep thi PASS, chay qua pytest thi FAIL. Tin hieu ASCII moi dang tin.
$refused   = ($packExit -ne 0)
$noResidue = (-not (Test-Path (Join-Path $RepoRoot "zip-tam-$PID"))) -and
             (@(Get-ChildItem $RepoRoot -Filter '*.zip' -ErrorAction SilentlyContinue).Count -eq 0)
$null = & powershell -NoProfile -ExecutionPolicy Bypass -Command "
    & '$RepoRoot\pack.ps1' -OutDir '$packOut'" *>&1 | Out-String
$zipFile = @(Get-ChildItem $packOut -Filter '*.zip' -ErrorAction SilentlyContinue)[0]
$zipClean = $false; $zipCount = 0
if ($zipFile) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $z = [System.IO.Compression.ZipFile]::OpenRead($zipFile.FullName)
    $names = @($z.Entries | ForEach-Object { $_.FullName }); $z.Dispose()
    $zipCount = $names.Count
    $zipClean = -not ($names | Where-Object { $_ -match '(^|/)\.env$|policy\.json$|\.venv/|\.bak' })
}
Remove-Item $packOut -Recurse -Force -ErrorAction SilentlyContinue
Add-Result 'E-pack-refuses-outdir-in-repo' ($refused -and $noResidue) `
    "daTuChoi=$refused khongDeLaiThuMucRong=$noResidue"
Add-Result 'E-pack-zip-has-no-secrets' ([bool]$zipFile -and $zipClean) `
    "coZip=$([bool]$zipFile) soFile=$zipCount khongCoSecret=$zipClean"

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

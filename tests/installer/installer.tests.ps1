# AUDIT HARNESS — chạy installer/uninstaller THẬT với USERPROFILE GIẢ.
# An toàn: mọi ghi đều vào $FakeHome; KHÔNG đụng config thật.
param(
  [string]$RepoRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
  [string]$PythonExe = ''
)
$ErrorActionPreference = 'Continue'
$S = Split-Path -Parent $MyInvocation.MyCommand.Path
$FakeHome = Join-Path $S 'fakehome'
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
$cmds = (Get-ChildItem (Join-Path $FakeHome '.claude\commands') -Filter 'pbi-*.md' -ErrorAction SilentlyContinue).Count
Add-Result 'C-skill-copy' ($n1 -eq 4 -and $cmds -eq 6) "skills=$n1/4 cmds=$cmds/6 staleSauLan2=$staleSurvives (true=DRIFT)"
# Nội dung skill, không chỉ số lượng: mẫu tài liệu (trụ 4) phải đi theo skill sang host.
# Thiếu assertion này thì đổi tên document-templates/ có thể hỏng mà test vẫn xanh.
$kpim    = Join-Path $sk 'kpim-analysis'
$docTpl  = Join-Path $kpim 'document-templates\PROJECT.md'
$oldTpl  = Join-Path $kpim 'templates'
Add-Result 'C-skill-content' ((Test-Path $docTpl) -and -not (Test-Path $oldTpl)) `
    "document-templates/PROJECT.md=$(Test-Path $docTpl) folderCu_templates=$(Test-Path $oldTpl) (true=CHUA_DOI_TEN)"
$null = Run-Uninstall 'claude'
$left = @(Get-ChildItem $sk -Directory -ErrorAction SilentlyContinue).Name -join ','
$cmdsLeft = @(Get-ChildItem (Join-Path $FakeHome '.claude\commands') -Filter 'pbi-*.md' -ErrorAction SilentlyContinue).Count
Add-Result 'C-uninstall-symmetric' ($left -eq '' -and $cmdsLeft -eq 0) "skillsConLai='$left' cmdsConLai=$cmdsLeft"

if (Test-Path $FakeHome) { Remove-Item $FakeHome -Recurse -Force }  # tự dọn residue
Write-Host "`n===== TONG KET ====="
$results | Format-Table -AutoSize | Out-String | Write-Host

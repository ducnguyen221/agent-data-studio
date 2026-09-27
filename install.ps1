<#
.SYNOPSIS
  Bộ cài Agent Data Studio chạy trực tiếp từ checkout repo.

.DESCRIPTION
  Cài đặt tại thư mục chứa file này:
    - Tạo / kiểm tra venv Python + cài dependencies.
    - Dò ADOMD.NET (đa phiên bản).
    - Đăng ký MCP vào Claude Code / Codex / Antigravity, trỏ về CHÍNH thư mục này
      (merge vào cấu hình có sẵn, có backup .bak, không xoá server khác).
    - Kiểm adapter skill trong repo để từng host đọc cùng một nguồn.
  Có thể đọc cấu hình đời cũ để chuyển các khoá không mật khẩu; không sao chép credential.

.EXAMPLE
  # Cách dùng chuẩn — mở PowerShell tại thư mục này rồi chạy:
  .\install.ps1

.PARAMETER Hosts
  Host cần đăng ký: claude, codex, antigravity, claude-desktop. Mặc định chỉ Codex.
  claude-desktop (tab chat của Claude Desktop) chỉ nhận MCP, không có skill/lệnh pbi-*; -Hosts claude không kéo theo nó.
.PARAMETER SkipVenv
  Bỏ qua tạo venv / cài pip (chỉ cập nhật cấu hình host).
.PARAMETER SkipHosts
  Chỉ dựng venv, không đụng cấu hình host nào.
.PARAMETER Only
  Chỉ kiểm adapter skill tại repo; không sao chép skill vào thư mục host.
#>
[CmdletBinding()]
param(
    [string[]] $Hosts = @("codex"),
    [switch]   $SkipVenv,
    [switch]   $SkipHosts,
    [ValidateSet("plugin")]
    [string]   $Only
)

# -Only plugin: chỉ kiểm adapter; không dựng trạm, config, binding hay đăng ký host.
# KHÔNG overload $SkipHosts: -SkipHosts có hợp đồng riêng ("không đụng thư mục host nào"),
# nếu dùng chung cờ thì -SkipHosts sẽ vẫn ghi skill/lệnh vào host — sai tài liệu.
$SkipMcp    = $SkipHosts
if ($Only -eq "plugin") { $SkipVenv = $true; $SkipMcp = $true }

$ErrorActionPreference = "Stop"
# `powershell -File install.ps1 -Hosts claude,codex` truyền MỘT chuỗi "claude,codex" (khác gọi trong PowerShell):
# trước đây không khớp host nào, installer vẫn báo HOÀN TẤT mà không đăng ký gì. Tách dấu phẩy, từ chối tên lạ.
$KnownHosts = @("claude", "codex", "antigravity", "claude-desktop")
$Hosts = @($Hosts | ForEach-Object { "$_" -split ',' } | ForEach-Object { $_.Trim().ToLowerInvariant() } | Where-Object { $_ })
$unknownHosts = @($Hosts | Where-Object { $KnownHosts -notcontains $_ })
if ($unknownHosts.Count -gt 0) {
    Write-Host "[X] Host không hỗ trợ: $($unknownHosts -join ', '). Chọn trong: $($KnownHosts -join ', ')." -ForegroundColor Red
    exit 1
}
$Root  = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"

function Info($m)  { Write-Host "[i] $m" -ForegroundColor Cyan }
function Ok($m)    { Write-Host "[OK] $m" -ForegroundColor Green }
function Warn($m)  { Write-Host "[!] $m" -ForegroundColor Yellow }
# Ba cho goi Err roi CHAY TIEP (merge JSON hong, config.toml khong parse, skill copy hong).
# Truoc day installer van in "HOAN TAT" va exit 0 -> CI xanh, script goi no tuong da cai xong.
$script:HadError = $false
function Err($m)   { $script:HadError = $true; Write-Host "[X] $m" -ForegroundColor Red }
function Step($m)  { Write-Host "`n=== $m ===" -ForegroundColor Magenta }
# PS 5.1 + Stop biến stderr của lệnh native thành lỗi dừng khi stderr bị chuyển hướng (2>&1 ở đây,
# hoặc người gọi gom *>&1/2>&1 vào biến) -> installer chết trước nhánh báo lỗi. Đánh giá bằng $LASTEXITCODE.
# `$command, $rest = $args` làm $rest thành CHUỖI khi chỉ có một đối số -> splat tách từng ký tự:
# `Invoke-Native $venvPy --version` chạy `python - - v e r ...` = đọc script từ stdin, treo ở console. Giữ mảng.
function Invoke-Native { $ErrorActionPreference = 'Continue'; $command = $args[0]; $rest = @($args | Select-Object -Skip 1); & $command @rest }

# Ghi file UTF-8 KHÔNG BOM (an toàn cho JSON/TOML)
function Write-Utf8NoBom([string]$Path, [string]$Text) {
    [System.IO.File]::WriteAllText($Path, $Text, (New-Object System.Text.UTF8Encoding($false)))
}
function Backup-File([string]$Path) {
    $script:LastBackup = $null
    if (Test-Path $Path) {
        $backup = "$Path.bak.$Stamp-$PID-$([guid]::NewGuid().ToString('N'))"
        Copy-Item -LiteralPath $Path -Destination $backup -ErrorAction Stop
        $script:LastBackup = $backup
        Info "Đã sao lưu: $backup"
    }
}
# Hash .NET thuần, KHÔNG dùng Get-FileHash: ở Windows PowerShell 5.1 đó là hàm trong module
# Microsoft.PowerShell.Utility, phải autoload -> PSModulePath lẫn module PowerShell 7 là CommandNotFoundException.
function Get-Sha256([string]$Path) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $stream = [System.IO.File]::OpenRead($Path)
    try { return [System.BitConverter]::ToString($sha.ComputeHash($stream)) }
    finally { $stream.Dispose(); $sha.Dispose() }
}
# Cài lại mà cấu hình không đổi thì bản sao lưu vừa tạo là thừa; chỉ xoá khi byte trùng khớp.
function Remove-UnchangedBackup([string]$Path) {
    $backup = $script:LastBackup
    $script:LastBackup = $null
    if ($backup -and (Test-Path -LiteralPath $backup -PathType Leaf) -and (Test-Path -LiteralPath $Path -PathType Leaf) -and
        (Get-Sha256 $backup) -eq (Get-Sha256 $Path)) {
        Remove-Item -LiteralPath $backup -Force
        Info "Cấu hình không đổi; bỏ bản sao lưu thừa."
    }
}
$foreignHint = "Server 'powerbi-mcp-bridge' trong host đang trỏ checkout khác: chạy uninstall.ps1 của checkout đó (hoặc đổi tên server đó trong cấu hình host) rồi chạy lại install.ps1."

Write-Host "Agent Data Studio · Cài đặt" -ForegroundColor Blue

Info "Thư mục cài (= vị trí MCP server): $Root"
Info "Host đăng ký: $($Hosts -join ', ')"

$serverPath = Join-Path $Root "mcp_server_powerbi.py"
if (-not (Test-Path $serverPath)) { Err "Không thấy mcp_server_powerbi.py cạnh install.ps1. Dừng."; exit 1 }
# POWERBI_INSTALL_PYTHON là override CI/test đi kèm -SkipVenv. Thiếu -SkipVenv và chưa có .venv thì
# bước venv sẽ coi Python đó là venv: pip install thẳng vào nó rồi ghi nó vào config host. Dừng trước khi ghi gì.
if ($env:POWERBI_INSTALL_PYTHON -and -not $SkipVenv -and -not (Test-Path (Join-Path $Root ".venv\Scripts\python.exe"))) {
    Err "POWERBI_INSTALL_PYTHON chỉ dùng kèm -SkipVenv (CI/test). Bỏ biến này để installer tạo .venv riêng, hoặc thêm -SkipVenv."; exit 1
}

if ($Only -eq "plugin") {
    $adapterScript = Join-Path $Root 'scripts\build_host_adapters.py'
    $adapterPython = if ($env:POWERBI_INSTALL_PYTHON) { $env:POWERBI_INSTALL_PYTHON } else { 'python' }
    Invoke-Native $adapterPython $adapterScript --check
    if ($LASTEXITCODE -ne 0) { Err "Adapter skill lệch nguồn; chạy generator trong repo và review trước khi cài."; exit 1 }
    Ok "Adapter skill trong repo đồng bộ. Không thay đổi trạm hay host."
    exit 0
}

function Expand-StationPath([string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { throw "Đường dẫn trạm trống." }
    $expanded = [Environment]::ExpandEnvironmentVariables($Value.Trim().Trim('"').Trim("'"))
    if ($expanded -eq '~') { $expanded = $env:USERPROFILE }
    elseif ($expanded.StartsWith('~\') -or $expanded.StartsWith('~/')) {
        $expanded = Join-Path $env:USERPROFILE $expanded.Substring(2)
    }
    $expanded = $expanded.Replace('/', '\')
    if ($expanded.StartsWith('\\?\UNC\', [StringComparison]::OrdinalIgnoreCase)) {
        $expanded = '\\' + $expanded.Substring(8)
    } elseif ($expanded.StartsWith('\\?\')) {
        $expanded = $expanded.Substring(4)
    }
    if ($expanded -match '^\\\\(?:localhost|127\.0\.0\.1)\\([A-Za-z])\$\\(.*)$') {
        $expanded = "$($Matches[1]):\$($Matches[2])"
    }
    if (-not [IO.Path]::IsPathRooted($expanded)) { throw 'Đường dẫn trạm phải tuyệt đối.' }
    return [System.IO.Path]::GetFullPath($expanded)
}

function Assert-NoReparsePoint([string]$Path, [string]$Label) {
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    if ($item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "$Label là junction/symlink; chọn đường dẫn thật rồi cài lại."
    }
}

# Gitignore không bảo vệ file đã nằm trong index. Dừng trước khi tạo dữ liệu mới.
$gitIndex = Join-Path $Root '.git'
if (Test-Path -LiteralPath $gitIndex) {
    $tracked = @(Invoke-Native git -C $Root -c core.quotePath=false ls-files --cached)
    if ($LASTEXITCODE -ne 0) { Err "Không kiểm được Git index; dừng trước khi tạo trạm."; exit 1 }
    $forcedIgnored = @(Invoke-Native git -C $Root ls-files --cached --ignored --exclude-standard)
    if ($LASTEXITCODE -ne 0) { Err "Không kiểm được file ignored trong Git index; dừng trước khi tạo trạm."; exit 1 }
    $unsafeTracked = @($tracked | Where-Object {
        $name = ($_ -replace '\\', '/')
        $leaf = [IO.Path]::GetFileName($name)
        $name -match '(^|/)workspace/' -or $name -eq '.ads-binding.json' -or
        $name -in @('policy.json','knowledge.config.json','.claude.json') -or
        $name -match '(^|/)(\.claude|\.codex|\.gemini)/(settings(\.local)?\.json|config\.toml|mcp_config\.json)$' -or
        ($leaf -match '^\.env($|\.)' -and $leaf -ne '.env.example') -or
        $leaf -in @('config.env','secrets.env','auth.json','oauth_creds.json') -or
        $leaf -match '\.(pem|key|credentials\.json)$'
    })
    if ($unsafeTracked.Count -gt 0 -or $forcedIgnored.Count -gt 0) {
        Err "Git index đang theo dõi dữ liệu/cấu hình riêng. Bỏ theo dõi và kiểm tra lịch sử trước khi cài."; exit 1
    }
}

# ---- Station: xác minh trước khi tạo bất kỳ file nào ----
$bindingFile = Join-Path $Root ".ads-binding.json"
$priorStation = $null
if (Test-Path -LiteralPath $bindingFile) {
    try {
        Assert-NoReparsePoint $bindingFile 'Binding trạm'
        $binding = Get-Content -LiteralPath $bindingFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($null -eq $binding -or $binding -isnot [pscustomobject] -or
            $binding.PSObject.Properties.Name -notcontains 'station_root' -or
            $binding.station_root -isnot [string] -or
            [string]::IsNullOrWhiteSpace($binding.station_root)) { throw 'Schema binding thiếu station_root.' }
        $priorStation = Expand-StationPath $binding.station_root
        $homeBinding = $binding.station_root -eq '~' -or
            $binding.station_root.StartsWith('~\') -or $binding.station_root.StartsWith('~/')
        if (-not [IO.Path]::IsPathRooted($binding.station_root) -and -not $homeBinding) {
            throw 'Binding phải dùng đường dẫn tuyệt đối.'
        }
    }
    catch { Err "Binding trạm cũ không hợp lệ. Dừng trước khi ghi dữ liệu."; exit 1 }
}
$requestedStation = $null
if ($env:ADS_DATA) {
    try { $requestedStation = Expand-StationPath $env:ADS_DATA }
    catch { Err "ADS_DATA không phải đường dẫn trạm hợp lệ."; exit 1 }
}
if ($priorStation -and $requestedStation -and
    -not [string]::Equals($priorStation, $requestedStation, [StringComparison]::OrdinalIgnoreCase)) {
    Err "ADS_DATA khác binding trạm đã cài. Dừng để tránh đổi trạm ngầm."; exit 1
}
if (-not $priorStation -and -not $requestedStation -and
    ((Test-Path -LiteralPath (Join-Path $Root ".env")) -or
     (Test-Path -LiteralPath (Join-Path $Root "knowledge.config.json")) -or
     (Test-Path -LiteralPath (Join-Path $Root "policy.json")))) {
    Err "Có cấu hình dữ liệu đời cũ tại source. Chọn ADS_DATA trỏ trạm hiện hữu rồi chạy lại; không tự chuyển dữ liệu."; exit 1
}
$stationRoot = if ($requestedStation) {
    $requestedStation
} elseif ($priorStation) {
    $priorStation
} else { Join-Path $Root "workspace" }
$repoFull = [System.IO.Path]::GetFullPath($Root).TrimEnd('\')
$workspaceFull = [System.IO.Path]::GetFullPath((Join-Path $Root "workspace")).TrimEnd('\')
$stationRoot = [System.IO.Path]::GetFullPath($stationRoot).TrimEnd('\')
$isInRepo = $stationRoot.Equals($repoFull, [StringComparison]::OrdinalIgnoreCase) -or
    $stationRoot.StartsWith($repoFull + '\', [StringComparison]::OrdinalIgnoreCase)
$isInWorkspace = $stationRoot.Equals($workspaceFull, [StringComparison]::OrdinalIgnoreCase)
if ($isInRepo -and -not $isInWorkspace) { Err "Trạm trỏ vào source của repo. Dừng."; exit 1 }
if ($priorStation -and $isInRepo) { Err "Binding trạm ngoài không được trỏ vào source."; exit 1 }
$ancestor = $stationRoot
while ($ancestor) {
    if (Test-Path -LiteralPath $ancestor) {
        $item = Get-Item -LiteralPath $ancestor -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            Err "Trạm đi qua junction/symlink; chọn đường dẫn thật rồi cài lại."; exit 1
        }
    }
    $parent = Split-Path -Parent $ancestor
    if (-not $parent -or $parent -eq $ancestor) { break }
    $ancestor = $parent
}
foreach ($subdir in @("projects", "knowledge", "outputs", "state")) {
    try { Assert-NoReparsePoint (Join-Path $stationRoot $subdir) "Thư mục $subdir" }
    catch { Err $_.Exception.Message; exit 1 }
}
foreach ($file in @('config.env', '.env')) {
    try { Assert-NoReparsePoint (Join-Path $stationRoot $file) "Cấu hình $file" }
    catch { Err $_.Exception.Message; exit 1 }
}
try { Assert-NoReparsePoint (Join-Path $Root '.env') 'Cấu hình đời cũ' }
catch { Err $_.Exception.Message; exit 1 }

# Xác nhận cấu hình cũ TRƯỚC khi tạo workspace/binding. Không in giá trị đã đọc.
$envFile = Join-Path $stationRoot 'config.env'
$envEx = Join-Path $Root '.env.example'
$safeLines = $null
if ((-not (Test-Path -LiteralPath $envFile)) -and (Test-Path -LiteralPath $envEx)) {
    $legacyEnv = Join-Path $stationRoot '.env'
    if (-not (Test-Path -LiteralPath $legacyEnv)) { $legacyEnv = Join-Path $Root '.env' }
    if (Test-Path -LiteralPath $legacyEnv) {
        $safeKeys = @('POWERBI_PROJECT_DIR','POWERBI_AGGREGATE_ONLY','POWERBI_MAX_ROWS',
            'POWERBI_DIMENSION_ROW_CAP','POWERBI_POLICY_FILE','POWERBI_AUDIT_DIR',
            'POWERBI_TEMPLATES_DIR','POWERBI_DISTILL_DIR','ADOMD_LIB_DIR','ADS_SECRETS_FILE')
        $safeLines = @(Get-Content -LiteralPath $legacyEnv -Encoding UTF8 | Where-Object {
            $_ -match '^([A-Z][A-Z0-9_]*)=' -and $safeKeys -contains $Matches[1]
        })
        $projectLine = @($safeLines | Where-Object { $_ -match '^POWERBI_PROJECT_DIR=' } | Select-Object -Last 1)
        if ($projectLine.Count -gt 0) {
            try {
                $projectValue = $projectLine[0].Substring('POWERBI_PROJECT_DIR='.Length).Trim().Trim('"').Trim("'")
                $projectPath = Expand-StationPath $projectValue
                $projectWithinStation = $projectPath.Equals($stationRoot, [StringComparison]::OrdinalIgnoreCase) -or
                    $projectPath.StartsWith($stationRoot + '\', [StringComparison]::OrdinalIgnoreCase)
                if (-not $projectWithinStation) { throw 'Project ở trạm khác.' }
            } catch {
                Err "POWERBI_PROJECT_DIR đời cũ không thuộc trạm đã chọn. Dừng để xác nhận trạm; chưa chuyển cấu hình."; exit 1
            }
        }
    }
}
foreach ($subdir in @("projects", "knowledge", "outputs", "state")) {
    New-Item -ItemType Directory -Path (Join-Path $stationRoot $subdir) -Force | Out-Null
}
Info "Trạm dữ liệu: $stationRoot"
if (-not $isInRepo -and -not $priorStation) {
    # Chuyển từ workspace/ trong checkout sang trạm ngoài: dữ liệu cũ ở lại nguyên chỗ, không tự di chuyển.
    if ((Test-Path -LiteralPath $workspaceFull -PathType Container) -and
        @(Get-ChildItem -LiteralPath $workspaceFull -Recurse -File -Force -ErrorAction SilentlyContinue | Select-Object -First 1).Count -gt 0) {
        Warn "workspace/ trong checkout còn dữ liệu; installer KHÔNG chuyển sang trạm mới $stationRoot. Dữ liệu cũ giữ nguyên tại $workspaceFull — tự chép nếu cần."
    }
    Write-Utf8NoBom $bindingFile ((@{ station_root = $stationRoot } | ConvertTo-Json -Compress) + "`n")
}

# ---- config.env: chỉ các khoá không phải credential; giữ nguyên khi cài lại ----
if ((-not (Test-Path $envFile)) -and (Test-Path $envEx)) {
    if ($null -ne $safeLines) {
        Write-Utf8NoBom $envFile (($safeLines -join "`n") + "`n")
        Warn "Đã chuyển các khoá cấu hình không mật khẩu sang trạm; credential cũ không được sao chép."
    } else {
        Copy-Item $envEx $envFile -Force
    }
}

# ============================================================
# 1) PYTHON VENV + DEPENDENCIES
# ============================================================
$venvPy = Join-Path $Root ".venv\Scripts\python.exe"
$venvRoot = Join-Path $Root '.venv'
$venvMarker = Join-Path $venvRoot '.ads-venv-owned'
# Override cho CI/test: dùng python chỉ định để merge/validate config.
# PHẢI thắng cả khi repo CÓ venv, miễn là -SkipVenv: nếu không thì harness chạy trên máy dev
# (có .venv) sẽ âm thầm dùng venv thật thay vì python mà test chỉ định — ca test wrapper
# trở thành XANH GIẢ, chỉ đỏ trong CI. (uninstall.ps1 vẫn theo luật cũ vì không có -SkipVenv.)
if ($env:POWERBI_INSTALL_PYTHON -and ($SkipVenv -or -not (Test-Path $venvPy))) {
    $venvPy = $env:POWERBI_INSTALL_PYTHON
}

if ($SkipVenv) {
    Warn "Bỏ qua venv/pip (-SkipVenv)."
} else {
    Step "1/3 Python venv + dependencies"

    # Khoảng hỗ trợ 3.11–3.14: sàn theo engine, trần theo pythonnet 3.1.0 (Requires-Python <3.15).
    # Phải khớp pyproject requires-python và doctor.ps1 (tests/test_installer.py giữ ba nơi khớp nhau).
    # Ưu tiên bản đã kiểm với Power BI Desktop (3.13, 3.12, 3.11), rồi 3.14, rồi bản mặc định của máy.
    $PyMinMinor = 11; $PyMaxMinor = 14
    $script:PythonRejected = @()
    function Get-Python {
        foreach ($c in @(@("py",@("-3.13")),@("py",@("-3.12")),@("py",@("-3.11")),@("py",@("-3.14")),@("py",@("-3")),@("python",@()),@("python3",@()))) {
            $exe=$c[0]; $pre=$c[1]
            if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
            try {
                $ver = & $exe @pre -c "import sys;print('%d.%d'%sys.version_info[:2])" 2>$null
                if ($ver -match '^(\d+)\.(\d+)$' -and [int]$Matches[1] -eq 3 -and
                    [int]$Matches[2] -ge $PyMinMinor -and [int]$Matches[2] -le $PyMaxMinor) {
                    return ,@($exe,$pre,$ver)
                }
                if ($ver -match '^\d+\.\d+$' -and $script:PythonRejected -notcontains $ver) { $script:PythonRejected += $ver }
            } catch {}
        }
        return $null
    }

    # Venv có sẵn không có marker thuộc checkout này là của người dùng/đời cũ: không nhận sở hữu.
    try {
        Assert-NoReparsePoint $venvRoot 'Môi trường Python'
        Assert-NoReparsePoint $venvMarker 'Dấu sở hữu môi trường Python'
    } catch { Err $_.Exception.Message; exit 1 }
    if (Test-Path -LiteralPath $venvRoot) {
        if (-not (Test-Path -LiteralPath $venvMarker -PathType Leaf)) {
            Err 'Môi trường .venv đã có nhưng chưa có dấu sở hữu của bộ cài. Dừng để tránh thay đổi môi trường của bạn.'; exit 1
        }
        $markerRoot = (Get-Content -LiteralPath $venvMarker -Raw -Encoding UTF8).Trim()
        if (-not [string]::Equals($markerRoot, $Root, [StringComparison]::OrdinalIgnoreCase)) {
            Err 'Dấu sở hữu .venv không khớp checkout này. Dừng.'; exit 1
        }
    }

    $needBuild = $true
    if (Test-Path $venvPy) {
        Invoke-Native $venvPy --version *> $null
        if ($LASTEXITCODE -eq 0) { $needBuild = $false; Info "venv hợp lệ -> tái sử dụng." }
        else { Err 'Môi trường .venv không chạy được. Giữ nguyên để kiểm tra/sửa thủ công trước khi cài lại.'; exit 1 }
    } elseif (Test-Path -LiteralPath $venvRoot) {
        Err 'Môi trường .venv thiếu Python; giữ nguyên để kiểm tra/sửa thủ công trước khi cài lại.'; exit 1
    }

    if ($needBuild) {
        $py = Get-Python
        if (-not $py) {
            $range = "3.$PyMinMinor–3.$PyMaxMinor"
            if ($script:PythonRejected.Count -gt 0) {
                Err "Máy có Python $($script:PythonRejected -join ', ') nhưng Agent Data Studio cần Python $range (khuyên dùng 3.12 hoặc 3.13). Bản ngoài khoảng này chưa cài được thư viện Power BI."
            } else {
                Err "Không thấy Python $range (đã thử lệnh py và python)."
            }
            Err "Cài Python 3.12: 'winget install --id Python.Python.3.12 -e' hoặc tải từ https://www.python.org/downloads/ (tick 'Add to PATH'), rồi chạy lại install.ps1."
            exit 1
        }
        Ok "Dùng Python $($py[2])"
        Invoke-Native $py[0] @($py[1]) -m venv $venvRoot
        if ($LASTEXITCODE -ne 0) { Err "Tạo venv thất bại."; exit 1 }
        # Sở hữu được xác lập khi chính installer tạo venv; lỗi mạng/pip sau đó vẫn cho phép repair.
        Write-Utf8NoBom $venvMarker ($Root + "`n")
    }

    Info "Nâng cấp pip..."
    Invoke-Native $venvPy -m pip install --upgrade pip --quiet

    $req   = Join-Path $Root "requirements.txt"
    Info "Cài dependencies (requirements.txt)..."
    Invoke-Native $venvPy -m pip install -r $req --quiet
    if ($LASTEXITCODE -ne 0) { Err "Cài dependencies ghim phiên bản thất bại. Kiểm tra mạng/chính sách rồi thử lại."; exit 1 }
    # Gỡ venv chỉ được phép khi marker khớp checkout và không còn host nào tham chiếu.
    Ok "Dependencies sẵn sàng."
}

# ============================================================
# 2) KIỂM TRA ADOMD.NET
# ============================================================
Step "2/3 Kiểm tra ADOMD.NET"
$adomdDll = "Microsoft.AnalysisServices.AdomdClient.dll"
$found = $null
$adomdOverride = $null
$tabularMissing = $false
# Một nguồn với engine: hỏi powerbi_agent.adomd.find_adomd_dlls() (chỉ dò đĩa, không nạp pythonnet) —
# cùng thứ tự thư mục, cùng luật ADOMD_LIB_DIR (biến môi trường thắng config.env, override độc quyền).
# Không nháy kép trong mã Python: PS 5.1 làm hỏng dấu " khi truyền đối số cho lệnh native.
$adomdProbe = @'
import json, sys
sys.path.insert(0, sys.argv[1])
from powerbi_agent.adomd import find_adomd_dlls
print('ADOMD_JSON ' + json.dumps(find_adomd_dlls(sys.argv[2])))
'@
$adomdInfo = $null
if (Test-Path $venvPy) {
    $adomdOut = @(Invoke-Native $venvPy -c $adomdProbe $Root $envFile 2>$null)
    $adomdLine = @($adomdOut | ForEach-Object { "$_" } | Where-Object { $_.StartsWith('ADOMD_JSON ') } | Select-Object -Last 1)
    if ($LASTEXITCODE -eq 0 -and $adomdLine.Count -eq 1) {
        try { $adomdInfo = $adomdLine[0].Substring(11) | ConvertFrom-Json } catch { $adomdInfo = $null }
    }
}
if ($adomdInfo) {
    $adomdOverride = $adomdInfo.override
    $hitAdomd = @($adomdInfo.dirs | Where-Object { $_.adomd } | Select-Object -First 1)
    if ($hitAdomd.Count -gt 0) { $found = Join-Path $hitAdomd[0].dir $adomdDll }
    elseif (-not $adomdOverride -and $adomdInfo.gac.adomd) { $found = "GAC (Microsoft.AnalysisServices.AdomdClient)" }
    $tabularMissing = -not (@($adomdInfo.dirs | Where-Object { $_.tabular }).Count -gt 0 -or
                            (-not $adomdOverride -and $adomdInfo.gac.tabular))
} else {
    # Đường lùi khi không chạy được Python: glob PowerShell chép đúng thứ tự candidate_adomd_dirs().
    Info "Không hỏi được engine; dò ADOMD.NET bằng danh sách thư mục dự phòng."
    $pf = ${env:ProgramFiles}; if (-not $pf) { $pf="C:\Program Files" }
    $pf86 = ${env:ProgramFiles(x86)}; if (-not $pf86) { $pf86="C:\Program Files (x86)" }
    if ($env:ADOMD_LIB_DIR) {
        # Override độc quyền, đúng thư mục đó (không đệ quy, không wildcard) như engine.
        $adomdOverride = $env:ADOMD_LIB_DIR
        $globs = @()
        $candidate = Join-Path $env:ADOMD_LIB_DIR $adomdDll
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { $found = $candidate }
    } else {
        $globs = @(
            (Join-Path $pf   "Microsoft SQL Server Management Studio*\*\Common7\IDE"),
            (Join-Path $pf   "Microsoft SQL Server Management Studio*\Common7\IDE"),
            (Join-Path $pf86 "Microsoft SQL Server Management Studio*\*\Common7\IDE"),
            (Join-Path $pf86 "Microsoft SQL Server Management Studio*\Common7\IDE"),
            (Join-Path $pf   "Microsoft.NET\ADOMD.NET\*"),
            (Join-Path $pf86 "Microsoft.NET\ADOMD.NET\*"),
            (Join-Path $pf   "Microsoft SQL Server\*\SDK\Assemblies"),
            (Join-Path $pf86 "Microsoft SQL Server\*\SDK\Assemblies"),
            (Join-Path $pf   "Microsoft Power BI Desktop\bin")
        )
    }
    foreach ($g in $globs) {
        $hit = Get-ChildItem -Path $g -Filter $adomdDll -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($hit) { $found = $hit.FullName; break }
    }
}
if ($found) {
    if ($adomdOverride) { Ok "Tìm thấy ADOMD.NET (ADOMD_LIB_DIR): $found" } else { Ok "Tìm thấy ADOMD.NET: $found" }
    if ($tabularMissing) { Warn "Thiếu Microsoft.AnalysisServices.Tabular.dll: tool GHI model (TOM) sẽ báo lỗi; truy vấn vẫn chạy." }
} elseif ($adomdOverride) {
    Warn "ADOMD_LIB_DIR=$adomdOverride không chứa $adomdDll. Override là độc quyền: tool LOCAL sẽ lỗi tới khi sửa (không dò SSMS/GAC)."
} else {
    Warn "KHÔNG thấy ADOMD.NET. Tool Cloud vẫn chạy; tool LOCAL sẽ lỗi tới khi cài."
    Warn "  Cài 'Analysis Services client libraries': https://learn.microsoft.com/analysis-services/client-libraries"
    Warn "  Hoặc đặt ADOMD_LIB_DIR trong $envFile tới thư mục chứa $adomdDll."
}

# ============================================================
# 3) ĐĂNG KÝ MCP VÀO HOST (trỏ về CHÍNH thư mục này)
# ============================================================
$pyJson  = $venvPy.Replace('\','/')
$srvJson = $serverPath.Replace('\','/')

# -NoType: Claude Desktop dùng đúng lược đồ tài liệu {command,args,env} (không có khoá type).
function Merge-McpJson([string]$Path, [switch]$NoType) {
    # BẪY ĐÃ TÁI HIỆN (audit 2026-07-15): KHÔNG round-trip JSON của host bằng PS 5.1.
    #   (1) ~/.claude.json thật chứa key rỗng "" -> ConvertFrom-Json PS 5.1 CRASH luôn
    #       ("value of argument name is not valid") -> nhánh fallback này chưa bao giờ chạy nổi.
    #   (2) ConvertTo-Json quá -Depth thì ÂM THẦM biến tầng sâu hơn thành chuỗi '@{n=}' (mất dữ liệu).
    # => Merge bằng Python của venv (json chuẩn: không depth limit, không sợ key rỗng,
    #    ensure_ascii=False giữ tiếng Việt) + VALIDATE parse lại sau khi ghi.
    $dir = Split-Path -Parent $Path
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if (-not (Test-Path $venvPy)) {
        Warn "Không có venv Python ($venvPy) để merge JSON an toàn -> BỎ QUA $Path."
        Warn "  Chạy lại install.ps1 KHÔNG kèm -SkipVenv, hoặc thêm tay block powerbi-mcp-bridge (xem hosts/)."
        return
    }
    $mergePy = @'
import json, os, pathlib, sys, tempfile
path, py, srv = sys.argv[1], sys.argv[2], sys.argv[3]
with_type = sys.argv[4:5] != ["no-type"]
target = pathlib.Path(path)
original = target.read_bytes() if target.exists() else None
try:
    data = json.loads(original.decode("utf-8-sig")) if original is not None else {}
except (UnicodeError, ValueError):
    sys.exit("INVALID_JSON")
if not isinstance(data, dict):
    sys.exit("INVALID_JSON_ROOT")
servers = data.setdefault("mcpServers", {})
if not isinstance(servers, dict):
    sys.exit("INVALID_MCP_SERVERS")
current = servers.get("powerbi-mcp-bridge")
if "powerbi-mcp-bridge" in servers:
    args = current.get("args") if isinstance(current, dict) else None
    command = current.get("command") if isinstance(current, dict) else None
    command_owned = isinstance(command, str) and (
        os.path.normcase(os.path.realpath(command)) ==
        os.path.normcase(os.path.realpath(py))
    )
    if not command_owned or not isinstance(args, list) or not any(
        isinstance(arg, str) and os.path.normcase(os.path.realpath(arg)) ==
        os.path.normcase(os.path.realpath(srv)) for arg in args
    ):
        sys.exit("FOREIGN_SAME_NAME_ENTRY")
    # Giữ nguyên mọi tuỳ chỉnh người dùng đã thêm vào entry đang trỏ đúng checkout.
    print("MERGE_OK")
    sys.exit(0)
entry = {"command": py, "args": ["-u", srv], "env": {"PYTHONUNBUFFERED": "1"}}
servers["powerbi-mcp-bridge"] = {"type": "stdio", **entry} if with_type else entry
out = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
json.loads(out.decode("utf-8"))
if original == out:
    print("MERGE_OK")
    sys.exit(0)
fd, tmp = tempfile.mkstemp(prefix=target.name + ".ads-", suffix=".tmp", dir=target.parent)
try:
    with os.fdopen(fd, "wb") as f:
        f.write(out)
    if (target.read_bytes() if target.exists() else None) != original:
        sys.exit("CONFIG_CHANGED_DURING_MERGE")
    os.replace(tmp, path)
    tmp = None
    try:
        json.loads(target.read_bytes().decode("utf-8"))
    except Exception:
        try:
            if original is not None:
                fd, restore = tempfile.mkstemp(prefix=target.name + ".restore-", dir=target.parent)
                try:
                    with os.fdopen(fd, "wb") as f:
                        f.write(original)
                    os.replace(restore, path)
                finally:
                    if os.path.exists(restore):
                        os.unlink(restore)
            else:
                target.unlink()
        except Exception:
            sys.exit("POSTWRITE_JSON_RESTORE_FAILED")
        sys.exit("POSTWRITE_JSON_INVALID_RESTORED")
finally:
    if tmp is not None and os.path.exists(tmp):
        os.unlink(tmp)
print("MERGE_OK")
'@
    Backup-File $Path
    # Ten DUY NHAT theo tien trinh: ten co dinh thi hai lan chay song song (pytest goi
    # harness, harness goi installer) xoa file cua nhau giua chung -> "can't open file".
    $tmpPy = Join-Path $env:TEMP ("powerbi-merge-mcp-$PID-" + [guid]::NewGuid().ToString("N") + ".py")
    Write-Utf8NoBom $tmpPy $mergePy
    # KHONG dung `2>&1` phia PowerShell voi native command khi $ErrorActionPreference=Stop:
    # stderr bi boc thanh NativeCommandError TERMINATING -> script chet TRUOC khi toi nhanh
    # xu ly loi ben duoi, va installer dung o giua (buoc 4 khong chay).
    # Cung KHONG boc qua cmd /c: tham so o day la JSON co dau nhay, cmd se lam hong.
    # Cach an toan: ha ErrorActionPreference dung quanh loi goi roi tra lai.
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $helperExit = 1
    $typeArg = if ($NoType) { 'no-type' } else { 'stdio' }
    try     { $out = & $venvPy $tmpPy $Path $pyJson $srvJson $typeArg 2>&1; $helperExit = $LASTEXITCODE }
    finally { $ErrorActionPreference = $prevEap
              # Dọn trong finally: ném giữa chừng mà dọn ở ngoài thì mỗi lần chạy để lại
              # một file tạm TÊN DUY NHẤT -> rác tích tụ trong %TEMP% thay vì bị ghi đè.
              Remove-Item $tmpPy -Force -ErrorAction SilentlyContinue }
    # PHAI doc $LASTEXITCODE, va khop NEO DONG. Truoc day chi tim chuoi con trong
    # stdout+stderr da gop: helper in "MERGE_OK" roi exit 1, hoac traceback tinh co
    # chua chuoi do, deu lam installer bao dang ky THANH CONG trong khi khong co gi xay ra.
    # `"$out"` nối MẢNG bằng DẤU CÁCH, không phải newline -> neo `(?m)^...$` chỉ khớp khi
    # MERGE_OK là TOÀN BỘ output. Python in thêm một dòng warning bất kỳ (PYTHONWARNINGS,
    # sitecustomize...) là merge THÀNH CÔNG mà installer báo thất bại, khuyên restore .bak oan.
    $outText = (@($out) | ForEach-Object { "$_" }) -join "`n"
    if ($helperExit -eq 0 -and $outText -match "(?m)^MERGE_OK\s*$") { Ok "Đã ghi + validate cấu hình MCP trong $Path"; Remove-UnchangedBackup $Path }
    else { Err "Merge JSON thất bại ($out). Cấu hình trước đó được giữ nguyên hoặc phục hồi từ bản sao lưu."; }
    if ($outText -match "FOREIGN_SAME_NAME_ENTRY") { Info $foreignHint }
}

function Register-Claude {
    Info "Claude Code..."
    Merge-McpJson (Join-Path $env:USERPROFILE ".claude.json")
}
function Register-Antigravity { Info "Antigravity..."; Merge-McpJson (Join-Path $env:USERPROFILE ".gemini\antigravity\mcp_config.json") }
function Register-ClaudeDesktop {
    Info "Claude Desktop (chỉ MCP, không có skill)..."
    if (-not $env:APPDATA) { Err "Không xác định được %APPDATA%; giữ nguyên cấu hình Claude Desktop."; return }
    Merge-McpJson (Join-Path $env:APPDATA "Claude\claude_desktop_config.json") -NoType
}
function Register-Codex {
    Info "Codex..."
    $cfg = Join-Path $env:USERPROFILE ".codex\config.toml"
    $dir = Split-Path -Parent $cfg
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if (-not (Test-Path $venvPy)) {
        Err "Không có Python >= 3.11 để kiểm TOML an toàn; giữ nguyên $cfg."
        return
    }
    $mergePy = @'
import json, os, pathlib, re, sys, tempfile, tomllib

path, py, srv = sys.argv[1], sys.argv[2], sys.argv[3]
target = pathlib.Path(path)
original = target.read_bytes() if target.exists() else None
try:
    text = original.decode("utf-8-sig") if original is not None else ""
    parsed = tomllib.loads(text)
except (UnicodeError, tomllib.TOMLDecodeError):
    sys.exit("INVALID_TOML")
servers = parsed.get("mcp_servers", {})
if not isinstance(servers, dict):
    sys.exit("INVALID_MCP_SERVERS")
current = servers.get("powerbi-mcp-bridge")
if current is not None:
    args = current.get("args") if isinstance(current, dict) else None
    command = current.get("command") if isinstance(current, dict) else None
    command_owned = isinstance(command, str) and (
        os.path.normcase(os.path.realpath(command)) ==
        os.path.normcase(os.path.realpath(py))
    )
    if not command_owned or not isinstance(args, list) or not any(
        isinstance(arg, str) and os.path.normcase(os.path.realpath(arg)) ==
        os.path.normcase(os.path.realpath(srv)) for arg in args
    ):
        sys.exit("FOREIGN_SAME_NAME_ENTRY")
    # Không viết lại block đã trỏ đúng checkout: giữ enabled/env/timeout của người dùng.
    print("MERGE_OK")
    sys.exit(0)

# Chỉ thay đúng table của mình. Các table khác, kể cả table dạng [[array]], được giữ.
own_header = re.compile(
    r"^[ \t]*\[mcp_servers\.powerbi-mcp-bridge(?:\.[^\]\r\n]+)?\]"
    r"[ \t]*(?:#.*)?$"
)
remaining = []
skip = False
found = False
for line in text.splitlines(keepends=True):
    header = line.rstrip("\r\n")
    if re.match(r"^[ \t]*\[", header):
        skip = bool(own_header.fullmatch(header))
        found = found or skip
    if not skip:
        remaining.append(line)
if current is not None and not found:
    sys.exit("UNSUPPORTED_OWN_ENTRY_LAYOUT")
body = "".join(remaining).rstrip()
if body:
    body += "\n\n"
block = (
    "[mcp_servers.powerbi-mcp-bridge]\n"
    "command = " + json.dumps(py, ensure_ascii=False) + "\n"
    "args = [\"-u\", " + json.dumps(srv, ensure_ascii=False) + "]\n\n"
    "[mcp_servers.powerbi-mcp-bridge.env]\n"
    "PYTHONUNBUFFERED = \"1\"\n"
)
out = (body + block).encode("utf-8")
try:
    tomllib.loads(out.decode("utf-8"))
except tomllib.TOMLDecodeError:
    sys.exit("MERGED_TOML_INVALID")
if original == out:
    print("MERGE_OK")
    sys.exit(0)
fd, tmp = tempfile.mkstemp(prefix=target.name + ".ads-", suffix=".tmp", dir=target.parent)
try:
    with os.fdopen(fd, "wb") as f:
        f.write(out)
    if (target.read_bytes() if target.exists() else None) != original:
        sys.exit("CONFIG_CHANGED_DURING_MERGE")
    os.replace(tmp, path)
    tmp = None
    try:
        tomllib.loads(target.read_bytes().decode("utf-8"))
    except Exception:
        try:
            if original is not None:
                fd, restore = tempfile.mkstemp(prefix=target.name + ".restore-", dir=target.parent)
                try:
                    with os.fdopen(fd, "wb") as f:
                        f.write(original)
                    os.replace(restore, path)
                finally:
                    if os.path.exists(restore):
                        os.unlink(restore)
            else:
                target.unlink()
        except Exception:
            sys.exit("POSTWRITE_TOML_RESTORE_FAILED")
        sys.exit("POSTWRITE_TOML_INVALID_RESTORED")
finally:
    if tmp is not None and os.path.exists(tmp):
        os.unlink(tmp)
print("MERGE_OK")
'@
    Backup-File $cfg
    $tmpPy = Join-Path $env:TEMP ("powerbi-merge-toml-$PID-" + [guid]::NewGuid().ToString("N") + ".py")
    Write-Utf8NoBom $tmpPy $mergePy
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $helperExit = 1
    try     { $out = & $venvPy $tmpPy $cfg $pyJson $srvJson 2>&1; $helperExit = $LASTEXITCODE }
    finally { $ErrorActionPreference = $prevEap
              Remove-Item $tmpPy -Force -ErrorAction SilentlyContinue }
    $outText = (@($out) | ForEach-Object { "$_" }) -join "`n"
    if ($helperExit -eq 0 -and $outText -match "(?m)^MERGE_OK\s*$") {
        Ok "Đã ghi + kiểm TOML cấu hình MCP trong $cfg"
        Remove-UnchangedBackup $cfg
    } else {
        Err "Không thể đăng ký Codex ($out). Cấu hình trước đó được giữ nguyên hoặc phục hồi từ bản sao lưu."
        if ($outText -match "FOREIGN_SAME_NAME_ENTRY") { Info $foreignHint }
    }
}
Step "3/4 Đăng ký MCP vào host"
if ($SkipMcp) {
    if ($Only -eq "plugin") { Info "Bỏ qua đăng ký MCP (-Only plugin)." }
    else                    { Warn "Bỏ qua đăng ký host (-SkipHosts)." }
} else {
    if ($Hosts -contains "claude")      { Register-Claude }
    if ($Hosts -contains "codex")       { Register-Codex }
    if ($Hosts -contains "antigravity") { Register-Antigravity }
    if ($Hosts -contains "claude-desktop") { Register-ClaudeDesktop }
}

# ---- Bước 4: host đọc adapter trong repo; nội dung gốc chỉ ở skills/ ----
Step "4/4 Kiểm adapter skill tại repo"
$adapterPy = if (Test-Path $venvPy) { $venvPy } else { 'python' }
Invoke-Native $adapterPy (Join-Path $Root 'scripts\build_host_adapters.py') --check
if ($LASTEXITCODE -ne 0) { Err "Adapter skill lệch nguồn; chạy generator trong repo và review trước khi cài." }
else { Ok "Adapter project-local đồng bộ với 9 skill gốc; không sao chép skill sang host." }

# ---- Smoke test ----
# Không chỉ kiểm import: kiểm luôn 2 năng lực người dùng đụng vào đầu tiên (kit + Knowledge Dir),
# để câu "việc cần làm tiếp" bên dưới nói đúng trạng thái THẬT của máy này thay vì đoán.
$knowledgeReady = $false
if ((-not $SkipVenv) -and (Test-Path $venvPy)) {
    Step "Kiểm thử nhanh"
    $probe = "import importlib;[importlib.import_module(m) for m in ('mcp.server.fastmcp','pyadomd','pandas','msal','dotenv','tabulate')];print('IMPORTS_OK')"
    $out = Invoke-Native $venvPy -c $probe 2>&1
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
    $out2 = Invoke-Native $venvPy -c $probe2 $Root 2>&1
    $probeOk = "$out2" -match "KITS=(\d+)"
    if ($probeOk) { Ok "Kit báo cáo dùng được: $($Matches[1])" }
    else { Warn "Không kiểm được kho kit / Knowledge Dir (probe lỗi): $out2" }
    if ($probeOk) {
        if ("$out2" -match "KNOWLEDGE=yes") { $knowledgeReady = $true; Ok "Knowledge Dir đã thiết lập." }
        else { Info "Knowledge Dir CHƯA thiết lập (bình thường ở máy mới)." }
    }
}

Write-Host "`n=============================================" -ForegroundColor Green
if ($script:HadError) {
    Err "CHƯA HOÀN TẤT — có bước lỗi ở trên (xem dòng [X]). Sửa rồi chạy lại install.ps1."
    Write-Host "Bản sao lưu .bak.$Stamp còn nguyên cạnh mỗi file cấu hình." -ForegroundColor Gray
    exit 1
}
Ok "HOÀN TẤT."
$desktopNote = if ($Hosts -contains 'claude-desktop') { '; Claude Desktop: thoát hẳn từ khay hệ thống rồi mở lại — chỉ có công cụ MCP, không có lệnh /pbi-*' } else { '' }
$nextSetup = if ($knowledgeReady) { "(đã xong — bỏ qua)" } else { "/pbi-setup   -> chỉ định Knowledge Dir (làm 1 lần)" }
Write-Host @"

VIỆC CẦN LÀM TIẾP — 3 bước:
  1. KHỞI ĐỘNG LẠI host để nạp MCP (Claude: 'claude mcp list' để kiểm$desktopNote).
  2. $nextSetup
  3. /pbi-help    -> agent tự liệt kê năng lực và định tuyến việc của bạn.

Server tại : $Root
Cập nhật riêng phần quy trình (không đụng venv/MCP): .\install.ps1 -Only plugin
Gỡ cài     : .\uninstall.ps1
"@ -ForegroundColor Gray

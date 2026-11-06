# Đích venv MCP Power BI: dùng chung cho install.ps1, update.ps1, uninstall.ps1, doctor.ps1 (dot-source).
# Máy có OpcOS  -> <R>\mcp\agent-data-studio\powerbi (R = gốc runtime, tạo bằng `opcos-runtime ensure`).
# Máy không có  -> <checkout>\.venv như trước.
# Quy tắc tìm R khớp hợp đồng runtime-resource-v1 (addressing.root) và các véc-tơ VT1-VT4.
# KHÔNG có khối param: dot-source mà có param sẽ ghi đè biến $Root của người gọi.
# Chạy trực tiếp để in đường (dùng cho test): powershell -File scripts\ads-venv.ps1 --print <Root>

$script:AdsRuntimeCategory = 'mcp'
$script:AdsRuntimeRepoKey = 'agent-data-studio'
$script:AdsRuntimeResourceKey = 'powerbi'

# Gốc runtime R theo thứ tự: OPCOS_RUNTIME -> OPCOS_ROOT\runtime -> ~\OpcOS\runtime (chỉ khi có ~\OpcOS\paths.json,
# ~ = USERPROFILE) -> $null. Biến rỗng/chỉ khoảng trắng coi như không đặt.
function Get-AdsRuntimeRoot {
    $r = [string]$env:OPCOS_RUNTIME
    if ($r.Trim()) { return $r.Trim() }
    $o = [string]$env:OPCOS_ROOT
    if ($o.Trim()) { return (Join-Path $o.Trim() 'runtime') }
    $h = [string]$env:USERPROFILE
    if ($h.Trim() -and (Test-Path -LiteralPath (Join-Path $h 'OpcOS\paths.json') -PathType Leaf)) {
        return (Join-Path $h 'OpcOS\runtime')
    }
    return $null
}

# Đích venv: có R -> R\mcp\agent-data-studio\powerbi; không -> <Root>\.venv.
function Resolve-AdsVenvRoot([string]$Root) {
    $r = Get-AdsRuntimeRoot
    if ($r) { return (Join-Path $r ($script:AdsRuntimeCategory + '\' + $script:AdsRuntimeRepoKey + '\' + $script:AdsRuntimeResourceKey)) }
    return (Join-Path $Root '.venv')
}

# CLI opcos-runtime nằm ở <R>\..\system\operations\runtime\opcos-runtime.ps1; $null nếu không có R hoặc thiếu tệp.
function Get-OpcosRuntimeCli {
    $r = Get-AdsRuntimeRoot
    if (-not $r) { return $null }
    $cli = [System.IO.Path]::GetFullPath((Join-Path $r '..\system\operations\runtime\opcos-runtime.ps1'))
    if (Test-Path -LiteralPath $cli -PathType Leaf) { return $cli }
    return $null
}

# Đọc tệp khai sinh .opcos-resource.json của tài nguyên; $null nếu không có hoặc hỏng (không ném lỗi).
function Read-AdsResourceManifest([string]$VenvRoot) {
    $file = Join-Path $VenvRoot '.opcos-resource.json'
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { return $null }
    try { return (Get-Content -LiteralPath $file -Raw -Encoding UTF8 | ConvertFrom-Json) } catch { return $null }
}

# Tệp khai sinh thuộc repo này (repoKey và installed_by đều là agent-data-studio)?
function Test-AdsManifestOwned($Manifest) {
    return [bool]($Manifest -and $Manifest.repoKey -eq $script:AdsRuntimeRepoKey -and
        $Manifest.installed_by -eq $script:AdsRuntimeRepoKey)
}

if ($MyInvocation.InvocationName -ne '.' -and $args.Count -ge 2 -and $args[0] -eq '--print') {
    Write-Output (Resolve-AdsVenvRoot $args[1])
}

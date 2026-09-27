<#
.SYNOPSIS
  Tạo ZIP public từ commit sạch của Agent Data Studio.
.DESCRIPTION
  Chỉ đóng gói bytes trong HEAD. Không có tùy chọn đưa .env, credential hay workspace vào gói.
.PARAMETER OutDir
  Thư mục ngoài repo để đặt ZIP; bắt buộc khai báo tường minh.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string] $OutDir
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = [System.IO.Path]::GetFullPath($Root).TrimEnd('\')
$target = [System.IO.Path]::GetFullPath($OutDir).TrimEnd('\')
if ($target.Equals($Root, [StringComparison]::OrdinalIgnoreCase) -or
    $target.StartsWith($Root + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Thư mục ZIP phải nằm ngoài repo source.'
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Cần Git để đóng gói từ commit.' }
$dirty = & git -C $Root status --porcelain --untracked-files=all
if ($LASTEXITCODE -ne 0) { throw 'Không đọc được trạng thái Git.' }
if ($dirty) { throw 'Checkout còn thay đổi; review và commit trước khi tạo artifact public.' }
$forced = & git -C $Root ls-files --cached --ignored --exclude-standard
if ($LASTEXITCODE -ne 0) { throw 'Không kiểm được Git index.' }
if ($forced) { throw 'Git index có file bị ignore nhưng đã track; kiểm tra trước khi đóng gói.' }
$tracked = @(& git -C $Root ls-tree -r --name-only HEAD)
if ($LASTEXITCODE -ne 0 -or $tracked.Count -eq 0) { throw 'Không kiểm được danh sách file trong HEAD.' }
$allowedRoots = @('.agents', '.claude', '.claude-plugin', '.codex-plugin', '.github',
    'LICENSES', 'agents', 'commands', 'docs', 'hosts',
    'powerbi_agent', 'report-templates', 'samples', 'scripts', 'skills', 'templates',
    'tests', 'upstream', 'workflows')
$allowedFiles = @('.env.example', '.gitattributes', '.gitignore', 'AGENTS.md', 'CLAUDE.md', 'GEMINI.md',
    'INDEX.md', 'INSTALL.md', 'LICENSE', 'NOTICE.md', 'README.md', 'README.vi.md', 'ROADMAP.md', 'START-HERE.md',
    'doctor.ps1', 'install.ps1', 'mcp_server_powerbi.py', 'pack.ps1', 'policy.example.json',
    'pyproject.toml', 'requirements.loose.txt', 'requirements.txt',
    'THIRD_PARTY_NOTICES.md', 'uninstall.ps1', 'update.ps1')
$required = @('.env.example', 'LICENSE', 'THIRD_PARTY_NOTICES.md',
    'LICENSES/microsoft-skills-for-fabric.txt', 'install.ps1', 'doctor.ps1')
foreach ($name in $required) {
    if ($name -notin $tracked) { throw "HEAD thiếu file bắt buộc cho gói public: $name" }
}
foreach ($name in $tracked) {
    $normalized = $name.Replace('\', '/')
    $rootName = ($normalized -split '/', 2)[0]
    if (($normalized -notin $allowedFiles) -and ($rootName -notin $allowedRoots)) {
        throw "HEAD chứa file ngoài allowlist public: $normalized"
    }
    if ($normalized -ne '.env.example' -and
        $normalized -match '(^|/)(workspace|\.venv|\.env(?:\.[^/]*)?|config\.env|secrets\.env|policy\.json|knowledge\.config\.json|docs/internal)(/|$)') {
        throw "HEAD chứa dữ liệu/cấu hình riêng: $normalized"
    }
}
# Asset KPIM chia sẻ cho cộng đồng chỉ vào gói khi nhóm asset có PROVENANCE.md trong HEAD
# và gốc repo có NOTICE.md. Nhóm = thư mục hồ sơ dữ liệu, từng kit trong report-templates/,
# hoặc thư mục của workbook mẫu. Nhóm thiếu ghi nguồn vẫn bị chặn như trước.
$trackedSet = @{}
foreach ($name in $tracked) { $trackedSet[$name.Replace('\', '/')] = $true }
$gatedCount = 0
$unapproved = @()
foreach ($name in $tracked) {
    $normalized = $name.Replace('\', '/')
    $group = $null
    if ($normalized -like 'skills/data-mockup/references/kpim/kpim-datasets/*') {
        $group = 'skills/data-mockup/references/kpim/kpim-datasets'
    } elseif ($normalized -like 'report-templates/*/*') {
        $group = 'report-templates/' + ($normalized -split '/')[1]
    } elseif ($normalized -eq 'templates/documents/Project_Management.xlsx') {
        $group = 'templates/documents'
    }
    if (-not $group) { continue }
    $gatedCount++
    if (-not $trackedSet.ContainsKey("$group/PROVENANCE.md")) { $unapproved += $normalized }
}
if ($unapproved.Count -gt 0) {
    throw "HEAD còn $($unapproved.Count) file hồ sơ dữ liệu hoặc tài sản template thiếu PROVENANCE.md trong nhóm; dừng trước khi tạo ZIP."
}
if ($gatedCount -gt 0 -and -not $trackedSet.ContainsKey('NOTICE.md')) {
    throw 'HEAD có asset KPIM nhưng thiếu NOTICE.md ở gốc repo; dừng trước khi tạo ZIP.'
}
$sha = (& git -C $Root rev-parse --short=12 HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or -not $sha) { throw 'Không đọc được commit HEAD.' }
$zip = Join-Path $target "agent-data-studio-$sha.zip"
if (Test-Path -LiteralPath $zip) { throw 'Artifact cùng commit đã tồn tại; không ghi đè.' }
New-Item -ItemType Directory -Path $target -Force | Out-Null
& git -C $Root archive --format=zip --output=$zip HEAD
if ($LASTEXITCODE -ne 0) { throw 'Git archive thất bại.' }
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead($zip)
try {
    $bad = @($archive.Entries | Where-Object {
        $name = $_.FullName.Replace('\','/').ToLowerInvariant()
        $name -match '(^|/)(workspace|\.venv|\.env|config\.env|secrets\.env|policy\.json|knowledge\.config\.json|docs/internal)(/|$)' -or
        $name -eq '.ads-binding.json'
    })
    if ($bad.Count -gt 0) { throw 'Artifact chứa file dữ liệu/cấu hình riêng; không được phát hành.' }
} finally { $archive.Dispose() }
Write-Output "Artifact: $zip"
Write-Output "Commit: $sha"

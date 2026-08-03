<#
.SYNOPSIS
  Đóng gói repo thành .zip mang sang máy khác.

.DESCRIPTION
  Đóng gói theo ALLOWLIST — chỉ những file GIT ĐANG TRACK mới vào zip.

  Vì sao không dùng blacklist như trước: bản cũ copy MỌI thứ ở gốc rồi trừ vài cái, nên
  zip mang theo cả `policy.json` (tên cột PII thật của khách), `knowledge.config.json`
  (đường dẫn cá nhân), `docs/internal/`, cache… — mà zip này sinh ra để ĐƯA CHO NGƯỜI KHÁC.
  Danh sách loại trừ luôn tụt lại phía sau: thêm file riêng tư mới là nó tự lọt.

  Allowlist đảo ngược mặc định: thứ gì chưa được commit thì KHÔNG ra khỏi máy.

.PARAMETER OutDir
  Nơi ghi file zip. Mặc định thư mục hiện tại.
.PARAMETER IncludeEnv
  Kèm `.env` (SECRET + đường dẫn cá nhân). Chỉ dùng khi tự mang sang máy CỦA MÌNH.
#>
[CmdletBinding()]
param(
    [string] $OutDir = ".",
    [switch] $IncludeEnv
)
$ErrorActionPreference = "Stop"
$Root  = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format "yyyyMMdd"
$stage = Join-Path $env:TEMP ("pbimcp-pack-" + (Get-Date -Format "yyyyMMddHHmmss"))
$zip   = Join-Path $OutDir "powerbi-mcp-setup-$Stamp.zip"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Cần git để lấy danh sách file được phép đóng gói (allowlist). Không có git thì DỪNG — không fallback sang copy-tất-cả."
}

try {
    New-Item -ItemType Directory -Path $stage -Force | Out-Null
    if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }

    Write-Host "[i] Đóng gói từ: $Root (allowlist = git ls-files)" -ForegroundColor Cyan
    $files = & git -C $Root ls-files
    if ($LASTEXITCODE -ne 0 -or -not $files) { throw "git ls-files không trả về file nào — dừng để không đóng gói nhầm." }

    foreach ($rel in $files) {
        $src = Join-Path $Root $rel
        if (-not (Test-Path -LiteralPath $src)) { continue }   # file đã xoá nhưng chưa commit
        $dst = Join-Path $stage $rel
        $dir = Split-Path -Parent $dst
        if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        Copy-Item -LiteralPath $src -Destination $dst -Force
    }
    Write-Host "[OK] $($files.Count) file được track -> staging" -ForegroundColor Green

    # .env là NGOẠI LỆ có chủ đích: gitignored nên allowlist không lấy, chỉ thêm khi user yêu cầu rõ.
    if ($IncludeEnv) {
        $envSrc = Join-Path $Root ".env"
        if (Test-Path $envSrc) {
            Copy-Item -LiteralPath $envSrc -Destination (Join-Path $stage ".env") -Force
            Write-Host "[!] ĐÃ KÈM .env — chứa SECRET và đường dẫn cá nhân. Chỉ mang sang máy CỦA BẠN." -ForegroundColor Yellow
        }
    }

    # Chốt an toàn: dù allowlist đã lọc, vẫn khẳng định lại không có file riêng tư nào lọt.
    $forbidden = @('policy.json', 'knowledge.config.json')
    if (-not $IncludeEnv) { $forbidden += '.env' }
    $leaked = Get-ChildItem $stage -Recurse -Force -File -ErrorAction SilentlyContinue |
        Where-Object { $forbidden -contains $_.Name -or $_.FullName -like '*\docs\internal\*' }
    if ($leaked) {
        throw "DỪNG: file riêng tư lọt vào staging: $($leaked.FullName -join ', ')"
    }

    if (Test-Path $zip) { Remove-Item $zip -Force }
    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -Force
    Write-Host "[OK] Đã tạo: $zip" -ForegroundColor Green
    Write-Host "     Bên trong CHỈ có file đã commit — không có policy.json / docs internal / cache." -ForegroundColor Gray
}
finally {
    # finally: hỏng giữa chừng cũng không được để bản sao dữ liệu nằm lại trong %TEMP%.
    if (Test-Path $stage) { Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue }
}

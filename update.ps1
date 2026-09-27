# Update preview; apply only a reviewed commit after staged validation and with rollback journal.
[CmdletBinding()]
param(
    [switch] $Apply,
    [ValidatePattern('^[0-9a-f]{40,64}$')] [string] $ExpectedCommit
)
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath($PSScriptRoot)
function Fail($reason) { Write-Host ('[FAIL] {0}' -f $reason); exit 1 }
# PS 5.1 + Stop biến stderr của lệnh native thành lỗi dừng khi stderr bị chuyển hướng (2>$null ở đây,
# hoặc người gọi gom *>&1/2>&1 vào biến) -> script chết không in [FAIL]. Lệnh native chỉ đánh giá bằng $LASTEXITCODE.
function Invoke-Native { $ErrorActionPreference = 'Continue'; $command, $rest = $args; & $command @rest }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Fail 'Git unavailable.' }
$inside = Invoke-Native git -C $repoRoot rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0 -or [IO.Path]::GetFullPath($inside) -ne $repoRoot) { Fail 'Not this script checkout.' }
$old = Invoke-Native git -C $repoRoot rev-parse --verify HEAD 2>$null
if ($LASTEXITCODE -ne 0 -or $old -notmatch '^[0-9a-f]{40,64}$') { Fail 'Current commit unknown.' }
$branch = Invoke-Native git -C $repoRoot symbolic-ref --quiet --short HEAD 2>$null
if ($LASTEXITCODE -ne 0 -or -not $branch) { Fail 'Detached HEAD.' }
$dirty = Invoke-Native git -C $repoRoot status --porcelain=v1 --untracked-files=all
if ($LASTEXITCODE -ne 0 -or $dirty) { Fail 'Checkout has uncommitted or untracked files.' }
$upstream = Invoke-Native git -C $repoRoot rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null
if ($LASTEXITCODE -ne 0 -or -not $upstream -or $upstream -notmatch '^[^/]+/.+$') { Fail 'Branch upstream unavailable.' }
$remote = ($upstream -split '/', 2)[0]
# CIM trả CommandLine đúng dạng lúc khởi chạy, kể cả tên ngắn 8.3 (DUCNGU~1) và dạng trộn ngắn-dài
# từng đoạn -> so với mọi dạng của đường. Ổ tắt 8.3 thì ShortName = tên dài (chỉ còn 1 dạng).
function Get-PathForms([string] $path) {
    $fso = New-Object -ComObject Scripting.FileSystemObject
    $parts = $path.TrimEnd('\').Split('\')
    $forms = @($parts[0])
    $prefix = $parts[0]
    for ($i = 1; $i -lt $parts.Count; $i++) {
        $part = $parts[$i]
        $prefix = $prefix + '\' + $part
        $short = if (Test-Path -LiteralPath $prefix -PathType Container) { $fso.GetFolder($prefix).ShortName } else { '' }
        $forms = @(foreach ($form in $forms) {
            $form + '\' + $part
            if ($short -and $short -ne $part) { $form + '\' + $short }
        })
        if ($forms.Count -gt 1024) { throw 'PATH_FORMS_OVERFLOW' }
    }
    return $forms
}
try {
    $repoForms = Get-PathForms $repoRoot
    $active = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" -ErrorAction Stop |
        Where-Object {
            $commandLine = $_.CommandLine
            # Gốc phải dừng ở biên đoạn (\ hoặc / sau gốc, nháy, khoảng trắng, hết chuỗi): clone anh em
            # có tiền tố giống (checkout2, checkout-old) không phải checkout này.
            $commandLine -and @($repoForms | Where-Object {
                [regex]::IsMatch($commandLine, [regex]::Escape($_) + '(?=[\\/"\s]|$)', 'IgnoreCase, CultureInvariant')
            }).Count -gt 0
        })
} catch {
    if ($_.Exception.Message -eq 'PATH_FORMS_OVERFLOW') { Fail 'PATH_FORMS_OVERFLOW: too many 8.3 short-name path forms; cannot establish whether this checkout is in use.' }
    Fail 'Cannot establish whether this checkout is in use.'
}
if ($active.Count -gt 0) { Fail 'A Python process is using this checkout.' }
Invoke-Native git -C $repoRoot fetch --no-tags $remote
if ($LASTEXITCODE -ne 0) { Fail 'Fetch failed. Checkout was not changed.' }
$target = Invoke-Native git -C $repoRoot rev-parse --verify $upstream 2>$null
if ($LASTEXITCODE -ne 0 -or $target -notmatch '^[0-9a-f]{40,64}$') { Fail 'Fetched commit unknown.' }
if ($target -eq $old) { Write-Host ('[PASS] UP_TO_DATE source={0}' -f $old); exit 0 }
Invoke-Native git -C $repoRoot merge-base --is-ancestor $old $target
if ($LASTEXITCODE -ne 0) { Fail 'Upstream diverged. No update was applied.' }
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) { Fail 'Python is required for candidate validation.' }
$check = @'
import subprocess
import sys

root, old, target = sys.argv[1:]
def git(*args):
    return subprocess.check_output(["git", "-C", root, *args], stderr=subprocess.DEVNULL)
def blob(ref, name):
    return git("show", ref + ":" + name)
try:
    names = git("ls-tree", "-r", "--name-only", target).decode("utf-8").splitlines()
    required = {"install.ps1", "uninstall.ps1", "doctor.ps1", "update.ps1",
                "mcp_server_powerbi.py", "requirements.txt", "scripts/update_release.py"}
    if not required.issubset(names):
        print("CANDIDATE_FAIL missing lifecycle files")
        sys.exit(1)
    changed = git("diff", "--no-renames", "--name-only", "-z", old, target).decode("utf-8").split("\0")
    if any(name.lower() == ".gitignore" or name.lower().endswith("/.gitignore") for name in changed if name):
        print("CANDIDATE_FAIL ignore rules changed; manual upgrade required")
        sys.exit(1)
    private_roots = {"workspace", ".venv", "lab", "out", "audit"}
    private_files = {".ads-binding.json", "config.env", "secrets.env", "policy.json", "knowledge.config.json"}
    for name in names:
        parts = name.replace("\\", "/").lower().split("/")
        if (parts[0] in private_roots or name.lower() in private_files
                or parts[0].startswith(".env") and name != ".env.example"
                or parts[:2] == ["docs", "internal"]):
            print("CANDIDATE_FAIL private path")
            sys.exit(1)
    ignored = subprocess.run(
        ["git", "-C", root, "check-ignore", "--no-index", "-z", "--stdin"],
        input="\0".join(names) + "\0", capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=False, timeout=60,
    )
    if ignored.returncode != 1:
        print("CANDIDATE_FAIL ignored path or ignore check")
        sys.exit(1)
    py_names = [name for name in names if name.endswith(".py")]
    for name in py_names:
        compile(blob(target, name), name, "exec")
    if blob(old, "requirements.txt") != blob(target, "requirements.txt"):
        print("DEPENDENCIES_CHANGED")
    else:
        print("DEPENDENCIES_UNCHANGED")
    print("PYTHON_SYNTAX_PASS " + str(len(py_names)))
except Exception:
    print("CANDIDATE_FAIL verification error")
    sys.exit(1)
'@
$checkFile = Join-Path ([IO.Path]::GetTempPath()) ('ads-update-check-' + [guid]::NewGuid().ToString('N') + '.py')
[IO.File]::WriteAllText($checkFile, $check, (New-Object Text.UTF8Encoding($false)))
try {
    $result = Invoke-Native $pythonCommand.Source $checkFile $repoRoot $old $target 2>$null
    $checkExit = $LASTEXITCODE
} finally { Remove-Item -LiteralPath $checkFile -Force -ErrorAction SilentlyContinue }
if ($checkExit -ne 0) { Fail 'Candidate failed static checks. No update was applied.' }
if (@($result) -contains 'DEPENDENCIES_CHANGED') { Fail 'Dependencies changed. No update was applied.' }
if (@($result) -notcontains 'DEPENDENCIES_UNCHANGED') { Fail 'Candidate dependency check missing. No update was applied.' }
foreach ($file in @('install.ps1','uninstall.ps1','doctor.ps1','update.ps1')) {
    $source = ((Invoke-Native git -C $repoRoot show ($target + ':' + $file)) -join [Environment]::NewLine).TrimStart([char]0xFEFF)
    if ($LASTEXITCODE -ne 0) { Fail 'Candidate PowerShell source unavailable.' }
    $tokens = $null; $errors = $null
    [Management.Automation.Language.Parser]::ParseInput($source, [ref]$tokens, [ref]$errors) | Out-Null
    if ($errors.Count -gt 0) { Fail 'Candidate PowerShell syntax failed.' }
}
$dirty = Invoke-Native git -C $repoRoot status --porcelain=v1 --untracked-files=all
if ($LASTEXITCODE -ne 0 -or $dirty) { Fail 'Checkout changed during preflight.' }
Write-Host ('[PASS] CANDIDATE_STATIC_CHECK old={0} target={1}' -f $old, $target)
Write-Host '[NOT_CHECKED] Static preview does not prove candidate startup, host restart, or Power BI connection.'
if (-not $Apply) {
    Write-Host '[PENDING] READY_FOR_REVIEW. No checkout, venv, station, or host was changed.'
    Write-Host 'Review the target commit before running -Apply -ExpectedCommit <full SHA>.'
    exit 2
}
if (-not $ExpectedCommit -or $ExpectedCommit -ne $target) {
    Fail 'Apply requires -ExpectedCommit matching the reviewed upstream SHA.'
}
$helper = Join-Path $repoRoot 'scripts\update_release.py'
if (-not (Test-Path -LiteralPath $helper -PathType Leaf)) { Fail 'Updater helper missing in current checkout.' }
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
$marker = Join-Path $repoRoot '.venv\.ads-venv-owned'
if ($env:POWERBI_INSTALL_PYTHON) {
    $runtimePython = $env:POWERBI_INSTALL_PYTHON
} elseif ((Test-Path -LiteralPath $venvPython -PathType Leaf) -and
          (Test-Path -LiteralPath $marker -PathType Leaf) -and
          (Get-Content -LiteralPath $marker -Raw -Encoding UTF8).Trim() -eq $repoRoot.TrimEnd('\', '/')) {
    $runtimePython = $venvPython
} else { Fail 'Owned runtime Python unavailable. Run installer before applying an update.' }
if (-not (Test-Path -LiteralPath $runtimePython -PathType Leaf)) { Fail 'Configured runtime Python unavailable.' }
Invoke-Native $runtimePython $helper --repo $repoRoot --old $old --target $target --runtime-python $runtimePython
if ($LASTEXITCODE -ne 0) { Fail 'Apply or rollback failed; inspect update journal and checkout status.' }
Write-Host ('[PENDING] Source updated to {0}; restart each registered host and verify its source path.' -f $target)
exit 0

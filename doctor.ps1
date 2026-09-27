[CmdletBinding()]
param(
    [ValidateSet('claude', 'codex', 'antigravity')]
    [string[]] $Hosts = @('codex'),
    [ValidateRange(1, 60)] [int] $TimeoutSeconds = 10,
    # Thử kết nối Power BI Desktop đang mở bằng EVALUATE ROW("x",1); mặc định không chạm Desktop.
    [switch] $ProbeDesktop
)
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$server = Join-Path $repoRoot 'mcp_server_powerbi.py'
$failed = $false
function Report($state, $area, $detail) {
    Write-Host ('[{0}] {1}: {2}' -f $state, $area, $detail)
    if ($state -eq 'FAIL') { $script:failed = $true }
}
if (Test-Path -LiteralPath $server -PathType Leaf) { Report PASS source 'MCP entrypoint exists.' }
else { Report FAIL source 'MCP entrypoint missing.' }
$adapterPaths = @()
if ($Hosts -contains 'codex' -or $Hosts -contains 'antigravity') { $adapterPaths += '.agents\skills' }
if ($Hosts -contains 'claude') { $adapterPaths += '.claude\skills' }
foreach ($relative in $adapterPaths) {
    if (Test-Path -LiteralPath (Join-Path $repoRoot $relative) -PathType Container) { Report PASS adapter "$relative exists." }
    else { Report FAIL adapter "$relative missing." }
}
$station = Join-Path $repoRoot 'workspace'
$binding = Join-Path $repoRoot '.ads-binding.json'
if (Test-Path -LiteralPath $binding -PathType Leaf) {
    try {
        $data = Get-Content -LiteralPath $binding -Raw -Encoding UTF8 | ConvertFrom-Json
        if (-not $data.station_root -or -not [IO.Path]::IsPathRooted([string]$data.station_root)) { throw 'invalid binding' }
        $station = [string]$data.station_root
        if (Test-Path -LiteralPath $station -PathType Container) { Report PASS station 'Bound station exists.' }
        else { Report FAIL station 'Bound station missing.' }
    } catch { Report FAIL station 'Binding malformed.' }
} elseif ($env:ADS_DATA) {
    Report WARN station 'ADS_DATA is set but this checkout has no station binding. Run install.ps1 to confirm the existing station.'
} elseif (Test-Path -LiteralPath $station -PathType Container) { Report PASS station 'Basic workspace exists.' }
else { Report WARN station 'Basic workspace has not been created.' }
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
$python = if (Test-Path -LiteralPath $venvPython -PathType Leaf) { $venvPython } elseif ($env:POWERBI_INSTALL_PYTHON) { $env:POWERBI_INSTALL_PYTHON } else { $null }
if (-not $python -or -not (Test-Path -LiteralPath $python -PathType Leaf)) {
    Report FAIL python 'Checkout Python unavailable.'
    Report NOT_CHECKED import 'Python unavailable.'
    Report NOT_CHECKED driver 'Python unavailable.'
    Report NOT_CHECKED startup 'Python unavailable.'
    Report NOT_CHECKED connection 'Python unavailable.'
    foreach ($h in $Hosts) { Report NOT_CHECKED mcp "$h registration not checked." }
} else {
    Report PASS python 'Python executable exists.'
    $probe = @'
import importlib.util, json, os, sys, tomllib
from pathlib import Path
root, server, profile, selected = sys.argv[1:5]
probe_desktop = sys.argv[5:6] == ["1"]
sys.path.insert(0, root)
print("IMPORT_" + ("PASS" if all(importlib.util.find_spec(x) for x in ("powerbi_agent", "mcp", "pydantic", "dotenv")) else "FAIL"))
print("DRIVER_" + ("PASS" if all(importlib.util.find_spec(x) for x in ("clr", "pyadomd")) else "WARN"))
try:
    for name in ("mcp_server_powerbi.py", "powerbi_agent/app.py"):
        compile(Path(root, name).read_bytes(), name, "exec")
    print("SYNTAX_PASS")
except Exception:
    print("SYNTAX_FAIL")
def station_adomd_lib_dir():
    # Probe tắt load_dotenv nên đọc RIÊNG ADOMD_LIB_DIR từ config.env của trạm đang dùng
    # (chọn trạm theo quy tắc engine); không nạp biến nào khác, không đọc file secret.
    if "ADOMD_LIB_DIR" in os.environ:
        return None  # biến môi trường thắng config.env như load_dotenv(override=False)
    try:
        import io, re, dotenv
        from powerbi_agent import _env
        path = Path(_env.env_file())
        if not path.is_file():
            return None
        value = None
        for line in path.read_text(encoding="utf-8").splitlines():
            if re.match(r"\s*(export\s+)?ADOMD_LIB_DIR\s*=", line):
                value = dotenv.dotenv_values(stream=io.StringIO(line)).get("ADOMD_LIB_DIR")
        return value
    except Exception:
        # Không nuốt im: không xác định được trạm thì báo mã riêng (không in lý do/đường dẫn).
        print("CONNECTION_STATION_UNRESOLVED")
        return None
if probe_desktop:
    lib_dir = station_adomd_lib_dir()
    if lib_dir is not None:
        os.environ["ADOMD_LIB_DIR"] = lib_dir
try:
    import tempfile
    with tempfile.TemporaryDirectory(prefix="ads-doctor-station-") as station:
        os.environ["ADS_DATA"] = station
        import dotenv
        dotenv.load_dotenv = lambda *args, **kwargs: False
        from powerbi_agent import _env
        _env.data_dir = lambda: station
        _env.env_file = lambda: str(Path(station, "config.env"))
        _env.secrets_file = lambda: str(Path(station, "secrets.env"))
        from powerbi_agent import app
        manager = getattr(app.mcp, "_tool_manager", None)
        tools = manager.list_tools() if manager is not None else []
        print("STARTUP_PASS" if len(tools) >= 16 else "STARTUP_FAIL")
except Exception:
    print("STARTUP_FAIL")
if probe_desktop and "powerbi_agent.app" in sys.modules:
    # Chỉ in mã trạng thái; lỗi kết nối được che (không in thông điệp/đường dẫn/model).
    try:
        from powerbi_agent.discovery import find_active_pbi_ports
        instances = find_active_pbi_ports()
        if not instances:
            print("CONNECTION_NO_INSTANCE")
        elif not sys.modules["powerbi_agent.app"].ADOMD_LOADED:
            print("CONNECTION_NO_ADOMD")
        else:
            from powerbi_agent.tools_query import _query_df
            answered = False
            for inst in instances:
                try:
                    catalogs = _query_df(inst["port"], None, "SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS")
                    model_id = str(catalogs.iloc[0, 0]) if not catalogs.empty else None
                    if not _query_df(inst["port"], model_id, 'EVALUATE ROW("x", 1)').empty:
                        answered = True
                        break
                except Exception:
                    pass
            print("CONNECTION_PASS" if answered else "CONNECTION_FAIL")
    except Exception:
        print("CONNECTION_FAIL")
for host, kind, relative in (
    ("claude", "json", ".claude.json"),
    ("codex", "toml", ".codex/config.toml"),
    ("antigravity", "json", ".gemini/antigravity/mcp_config.json"),
):
    if host not in selected.split(","):
        continue
    path = Path(profile, relative)
    if not path.exists():
        print(host + "_ABSENT")
        continue
    try:
        raw = path.read_text(encoding="utf-8-sig")
        data = (json.loads(raw) if kind == "json" else tomllib.loads(raw)) if raw.strip() else {}
        entry = data.get("mcpServers" if kind == "json" else "mcp_servers", {}).get("powerbi-mcp-bridge")
        args = entry.get("args", []) if isinstance(entry, dict) else []
        owned = any(isinstance(a, str) and os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(server)) for a in args)
        print(host + ("_PASS" if owned else "_FOREIGN" if entry is not None else "_ABSENT"))
    except Exception:
        print(host + "_INVALID")
'@
    $probeFile = Join-Path ([IO.Path]::GetTempPath()) ('ads-doctor-' + [guid]::NewGuid().ToString('N') + '.py')
    [IO.File]::WriteAllText($probeFile, $probe, (New-Object Text.UTF8Encoding($false)))
    # Tiến trình con thay cho Start-Job: job PS 5.1 cần Persistence Path dưới hồ sơ người dùng,
    # hỏng khi USERPROFILE trỏ hồ sơ trống hoặc bị hạn chế. Stdout/stderr ghi ra file tạm rồi xoá.
    $probeOut = [IO.Path]::ChangeExtension($probeFile, '.out')
    $probeErr = [IO.Path]::ChangeExtension($probeFile, '.err')
    $proc = $null
    try {
        $probeArgs = @($probeFile, $repoRoot, $server, [string]$env:USERPROFILE, ($Hosts -join ','), $(if ($ProbeDesktop) { '1' } else { '0' })) | ForEach-Object {
            # Quy tắc tách tham số Windows: nhân đôi dấu \ đứng trước " hoặc ở cuối, rồi bọc trong ".
            '"' + (([string]$_ -replace '(\\*)"', '$1$1\"') -replace '(\\+)$', '$1$1') + '"'
        }
        $timedOut = $false
        $lines = @()
        try {
            $proc = Start-Process -FilePath $python -ArgumentList ($probeArgs -join ' ') -NoNewWindow -PassThru `
                -RedirectStandardOutput $probeOut -RedirectStandardError $probeErr
        } catch { $proc = $null }
        # Dò cổng Desktop (tối đa 10 giây) và truy vấn thử cần thêm thời gian ngoài phần nạp engine.
        $waitSeconds = $TimeoutSeconds
        if ($ProbeDesktop) { $waitSeconds += 30 }
        if ($proc) {
            if (-not $proc.WaitForExit($waitSeconds * 1000)) {
                $timedOut = $true
                try { $proc.Kill() } catch { }
                [void]$proc.WaitForExit(5000)
            } else {
                $proc.WaitForExit()  # đã thoát; bảo đảm luồng ghi file đã xả xong
            }
            if (-not $timedOut -and (Test-Path -LiteralPath $probeOut -PathType Leaf)) {
                $lines = @(Get-Content -LiteralPath $probeOut -Encoding UTF8 | ForEach-Object { "$_".Trim() })
            }
        }
        if ($timedOut) {
            Report FAIL import "Probe timed out after $waitSeconds seconds."
            Report NOT_CHECKED driver 'Probe timed out.'
            Report NOT_CHECKED startup 'Probe timed out.'
            Report NOT_CHECKED connection 'Probe timed out.'
            foreach ($h in $Hosts) { Report NOT_CHECKED mcp "$h registration not checked." }
        } else {
            if ($lines -contains 'IMPORT_PASS') { Report PASS import 'Required package modules found; server startup not checked.' }
            else { Report FAIL import 'Required package modules missing or probe failed.' }
            if ($lines -contains 'DRIVER_PASS') { Report PASS driver 'ADOMD Python modules found; live connection not checked.' }
            elseif ($lines -contains 'DRIVER_WARN') { Report WARN driver 'ADOMD Python modules missing; CSV may still work.' }
            else { Report NOT_CHECKED driver 'No driver result.' }
            if ($lines -contains 'SYNTAX_PASS') { Report PASS syntax 'Entrypoint and app Python syntax compile.' }
            else { Report FAIL syntax 'Entrypoint or app syntax failed.' }
            if ($lines -contains 'STARTUP_PASS') { Report PASS startup 'App imports and registers at least 16 MCP tools with isolated empty station.' }
            else { Report FAIL startup 'App import or tool registration failed in isolated station.' }
            # Không xác định được trạm: ghi chú vào chính dòng connection (giữ một dòng mỗi mục).
            $stationNote = if ($lines -contains 'CONNECTION_STATION_UNRESOLVED') { ' Station config unresolved (CONNECTION_STATION_UNRESOLVED); station ADOMD_LIB_DIR not applied.' } else { '' }
            if (-not $ProbeDesktop) { Report NOT_CHECKED connection 'Live host MCP handshake and Power BI Desktop connection not attempted.' }
            elseif ($lines -contains 'CONNECTION_PASS') { Report PASS connection ('Power BI Desktop answered EVALUATE ROW("x",1); live host MCP handshake not checked.' + $stationNote) }
            elseif ($lines -contains 'CONNECTION_NO_INSTANCE') { Report NOT_CHECKED connection ('Power BI Desktop chưa mở — mở report rồi chạy lại.' + $stationNote) }
            elseif ($lines -contains 'CONNECTION_NO_ADOMD') { Report FAIL connection ('Power BI Desktop is open but ADOMD.NET is not loaded; install SSMS/ADOMD.NET or fix ADOMD_LIB_DIR.' + $stationNote) }
            elseif ($lines -contains 'CONNECTION_FAIL') { Report FAIL connection ('Power BI Desktop is open but EVALUATE ROW("x",1) failed; details hidden.' + $stationNote) }
            else { Report NOT_CHECKED connection ('No connection result.' + $stationNote) }
            foreach ($h in $Hosts) {
                if ($lines -contains ($h + '_PASS')) { Report PASS mcp "$h points to this checkout." }
                elseif ($lines -contains ($h + '_FOREIGN')) { Report WARN mcp "$h same-name entry points elsewhere." }
                elseif ($lines -contains ($h + '_INVALID')) { Report FAIL mcp "$h config cannot be parsed." }
                else { Report WARN mcp "$h has no registration for this checkout." }
            }
        }
    } finally {
        if ($proc) { $proc.Dispose() }
        foreach ($tempFile in @($probeFile, $probeOut, $probeErr)) {
            Remove-Item -LiteralPath $tempFile -Force -ErrorAction SilentlyContinue
        }
    }
}
foreach ($h in $Hosts) {
    if (Get-Command $h -ErrorAction SilentlyContinue) { Report PASS host "$h command available." }
    # CLI của Antigravity có tên `agy`; vẫn nhận lệnh `antigravity` nếu máy có.
    elseif ($h -eq 'antigravity' -and (Get-Command agy -ErrorAction SilentlyContinue)) { Report PASS host "$h command available (agy)." }
    else { Report WARN host "$h command unavailable in PATH." }
}
if ($failed) { exit 1 }

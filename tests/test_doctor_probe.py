"""WP-06a — doctor -ProbeDesktop, nhánh KHÔNG có Power BI Desktop (T07 một phần).

Checkout giả với `powerbi_agent/discovery.py` thay bằng bản giả trả danh sách instance rỗng,
nên doctor không bao giờ dò hay kết nối phiên Desktop thật đang mở trên máy. Nhánh có
instance (EVALUATE ROW) cố ý không chạy trong test.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")

NO_INSTANCE_DISCOVERY = (
    '"""Bản giả cho test: máy không có Power BI Desktop nào đang mở."""\n'
    "from pathlib import Path\n\n\n"
    "def find_active_pbi_ports():\n"
    "    Path(__file__).with_name('discovery-called.txt').write_text('1', encoding='utf-8')\n"
    "    return []\n"
)
# v0.7.1 WP-C: 7 dòng `prereq` (PowerShell, ExecutionPolicy, Git, Python, ADOMD.NET, Node, az) đứng TRƯỚC
# các dòng cũ; thứ tự/nhãn các dòng cũ giữ nguyên.
PREREQ_AREAS = ["prereq"] * 7
DEFAULT_AREAS = PREREQ_AREAS + ["source", "adapter", "station", "python", "import", "driver", "syntax",
                                "startup", "connection", "mcp", "host"]


@pytest.fixture
def doctor_checkout(tmp_path):
    source = tmp_path / "checkout có dấu"
    source.mkdir()
    shutil.copy2(REPO / "doctor.ps1", source / "doctor.ps1")
    (source / "mcp_server_powerbi.py").write_text("pass\n", encoding="utf-8")
    shutil.copytree(REPO / "powerbi_agent", source / "powerbi_agent",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (source / "powerbi_agent" / "discovery.py").write_text(NO_INSTANCE_DISCOVERY, encoding="utf-8")
    (source / ".agents" / "skills").mkdir(parents=True)
    profile = tmp_path / "profile"
    profile.mkdir()
    env = os.environ.copy()
    env.pop("ADOMD_LIB_DIR", None)
    env["USERPROFILE"] = str(profile)
    env["POWERBI_INSTALL_PYTHON"] = sys.executable
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return source, env


def _doctor(source, env, *extra, hosts="codex"):
    # Ép UTF-8 cho stdout của PowerShell 5.1 để đọc đúng dòng tiếng Việt khi bị chuyển hướng.
    command = (
        "[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false); "
        f"& '{source / 'doctor.ps1'}' -Hosts {hosts} {' '.join(extra)}; exit $LASTEXITCODE"
    )
    result = subprocess.run(
        [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        env=env, capture_output=True, timeout=180,
    )
    return result.returncode, result.stdout.decode("utf-8", "replace"), result.stderr.decode("utf-8", "replace")


def _areas(stdout):
    return [m.group(2) for m in re.finditer(r"^\[(PASS|WARN|FAIL|NOT_CHECKED)\] (\w+):", stdout, re.M)]


@pytest.mark.skipif(not POWERSHELL or sys.platform != "win32", reason="Windows PowerShell required")
def test_probe_desktop_without_instance_reports_not_checked(doctor_checkout):
    source, env = doctor_checkout
    _code, stdout, stderr = _doctor(source, env, "-ProbeDesktop")

    assert "[PASS] startup:" in stdout, stdout + stderr
    assert "[NOT_CHECKED] connection: Power BI Desktop chưa mở — mở report rồi chạy lại" in stdout, stdout + stderr
    assert (source / "powerbi_agent" / "discovery-called.txt").exists()  # kết luận đến từ bước dò cổng
    assert "not attempted" not in stdout
    assert _areas(stdout) == DEFAULT_AREAS


@pytest.mark.skipif(not POWERSHELL or sys.platform != "win32", reason="Windows PowerShell required")
def test_doctor_without_flag_keeps_previous_lines_and_skips_discovery(doctor_checkout):
    source, env = doctor_checkout
    _code, stdout, stderr = _doctor(source, env)

    assert "[PASS] startup:" in stdout, stdout + stderr
    assert ("[NOT_CHECKED] connection: Live host MCP handshake and Power BI Desktop connection not attempted."
            in stdout)
    assert "chưa mở" not in stdout
    assert not (source / "powerbi_agent" / "discovery-called.txt").exists()
    assert _areas(stdout) == DEFAULT_AREAS


# WP-06b — probe tắt load_dotenv nhưng vẫn phải áp ADOMD_LIB_DIR trong config.env của trạm.
# Discovery giả trả MỘT instance cổng giả và ghi lại ADOMD_LIB_DIR / OTHER_SETTING probe thấy;
# `_query_df` bị thay bằng bản giả nên test không bao giờ mở kết nối nào.
ONE_INSTANCE_DISCOVERY = (
    '"""Bản giả cho test: một Power BI Desktop giả, không kết nối thật."""\n'
    "import os\n"
    "from pathlib import Path\n\n\n"
    "def find_active_pbi_ports():\n"
    "    Path(__file__).with_name('discovery-called.txt').write_text(\n"
    "        os.environ.get('ADOMD_LIB_DIR', '<unset>') + '|' + os.environ.get('OTHER_SETTING', '<unset>'),\n"
    "        encoding='utf-8')\n"
    "    return [{'port': '1', 'pid': 0, 'name': 'giả'}]\n"
)
NO_CONNECT_QUERY = (
    "\n\ndef _query_df(*args, **kwargs):  # bản giả cho test: không bao giờ kết nối\n"
    "    __import__('pathlib').Path(__file__).with_name('query-called.txt').write_text('1', encoding='utf-8')\n"
    "    raise RuntimeError('test: không kết nối')\n"
)


@pytest.fixture
def station_checkout(doctor_checkout, tmp_path):
    source, env = doctor_checkout
    agent = source / "powerbi_agent"
    (agent / "discovery.py").write_text(ONE_INSTANCE_DISCOVERY, encoding="utf-8")
    with open(agent / "tools_query.py", "a", encoding="utf-8") as handle:
        handle.write(NO_CONNECT_QUERY)
    # Đủ dấu hiệu checkout để engine chọn trạm theo ADS_DATA như khi chạy thật.
    (source / "install.ps1").write_text("# checkout giả cho test\n", encoding="utf-8")
    (source / "skills").mkdir()
    station = tmp_path / "Trạm giả Đức"
    station.mkdir()
    (station / "CANARY.txt").write_text("canary\n", encoding="utf-8")
    empty = tmp_path / "ADOMD rỗng"
    empty.mkdir()
    (station / "config.env").write_text(
        f"OTHER_SETTING=khong-duoc-nap\nADOMD_LIB_DIR={empty}\n", encoding="utf-8")  # như .env.example
    env["ADS_DATA"] = str(station)
    return source, env, empty


@pytest.mark.skipif(not POWERSHELL or sys.platform != "win32", reason="Windows PowerShell required")
def test_probe_desktop_applies_station_adomd_lib_dir(station_checkout):
    source, env, empty = station_checkout
    _code, stdout, stderr = _doctor(source, env, "-ProbeDesktop")

    agent = source / "powerbi_agent"
    # Chỉ ADOMD_LIB_DIR được áp; biến khác trong config.env của trạm không được nạp.
    assert (agent / "discovery-called.txt").read_text(encoding="utf-8") == f"{empty}|<unset>", stdout + stderr
    assert "[FAIL] connection: Power BI Desktop is open but ADOMD.NET is not loaded" in stdout, stdout + stderr
    assert "[PASS] connection" not in stdout
    assert not (agent / "query-called.txt").exists()
    assert _areas(stdout) == DEFAULT_AREAS


@pytest.mark.skipif(not POWERSHELL or sys.platform != "win32", reason="Windows PowerShell required")
def test_probe_desktop_process_env_wins_over_station_config(station_checkout, tmp_path):
    source, env, _empty = station_checkout
    chosen = tmp_path / "ADOMD từ biến môi trường"
    chosen.mkdir()
    env["ADOMD_LIB_DIR"] = str(chosen)
    _code, stdout, stderr = _doctor(source, env, "-ProbeDesktop")

    assert (source / "powerbi_agent" / "discovery-called.txt").read_text(encoding="utf-8") == f"{chosen}|<unset>", \
        stdout + stderr
    assert "[FAIL] connection: Power BI Desktop is open but ADOMD.NET is not loaded" in stdout, stdout + stderr


# WP-03d — không xác định được trạm thì probe báo mã riêng thay vì nuốt im lỗi.
@pytest.mark.skipif(not POWERSHELL or sys.platform != "win32", reason="Windows PowerShell required")
def test_probe_desktop_reports_unresolved_station(station_checkout):
    source, env, _empty = station_checkout
    env["ADS_DATA"] = str(source / "powerbi_agent")  # trạm trỏ vào source: engine từ chối
    _code, stdout, stderr = _doctor(source, env, "-ProbeDesktop")

    line = [x for x in stdout.splitlines()
            if x.startswith(("[PASS] connection:", "[FAIL] connection:", "[NOT_CHECKED] connection:"))]
    assert len(line) == 1 and "Station config unresolved (CONNECTION_STATION_UNRESOLVED)" in line[0], \
        stdout + stderr
    assert _areas(stdout) == DEFAULT_AREAS  # vẫn một dòng mỗi mục
    _code, plain, stderr = _doctor(source, env)
    assert "CONNECTION_STATION_UNRESOLVED" not in plain, plain + stderr
    assert _areas(plain) == DEFAULT_AREAS


# WP-04-fix — CLI Antigravity có tên `agy`; doctor không được báo WARN sai khi chỉ có `agy`.
@pytest.mark.skipif(not POWERSHELL or sys.platform != "win32", reason="Windows PowerShell required")
def test_doctor_accepts_agy_command_for_antigravity(doctor_checkout, tmp_path):
    source, env = doctor_checkout
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "agy.cmd").write_text("@exit /b 0\r\n", encoding="ascii")
    env["PATH"] = os.pathsep.join([str(bin_dir), str(Path(POWERSHELL).parent),
                                   str(Path(os.environ["SystemRoot"]) / "System32")])
    command = f"& '{source / 'doctor.ps1'}' -Hosts antigravity; exit $LASTEXITCODE"
    result = subprocess.run([POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
                            env=env, capture_output=True, timeout=180)
    stdout = result.stdout.decode("utf-8", "replace")
    assert "[PASS] host: antigravity command available (agy)." in stdout, stdout
    (bin_dir / "agy.cmd").unlink()
    result = subprocess.run([POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
                            env=env, capture_output=True, timeout=180)
    assert "[WARN] host: antigravity command unavailable in PATH." in result.stdout.decode("utf-8", "replace")


# ---- v0.7.1 WP-C — nhóm `prereq` + cờ -Preflight ----
def _lines(stdout, area):
    return [line for line in stdout.splitlines() if re.match(rf"^\[(PASS|WARN|FAIL|NOT_CHECKED)\] {area}:", line)]


@pytest.mark.skipif(not POWERSHELL or sys.platform != "win32", reason="Windows PowerShell required")
def test_preflight_runs_only_prereq_without_venv_or_install(tmp_path):
    """Ngay sau clone: chưa có .venv, chưa chạy install -> -Preflight vẫn chạy và chỉ in nhóm prereq."""
    source = tmp_path / "vừa clone"
    source.mkdir()
    shutil.copy2(REPO / "doctor.ps1", source / "doctor.ps1")
    shutil.copytree(REPO / "powerbi_agent", source / "powerbi_agent",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    env = {k: v for k, v in os.environ.items() if k.upper() not in ("PSMODULEPATH", "POWERBI_INSTALL_PYTHON")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    code, stdout, stderr = _doctor(source, env, "-Preflight")

    assert _areas(stdout) == PREREQ_AREAS, stdout + stderr
    assert code == 0, stdout + stderr  # máy chạy test có Git + Python trong khoảng
    assert re.search(r"^\[PASS\] prereq: Python 3\.1[1-4] \(.+\) within supported range 3\.11-3\.14\.$", stdout, re.M), stdout
    assert re.search(r"^\[PASS\] prereq: Git: git version ", stdout, re.M), stdout
    assert "ExecutionPolicy" in stdout and "MachinePolicy=" in stdout
    assert not (source / "workspace").exists()


@pytest.mark.skipif(not POWERSHELL or sys.platform != "win32", reason="Windows PowerShell required")
def test_preflight_reports_missing_git_and_python_outside_range(tmp_path):
    source = tmp_path / "checkout"
    source.mkdir()
    shutil.copy2(REPO / "doctor.ps1", source / "doctor.ps1")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    for name in ("py.cmd", "python.cmd", "python3.cmd"):
        (fake_bin / name).write_text("@echo 3.15\r\n", encoding="ascii")
    env = {k: v for k, v in os.environ.items() if k.upper() not in ("PATH", "PSMODULEPATH", "POWERBI_INSTALL_PYTHON")}
    env["PATH"] = os.pathsep.join([str(fake_bin), str(Path(POWERSHELL).parent),
                                   str(Path(os.environ["SystemRoot"]) / "System32")])
    code, stdout, stderr = _doctor(source, env, "-Preflight")

    assert code == 1, stdout + stderr
    assert _areas(stdout) == PREREQ_AREAS, stdout + stderr
    assert ("[FAIL] prereq: Git not found in PATH; needed to clone and update. Install: winget install --id Git.Git -e"
            in stdout), stdout
    assert ("[FAIL] prereq: Python 3.15 found but outside supported range 3.11-3.14. "
            "Install Python 3.12: winget install --id Python.Python.3.12 -e" in stdout), stdout
    assert "[NOT_CHECKED] prereq: ADOMD.NET DLL not checked: powerbi_agent\\adomd.py missing in checkout." in stdout
    assert "[WARN] prereq: Node.js not found" in stdout
    assert "[NOT_CHECKED] prereq: Azure CLI not found" in stdout


# ---- v0.7.1 WP-B — dòng prereq ADOMD và dòng driver dùng cùng find_adomd_dlls() với engine ----
@pytest.mark.skipif(not POWERSHELL or sys.platform != "win32", reason="Windows PowerShell required")
def test_adomd_lines_follow_engine_override(doctor_checkout, tmp_path):
    source, env = doctor_checkout
    empty = tmp_path / "ADOMD rỗng"
    empty.mkdir()
    env["ADOMD_LIB_DIR"] = str(empty)
    _code, stdout, stderr = _doctor(source, env)
    missing = f"ADOMD_LIB_DIR={empty} has no AdomdClient.dll (override is exclusive; SSMS/GAC not searched)."
    assert f"[WARN] prereq: ADOMD.NET: {missing}" in stdout, stdout + stderr
    driver = _lines(stdout, "driver")
    assert len(driver) == 1 and driver[0].startswith("[WARN] driver:") and driver[0].endswith(missing), stdout
    assert _areas(stdout) == DEFAULT_AREAS

    chosen = tmp_path / "ADOMD đã chọn"
    chosen.mkdir()
    for dll in ("Microsoft.AnalysisServices.AdomdClient.dll", "Microsoft.AnalysisServices.Tabular.dll"):
        (chosen / dll).write_bytes(b"fixture")
    env["ADOMD_LIB_DIR"] = str(chosen)
    _code, stdout, stderr = _doctor(source, env)
    found = f"AdomdClient.dll on disk (ADOMD_LIB_DIR): {chosen}."
    assert f"[PASS] prereq: ADOMD.NET: {found}" in stdout, stdout + stderr
    driver = _lines(stdout, "driver")
    assert len(driver) == 1 and driver[0].endswith(found), stdout
    assert _areas(stdout) == DEFAULT_AREAS


# ---- v0.7.1 WP-D — Claude Desktop (MCP-only) ----
@pytest.mark.skipif(not POWERSHELL or sys.platform != "win32", reason="Windows PowerShell required")
def test_doctor_claude_desktop_reads_appdata_config_and_install_path(doctor_checkout, tmp_path):
    source, env = doctor_checkout
    appdata = tmp_path / "AppData giả" / "Roaming"
    local = tmp_path / "AppData giả" / "Local"
    config = appdata / "Claude" / "claude_desktop_config.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"mcpServers": {"powerbi-mcp-bridge": {
        "command": sys.executable, "args": ["-u", str(source / "mcp_server_powerbi.py")]}}}), encoding="utf-8")
    (local / "AnthropicClaude").mkdir(parents=True)
    env["APPDATA"] = str(appdata)
    env["LOCALAPPDATA"] = str(local)
    _code, stdout, stderr = _doctor(source, env, hosts="claude-desktop")

    assert "[PASS] mcp: claude-desktop points to this checkout." in stdout, stdout + stderr
    assert "[PASS] host: claude-desktop app installed (claude.ai installer)" in stdout, stdout
    assert not _lines(stdout, "adapter")  # MCP-only: không có adapter skill cho Claude Desktop
    assert "[PASS] startup:" in stdout

    shutil.rmtree(local / "AnthropicClaude")
    virtual = local / "Packages" / "Claude_test" / "LocalCache" / "Roaming" / "Claude"
    virtual.mkdir(parents=True)
    (virtual / "claude_desktop_config.json").write_text("{}", encoding="utf-8")
    _code, stdout, stderr = _doctor(source, env, hosts="claude-desktop")
    assert "[WARN] host: claude-desktop Store package has its own config copy" in stdout, stdout + stderr
    shutil.rmtree(local / "Packages")
    config.unlink()
    _code, stdout, stderr = _doctor(source, env, hosts="claude-desktop")
    assert "[WARN] mcp: claude-desktop has no registration for this checkout." in stdout, stdout + stderr
    assert "[WARN] host: claude-desktop app not found" in stdout

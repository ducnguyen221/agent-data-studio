"""WP-06a — doctor -ProbeDesktop, nhánh KHÔNG có Power BI Desktop (T07 một phần).

Checkout giả với `powerbi_agent/discovery.py` thay bằng bản giả trả danh sách instance rỗng,
nên doctor không bao giờ dò hay kết nối phiên Desktop thật đang mở trên máy. Nhánh có
instance (EVALUATE ROW) cố ý không chạy trong test.
"""

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
DEFAULT_AREAS = ["source", "adapter", "station", "python", "import", "driver", "syntax",
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


def _doctor(source, env, *extra):
    # Ép UTF-8 cho stdout của PowerShell 5.1 để đọc đúng dòng tiếng Việt khi bị chuyển hướng.
    command = (
        "[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false); "
        f"& '{source / 'doctor.ps1'}' -Hosts codex {' '.join(extra)}; exit $LASTEXITCODE"
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

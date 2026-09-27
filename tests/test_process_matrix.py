"""Ma trận T01/T02/T03/T25a ở mức tiến trình — checkout giả, trạm giả, không đụng trạm thật.

Mỗi ca chạy Python con từ một bản copy engine đặt dưới đường có dấu tiếng Việt và khoảng
trắng, cwd nằm ngoài checkout. Không mở Power BI Desktop: ca T03 chặn nạp DLL
AnalysisServices ngay trong tiến trình con và chỉ gọi tool với cổng giả.
"""

import hashlib
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading

import pytest

from test_installer import run_install, source_fixture  # noqa: F401 (shared synthetic source fixture)

REPO = Path(__file__).resolve().parents[1]
# Biến có thể đổi trạm/đường dẫn của tiến trình con; mỗi ca tự đặt đúng biến nó cần.
_CHILD_ENV_DROP = (
    "ADS_DATA", "POWERBI_PROJECT_DIR", "POWERBI_AUDIT_DIR", "POWERBI_POLICY_FILE",
    "POWERBI_TEMPLATES_DIR", "POWERBI_DISTILL_DIR", "ADS_SECRETS_FILE", "ADOMD_LIB_DIR", "PYTHONPATH",
)

DATA_DIR_PROBE = (
    "import json, os, powerbi_agent\n"
    "from powerbi_agent import _env\n"
    "out = {'pkg': os.path.realpath(powerbi_agent.__file__)}\n"
    "try:\n"
    "    out['data_dir'] = _env.data_dir()\n"
    "except Exception as exc:\n"
    "    out['error'] = type(exc).__name__\n"
    "    out['message'] = str(exc)\n"
    "print(json.dumps(out, ensure_ascii=False))\n"
)

# Giả lập máy không có ADOMD/TOM ở bất kỳ đâu (thư mục ứng viên lẫn GAC) mà vẫn giữ pythonnet
# thật; ghi lại trạng thái lúc engine thử nạp DLL lần đầu.
DENY_ANALYSIS_SERVICES = (
    "import json, os, sys\n"
    "try:\n"
    "    import clr\n"
    "except Exception:\n"
    "    print(json.dumps({'no_clr': True}))\n"
    "    raise SystemExit(0)\n"
    "_real_add_reference = clr.AddReference\n"
    "SEEN = []\n"
    "def _deny(name):\n"
    "    if 'AnalysisServices' in str(name):\n"
    "        SEEN.append({'env': os.environ.get('ADOMD_LIB_DIR'), 'pyadomd': 'pyadomd' in sys.modules})\n"
    "        raise OSError('dll-missing-canary')\n"
    "    return _real_add_reference(name)\n"
    "clr.AddReference = _deny\n"
)


@pytest.fixture
def checkout(tmp_path):
    """Checkout tối thiểu mà `_env.data_dir()` chấp nhận, dưới đường có dấu và khoảng trắng."""
    root = tmp_path / "Kho mã nguồn Đức" / "agent data studio"
    shutil.copytree(REPO / "powerbi_agent", root / "powerbi_agent",
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(REPO / "mcp_server_powerbi.py", root / "mcp_server_powerbi.py")
    (root / "install.ps1").write_text("# checkout giả cho test\n", encoding="utf-8")
    (root / "skills").mkdir()
    return root


@pytest.fixture
def outside_cwd(tmp_path):
    cwd = tmp_path / "thư mục làm việc ngoài"
    cwd.mkdir()
    return cwd


def _child_env(**extra):
    env = os.environ.copy()
    for name in _CHILD_ENV_DROP:
        env.pop(name, None)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.update({name: str(value) for name, value in extra.items()})
    return env


def _same(left, right) -> bool:
    return os.path.normcase(os.path.realpath(str(left))) == os.path.normcase(os.path.realpath(str(right)))


def _inside(path, root) -> bool:
    path = os.path.normcase(os.path.realpath(str(path)))
    root = os.path.normcase(os.path.realpath(str(root)))
    return os.path.commonpath([path, root]) == root


def _run_python(checkout, code, cwd, **env):
    return subprocess.run(
        [sys.executable, "-c", code], cwd=cwd, env=_child_env(PYTHONPATH=checkout, **env),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )


def _probe_data_dir(checkout, cwd, **env):
    result = _run_python(checkout, DATA_DIR_PROBE, cwd, **env)
    assert result.returncode == 0, result.stderr[-800:]
    out = json.loads(result.stdout.strip().splitlines()[-1])
    # ADS_DATA/cwd chỉ chọn trạm, không đổi nơi lấy engine.
    assert _inside(out["pkg"], checkout), out["pkg"]
    return out


def _snapshot(root: Path) -> dict:
    items = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            stat = path.stat()
            items[str(path.relative_to(root))] = (
                stat.st_size, stat.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()
            )
    return items


def _external_station(tmp_path, name="Trạm dữ liệu Đức") -> Path:
    station = tmp_path / name
    (station / "projects").mkdir(parents=True)
    (station / "CANARY.txt").write_text("canary trạm ngoài\n", encoding="utf-8")
    return station


def _bind(checkout: Path, station: Path) -> Path:
    binding = checkout / ".ads-binding.json"
    binding.write_text(json.dumps({"station_root": str(station)}, ensure_ascii=False) + "\n", encoding="utf-8")
    return binding


# ---------------------------------------------------------------------------
# T01 — chọn trạm theo FINAL-PLAN §3.2
# ---------------------------------------------------------------------------

def test_t01_external_binding_rejects_other_ads_data_without_touching_stations(checkout, outside_cwd, tmp_path):
    station = _external_station(tmp_path)
    binding = _bind(checkout, station)
    other = tmp_path / "Trạm khác có dấu"
    before, binding_before = _snapshot(station), binding.read_bytes()

    out = _probe_data_dir(checkout, outside_cwd, ADS_DATA=other)
    assert out.get("error") == "ValueError", out
    assert "ADS_DATA khác binding" in out["message"]

    # Entrypoint thật (đường tuyệt đối có dấu/khoảng trắng) dừng rõ ràng, không phục vụ stdio.
    started = subprocess.run(
        [sys.executable, str(checkout / "mcp_server_powerbi.py")], cwd=outside_cwd,
        env=_child_env(ADS_DATA=other), stdin=subprocess.DEVNULL,
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    assert started.returncode != 0
    assert "ADS_DATA khác binding" in started.stderr

    assert _snapshot(station) == before
    assert binding.read_bytes() == binding_before
    assert not other.exists()


def test_t01_external_binding_used_and_same_station_spelling_accepted(checkout, outside_cwd, tmp_path):
    station = _external_station(tmp_path)
    _bind(checkout, station)

    assert _same(_probe_data_dir(checkout, outside_cwd)["data_dir"], station)
    spellings = [str(station) + os.sep]
    if os.name == "nt":
        spellings.append(str(station).upper())
    for spelling in spellings:
        out = _probe_data_dir(checkout, outside_cwd, ADS_DATA=spelling)
        assert "error" not in out, out
        assert _same(out["data_dir"], station)


def test_t01_basic_without_binding_follows_ads_data_then_workspace(checkout, outside_cwd, tmp_path):
    station = _external_station(tmp_path)
    workspace = checkout / "workspace"

    assert _same(_probe_data_dir(checkout, outside_cwd, ADS_DATA=station)["data_dir"], station)
    assert _same(_probe_data_dir(checkout, outside_cwd)["data_dir"], workspace)
    assert _same(_probe_data_dir(checkout, outside_cwd, ADS_DATA=workspace)["data_dir"], workspace)
    # Chọn trạm không tự tạo dữ liệu; tạo workspace là việc của installer.
    assert not workspace.exists()
    assert not (checkout / ".ads-binding.json").exists()


def test_t01_legacy_source_config_requires_explicit_station(checkout, outside_cwd, tmp_path):
    (checkout / "policy.json").write_text('{"blocked_columns": []}\n', encoding="utf-8")
    out = _probe_data_dir(checkout, outside_cwd)
    assert out.get("error") == "RuntimeError", out
    assert "cấu hình dữ liệu đời cũ" in out["message"]

    station = _external_station(tmp_path)
    assert _same(_probe_data_dir(checkout, outside_cwd, ADS_DATA=station)["data_dir"], station)


# ---------------------------------------------------------------------------
# T02 — trạm trỏ vào source bị từ chối ở mức tiến trình
# ---------------------------------------------------------------------------

def test_t02_station_inside_source_rejected(checkout, outside_cwd, tmp_path):
    for bad in (checkout, checkout / "skills", checkout / "powerbi_agent", checkout / "workspace" / "team"):
        out = _probe_data_dir(checkout, outside_cwd, ADS_DATA=bad)
        assert out.get("error") == "ValueError", (bad, out)

    # Binding trạm ngoài không được trỏ về workspace của chính checkout.
    _bind(checkout, checkout / "workspace")
    out = _probe_data_dir(checkout, outside_cwd)
    assert out.get("error") == "ValueError", out


# ---------------------------------------------------------------------------
# T03 — config trạm trước DLL, thiếu DLL chỉ chặn năng lực Power BI
# ---------------------------------------------------------------------------

def test_t03_missing_adomd_blocks_power_bi_but_not_data_only(checkout, outside_cwd, tmp_path):
    station = _external_station(tmp_path)
    empty_dll_dir = tmp_path / "Thư mục ADOMD rỗng"
    empty_dll_dir.mkdir()
    # Override chỉ nằm trong config của trạm, không có trong môi trường tiến trình.
    (station / "config.env").write_text(f"ADOMD_LIB_DIR='{empty_dll_dir}'\n", encoding="utf-8")
    code = DENY_ANALYSIS_SERVICES + (
        "from powerbi_agent import app\n"
        "from powerbi_agent.adomd import candidate_adomd_dirs\n"
        "tools = app.mcp._tool_manager._tools\n"
        "out = {'adomd': app.ADOMD_LOADED, 'tabular': app.TABULAR_LOADED,\n"
        "       'first': SEEN[0] if SEEN else None, 'first_dir': (candidate_adomd_dirs() or [None])[0],\n"
        "       'knowledge': tools['knowledge_status'].fn(),\n"
        "       'list_tables': tools['list_tables'].fn(port='1', model_id='m')}\n"
        "print(json.dumps(out, ensure_ascii=False))\n"
    )
    result = _run_python(checkout, code, outside_cwd, ADS_DATA=station)
    assert result.returncode == 0, result.stderr[-800:]
    out = json.loads(result.stdout.strip().splitlines()[-1])
    if out.get("no_clr"):
        pytest.skip("pythonnet/clr không có trong môi trường này")

    assert out["adomd"] is False and out["tabular"] is False
    # config.env của trạm đã nạp TRƯỚC lần thử DLL đầu tiên; DLL thử TRƯỚC import pyadomd.
    assert out["first"] == {"env": str(empty_dll_dir), "pyadomd": False}
    assert _same(out["first_dir"], empty_dll_dir)
    # Data-only vẫn chạy; năng lực Power BI trả lỗi thay vì làm sập server.
    assert isinstance(out["knowledge"], str) and not out["knowledge"].startswith("Lỗi")
    assert out["list_tables"].startswith("Lỗi list_tables")


def test_t03_mcp_stdio_from_vietnamese_path_keeps_data_only_tools(checkout, tmp_path):
    station = _external_station(tmp_path)
    # Mồi nhử: package trùng tên trong trạm (cũng là cwd) không được nạp thay engine của checkout.
    decoy = station / "powerbi_agent"
    decoy.mkdir()
    (decoy / "__init__.py").write_text("raise RuntimeError('decoy-engine-from-station')\n", encoding="utf-8")
    entry = checkout / "mcp_server_powerbi.py"
    code = DENY_ANALYSIS_SERVICES + f"import runpy\nrunpy.run_path({str(entry)!r}, run_name='__main__')\n"
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "ads-test", "version": "0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "knowledge_status", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "list_tables", "arguments": {"port": "1", "model_id": "m"}}},
    ]
    proc = subprocess.Popen(
        [sys.executable, "-c", code], cwd=station, env=_child_env(ADS_DATA=station),
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    lines: queue.Queue = queue.Queue()
    threading.Thread(target=lambda: [lines.put(raw) for raw in proc.stdout], daemon=True).start()
    stderr_chunks: list[bytes] = []
    threading.Thread(target=lambda: stderr_chunks.append(proc.stderr.read()), daemon=True).start()
    raw_lines, responses = [], {}
    try:
        proc.stdin.write("".join(json.dumps(m) + "\n" for m in messages).encode("utf-8"))
        proc.stdin.flush()
        while 3 not in responses:
            try:
                raw = lines.get(timeout=120)
            except queue.Empty:
                break
            raw_lines.append(raw)
            message = json.loads(raw.decode("utf-8"))  # stdout chỉ được chứa JSON-RPC
            if "id" in message:
                responses[message["id"]] = message
    finally:
        proc.stdin.close()
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=30)
    stderr = b"".join(stderr_chunks).decode("utf-8", "replace")
    assert "decoy-engine-from-station" not in stderr
    if raw_lines and "no_clr" in raw_lines[0].decode("utf-8"):
        pytest.skip("pythonnet/clr không có trong môi trường này")
    assert 3 in responses, stderr[-800:]

    knowledge = responses[2]["result"]
    assert not knowledge.get("isError") and not knowledge["content"][0]["text"].startswith("Lỗi")
    assert responses[3]["result"]["content"][0]["text"].startswith("Lỗi list_tables")


# ---------------------------------------------------------------------------
# T25a — ranh giới Git ở chế độ trạm ngoài
# ---------------------------------------------------------------------------

def _git(source: Path, *args):
    return subprocess.run(["git", "-C", str(source), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
def test_t25a_external_install_keeps_repo_index_and_tree_clean(source_fixture):
    source = source_fixture
    assert _git(source, "init", "-q").returncode == 0
    station = source.parent / "Trạm ngoài có dấu"
    result = run_install(source, ads_data=str(station))
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-1500:]

    assert (station / "projects").is_dir() and (station / "config.env").is_file()
    assert not (source / "workspace").exists()
    assert _git(source, "check-ignore", "-q", ".ads-binding.json").returncode == 0
    assert _git(source, "ls-files", "--cached").stdout.strip() == ""
    status = _git(source, "-c", "core.quotePath=false", "status", "--porcelain", "--ignored", "-uall")
    assert status.returncode == 0, status.stderr
    entries = status.stdout.splitlines()
    assert "!! .ads-binding.json" in entries
    # Dữ liệu trạm ngoài không được chép vào repo.
    assert not any(name in line for line in entries for name in ("config.env", "projects/", "CANARY"))


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
def test_t25a_forced_binding_in_index_blocks_external_install(source_fixture):
    source = source_fixture
    assert _git(source, "init", "-q").returncode == 0
    station = source.parent / "Trạm ngoài có dấu"
    _bind(source, station)
    assert _git(source, "add", "-f", ".ads-binding.json").returncode == 0

    result = run_install(source, ads_data=str(station))
    assert result.returncode != 0
    assert "Git index" in result.stdout + result.stderr
    assert not station.exists()

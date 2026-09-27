"""WP-03b — ADOMD_LIB_DIR độc quyền, gate ADOMD trước import pyadomd, stdout MCP sạch.

Chạy pythonnet THẬT trong tiến trình con (không chặn AddReference như T03) từ bản copy
engine dưới đường có dấu, trạm giả trong thư mục tạm. Không mở Power BI Desktop: dò cổng
được thay bằng danh sách rỗng và mọi tool Desktop chỉ nhận cổng giả '1'.
"""

import json
import queue
import shutil
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from test_process_matrix import _child_env, _external_station

REPO = Path(__file__).resolve().parents[1]

ADOMD_DLL = "Microsoft.AnalysisServices.AdomdClient.dll"
TABULAR_DLL = "Microsoft.AnalysisServices.Tabular.dll"

# Thay dò cổng Desktop bằng danh sách rỗng TRƯỚC khi tool nào chạy — test không bao giờ
# chạm phiên Power BI Desktop thật đang mở trên máy.
NO_DESKTOP = (
    "from powerbi_agent import discovery, tools_distill, tools_query\n"
    "for _m in (discovery, tools_distill, tools_query):\n"
    "    _m.find_active_pbi_ports = lambda: []\n"
)

REQUIRE_CLR = (
    "import json, sys\n"
    "try:\n"
    "    import clr  # noqa: F401\n"
    "except Exception:\n"
    "    print(json.dumps({'no_clr': True}))\n"
    "    raise SystemExit(0)\n"
)

# Máy không có DLL ở thư mục ứng viên nào; GAC vẫn được thử bằng đường thật.
NO_CANDIDATES = "import powerbi_agent.adomd as _adomd\n_adomd.candidate_adomd_dirs = lambda: []\n"


@pytest.fixture
def checkout(tmp_path):
    """Checkout tối thiểu (như test_process_matrix) dưới đường có dấu và khoảng trắng."""
    root = tmp_path / "Kho mã nguồn Đức" / "agent data studio"
    shutil.copytree(REPO / "powerbi_agent", root / "powerbi_agent",
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(REPO / "mcp_server_powerbi.py", root / "mcp_server_powerbi.py")
    (root / "install.ps1").write_text("# checkout giả cho test\n", encoding="utf-8")
    (root / "skills").mkdir()
    return root


def _run(checkout, code, cwd, **env):
    return subprocess.run(
        [sys.executable, "-c", code], cwd=cwd, env=_child_env(PYTHONPATH=checkout, **env),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )


def _last_json(result):
    assert result.returncode == 0, result.stderr[-1500:]
    out = json.loads(result.stdout.strip().splitlines()[-1])
    if out.get("no_clr"):
        pytest.skip("pythonnet/clr không có trong môi trường này")
    return out


def test_empty_override_is_exclusive_and_names_the_path(checkout, tmp_path):
    station = _external_station(tmp_path)
    empty = tmp_path / "ADOMD override rỗng"
    empty.mkdir()
    code = REQUIRE_CLR + (
        "from powerbi_agent import app\n" + NO_DESKTOP +
        "tools = app.mcp._tool_manager._tools\n"
        "out = {'adomd': app.ADOMD_LOADED, 'tabular': app.TABULAR_LOADED,\n"
        "       'reports': tools['list_local_reports'].fn(),\n"
        "       'tables': tools['list_tables'].fn(port='1', model_id='m'),\n"
        "       'describe': tools['describe_table'].fn(port='1', model_id='m', table_name='t'),\n"
        "       'distill': tools['distill_model_schema'].fn(port='1', model_id='m'),\n"
        "       'pyadomd_imported': 'pyadomd' in sys.modules}\n"
        "print(json.dumps(out, ensure_ascii=False))\n"
    )
    result = _run(checkout, code, tmp_path, ADS_DATA=station, ADOMD_LIB_DIR=empty)
    out = _last_json(result)

    # Override độc quyền: không lặng lẽ nạp SSMS/GAC khi thư mục chỉ định thiếu DLL.
    assert out["adomd"] is False and out["tabular"] is False, out
    assert f"ADOMD_LIB_DIR={empty} không chứa {ADOMD_DLL}" in result.stderr, result.stderr[-1500:]
    assert f"ADOMD_LIB_DIR={empty} không chứa {TABULAR_DLL}" in result.stderr, result.stderr[-1500:]
    # Tool Desktop báo thiếu thành phần (kèm lý do có đường dẫn), không import pyadomd.
    for key in ("reports", "tables", "describe", "distill"):
        assert "Thiếu ADOMD.NET" in out[key] and str(empty) in out[key], (key, out[key])
    assert out["tables"].startswith("Lỗi list_tables")
    assert "NameError" not in json.dumps(out, ensure_ascii=False)
    assert out["pyadomd_imported"] is False


def test_mcp_stdout_stays_json_when_adomd_missing(checkout, tmp_path):
    station = _external_station(tmp_path)
    entry = checkout / "mcp_server_powerbi.py"
    probe = _run(checkout, REQUIRE_CLR + NO_CANDIDATES + (
        "from powerbi_agent.adomd import load_adomd\n"
        "print(json.dumps({'loaded': load_adomd()}))\n"
    ), tmp_path, ADS_DATA=station)
    if _last_json(probe)["loaded"]:
        pytest.skip("GAC của máy có AdomdClient; không giả lập được máy thiếu DLL bằng đường thật")

    code = REQUIRE_CLR + NO_CANDIDATES + NO_DESKTOP + (
        f"import runpy\nrunpy.run_path({str(entry)!r}, run_name='__main__')\n"
    )
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "ads-test", "version": "0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "list_tables", "arguments": {"port": "1", "model_id": "m"}}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "describe_table", "arguments": {"port": "1", "model_id": "m", "table_name": "t"}}},
    ]
    # PYTHONUNBUFFERED như host chạy `python -u`: print() của thư viện ra stdout ngay, không
    # nằm chờ trong buffer rồi mất lúc thoát — rác (nếu có) chắc chắn lọt vào kênh JSON-RPC.
    proc = subprocess.Popen(
        [sys.executable, "-c", code], cwd=tmp_path,
        env=_child_env(PYTHONPATH=checkout, ADS_DATA=station, PYTHONUNBUFFERED=1),
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    lines: queue.Queue = queue.Queue()
    reader = threading.Thread(target=lambda: [lines.put(raw) for raw in proc.stdout], daemon=True)
    reader.start()
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
            try:
                message = json.loads(raw.decode("utf-8"))
            except ValueError:
                break  # rác trên stdout — khẳng định bên dưới sẽ nêu dòng đó
            if "id" in message:
                responses[message["id"]] = message
    finally:
        proc.stdin.close()
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=30)
    # Đọc nốt phần stdout xả lúc thoát: print() của thư viện có thể nằm trong buffer tới cuối.
    reader.join(timeout=30)
    while not lines.empty():
        raw_lines.append(lines.get_nowait())
    stderr = b"".join(stderr_chunks).decode("utf-8", "replace")
    junk = [raw[:120] for raw in raw_lines if not raw.strip().startswith(b"{")]
    assert not junk, junk  # stdout chỉ được chứa JSON-RPC
    for raw in raw_lines:
        assert isinstance(json.loads(raw.decode("utf-8")), dict)
    assert 3 in responses, stderr[-1500:]
    for request_id, tool in ((2, "list_tables"), (3, "describe_table")):
        text = responses[request_id]["result"]["content"][0]["text"]
        assert text.startswith(f"Lỗi {tool}") and "ADOMD" in text, text
        assert "NameError" not in text


def test_import_pyadomd_keeps_banner_off_stdout(checkout, tmp_path):
    station = _external_station(tmp_path)
    code = REQUIRE_CLR + NO_CANDIDATES + (
        "import io, contextlib\n"
        "from powerbi_agent import adomd\n"
        "if adomd.load_adomd():\n"
        "    print(json.dumps({'skip': True}))\n"
        "    raise SystemExit(0)\n"
        "captured = io.StringIO()\n"
        "with contextlib.redirect_stdout(captured):\n"
        "    try:\n"
        "        adomd.import_pyadomd()\n"
        "    except Exception:\n"
        "        pass\n"
        "print(json.dumps({'stdout': captured.getvalue()}))\n"
    )
    result = _run(checkout, code, tmp_path, ADS_DATA=station)
    out = _last_json(result)
    if out.get("skip"):
        pytest.skip("GAC của máy có AdomdClient; pyadomd không in banner")
    # pyadomd 0.1.1 in banner ~1,8 KB khi thiếu DLL; banner phải sang stderr.
    assert out["stdout"] == "", out["stdout"][:300]
    assert "AdomdClient" in result.stderr


def test_cli_list_reports_missing_adomd_as_json_only(checkout, tmp_path):
    """WP-03c — `scripts/cli.py list` thiếu DLL: stdout chỉ một dòng JSON lỗi rõ, không banner."""
    station = _external_station(tmp_path)
    (checkout / "scripts").mkdir()
    shutil.copy2(REPO / "scripts" / "cli.py", checkout / "scripts" / "cli.py")
    empty = tmp_path / "ADOMD override rỗng"
    empty.mkdir()
    cli = checkout / "scripts" / "cli.py"
    # Dò cổng Desktop bị thay bằng danh sách rỗng TRƯỚC khi cli.py import nó: không chạm Desktop thật.
    code = REQUIRE_CLR + (
        "from powerbi_agent import discovery\n"
        "discovery.find_active_pbi_ports = lambda: []\n"
        f"import runpy\nsys.argv = [{str(cli)!r}, 'list']\n"
        f"runpy.run_path({str(cli)!r}, run_name='__main__')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path,
        env=_child_env(PYTHONPATH=checkout, ADS_DATA=station, ADOMD_LIB_DIR=empty),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1, result.stdout[:600]  # không banner pyadomd, không dòng rác
    out = json.loads(lines[0])
    if out.get("no_clr"):
        pytest.skip("pythonnet/clr không có trong môi trường này")
    assert result.returncode == 2, result.stderr[-1500:]
    assert out["status"] == "error", out
    assert out["message"].startswith("Thiếu ADOMD.NET") and str(empty) in out["message"], out
    assert "NameError" not in result.stdout + result.stderr



@pytest.mark.parametrize("command", [["query", "1", "m", 'EVALUATE ROW("x", 1)'], ["tables", "1", "m"]])
def test_cli_query_and_tables_report_missing_adomd(checkout, tmp_path, command):
    """WP-03d — `query`/`tables` thiếu DLL: gate ADOMD trước policy, thông điệp nêu rõ lý do."""
    station = _external_station(tmp_path)
    (checkout / "scripts").mkdir()
    shutil.copy2(REPO / "scripts" / "cli.py", checkout / "scripts" / "cli.py")
    empty = tmp_path / "ADOMD override rỗng"
    empty.mkdir()
    cli = checkout / "scripts" / "cli.py"
    code = REQUIRE_CLR + (
        f"import runpy\nsys.argv = [{str(cli)!r}, *{command!r}]\n"
        f"runpy.run_path({str(cli)!r}, run_name='__main__')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path,
        env=_child_env(PYTHONPATH=checkout, ADS_DATA=station, ADOMD_LIB_DIR=empty),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1, result.stdout[:600]
    out = json.loads(lines[0])
    if out.get("no_clr"):
        pytest.skip("pythonnet/clr không có trong môi trường này")
    assert result.returncode == 2, result.stderr[-1500:]
    assert out["status"] == "error", out
    assert out["message"].startswith("Thiếu ADOMD.NET") and str(empty) in out["message"], out
    assert "NameError" not in result.stdout + result.stderr

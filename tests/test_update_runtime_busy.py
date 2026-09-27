"""`_runtime_busy` chạy thật từ launcher `.venv` (không giả hàm, không đặt POWERBI_INSTALL_PYTHON).

Trên Windows `.venv\\Scripts\\python.exe` là launcher: nó sinh tiến trình Python con với cùng
đối số. Updater chạy bằng `.venv` do installer tạo thì launcher (cha của chính updater) không
được tính là "phiên khác đang dùng source"; tiến trình khác thật sự chạy từ source vẫn phải bị bắt.
"""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

DRIVER = """
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("update_release", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print("BUSY" if module._runtime_busy(Path(sys.argv[2])) else "FREE")
"""


@pytest.fixture
def venv_checkout(tmp_path):
    checkout = tmp_path.resolve() / "checkout"
    checkout.mkdir()
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(checkout / ".venv")],
                   check=True, capture_output=True, timeout=120)
    launcher = checkout / ".venv" / "Scripts" / "python.exe"
    assert launcher.is_file()
    (checkout / "driver.py").write_text(DRIVER, encoding="utf-8")
    (checkout / "idle.py").write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
    return checkout, launcher


def _driver_command(checkout: Path, launcher: Path) -> list[str]:
    return [str(launcher), str(checkout / "driver.py"), str(REPO / "scripts" / "update_release.py"),
            str(checkout)]


def _check_from_launcher(checkout: Path, launcher: Path) -> str:
    result = subprocess.run(
        _driver_command(checkout, launcher), capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=60, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout.strip()


@pytest.mark.skipif(os.name != "nt", reason="Windows venv launcher and process query required")
def test_runtime_busy_ignores_own_venv_launcher(venv_checkout):
    checkout, launcher = venv_checkout
    assert _check_from_launcher(checkout, launcher) == "FREE"


@pytest.mark.skipif(os.name != "nt", reason="Windows venv launcher and process query required")
@pytest.mark.parametrize("other", ["base_python_script", "venv_launcher"])
def test_runtime_busy_still_sees_other_source_process(venv_checkout, other):
    checkout, launcher = venv_checkout
    command = ([sys.executable, str(checkout / "idle.py")] if other == "base_python_script"
               else [str(launcher), "-c", "import time; time.sleep(60)"])
    child = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        assert _check_from_launcher(checkout, launcher) == "BUSY"
    finally:
        # Launcher có tiến trình con: gỡ cả cây để không sót python ngủ 60 giây.
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(child.pid)],
                       capture_output=True, timeout=30, check=False)
        child.wait(timeout=10)


@pytest.mark.skipif(os.name != "nt", reason="Windows venv launcher and process query required")
def test_runtime_busy_still_sees_python_ancestor_with_other_arguments(venv_checkout):
    """Chỉ loại chuỗi launcher cùng đối số; Python khác chạy từ source dù là tổ tiên vẫn bị bắt."""
    checkout, launcher = venv_checkout
    parent = checkout / "parent.py"
    parent.write_text(
        "import subprocess, sys\n"
        "result = subprocess.run(sys.argv[1:], capture_output=True, text=True)\n"
        "print(result.stdout.strip() or result.stderr)\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(parent), *_driver_command(checkout, launcher)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, check=False,
    )
    assert result.stdout.strip() == "BUSY", result.stdout + result.stderr


def _short_path(path: Path) -> str:
    import ctypes

    buffer = ctypes.create_unicode_buffer(32768)
    length = ctypes.windll.kernel32.GetShortPathNameW(str(path), buffer, len(buffer))
    return buffer.value if 0 < length < len(buffer) else str(path)


def _mixed_short_path(path: Path) -> str:
    """Chỉ rút ngắn MỘT đoạn tổ tiên (như đường ghép từ %TEMP% dạng 8.3 với phần đuôi dạng dài)."""
    parts = path.parts
    for index in range(1, len(parts)):
        prefix = Path(*parts[:index + 1])
        short = _short_path(prefix)
        if short.lower() != str(prefix).lower():
            return str(Path(short, *parts[index + 1:]))
    return str(path)


@pytest.mark.skipif(os.name != "nt", reason="Windows 8.3 short names and process query required")
@pytest.mark.parametrize("form", ["short_script", "mixed_script", "short_launcher"])
def test_runtime_busy_sees_source_process_started_by_short_path(venv_checkout, form):
    """CIM trả CommandLine/ExecutablePath đúng dạng lúc khởi chạy: đường 8.3 vẫn phải là BUSY."""
    checkout, launcher = venv_checkout
    script = checkout / "idle.py"
    if _short_path(script).lower() == str(script).lower():
        pytest.skip("Ổ đĩa này tắt tên ngắn 8.3: dạng ngắn trùng dạng dài, không có gì để so.")
    if form == "short_script":
        command = [sys.executable, _short_path(script)]
    elif form == "mixed_script":
        command = [sys.executable, _mixed_short_path(script)]
    else:
        command = [_short_path(launcher), "-c", "import time; time.sleep(60)"]
    child = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        assert _check_from_launcher(checkout, launcher) == "BUSY"
    finally:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(child.pid)],
                       capture_output=True, timeout=30, check=False)
        child.wait(timeout=10)


def _check_with_child(checkout: Path, launcher: Path, command: list[str]) -> str:
    child = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        return _check_from_launcher(checkout, launcher)
    finally:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(child.pid)],
                       capture_output=True, timeout=30, check=False)
        child.wait(timeout=10)


@pytest.mark.skipif(os.name != "nt", reason="Windows venv launcher and process query required")
@pytest.mark.parametrize("suffix", ["2", "-old"])
def test_runtime_busy_ignores_sibling_clone_with_same_prefix(venv_checkout, suffix):
    """Clone anh em `<gốc>2`, `<gốc>-old` chung tiền tố với gốc nhưng không phải source này -> FREE."""
    checkout, launcher = venv_checkout
    sibling = checkout.parent / (checkout.name + suffix)
    sibling.mkdir()
    (sibling / "idle.py").write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
    assert _check_with_child(checkout, launcher, [sys.executable, str(sibling / "idle.py")]) == "FREE"


@pytest.mark.skipif(os.name != "nt", reason="Windows venv launcher and process query required")
@pytest.mark.parametrize("form", ["long", "short"])
def test_runtime_busy_sees_checkout_root_as_last_argument(venv_checkout, form):
    """Gốc đứng cuối CommandLine (làm cwd/đối số, không có `\\` theo sau) vẫn là dùng source -> BUSY."""
    checkout, launcher = venv_checkout
    root = str(checkout) if form == "long" else _short_path(checkout)
    if form == "short" and root.lower() == str(checkout).lower():
        pytest.skip("Ổ đĩa này tắt tên ngắn 8.3: dạng ngắn trùng dạng dài, không có gì để so.")
    command = [sys.executable, "-c", "import time; time.sleep(60)", root]
    assert _check_with_child(checkout, launcher, command) == "BUSY"


@pytest.mark.skipif(os.name != "nt", reason="Windows 8.3 short names and process query required")
def test_runtime_busy_reports_path_forms_overflow(tmp_path):
    """Quá 1024 dạng đường 8.3 -> dừng với mã riêng, không trả FREE im lặng."""
    deep = tmp_path.resolve()
    for _ in range(11):
        deep = deep / "a b"
        deep.mkdir()
    if _short_path(deep).lower() == str(deep).lower():
        pytest.skip("Ổ đĩa này tắt tên ngắn 8.3: chỉ có một dạng đường.")
    spec = importlib.util.spec_from_file_location("update_release", REPO / "scripts" / "update_release.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(module.UpdateError, match="^PATH_FORMS_OVERFLOW"):
        module._runtime_busy(deep)

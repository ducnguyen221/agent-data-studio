"""SPR-61 TK7.1 (L2) — khoá `locks/powerbi-windows.txt` phải khớp `requirements.txt` và giải được bằng resolver thật."""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
LOCK = REPO / "locks" / "powerbi-windows.txt"
REQUIREMENTS = REPO / "requirements.txt"

# Nhóm (a) theo spr61-br1-fixes: công cụ phát triển (và gói chỉ chúng kéo) không thuộc venv runtime.
DEV_ONLY = {"pytest", "ruff", "iniconfig", "pluggy", "pygments", "colorama", "packaging"}
# Ghim của khoá mâu thuẫn ràng buộc của pythonnet==3.1.0 (clr-loader>=0.3.1) -> để resolver chọn.
RESOLVER_CHOSEN = {"clr-loader"}


def _pins(path: Path) -> dict[str, str]:
    pins = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Za-z0-9_.\-]+)==(\S+)\s*$", line)
        if m:
            pins[m.group(1).lower().replace("_", "-")] = m.group(2)
    return pins


def test_lock_agrees_with_requirements():
    lock, req = _pins(LOCK), _pins(REQUIREMENTS)
    assert req, "requirements.txt phải có ghim"
    disagree = {k: (v, lock[k]) for k, v in req.items() if k in lock and lock[k] != v}
    assert disagree == {}


def test_lock_has_no_dev_tools_or_conflicting_pins():
    lock = _pins(LOCK)
    assert sorted(DEV_ONLY & set(lock)) == []
    assert sorted(RESOLVER_CHOSEN & set(lock)) == []


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("uv") is None, reason="cần uv để phân giải")
def test_lock_resolves_with_requirements(tmp_path):
    out = tmp_path / "compiled.txt"
    result = subprocess.run(
        [shutil.which("uv"), "pip", "compile", str(REQUIREMENTS), "-c", str(LOCK),
         "--python-version", "3.12", "--python-platform", "windows", "-o", str(out)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300,
    )
    assert result.returncode == 0, result.stderr[-1500:]
    compiled = _pins(out)
    lock = _pins(LOCK)
    assert {k: (v, lock[k]) for k, v in compiled.items() if k in lock and lock[k] != v} == {}, sys.platform

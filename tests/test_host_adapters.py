"""Adapter host project-local (.agents/skills, .claude/skills) phải khớp nguồn trên chính checkout.

`test_installer.py` copy generator ra fixture rồi sinh mới nên không bắt được adapter đã commit
lệch `skills/*/SKILL.md` hoặc `commands/pbi-*.md`. Test này chạy `--check` trên checkout thật.
"""

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GENERATOR = REPO / "scripts" / "build_host_adapters.py"


def test_host_adapters_match_source():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8",
        timeout=60, check=False,
    )
    assert result.returncode == 0, (
        "Adapter lệch nguồn: chạy `python scripts/build_host_adapters.py` rồi review diff.\n"
        + result.stdout + result.stderr
    )

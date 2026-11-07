"""`.claude/CLAUDE.md` là con trỏ duy nhất của Claude Code về `AGENTS.md`.

`claude plugin validate --strict` đỏ khi plugin có `CLAUDE.md` ở gốc («not loaded as project
context»), và `@import` tính đường từ file chứa dòng `@` — nên dòng phải là `@../AGENTS.md`.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_khong_co_claude_md_o_goc():
    assert not (ROOT / "CLAUDE.md").exists(), "CLAUDE.md ở gốc plugin làm validate --strict đỏ"


def test_dot_claude_claude_md_nap_agents_md():
    lines = (ROOT / ".claude" / "CLAUDE.md").read_text(encoding="utf-8").splitlines()
    assert "@../AGENTS.md" in lines

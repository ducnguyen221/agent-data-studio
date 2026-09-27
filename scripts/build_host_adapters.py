"""Sinh adapter project-local từ 9 skill và 8 lệnh canonical trong source repo."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills"
COMMANDS = ROOT / "commands"
HOST_DIRS = (ROOT / ".agents" / "skills", ROOT / ".claude" / "skills")


def _adapter(skill: Path) -> str:
    frontmatter = skill.read_text(encoding="utf-8").split("---", 2)[1]
    fields = {}
    for line in frontmatter.splitlines():
        for key in ("name", "description"):
            if line.startswith(f"{key}:"):
                fields[key] = line
    if set(fields) != {"name", "description"}:
        raise ValueError(f"Skill thiếu name/description: {skill.parent.name}")
    name = skill.parent.name
    return (
        f"---\n{fields['name']}\n{fields['description']}\n---\n\n"
        f"# {name} — adapter nguồn\n\n"
        f"Đọc toàn bộ [SKILL.md](../../../skills/{name}/SKILL.md) gốc trong repo trước khi làm. "
        "Mọi script, reference, workflow và template phải mở trực tiếp từ repo này; "
        "không dùng bản copy trong cache hoặc trạm dữ liệu. "
        "Nếu không mở được file gốc, báo thiếu source và dừng tác vụ này.\n"
    )


def _command_adapter(command: Path) -> str:
    parts = command.read_text(encoding="utf-8").split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Lệnh thiếu frontmatter: {command.name}")
    description = next((line for line in parts[1].splitlines() if line.startswith("description:")), None)
    if not description:
        raise ValueError(f"Lệnh thiếu description: {command.name}")
    name = command.stem
    return (
        f"---\nname: {name}\n{description}\n---\n\n"
        f"# {name} — adapter quy trình\n\n"
        f"Đọc toàn bộ [quy trình gốc](../../../commands/{command.name}) trong repo trước khi làm. "
        "Thay `$ARGUMENTS` bằng nội dung người dùng cung cấp; nếu thiếu mục tiêu thì hỏi ngắn gọn. "
        "Đọc skill và workflow được dẫn tới trực tiếp từ repo; không lấy bản cache hoặc bản trong trạm. "
        "Nếu file gốc không mở được, báo thiếu source và dừng quy trình này.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    skills = sorted(SOURCE.glob("*/SKILL.md"))
    if len(skills) != 9:
        raise ValueError(f"Dự kiến 9 skill gốc, tìm thấy {len(skills)}")
    commands = sorted(COMMANDS.glob("pbi-*.md"))
    if len(commands) != 8:
        raise ValueError(f"Dự kiến 8 lệnh gốc, tìm thấy {len(commands)}")
    drift = []
    for host_dir in HOST_DIRS:
        entries = [(source.parent.name, _adapter(source)) for source in skills]
        entries += [(command.stem, _command_adapter(command)) for command in commands]
        for name, expected in entries:
            dest = host_dir / name / "SKILL.md"
            if dest.exists() and dest.read_text(encoding="utf-8") == expected:
                continue
            drift.append(str(dest.relative_to(ROOT)))
            if not args.check:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(expected, encoding="utf-8", newline="\n")
    if drift:
        print("Adapters need update:" if args.check else "Created adapters:", ", ".join(drift))
    return 1 if args.check and drift else 0


if __name__ == "__main__":
    raise SystemExit(main())

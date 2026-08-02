"""Knowledge OS — tầng lưu trữ tri thức NGOÀI repo, do user chỉ định (ROADMAP §M5.0).

Thứ tự resolve Knowledge Dir:
1. env `POWERBI_KNOWLEDGE_DIR`
2. `knowledge.config.json` ở gốc repo (GITIGNORED — cấu hình của MÁY, không theo repo)
3. Chưa có → None (tool trả hướng dẫn chạy setup; agent DỪNG hỏi user chỉ định folder,
   ưu tiên knowledge base/Brain có sẵn của user).

Luật riêng tư: Knowledge Dir + config KHÔNG BAO GIỜ được commit vào repo public.
"""

import json
import os
import re
import unicodedata
from datetime import date

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(_REPO_ROOT, "knowledge.config.json")

# 4 trục đóng gói tri thức (quy trình #3)
KNOWLEDGE_AXES = ("tech-stack", "industry", "business-domain", "powerbi")


def slugify(name: str) -> str:
    """Tên dự án tiếng Việt → slug an toàn cho tên folder."""
    s = unicodedata.normalize("NFD", name)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s or "project"


def resolve_root() -> str | None:
    """Trả về <KNOWLEDGE_DIR>/powerbi-agent nếu đã setup, ngược lại None."""
    base = os.getenv("POWERBI_KNOWLEDGE_DIR")
    if not base and os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                base = json.load(f).get("knowledge_dir")
        except Exception:
            base = None
    if not base:
        return None
    return os.path.join(os.path.expanduser(base), "powerbi-agent")


NOT_SETUP_MSG = (
    "Knowledge Dir CHƯA được thiết lập. Hỏi user chỉ định một folder NGOÀI repo để lưu "
    "tri thức (ưu tiên knowledge base / folder Brain có sẵn của user; chưa có thì đề xuất "
    "tạo mới, vd ~/powerbi-knowledge). Sau đó gọi tool setup_knowledge(path). "
    "KHÔNG lưu tri thức dự án vào trong repo."
)


def ensure_skeleton(root: str) -> None:
    """Dựng cấu trúc chuẩn (idempotent)."""
    os.makedirs(os.path.join(root, "projects"), exist_ok=True)
    os.makedirs(os.path.join(root, "templates"), exist_ok=True)
    for axis in KNOWLEDGE_AXES:
        os.makedirs(os.path.join(root, "knowledge", axis), exist_ok=True)

    index = os.path.join(root, "INDEX.md")
    if not os.path.exists(index):
        with open(index, "w", encoding="utf-8", newline="\n") as f:
            f.write(
                "# INDEX — powerbi-agent Knowledge\n\n"
                "> Mục lục tri thức. Agent đọc file này ĐẦU TIÊN mỗi khi làm việc "
                "với Power BI để nạp bối cảnh + kinh nghiệm cũ.\n\n"
                "## Dự án (projects/)\n\n_(chưa có — `/powerbi-new <tên>` để bắt đầu)_\n\n"
                "## Tri thức đã đóng gói (knowledge/)\n\n"
                "- `tech-stack/` — bài học theo công nghệ (SQL, M, DAX, nguồn dữ liệu…)\n"
                "- `industry/` — theo ngành (viễn thông, bán lẻ, ngân hàng…)\n"
                "- `business-domain/` — theo nghiệp vụ (doanh thu, churn, tồn kho…)\n"
                "- `powerbi/` — kỹ thuật Power BI thuần (model, visual, PBIR…)\n\n"
                "## Template riêng (templates/)\n\n"
                "_(kit chưa sanitize — trỏ env POWERBI_TEMPLATES_DIR vào đây để apply_template thấy)_\n\n"
                "## Dòng thời gian\n\nXem [TIMELINE.md](TIMELINE.md).\n"
            )

    timeline = os.path.join(root, "TIMELINE.md")
    if not os.path.exists(timeline):
        with open(timeline, "w", encoding="utf-8", newline="\n") as f:
            f.write(
                "# TIMELINE — lịch sử dự án & bài học (append-only)\n\n"
                "| Ngày | Dự án | Sự kiện | Bài học / sản phẩm | Link |\n"
                "|---|---|---|---|---|\n"
            )


def append_timeline(root: str, project: str, event: str, lesson: str = "", link: str = "") -> None:
    ensure_skeleton(root)
    line = f"| {date.today().isoformat()} | {project} | {event} | {lesson} | {link} |\n"
    with open(os.path.join(root, "TIMELINE.md"), "a", encoding="utf-8", newline="\n") as f:
        f.write(line)


def register_project_in_index(root: str, slug: str, name: str) -> None:
    """Thêm dòng dự án vào INDEX (thay placeholder nếu còn)."""
    index = os.path.join(root, "INDEX.md")
    with open(index, encoding="utf-8") as f:
        txt = f.read()
    entry = f"- [{name}](projects/{slug}/PROJECT.md) — khởi tạo {date.today().isoformat()}\n"
    if entry in txt:
        return
    # Phải nhận CẢ placeholder cũ `/pbi-new` (Knowledge Dir dựng bởi bản < 0.5.0).
    # ensure_skeleton chỉ ghi INDEX.md khi file CHƯA tồn tại, nên người nâng cấp vẫn giữ
    # dòng cũ trên đĩa. Nếu chỉ so khớp tên mới thì placeholder cũ không bao giờ bị thay,
    # và INDEX của họ mãi mãi bảo chạy `/pbi-new` — lệnh mà installer vừa xoá.
    placeholders = (
        "_(chưa có — `/powerbi-new <tên>` để bắt đầu)_\n",
        "_(chưa có — `/pbi-new <tên>` để bắt đầu)_\n",
    )
    for ph in placeholders:
        if ph in txt:
            txt = txt.replace(ph, entry)
            break
    else:
        txt = txt.replace("## Dự án (projects/)\n\n", "## Dự án (projects/)\n\n" + entry, 1)
    with open(index, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)

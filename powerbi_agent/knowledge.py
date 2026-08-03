"""Knowledge OS — nơi lưu tài liệu dự án, NẰM NGOÀI repo.

Hai vùng tách bạch, không vùng nào nằm trong repo:

  MÁY   %LOCALAPPDATA%\\powerbi-agent\\     con trỏ + sổ ghi nhớ + audit + distill
        config.json      địa chỉ thư mục dự án của máy này
        projects.json    SỔ GHI NHỚ: dự án nào, tài liệu nằm ở đâu, lúc nào
  DỮ LIỆU  <project_dir>, mặc định ~/powerbi-project/
        <slug>/ · knowledge/{4 trục}/ · templates/ · INDEX.md · TIMELINE.md

Vì sao con trỏ KHÔNG để trong repo (trước đây là `knowledge.config.json` ở gốc repo):
  - repo bị xoá / clone lại / đổi máy là mất sạch con trỏ, agent quên hết dự án cũ;
  - file nằm trong working tree thì luôn cách một lệnh `git add -A` là bị commit.
Đặt ở LOCALAPPDATA thì nó sống sót mọi thao tác với repo và không thể bị commit.

Thứ tự resolve:
1. env `POWERBI_PROJECT_DIR`
2. `config.json` trong thư mục máy
3. `knowledge.config.json` cũ ở gốc repo — CHỈ ĐỌC, để bản cài cũ không gãy
4. Chưa có → None (agent dừng, hỏi user chọn nơi lưu; gợi ý mặc định ~/powerbi-project)
"""

import json
import os
import re
import unicodedata
from datetime import date

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Con trỏ đời cũ — chỉ đọc để migrate, không ghi mới vào đây nữa.
LEGACY_CONFIG_FILE = os.path.join(_REPO_ROOT, "knowledge.config.json")

DEFAULT_PROJECT_DIRNAME = "powerbi-project"


def machine_dir() -> str:
    """Thư mục cấu hình theo MÁY. Không có dấu chấm ở tên (yêu cầu của chủ repo).

    Windows dùng %LOCALAPPDATA% — đúng chỗ quy ước cho state của ứng dụng.
    Nền khác thì lùi về ~/powerbi-agent để code vẫn chạy được khi test.
    """
    base = os.getenv("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "powerbi-agent")


CONFIG_FILE = os.path.join(machine_dir(), "config.json")
REGISTRY_FILE = os.path.join(machine_dir(), "projects.json")


def default_project_dir() -> str:
    """Gợi ý mặc định để user chỉ cần bấm Enter."""
    return os.path.join(os.path.expanduser("~"), DEFAULT_PROJECT_DIRNAME)

# 4 trục đóng gói tri thức (quy trình #3)
KNOWLEDGE_AXES = ("tech-stack", "industry", "business-domain", "powerbi")


def slugify(name: str) -> str:
    """Tên dự án tiếng Việt → slug an toàn cho tên folder."""
    s = unicodedata.normalize("NFD", name)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s or "project"


def _read_json(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)  # thay ATOMIC — không để lại file nửa vời nếu tiến trình chết


def resolve_root() -> str | None:
    """Thư mục dự án của máy này, hoặc None nếu chưa setup.

    Thư mục user chọn CHÍNH LÀ gốc — không tự đẻ thêm cấp con, để cái user thấy
    trong File Explorer đúng bằng cái agent ghi vào.
    """
    base = os.getenv("POWERBI_PROJECT_DIR") or _read_json(CONFIG_FILE).get("project_dir")
    if not base:
        # Bản cài cũ: con trỏ còn nằm trong repo. Chỉ đọc, không ghi lại vào đó.
        base = _read_json(LEGACY_CONFIG_FILE).get("knowledge_dir")
        if base:
            legacy = os.path.join(os.path.expanduser(base), "powerbi-agent")
            return legacy if os.path.isdir(legacy) else os.path.expanduser(base)
    return os.path.expanduser(base) if base else None


def set_project_dir(path: str) -> str:
    """Ghi con trỏ vào thư mục MÁY (ngoài repo) và trả về đường dẫn đã chuẩn hoá."""
    full = os.path.abspath(os.path.expanduser(path))
    cfg = _read_json(CONFIG_FILE)
    cfg["project_dir"] = full
    _write_json(CONFIG_FILE, cfg)
    return full


# ---- Sổ ghi nhớ dự án -------------------------------------------------------
# Mục đích: 6 tháng sau vẫn truy vết được "tài liệu dự án X nằm ở đâu", kể cả khi
# user cho agent ghi ra một thư mục hoàn toàn khác ngoài thư mục dự án mặc định.

def load_registry() -> list[dict]:
    data = _read_json(REGISTRY_FILE)
    return data.get("projects", []) if isinstance(data, dict) else []


def register_project(slug: str, name: str, path: str, note: str = "") -> None:
    """Ghi/cập nhật một dự án vào sổ. Khoá theo slug — chạy lại không tạo bản trùng."""
    items = load_registry()
    entry = {
        "slug": slug,
        "name": name,
        "path": os.path.abspath(os.path.expanduser(path)),
        "opened": date.today().isoformat(),
        "note": note,
    }
    for i, it in enumerate(items):
        if it.get("slug") == slug:
            entry["opened"] = it.get("opened", entry["opened"])
            items[i] = {**it, **entry}
            break
    else:
        items.append(entry)
    _write_json(REGISTRY_FILE, {"projects": items})


NOT_SETUP_MSG = (
    "Chưa thiết lập nơi lưu tài liệu dự án. HỎI user một câu duy nhất: lưu ở đâu?\n"
    f"  1. {default_project_dir()}   (mặc định — user chỉ cần đồng ý)\n"
    "  2. Một thư mục khác — user dán đường dẫn.\n"
    "Rồi gọi tool setup_knowledge(path).\n"
    "TUYỆT ĐỐI không lưu tài liệu dự án vào trong repo: repo là git working tree, "
    "chỉ một lệnh `git add -A` là dữ liệu khách hàng bị commit."
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

"""Knowledge OS — nơi lưu tài liệu dự án, NẰM NGOÀI repo.

MỘT nguyên tắc, không ngoại lệ:
**repo giữ thứ đến từ GitHub; MỌI sản phẩm tạo ra nằm ở thư mục dữ liệu ngoài repo.**

  REPO     ~/.mcp/powerbi-mcp/    code · skill · template public
           .env                   (gitignored) POWERBI_PROJECT_DIR= + secret
  DỮ LIỆU  <project_dir>, mặc định ~/powerbi-project/
           projects/<slug>/ · knowledge/{4 trục}/ · templates/ · INDEX.md · TIMELINE.md
           projects.json   SỔ GHI NHỚ: dự án nào, tài liệu nằm ở đâu, lúc nào
           policy.json     cột PII của khách
           audit/          log truy vấn DAX

Chỉ 2 thư mục. Con trỏ là MỘT DÒNG trong `.env` — không cần thư mục cấu hình thứ ba,
và `.env` vốn đã được `app.py` nạp sẵn nên không thêm cơ chế mới nào.

`audit/`, `policy.json`, `distilled/` nằm ở thư mục DỮ LIỆU chứ không phải repo: chúng nói
VỀ dữ liệu khách hàng (câu DAX, tên cột PII, schema model). Để trong repo là lặp lại đúng
lỗi đã làm lọt tên khách ra bản public.

Thứ tự resolve:
1. env `POWERBI_PROJECT_DIR` (đặt trong `.env` hoặc env thật của máy)
2. `knowledge.config.json` cũ ở gốc repo — CHỈ ĐỌC, để bản cài cũ không gãy
3. Chưa có → None (agent dừng, hỏi user chọn nơi lưu; gợi ý mặc định ~/powerbi-project)
"""

import json
import os
import re
import shutil
import unicodedata
from datetime import date, datetime

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(_REPO_ROOT, ".env")
ENV_KEY = "POWERBI_PROJECT_DIR"
# Con trỏ đời cũ — chỉ đọc để migrate, không ghi mới vào đây nữa.
LEGACY_CONFIG_FILE = os.path.join(_REPO_ROOT, "knowledge.config.json")

DEFAULT_PROJECT_DIRNAME = "powerbi-project"


def default_project_dir() -> str:
    """Gợi ý mặc định để user chỉ cần bấm đồng ý."""
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
    base = os.getenv(ENV_KEY)
    if not base:
        # Bản cài cũ: con trỏ còn nằm trong repo. Chỉ đọc, không ghi lại vào đó.
        base = _read_json(LEGACY_CONFIG_FILE).get("knowledge_dir")
        if base:
            legacy = os.path.join(os.path.expanduser(base), "powerbi-agent")
            return legacy if os.path.isdir(legacy) else os.path.expanduser(base)
    if not base:
        return None
    # Chuẩn hoá Ở CHỖ ĐỌC nữa: set_project_dir đã strip nhưng biến môi trường do user tự
    # `setx` thì không qua đó — giá trị `"C:\Data"` (kèm nháy) sẽ tạo thư mục tên có nháy.
    root = os.path.expanduser(base.strip().strip('"').strip("'"))
    # CHỐT DUY NHẤT: env trỏ thẳng vào repo thì mọi thứ dựng sau đó (INDEX.md, TIMELINE.md,
    # projects.json, audit/) đều rơi vào git working tree. Chặn ở đây thay vì ở từng chỗ gọi.
    try:
        ensure_outside_repo(root, "thư mục dự án")
    except ValueError:
        log_once_bad_project_dir(root)
        return None
    return root


_warned_bad_root: set[str] = set()


def log_once_bad_project_dir(root: str) -> None:
    if root in _warned_bad_root:
        return
    _warned_bad_root.add(root)
    from powerbi_agent.util import log
    log.error(
        "POWERBI_PROJECT_DIR trỏ vào TRONG repo (%s) — bỏ qua, coi như chưa setup. "
        "Chọn thư mục ngoài repo rồi chạy lại /powerbi-setup.", root
    )


def resolve_root_raw() -> str | None:
    """Giá trị con trỏ chưa qua kiểm tra — chỉ dùng để HIỂN THỊ trong thông báo lỗi."""
    base = os.getenv(ENV_KEY) or _read_json(LEGACY_CONFIG_FILE).get("knowledge_dir")
    return os.path.expanduser(base.strip().strip('"').strip("'")) if base else None


def set_project_dir(path: str) -> str:
    """Ghi con trỏ thành MỘT DÒNG trong `.env` của repo, rồi trả về đường dẫn chuẩn hoá.

    `.env` cũng chứa SECRET (service principal). Ghi ẩu là mất credential của user, nên
    dùng đúng kỷ luật đã kiểm chứng ở install.ps1: backup trước → upsert đúng một dòng,
    giữ nguyên mọi dòng khác → đọc lại verify. Không viết lại cả file từ đầu.
    """
    full = os.path.abspath(os.path.expanduser(path))
    lines: list[str] = []
    if os.path.exists(ENV_FILE):
        shutil.copy2(ENV_FILE, f"{ENV_FILE}.bak.{datetime.now():%Y%m%d-%H%M%S}")
        with open(ENV_FILE, encoding="utf-8") as f:
            lines = f.read().splitlines()

    entry = f"{ENV_KEY}={full}"
    for i, ln in enumerate(lines):
        # chỉ khớp dòng khai báo THẬT, bỏ qua dòng ví dụ đang bị comment
        if ln.lstrip().startswith(f"{ENV_KEY}="):
            lines[i] = entry
            break
    else:
        if lines and lines[-1].strip():
            lines.append("")
        lines += ["# Thư mục dự án — mọi tài liệu agent tạo ra đi về đây (ngoài repo).", entry]

    with open(ENV_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    with open(ENV_FILE, encoding="utf-8") as f:
        if entry not in f.read().splitlines():
            raise OSError(f"Ghi {ENV_FILE} xong nhưng đọc lại không thấy dòng {ENV_KEY} — khôi phục từ .bak")
    os.environ[ENV_KEY] = full  # có hiệu lực ngay trong phiên này, khỏi restart host
    return full


# ---- Sổ ghi nhớ dự án -------------------------------------------------------
# Mục đích: 6 tháng sau vẫn truy vết được "tài liệu dự án X nằm ở đâu", kể cả khi
# user cho agent ghi ra một thư mục hoàn toàn khác ngoài thư mục dự án mặc định.
# Sổ nằm TRONG thư mục dữ liệu: backup dữ liệu là có luôn trí nhớ, và xoá repo
# không làm agent quên gì cả.

def registry_file() -> str | None:
    root = resolve_root()
    return os.path.join(root, "projects.json") if root else None


def load_registry() -> list[dict]:
    path = registry_file()
    data = _read_json(path) if path else {}
    return data.get("projects", []) if isinstance(data, dict) else []


def register_project(slug: str, name: str, path: str, note: str = "") -> None:
    """Ghi/cập nhật một dự án vào sổ. Khoá theo slug — chạy lại không tạo bản trùng."""
    reg = registry_file()
    if not reg:
        return
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
    _write_json(reg, {"projects": items})


def _to_drive_form(p: str) -> str:
    r"""Quy mọi cách viết "đường vòng" của Windows về dạng ổ đĩa thường.

    Đây là chỗ bản trước vẫn thủng: `realpath` + `normcase` GIỮ NGUYÊN tiền tố `\\?\`
    và UNC, nên `commonpath` ném ValueError ("khác ổ đĩa") và guard hiểu nhầm là an toàn —
    trong khi `\\?\C:\<repo>\x` và `\\localhost\C$\<repo>\x` trỏ đúng vào repo.
    """
    s = str(p).strip().strip('"').strip("'").replace("/", "\\")
    if s.startswith("\\\\?\\UNC\\"):
        s = "\\\\" + s[8:]
    elif s.startswith("\\\\?\\"):
        s = s[4:]
    # \\<host>\X$\...  ->  X:\...   (chỉ với host trỏ về máy này)
    m = re.match(r"^\\\\(localhost|127\.0\.0\.1|\?)\\([A-Za-z])\$\\(.*)$", s)
    if m:
        s = f"{m.group(2)}:\\{m.group(3)}"
    return s


def _canon(p: str) -> str:
    r"""Dạng chuẩn để SO SÁNH đường dẫn trên Windows.

    So chuỗi thô là không đủ — cùng một thư mục viết được nhiều kiểu và mọi kiểu đều
    lách qua guard: chữ thường, tên 8.3 (`DUCNGU~1` — đúng dạng %TEMP% trên máy này),
    UNC, tiền tố `\\?\`. `realpath` gỡ junction/symlink (abspath KHÔNG gỡ),
    `normcase` gỡ khác biệt hoa thường, `_to_drive_form` gỡ các tiền tố đường vòng.
    """
    return os.path.normcase(os.path.realpath(_to_drive_form(os.path.expanduser(str(p)))))


def _nearest_existing(p: str) -> str | None:
    """Tổ tiên gần nhất CÓ THẬT của `p` — để stat được cả đường dẫn chưa tồn tại."""
    cur = os.path.abspath(p)
    seen = set()
    while cur and cur not in seen:
        if os.path.exists(cur):
            return cur
        seen.add(cur)
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent
    return None


def _same_or_inside(target: str, root: str) -> bool | None:
    r"""So DANH TÍNH file thay vì so chuỗi. None = không xác định được.

    Đây là điểm then chốt: liệt kê cách viết đường dẫn (`\\?\`, UNC, 8.3, hoa/thường,
    tên máy, FQDN, alias DNS, share thường trỏ vào cùng thư mục…) là việc KHÔNG BAO GIỜ
    làm xong — ba vòng review liên tiếp đều tìm ra một cách viết mới lọt qua.
    `(st_dev, st_ino)` thì không quan tâm đường dẫn viết kiểu gì: cùng một thư mục
    trên đĩa luôn cho cùng một cặp số.
    """
    try:
        anc = _nearest_existing(target)
        if anc is None:
            return None
        st_root = os.stat(root)
        cur = anc
        while True:
            try:
                st = os.stat(cur)
            except OSError:
                return None
            if (st.st_dev, st.st_ino) == (st_root.st_dev, st_root.st_ino):
                return True
            parent = os.path.dirname(cur)
            if parent == cur:
                return False
            cur = parent
    except OSError:
        return None


def ensure_outside_repo(path: str, what: str = "dữ liệu", allow_public_kits: bool = False) -> str:
    """Chặn mọi đường ghi dữ liệu khách hàng vào TRONG repo. Raise ValueError nếu vi phạm.

    Mặc định an toàn là chưa đủ: `distill_*` đều nhận `out_dir` tuỳ ý, và env
    POWERBI_AUDIT_DIR / POWERBI_POLICY_FILE / POWERBI_DISTILL_DIR / POWERBI_PROJECT_DIR
    cũng trỏ được vào repo. Một lần trỏ nhầm là schema model / câu DAX / cột PII nằm
    trong git working tree — đúng con đường đã làm lọt tên khách ra bản public.

    `allow_public_kits` chỉ được bật bởi `distill_template` KHI sanitize=True. Trước đây
    `report-templates/` là ngoại lệ theo ĐƯỜNG DẪN, nên `distill_template(sanitize=False)`
    hay `POWERBI_DISTILL_DIR=<repo>/report-templates/...` đều tuồn được dữ liệu thô vào
    đúng thư mục công khai.
    """
    # Bỏ nháy/space TRƯỚC khi expanduser: `"~/pbi"` (dạng Explorer "Copy as path" sinh ra)
    # mà expand sau thì `~` không ở vị trí 0 nên không được mở, tạo ra thư mục tên `~`.
    cleaned = str(path).strip().strip('"').strip("'")
    try:
        full = os.path.realpath(_to_drive_form(os.path.expanduser(cleaned)))
    except OSError:
        # Host UNC không tồn tại/không phản hồi → không xác định được ⇒ FAIL CLOSED.
        raise ValueError(f"TỪ CHỐI ghi {what}: không phân giải được đường dẫn {cleaned!r}.") from None

    # Ưu tiên so DANH TÍNH (st_dev, st_ino) — không phụ thuộc cách viết đường dẫn.
    ident = _same_or_inside(full, _REPO_ROOT)
    if ident is None:
        # Không stat được ⇒ fail closed, trừ khi so chuỗi khẳng định rõ là ngoài repo.
        c_full, c_repo = _canon(full), _canon(_REPO_ROOT)
        ident = c_full == c_repo or c_full.startswith(c_repo.rstrip("\\/") + os.sep)
    if not ident:
        return full
    if allow_public_kits and _same_or_inside(full, os.path.join(_REPO_ROOT, "report-templates")):
        return full
    raise ValueError(
        f"TỪ CHỐI ghi {what} vào trong repo: {full}\n"
        "Repo là git working tree công khai — dữ liệu khách hàng phải nằm ở thư mục dự án "
        f"(hiện tại: {resolve_root_raw() or 'chưa setup, chạy /powerbi-setup'})."
    )


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


def migrate_index(root: str) -> bool:
    """Cập nhật INDEX.md của thư mục dữ liệu dựng bởi bản cũ. Idempotent, trả True nếu có sửa.

    ensure_skeleton chỉ GHI INDEX.md khi file chưa tồn tại, nên người nâng cấp giữ nguyên
    nội dung cũ trỏ tới các lệnh `/pbi-*` mà installer vừa xoá. Nếu chỉ vá lúc tạo dự án mới
    thì ai không tạo dự án sẽ không bao giờ được sửa — nên chạy ở cả setup lẫn status.
    """
    index = os.path.join(root, "INDEX.md")
    if not os.path.exists(index):
        return False
    with open(index, encoding="utf-8") as f:
        txt = old = f.read()
    # Chỉ đổi tên lệnh; KHÔNG đụng nội dung tri thức user tự viết.
    for cmd in ("setup", "new", "scan", "done", "pack", "recall"):
        txt = txt.replace(f"/pbi-{cmd}", f"/powerbi-{cmd}")
    if txt == old:
        return False
    with open(index, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)
    return True


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

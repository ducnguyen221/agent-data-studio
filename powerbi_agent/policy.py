"""Tầng chính sách an toàn dữ liệu (M1 — ROADMAP.md §M1).

Nguyên tắc: dữ liệu thô ở lại trong engine Power BI; chỉ kết quả TỔNG HỢP đi vào context LLM.

- `aggregate_only` (mặc định BẬT từ M1): chặn DAX dump bảng thô. Tắt: POWERBI_AGGREGATE_ONLY=0.
- PII blocklist: file `policy.json` trong THƯ MỤC DỮ LIỆU (hoặc env POWERBI_POLICY_FILE) — cột cấm xuất hiện
  trong truy vấn. Heuristic BẢO THỦ: chặn khi tên cột xuất hiện bất kỳ đâu trong DAX (parser DAX
  đầy đủ ngoài scope; thà chặn nhầm hơn lộ nhầm — user tắt được per-cột bằng cách sửa policy.json).
- Audit log JSONL: <thư mục dự án>/audit/YYYY-MM.jsonl (đổi qua POWERBI_AUDIT_DIR).

TRUNG THỰC VỀ GIỚI HẠN: đây là guard chống rò rỉ do SƠ Ý (agent tiện tay dump bảng),
KHÔNG phải bảo mật cứng. Bảo mật cứng = RLS trên model + service principal quyền tối thiểu.
"""

import json
import os
import tempfile
import re
from datetime import datetime, timezone

from powerbi_agent.util import log

# Các pattern DAX "dump bảng thô" — EVALUATE thẳng vào bảng/ALL() không qua tổng hợp.
_RAW_DUMP_PATTERNS = [
    # EVALUATE 'Tên bảng'  /  EVALUATE Bảng  (không có hàm bọc ngoài)
    re.compile(r"^\s*EVALUATE\s+'[^']+'\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*EVALUATE\s+[A-Za-z_][\w ]*\s*$", re.IGNORECASE | re.MULTILINE),
    # EVALUATE ALL('Bảng') / ALLNOBLANKROW(...)
    re.compile(r"^\s*EVALUATE\s+ALL(NOBLANKROW)?\s*\(", re.IGNORECASE | re.MULTILINE),
]

_REWRITE_HINT = (
    "Truy vấn bị chặn bởi chính sách an toàn dữ liệu (aggregate-only): "
    "không dump dữ liệu thô từng dòng vào context. Hãy viết lại bằng "
    "SUMMARIZECOLUMNS / GROUPBY / TOPN(n nhỏ) hoặc truy vấn measure "
    "(EVALUATE ROW(\"KQ\", [Measure])). Dữ liệu thô nên ở lại trong engine. "
    "(Tắt policy khi thực sự cần: POWERBI_AGGREGATE_ONLY=0)"
)

# Trần dòng cho kết quả CÓ CỘT DIMENSION khi aggregate_only bật (kết quả thuần số không bị siết).
DIMENSION_ROW_CAP = int(os.getenv("POWERBI_DIMENSION_ROW_CAP", "200"))


def aggregate_only_enabled() -> bool:
    """M1: mặc định BẬT. Tắt bằng POWERBI_AGGREGATE_ONLY=0."""
    return os.getenv("POWERBI_AGGREGATE_ONLY", "1") != "0"


# ---------------------------------------------------------------------------
# PII blocklist
# ---------------------------------------------------------------------------

def _policy_file() -> str:
    """Blocklist PII sống ở THƯ MỤC DỮ LIỆU, không phải trong repo.

    File này liệt kê tên cột PII THẬT của khách hàng — để trong repo là lặp lại đúng
    lỗi đã làm lọt tên khách ra bản public. Repo root chỉ còn là fallback cho bản cài cũ.
    """
    env = os.getenv("POWERBI_POLICY_FILE")
    if env:
        return env
    from powerbi_agent.knowledge import resolve_root
    root = resolve_root()
    if root:
        p = os.path.join(root, "policy.json")
        if os.path.exists(p):
            return p
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    legacy = os.path.join(repo_root, "policy.json")
    if os.path.exists(legacy):
        log.warning(
            "policy.json đang nằm TRONG repo (%s). Chuyển sang %s để tên cột PII không "
            "nằm trong git working tree.", legacy, os.path.join(root or "<thư mục dự án>", "policy.json")
        )
        return legacy
    return os.path.join(root, "policy.json") if root else legacy


def load_blocklist() -> list[str]:
    """Đọc danh sách cột cấm từ policy.json. Không có file = không chặn gì."""
    path = _policy_file()
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        cols = data.get("blocked_columns", [])
        return [c for c in cols if isinstance(c, str) and c.strip()]
    except Exception as e:
        log.warning("policy.json không đọc được (%s) — bỏ qua blocklist.", e)
        return []


def _find_blocked(dax_query: str, blocklist: list[str]) -> str | None:
    q = dax_query.lower()
    for col in blocklist:
        if col.lower() in q:
            return col
    return None


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

def _audit_dir() -> str:
    """Log truy vấn đi cùng DỮ LIỆU — backup dữ liệu là có luôn bằng chứng ai đã hỏi gì.

    Chưa setup thì vẫn có thể chạy DAX, mà câu DAX chứa tên bảng/cột khách hàng nên
    KHÔNG được ghi vào repo. Lúc đó lùi về %TEMP% — tạm nhưng nằm ngoài git.
    """
    env = os.getenv("POWERBI_AUDIT_DIR")
    if env:
        return env
    from powerbi_agent.knowledge import resolve_root
    root = resolve_root()
    if root:
        return os.path.join(root, "audit")
    return os.path.join(tempfile.gettempdir(), "powerbi-agent-audit")


def audit(tool: str, dax_query: str, verdict: str, rows: int = -1) -> None:
    """Ghi 1 dòng JSONL audit. Lỗi ghi audit KHÔNG được làm hỏng truy vấn."""
    try:
        d = _audit_dir()
        os.makedirs(d, exist_ok=True)
        now = datetime.now(timezone.utc)
        path = os.path.join(d, f"{now.strftime('%Y-%m')}.jsonl")
        entry = {
            "ts": now.isoformat(timespec="seconds"),
            "tool": tool,
            "verdict": verdict,          # allowed | blocked_raw_dump | blocked_pii | error
            "rows": rows,                 # -1 = không áp dụng / lỗi
            "dax": dax_query[:500],
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        log.warning("Không ghi được audit log: %s", e)


# ---------------------------------------------------------------------------
# Cổng kiểm tra chính
# ---------------------------------------------------------------------------

def check_dax(dax_query: str, tool: str = "execute_dax") -> tuple[bool, str]:
    """Kiểm tra 1 câu DAX theo policy. Trả (allowed, reason_nếu_chặn). Tự ghi audit khi CHẶN
    (case allowed do caller ghi sau khi biết số dòng kết quả)."""
    if aggregate_only_enabled():
        for pat in _RAW_DUMP_PATTERNS:
            if pat.search(dax_query):
                audit(tool, dax_query, "blocked_raw_dump")
                return False, _REWRITE_HINT

    blocked_col = _find_blocked(dax_query, load_blocklist())
    if blocked_col:
        audit(tool, dax_query, "blocked_pii")
        return False, (
            f"Truy vấn bị chặn: cột '{blocked_col}' nằm trong PII blocklist (policy.json). "
            "Cột này không được xuất vào context LLM. Nếu chỉ cần đếm/tổng hợp, hãy tính bằng "
            "measure không project cột đó; nếu thực sự cần, sửa policy.json (quyết định của người)."
        )

    return True, ""


def cap_dimension_rows(df, requested_max: int) -> int:
    """Trần dòng hiệu dụng: kết quả có cột dạng chữ (dimension) bị siết còn DIMENSION_ROW_CAP
    khi aggregate_only bật; kết quả thuần số giữ nguyên requested_max."""
    if not aggregate_only_enabled():
        return requested_max
    try:
        import pandas.api.types as ptypes
        has_text_col = any(
            not ptypes.is_numeric_dtype(dt) and not ptypes.is_datetime64_any_dtype(dt)
            for dt in df.dtypes
        )
    except Exception:
        return requested_max
    if not has_text_col:
        return requested_max
    if requested_max == 0:
        return DIMENSION_ROW_CAP
    return min(requested_max, DIMENSION_ROW_CAP)

# -*- coding: utf-8 -*-
"""mockpack — thư viện dùng chung của skill `mockup-data`.

Ba lệnh CLI, tất cả đọc cùng một nguồn sự thật là `dataset.yaml`:

    python mockpack.py dict   dataset.yaml -o DATASET_SPEC.md      # sinh phần cấu trúc của tài liệu
    python mockpack.py verify dataset.yaml data/                   # kiểm tra dữ liệu theo rule
    python mockpack.py pack   dataset.yaml data/ -o BoDuLieu.xlsx  # đóng gói Excel + Data Dictionary

Ngoài ra là thư viện helper cho generator (`import mockpack`):
    rng, id_seq, lognormal_amount, poisson_counts, pareto_pick,
    date_series, funnel, jitter, mask_email, mask_phone, vn_names

Engine verify (Report + toàn bộ rule) nằm ở `mockverify.py` CÙNG THƯ MỤC — lệnh
`verify` tự import; chép mockpack.py đi đâu thì chép kèm mockverify.py theo.

KHÔNG sửa file này cho từng dự án — phần riêng của dự án nằm ở generator.
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys
import unicodedata
from datetime import date, datetime

import numpy as np
import pandas as pd
import yaml

# Chỉ wrap khi console chưa phải UTF-8. Guard này còn chống double-wrap: khi chạy CLI,
# file này là `__main__` và mockverify import nó lần hai — wrap lần nữa sẽ làm wrapper cũ
# bị GC đóng mất buffer gốc ("I/O operation on closed file").
if hasattr(sys.stdout, "buffer") and (sys.stdout.encoding or "").lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

GEN_BEGIN = "<!-- BEGIN GENERATED"
GEN_END = "<!-- END GENERATED -->"

PII_FORBIDDEN = [
    "email", "phone", "sdt", "so_dien_thoai", "cccd", "cmnd", "passport",
    "full_name", "ho_ten", "dia_chi", "address", "card_number", "so_the",
]
PII_ALLOWED_SUFFIX = ("_masked", "_hash", "_token", "_id", "_key")

TYPE_LABEL = {
    "text": "Text", "int": "Whole Number", "decimal": "Decimal Number",
    "date": "Date", "timestamp": "Date/Time", "bool": "Boolean", "enum": "List",
}

# Tên bảng được ghép thẳng vào đường dẫn CSV nên regex này còn là hàng rào path traversal.
NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
VALID_TYPES = set(TYPE_LABEL)
VALID_LAYERS = {"business", "database", "both"}

# =============================================================================
# SPEC
# =============================================================================


def load_spec(path: str) -> dict:
    """Đọc dataset.yaml, kiểm tra tối thiểu và bổ sung giá trị mặc định."""
    with open(path, "r", encoding="utf-8") as fh:
        spec = yaml.safe_load(fh)

    if not isinstance(spec, dict) or "dataset" not in spec or "tables" not in spec:
        raise ValueError(f"{path}: thiếu khối `dataset:` hoặc `tables:`")

    ds = spec["dataset"]
    ds.setdefault("layer", "business")
    ds.setdefault("currency", "VND")
    if "seed" not in ds:
        raise ValueError("dataset.seed là bắt buộc — không có seed thì bộ dữ liệu không tái lập được")
    if ds["layer"] not in VALID_LAYERS:
        raise ValueError(f"dataset.layer=`{ds['layer']}` không hợp lệ — phải là một trong {sorted(VALID_LAYERS)}")

    seen = set()
    for tbl in spec["tables"]:
        for field in ("name", "grain", "columns"):
            if not tbl.get(field):
                raise ValueError(f"bảng `{tbl.get('name', '?')}`: thiếu `{field}`")
        if not NAME_RE.match(str(tbl["name"])):
            raise ValueError(f"bảng `{tbl['name']}`: tên bảng phải khớp ^[a-z][a-z0-9_]*$ "
                             "(chữ thường/số/gạch dưới — tên bảng ghép vào đường dẫn CSV nên cấm ký tự lạ)")
        if tbl["name"] in seen:
            raise ValueError(f"bảng `{tbl['name']}` bị khai hai lần")
        seen.add(tbl["name"])
        tbl.setdefault("label", tbl["name"])
        tbl.setdefault("type", "fact" if tbl["name"].startswith("fact") else "dim")
        tbl.setdefault("sheet", tbl["name"])
        tbl.setdefault("layer", "both")
        if tbl["layer"] not in VALID_LAYERS:
            raise ValueError(f"bảng `{tbl['name']}`: layer=`{tbl['layer']}` không hợp lệ — "
                             f"phải là một trong {sorted(VALID_LAYERS)}")
        cols, labels, pk_cols = set(), set(), []
        for col in tbl["columns"]:
            if not col.get("name"):
                raise ValueError(f"bảng `{tbl['name']}`: có cột thiếu `name`")
            if not NAME_RE.match(str(col["name"])):
                raise ValueError(f"bảng `{tbl['name']}`: tên cột `{col['name']}` phải khớp ^[a-z][a-z0-9_]*$")
            if col["name"] in cols:
                raise ValueError(f"bảng `{tbl['name']}`: cột `{col['name']}` bị khai hai lần")
            cols.add(col["name"])
            col.setdefault("type", "text")
            col.setdefault("label", col["name"])
            col.setdefault("nullable", True)
            if col["type"] not in VALID_TYPES:
                raise ValueError(f"bảng `{tbl['name']}`: cột `{col['name']}` có type=`{col['type']}` "
                                 f"không hợp lệ — phải là một trong {sorted(VALID_TYPES)}")
            if col["type"] == "enum" and not col.get("values"):
                raise ValueError(f"bảng `{tbl['name']}`: cột enum `{col['name']}` thiếu `values` "
                                 "(danh mục giá trị hợp lệ)")
            if col["label"] in labels:
                # nhãn trùng làm hỏng việc đọc ngược từ .xlsx (header sheet dữ liệu là nhãn)
                raise ValueError(f"bảng `{tbl['name']}`: nhãn `{col['label']}` bị dùng cho hai cột — "
                                 "mỗi cột phải có label riêng để đọc ngược được từ Excel")
            labels.add(col["label"])
            if col.get("key") == "PK":
                pk_cols.append(col["name"])
            if not col.get("definition"):
                # đang soạn dở vẫn phải chạy được — chỉ nhắc, không chặn
                print(f"! cảnh báo: {tbl['name']}.{col['name']} chưa có `definition` — bổ sung trước khi bàn giao")
        if len(pk_cols) > 1:
            raise ValueError(f"bảng `{tbl['name']}`: có {len(pk_cols)} cột key=PK ({pk_cols}) — "
                             "mỗi bảng chỉ được 0 hoặc 1 PK (khoá tổ hợp dùng rule `unique`)")

    # Tên sheet sau sanitize không được trùng — trùng là hai bảng đè nhau trong .xlsx
    sheets = {}
    for tbl in spec["tables"]:
        s = sanitize_sheet(tbl["sheet"])
        if s in sheets:
            raise ValueError(f"bảng `{tbl['name']}` và `{sheets[s]}` cùng ra tên sheet `{s}` sau khi "
                             "chuẩn hoá (cắt 31 ký tự, thay ký tự cấm) — đổi `sheet` của một trong hai")
        sheets[s] = tbl["name"]

    # FK trỏ tới bảng có thật và cột đó phải là PK của bảng đích
    for tbl in spec["tables"]:
        for col in tbl["columns"]:
            ref = parse_fk(col.get("key"))
            if not ref:
                continue
            rt, rc = ref
            target = find_table(spec, rt)
            if target is None:
                raise ValueError(f"{tbl['name']}.{col['name']}: FK trỏ tới bảng `{rt}` không tồn tại")
            tcol = next((c for c in target["columns"] if c["name"] == rc), None)
            if tcol is None:
                raise ValueError(f"{tbl['name']}.{col['name']}: FK trỏ tới cột `{rt}.{rc}` không tồn tại")
            if tcol.get("key") != "PK":
                raise ValueError(f"{tbl['name']}.{col['name']}: FK phải trỏ tới cột PK — "
                                 f"`{rt}.{rc}` không phải PK của bảng đích")

    spec.setdefault("relationships", [])
    spec.setdefault("metrics", [])
    spec.setdefault("rules", [])
    spec.setdefault("intentional_issues", [])

    # metric trỏ tới bảng ma là spec hỏng — bắt ngay từ lúc load
    for m in spec["metrics"]:
        mt = m.get("table")
        if mt and find_table(spec, mt) is None:
            raise ValueError(f"metric `{m.get('name', '?')}`: trỏ tới bảng `{mt}` không có trong tables")
    return spec


def parse_fk(key):
    if not key or not isinstance(key, str):
        return None
    m = re.match(r"^FK\s*->\s*([\w]+)\.([\w]+)$", key.strip())
    return (m.group(1), m.group(2)) if m else None


def find_table(spec: dict, name: str):
    for tbl in spec["tables"]:
        if tbl["name"] == name:
            return tbl
    return None


def tables_for_layer(spec: dict):
    """Lọc bảng theo `dataset.layer` (business | database | both)."""
    want = spec["dataset"].get("layer", "business")
    if want == "both":
        return list(spec["tables"])
    return [t for t in spec["tables"] if t.get("layer", "both") in (want, "both")]


def waived_ids(spec: dict) -> set:
    out = set()
    for issue in spec.get("intentional_issues", []):
        out.update(issue.get("waives", []) or [])
    for rule in spec.get("rules", []):
        if rule.get("intentional_fail"):
            out.add(rule.get("id", rule.get("name", "?")))
    return out


# =============================================================================
# ĐỌC DỮ LIỆU
# =============================================================================


def read_frames(spec: dict, source: str) -> dict:
    """Đọc dữ liệu từ thư mục CSV (mỗi bảng một file <ten_bang>.csv) hoặc từ file .xlsx đã đóng gói."""
    frames = {}
    if source.lower().endswith((".xlsx", ".xlsm")):
        book = pd.ExcelFile(source)
        by_sheet = {sanitize_sheet(t["sheet"]): t["name"] for t in spec["tables"]}
        for sheet in book.sheet_names:
            if sheet not in by_sheet:
                continue
            tbl = find_table(spec, by_sheet[sheet])
            df = book.parse(sheet, dtype=object)
            # sheet dữ liệu dùng nhãn tiếng Việt làm header cho người đọc —
            # đổi ngược về tên cột kỹ thuật để rule chạy được trên chính file .xlsx
            names = {c["name"] for c in tbl["columns"]}
            relabel = {c["label"]: c["name"] for c in tbl["columns"]
                       if c["label"] not in names and c["label"] in df.columns}
            frames[tbl["name"]] = df.rename(columns=relabel) if relabel else df
    else:
        # lớp phòng thủ thứ hai (sau regex tên bảng ở load_spec): file đọc phải nằm TRONG source,
        # kể cả khi có symlink/junction hay tên bảng lọt lưới bằng cách nào đó
        root = os.path.realpath(source)
        for tbl in spec["tables"]:
            path = os.path.realpath(os.path.join(source, f"{tbl['name']}.csv"))
            if path != root and not path.startswith(root + os.sep):
                raise ValueError(f"bảng `{tbl['name']}`: đường dẫn CSV `{path}` thoát ra ngoài thư mục nguồn `{root}`")
            if os.path.exists(path):
                frames[tbl["name"]] = pd.read_csv(path, dtype=str, keep_default_na=True)
    return frames


def to_datetime_smart(series: pd.Series) -> pd.Series:
    """Đọc ngày an toàn: ưu tiên ISO (`2026-09-12`), chỉ fallback dd/mm/yyyy cho phần ISO không đọc được.

    Không dùng dayfirst=True cho cả cột: pandas sẽ lật `2026-09-12` thành 12/09 → sai âm thầm.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    head = series.dropna().head(50)
    if len(head) and all(isinstance(v, (datetime, date, pd.Timestamp)) for v in head):
        return pd.to_datetime(series, errors="coerce")
    out = pd.to_datetime(series, errors="coerce", format="ISO8601")
    mask = out.isna() & series.notna()
    if mask.any():
        out.loc[mask] = pd.to_datetime(series[mask], errors="coerce", format="mixed", dayfirst=True)
    return out


def typed_frame(df: pd.DataFrame, tbl: dict) -> pd.DataFrame:
    """Ép kiểu theo spec để chạy rule. Giá trị không ép được thành NaN/NaT."""
    out = df.copy()
    for col in tbl["columns"]:
        name, ctype = col["name"], col["type"]
        if name not in out.columns:
            continue
        if ctype in ("int", "decimal"):
            out[name] = pd.to_numeric(out[name], errors="coerce")
        elif ctype in ("date", "timestamp"):
            out[name] = to_datetime_smart(out[name])
        elif ctype == "bool":
            out[name] = out[name].map(
                lambda v: True if str(v).strip().lower() in ("1", "true", "yes", "x")
                else (False if str(v).strip().lower() in ("0", "false", "no", "") else None)
            )
        else:
            out[name] = out[name].map(lambda v: None if v is None or (isinstance(v, float) and pd.isna(v)) else str(v))
    return out


# =============================================================================
# DICT — sinh phần cấu trúc của DATASET_SPEC.md
# =============================================================================


def render_dict_md(spec: dict) -> str:
    ds = spec["dataset"]
    out = []
    out += [
        "## §2. Thông tin bộ dữ liệu", "",
        "| Thuộc tính | Giá trị |", "|---|---|",
        f"| Mã bộ dữ liệu | `{ds['id']}` |",
        f"| Tên | {ds.get('name', '')} |",
        f"| Phiên bản | {ds.get('version', '1.0')} |",
        f"| Seed | `{ds['seed']}` |",
        f"| Mốc hiện tại (as_of_date) | {ds.get('as_of_date', '—')} |",
        f"| Khoảng thời gian | {ds.get('period_start', '—')} → {ds.get('as_of_date', '—')} |",
        f"| Tiền tệ | {ds.get('currency', '—')} |",
        f"| Lớp bàn giao | {ds.get('layer')} |",
        "",
    ]
    brief = spec.get("brief") or {}
    if brief.get("questions"):
        out += ["**Câu hỏi phân tích phải trả lời được:**", ""]
        out += [f"{i}. {q}" for i, q in enumerate(brief["questions"], 1)]
        out += [""]

    out += ["## §3. Danh sách bảng", "",
            "| Bảng | Nhãn | Loại | Grain (1 dòng = ?) | Sheet | Số dòng | Nguồn |", "|---|---|---|---|---|---|---|"]
    for t in spec["tables"]:
        out.append(f"| `{t['name']}` | {t['label']} | {t['type']} | {t['grain']} | "
                   f"{t['sheet']} | {t.get('rows', '—')} | {t.get('source_system', '—')} |")
    out += [""]

    out += ["## §4. Từ điển dữ liệu (Data Dictionary)", ""]
    for t in spec["tables"]:
        out += [f"### `{t['name']}` — {t['label']}", "",
                f"> **Grain:** {t['grain']}  ·  **Loại:** {t['type']}  ·  **Nguồn:** {t.get('source_system', '—')}", "",
                "| # | Cột | Nhãn | Kiểu | Khoá | Bắt buộc | Giá trị hợp lệ | Đơn vị | Cộng dồn | Định nghĩa | Công thức |",
                "|---|---|---|---|---|---|---|---|---|---|---|"]
        for i, c in enumerate(t["columns"], 1):
            vals = ", ".join(str(v) for v in c["values"]) if c.get("values") else (
                f"{c.get('min', '')}–{c.get('max', '')}" if c.get("min") is not None or c.get("max") is not None else "—")
            out.append(
                f"| {i} | `{c['name']}` | {c['label']} | {TYPE_LABEL.get(c['type'], c['type'])} | "
                f"{c.get('key', '—')} | {'Có' if not c.get('nullable', True) else 'Không'} | {vals} | "
                f"{c.get('unit', '—')} | {c.get('additive', '—')} | {c.get('definition', '')} | "
                f"{('`' + c['calc_rule'] + '`') if c.get('calc_rule') else '—'} |")
        out += [""]

    if spec.get("relationships"):
        out += ["## §5. Quan hệ giữa các bảng", "",
                "| Từ | Đến | Chiều | Ghi chú |", "|---|---|---|---|"]
        for r in spec["relationships"]:
            out.append(f"| `{r['from']}` | `{r['to']}` | {r.get('cardinality', 'many_to_one')} | {r.get('note', '')} |")
        out += ["", "```", *relationship_diagram(spec), "```", ""]

    if spec.get("metrics"):
        out += ["## §6. Chỉ số (Metrics)", "",
                "| Chỉ số | Công thức | Đơn vị | Bảng | Định nghĩa |", "|---|---|---|---|---|"]
        for m in spec["metrics"]:
            out.append(f"| {m['name']} | `{m.get('formula', '')}` | {m.get('unit', '—')} | "
                       f"`{m.get('table', '—')}` | {m.get('definition', '')} |")
        out += [""]

    out += ["## §6b. Rule kiểm tra dữ liệu", "",
            "Rule cơ bản (PK, FK, not-null, kiểu, danh mục, khoảng giá trị, mốc thời gian, PII) "
            "được suy tự động từ §4 — không liệt kê ở đây. Rule nghiệp vụ khai trong `dataset.yaml`:", "",
            "| ID | Nội dung | Loại | Bảng |", "|---|---|---|---|"]
    for r in spec.get("rules", []):
        out.append(f"| `{r.get('id', '')}` | {r.get('name', '')} | {r.get('kind', 'expression')} | "
                   f"`{r.get('table', r.get('child', '—'))}` |")
    out += [""]
    if spec.get("intentional_issues"):
        out += ["**Lỗi cài cắm có chủ đích:**", "",
                "| ID | Mô tả | Rule được miễn |", "|---|---|---|"]
        for issue in spec["intentional_issues"]:
            out.append(f"| {issue.get('id', '')} | {issue.get('description', '')} | "
                       f"{', '.join(f'`{w}`' for w in issue.get('waives', []) or []) or '—'} |")
        out += [""]
    return "\n".join(out)


def relationship_diagram(spec: dict):
    lines = []
    for r in spec["relationships"]:
        arrow = {"many_to_one": "→", "one_to_many": "←", "one_to_one": "—"}.get(r.get("cardinality"), "→")
        lines.append(f"{r['from']:<40} {arrow} {r['to']}")
    return lines


def write_dict(spec: dict, out_path: str):
    body = render_dict_md(spec)
    block = (f"{GEN_BEGIN} — sinh bởi mockpack.py từ {spec['dataset'].get('spec_yaml', 'dataset.yaml')}. "
             f"ĐỪNG SỬA TAY. -->\n\n{body}\n{GEN_END}")
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as fh:
            old = fh.read()
        if GEN_BEGIN in old and GEN_END in old:
            head = old.split(GEN_BEGIN)[0]
            tail = old.split(GEN_END, 1)[1]
            new = head + block + tail
        else:
            new = old.rstrip() + "\n\n" + block + "\n"
    else:
        ds = spec["dataset"]
        new = (f"---\ntitle: \"DATASET SPEC — {ds.get('name', ds['id'])}\"\ntype: dataset_spec\n"
               f"spec_yaml: {ds.get('spec_yaml', 'dataset.yaml')}\n---\n\n"
               f"# DATASET SPEC — {ds.get('name', ds['id'])}\n\n"
               "## §1. Brief nghiệp vụ  *(viết tay)*\n\n_TODO: bối cảnh, mục đích, quy trình, "
               "quy tắc nghiệp vụ, câu hỏi phân tích, giả định._\n\n---\n\n" + block + "\n")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(new)
    print(f"→ {out_path} (§2–§6 sinh từ YAML, §1 giữ nguyên)")


# =============================================================================
# PACK — Excel
# =============================================================================


def sanitize_sheet(name: str) -> str:
    out = re.sub(r"[\[\]:*?/\\]", "-", str(name)).strip()
    return (out[:31] or "Sheet")


def pack(spec: dict, source: str, out_path: str):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    ds = spec["dataset"]
    frames = read_frames(spec, source)
    tables = tables_for_layer(spec)

    # FAIL-FAST: gom đủ mọi thiếu hụt rồi raise một lần — tuyệt đối không lưu file thiếu sheet,
    # vì file .xlsx "gần đủ" trông như bàn giao được và lỗi sẽ trôi qua im lặng
    problems = []
    for t in tables:
        if t["name"] not in frames:
            problems.append(f"bảng `{t['name']}`: không có dữ liệu (thiếu file CSV/sheet)")
            continue
        missing = [c["name"] for c in t["columns"] if c["name"] not in frames[t["name"]].columns]
        if missing:
            problems.append(f"bảng `{t['name']}`: dữ liệu thiếu cột đã khai trong spec: {missing}")
    if problems:
        raise ValueError("pack dừng — dữ liệu không khớp spec, KHÔNG lưu .xlsx:\n  - "
                         + "\n  - ".join(problems))

    wb = Workbook()
    wb.remove(wb.active)
    head_fill = PatternFill("solid", fgColor="1F4E78")
    head_font = Font(color="FFFFFF", bold=True)

    def write_grid(ws, headers, rows, widths=None):
        ws.append([safe_excel_text(h) for h in headers])
        for cell in ws[1]:
            cell.fill, cell.font = head_fill, head_font
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        for row in rows:
            ws.append([safe_excel_text(v) for v in row])
        ws.freeze_panes = "A2"
        if rows:
            ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{len(rows) + 1}"
        for i, head in enumerate(headers, 1):
            sample = [str(r[i - 1]) for r in rows[:200] if r[i - 1] is not None]
            width = max([len(str(head))] + [len(s) for s in sample] + [8])
            ws.column_dimensions[get_column_letter(i)].width = min(width + 2, 45)

    # --- 00_README ---
    ws = wb.create_sheet("00_README")
    info = [
        ("Bộ dữ liệu", ds.get("name", ds["id"])),
        ("Mã", ds["id"]), ("Phiên bản", str(ds.get("version", "1.0"))),
        ("Mục đích", (spec.get("brief") or {}).get("purpose", "")),
        ("Lĩnh vực", (spec.get("brief") or {}).get("domain", "")),
        ("Seed", str(ds["seed"])),
        ("Mốc hiện tại", str(ds.get("as_of_date", ""))),
        ("Khoảng thời gian", f"{ds.get('period_start', '')} → {ds.get('as_of_date', '')}"),
        ("Tiền tệ", ds.get("currency", "")),
        ("Lớp bàn giao", ds.get("layer", "")),
        ("Sinh lúc", datetime.now().strftime("%Y-%m-%d %H:%M")),
        ("CẢNH BÁO", "DỮ LIỆU GIẢ LẬP — không phải dữ liệu thật, không chứa thông tin cá nhân có thật."),
    ]
    write_grid(ws, ["Thuộc tính", "Giá trị"], info)
    # mọi ws.append thủ công cũng đi qua safe_excel_text — một quy tắc, một chỗ định nghĩa
    ws.append([]); ws.append(["Danh sách sheet", ""])
    ws.append(["Sheet", "Nội dung"])
    ws.append(["01_Data_Dictionary", "Từ điển dữ liệu: mô tả từng bảng, từng cột, kiểu, khoá, định nghĩa"])
    ws.append(["02_Relationships", "Quan hệ giữa các bảng"])
    ws.append(["03_Metrics", "Chỉ số KPI và công thức"])
    for t in tables:
        ws.append([safe_excel_text(sanitize_sheet(t["sheet"])), safe_excel_text(f"{t['label']} — {t['grain']}")])
    if spec.get("intentional_issues"):
        ws.append([]); ws.append(["Lỗi cài cắm có chủ đích", ""])
        for issue in spec["intentional_issues"]:
            ws.append([safe_excel_text(issue.get("id", "")), safe_excel_text(issue.get("description", ""))])

    # --- 01_Data_Dictionary ---
    dict_headers = ["table", "table_label", "table_type", "grain", "sheet", "column_order", "column",
                    "column_label", "data_type", "format", "nullable", "key", "allowed_values", "unit",
                    "definition", "calc_rule", "additive", "pii", "source_system", "example"]
    dict_rows = []
    for t in tables:
        for i, c in enumerate(t["columns"], 1):
            dict_rows.append([
                t["name"], t["label"], t["type"], t["grain"], sanitize_sheet(t["sheet"]), i,
                c["name"], c["label"], TYPE_LABEL.get(c["type"], c["type"]), c.get("format", ""),
                "Không" if not c.get("nullable", True) else "Có", c.get("key", ""),
                ", ".join(str(v) for v in c["values"]) if c.get("values") else (
                    f"{c.get('min', '')}–{c.get('max', '')}"
                    if c.get("min") is not None or c.get("max") is not None else ""),
                c.get("unit", ""), c.get("definition", ""), c.get("calc_rule", ""),
                c.get("additive", ""), "Có" if c.get("pii") else "", t.get("source_system", ""),
                str(c.get("example", "")),
            ])
    write_grid(wb.create_sheet("01_Data_Dictionary"), dict_headers, dict_rows)

    write_grid(wb.create_sheet("02_Relationships"), ["from", "to", "cardinality", "note"],
               [[r["from"], r["to"], r.get("cardinality", "many_to_one"), r.get("note", "")]
                for r in spec.get("relationships", [])])

    write_grid(wb.create_sheet("03_Metrics"), ["metric", "formula", "unit", "table", "definition"],
               [[m["name"], m.get("formula", ""), m.get("unit", ""), m.get("table", ""), m.get("definition", "")]
                for m in spec.get("metrics", [])])

    # --- sheet dữ liệu --- (fail-fast phía trên đã bảo đảm mọi bảng đều có dữ liệu + đủ cột)
    for t in tables:
        df = typed_frame(frames[t["name"]], t)
        cols = [c for c in t["columns"] if c["name"] in df.columns]
        ws = wb.create_sheet(sanitize_sheet(t["sheet"]))
        ws.append([c["label"] for c in cols])
        for cell in ws[1]:
            cell.fill, cell.font = head_fill, head_font
            cell.alignment = Alignment(vertical="center", wrap_text=True)

        for _, row in df.iterrows():
            ws.append([excel_value(row[c["name"]], c["type"]) for c in cols])

        for i, c in enumerate(cols, 1):
            letter = get_column_letter(i)
            fmt = number_format(c)
            for cell in ws[letter][1:]:
                cell.number_format = fmt
            sample = df[c["name"]].astype(str).head(200)
            width = max([len(c["label"])] + [len(s) for s in sample] + [8])
            ws.column_dimensions[letter].width = min(width + 2, 45)
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{len(df) + 1}"

    wb.save(out_path)
    print(f"→ {out_path} ({len(wb.sheetnames)} sheet: {', '.join(wb.sheetnames[:6])}...)")


def safe_excel_text(value):
    """Chặn Excel formula injection: chuỗi bắt đầu bằng `=` `+` `-` `@` được prefix `'`.

    Chỉ đụng vào chuỗi — None/số/ngày/bool giữ nguyên. Đây là NƠI DUY NHẤT định nghĩa
    quy tắc: excel_value (ô dữ liệu) lẫn write_grid/README (sheet mô tả) đều gọi lại hàm này.
    """
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@"):
        return "'" + value
    return value


def excel_value(val, ctype):
    """Chuyển 1 ô sang giá trị Excel an toàn (giữ mã có số 0 đầu, chặn formula injection)."""
    if val is None or (isinstance(val, float) and pd.isna(val)) or val is pd.NaT:
        return None
    if ctype in ("date", "timestamp"):
        ts = pd.Timestamp(val)
        return ts.to_pydatetime() if ctype == "timestamp" else ts.date()
    if ctype == "int":
        return None if pd.isna(val) else int(val)
    if ctype == "decimal":
        return None if pd.isna(val) else float(val)
    if ctype == "bool":
        return bool(val)
    return safe_excel_text(str(val))


def number_format(col):
    ctype = col["type"]
    if ctype == "date":
        return "dd/mm/yyyy"
    if ctype == "timestamp":
        return "dd/mm/yyyy hh:mm"
    if ctype == "int":
        return "#,##0"
    if ctype == "decimal":
        return "#,##0" if str(col.get("unit", "")).upper() == "VND" else "#,##0.00"
    return "@"


# =============================================================================
# HELPER cho generator
# =============================================================================


def rng(seed: int) -> np.random.Generator:
    """Nguồn ngẫu nhiên DUY NHẤT của một generator. Không trộn với random.* toàn cục."""
    return np.random.default_rng(seed)


def id_seq(prefix: str, n: int, width: int = 6, start: int = 1):
    """`KH-000001`, `KH-000002`, ... — mã có prefix, không mất số 0 đầu khi mở Excel."""
    return [f"{prefix}{i:0{width}d}" for i in range(start, start + n)]


def lognormal_amount(r: np.random.Generator, n: int, median: float, sigma: float = 0.6,
                     round_to: int = 1000, cap: float | None = None):
    """Giá trị tiền tệ đuôi dài phải: nhiều giao dịch nhỏ, ít giao dịch rất lớn."""
    vals = r.lognormal(mean=np.log(median), sigma=sigma, size=n)
    if cap:
        vals = np.minimum(vals, cap)
    return np.maximum(np.round(vals / round_to) * round_to, round_to)


def poisson_counts(r: np.random.Generator, n: int, mean: float, minimum: int = 0):
    """Số lần xảy ra của một sự kiện đếm được (số đơn/khách, số lần đăng nhập...)."""
    return np.maximum(r.poisson(mean, n), minimum)


def pareto_pick(r: np.random.Generator, items, n: int, alpha: float = 1.2):
    """Chọn theo luật 80/20: ~20% mã đầu danh sách chiếm phần lớn lượt chọn."""
    items = list(items)
    w = np.array([1.0 / ((i + 1) ** alpha) for i in range(len(items))])
    return r.choice(items, size=n, p=w / w.sum())


def date_series(r: np.random.Generator, n: int, start, end,
                month_weights=None, dow_weights=None, trend: float = 0.0):
    """Sinh ngày có mùa vụ (theo tháng, theo thứ) và xu hướng tăng/giảm tuyến tính.

    month_weights: dict {1..12: hệ số}   dow_weights: dict {0=Thứ 2..6=CN: hệ số}
    trend: 0.3 nghĩa là cuối kỳ nhiều hơn đầu kỳ ~30%.
    """
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    days = pd.date_range(start, end, freq="D")
    w = np.ones(len(days), dtype=float)
    if month_weights:
        w *= np.array([month_weights.get(d.month, 1.0) for d in days])
    if dow_weights:
        w *= np.array([dow_weights.get(d.dayofweek, 1.0) for d in days])
    if trend:
        w *= np.linspace(1.0, 1.0 + trend, len(days))
    w *= r.uniform(0.9, 1.1, len(days))          # nhiễu ngày
    picked = r.choice(len(days), size=n, p=w / w.sum())
    return pd.to_datetime([days[i] for i in picked])


def funnel(r: np.random.Generator, n: int, rates, noise: float = 0.1):
    """Phễu chuyển đổi đơn điệu giảm. rates=[0.96, 0.32, 0.07] → trả về số lượng từng bước."""
    counts, cur = [n], n
    for rate in rates:
        rate = float(np.clip(rate * r.uniform(1 - noise, 1 + noise), 0, 1))
        cur = int(round(cur * rate))
        counts.append(cur)
    return counts


def jitter(r: np.random.Generator, values, pct: float = 0.1):
    """Thêm nhiễu ±pct — dữ liệu không nhiễu trông giả ngay từ cái nhìn đầu tiên."""
    values = np.asarray(values, dtype=float)
    return values * r.uniform(1 - pct, 1 + pct, size=values.shape)


def mask_email(name_slug: str, domain: str = "gmail.com") -> str:
    dom = domain.split(".")[0]
    return f"{name_slug[:2]}***@{dom[:2]}***.{domain.split('.')[-1]}"


def mask_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", str(phone))
    return f"{digits[:2]}*****{digits[-3:]}" if len(digits) >= 8 else "0*****000"


_HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương"]
_DEM = ["Văn", "Thị", "Hữu", "Đức", "Minh", "Quang", "Thu", "Ngọc", "Gia", "Bảo", "Anh", "Khánh"]
_TEN = ["An", "Bình", "Chi", "Dũng", "Giang", "Hà", "Hải", "Hạnh", "Hùng", "Khoa", "Lan", "Linh",
        "Mai", "Nam", "Nga", "Phúc", "Quân", "Sơn", "Tâm", "Thảo", "Trang", "Tuấn", "Vy", "Yến"]


def vn_names(r: np.random.Generator, n: int):
    """Họ tên tiếng Việt GIẢ LẬP — ghép ngẫu nhiên, không lấy từ dữ liệu người thật."""
    return [f"{r.choice(_HO)} {r.choice(_DEM)} {r.choice(_TEN)}" for _ in range(n)]


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFD", str(text))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", text.lower().replace("đ", "d"))


def save_frames(frames: dict, out_dir: str):
    """Ghi mỗi bảng ra <out_dir>/<ten_bang>.csv — đầu vào của verify và pack."""
    os.makedirs(out_dir, exist_ok=True)
    for name, df in frames.items():
        df.to_csv(os.path.join(out_dir, f"{name}.csv"), index=False, encoding="utf-8-sig")
        print(f"  {name}: {len(df):,} dòng")


# =============================================================================
# CLI
# =============================================================================


def _run(argv=None):
    ap = argparse.ArgumentParser(prog="mockpack", description="Công cụ dựng bộ dữ liệu mockup")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("dict", help="sinh §2–§6 của DATASET_SPEC.md từ dataset.yaml")
    p.add_argument("spec"); p.add_argument("-o", "--out", default="DATASET_SPEC.md")

    p = sub.add_parser("verify", help="kiểm tra dữ liệu theo rule trong spec")
    p.add_argument("spec"); p.add_argument("source", help="thư mục CSV hoặc file .xlsx")
    p.add_argument("-o", "--out", default=None, help="ghi báo cáo markdown")

    p = sub.add_parser("pack", help="đóng gói Excel kèm sheet Data Dictionary")
    p.add_argument("spec"); p.add_argument("source", help="thư mục CSV")
    p.add_argument("-o", "--out", required=True)

    args = ap.parse_args(argv)
    spec = load_spec(args.spec)

    if args.cmd == "dict":
        write_dict(spec, args.out)
        return 0
    if args.cmd == "verify":
        # import cục bộ để tránh vòng lặp import: mockverify cũng `import mockpack`
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from mockverify import verify
        rep = verify(spec, args.source, args.out)
        return 1 if rep.failed else 0
    pack(spec, args.source, args.out)
    return 0


def main(argv=None):
    # bọc để CLI trả exit code khác 0 khi spec/dữ liệu hỏng, thay vì traceback dài dòng
    try:
        return _run(argv)
    except ValueError as exc:
        print(f"LỖI: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

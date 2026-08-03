"""Helpers đọc/ghi PBIR (Power BI Enhanced Report Format — .pbip *.Report/definition).

Luật cứng (đúc từ thực chiến — xem skill powerbi-report-design):
- CHỈ sửa khi file .pbip ĐÓNG trong Power BI Desktop (Ctrl+S phiên mở sẽ đè mất JSON).
- Ghi UTF-8 KHÔNG BOM.
- Clone-and-rebind: giữ nguyên `visualContainerObjects` (style), chỉ đổi name/position/
  queryState/visualType.
"""

import json
import os
import re
import secrets


def new_guid() -> str:
    """GUID kiểu PBIR: 20 ký tự hex thường (khớp format các visual/page có sẵn)."""
    return secrets.token_hex(10)


def read_json(path: str):
    with open(path, encoding="utf-8-sig") as f:  # utf-8-sig nuốt BOM nếu lỡ có
        return json.load(f)


def write_json_no_bom(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def resolve_definition_dir(report_path: str) -> str:
    """Nhận đường dẫn linh hoạt (file .pbip, folder *.Report, hoặc folder definition)
    → trả về folder definition. Raise ValueError nếu không tìm thấy cấu trúc PBIR."""
    p = report_path.rstrip("\\/")
    if p.lower().endswith(".pbip"):
        base = os.path.splitext(p)[0]
        p = base + ".Report"
    if os.path.basename(p).lower() == "definition":
        candidate = p
    else:
        candidate = os.path.join(p, "definition")
    if not os.path.isdir(os.path.join(candidate, "pages")):
        raise ValueError(
            f"Không thấy cấu trúc PBIR tại '{report_path}' (cần *.Report/definition/pages). "
            "File .pbix phải Save As .pbip (bật Preview 'Power BI Project (.pbip) save option' + PBIR) trước."
        )
    return candidate


def find_page(definition_dir: str, page: str) -> tuple[str, dict]:
    """Tìm trang theo GUID hoặc displayName. Trả (page_dir, page_json)."""
    pages_root = os.path.join(definition_dir, "pages")
    # thử GUID trực tiếp
    direct = os.path.join(pages_root, page, "page.json")
    if os.path.exists(direct):
        return os.path.join(pages_root, page), read_json(direct)
    # dò theo displayName
    for d in os.listdir(pages_root):
        pj = os.path.join(pages_root, d, "page.json")
        if os.path.exists(pj):
            data = read_json(pj)
            if data.get("displayName") == page:
                return os.path.join(pages_root, d), data
    raise ValueError(f"Không tìm thấy trang '{page}'. Trang phải là GUID folder hoặc displayName chính xác.")


def list_visuals(page_dir: str) -> list[tuple[str, dict]]:
    """Trả [(visual_id, visual_json)] của 1 trang."""
    vroot = os.path.join(page_dir, "visuals")
    out = []
    if not os.path.isdir(vroot):
        return out
    for d in sorted(os.listdir(vroot)):
        vj = os.path.join(vroot, d, "visual.json")
        if os.path.exists(vj):
            out.append((d, read_json(vj)))
    return out


def projection(kind: str, entity: str, prop: str, display_name: str | None = None,
               active: bool | None = None) -> dict:
    """Sinh 1 projection entry chuẩn PBIR. kind = 'Measure' | 'Column'."""
    if kind not in ("Measure", "Column"):
        raise ValueError(f"kind phải là 'Measure' hoặc 'Column', nhận '{kind}'")
    entry = {
        "field": {kind: {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
        "queryRef": f"{entity}.{prop}",
        "nativeQueryRef": prop,
    }
    if display_name:
        entry["displayName"] = display_name
    if active is not None:
        entry["active"] = active
    return entry


def rebind_query_state(visual_obj: dict, fields: dict) -> None:
    """Thay projections của các Role có trong `fields` (Role khác giữ nguyên).
    fields = {Role: [{"type": "Measure"|"Column", "entity": ..., "property": ...,
                      "displayName"?: ..., "active"?: bool}]}"""
    query = visual_obj.setdefault("visual", {}).setdefault("query", {})
    qs = query.setdefault("queryState", {})
    for role, items in fields.items():
        projections = []
        for it in items:
            projections.append(projection(
                it["type"], it["entity"], it["property"],
                it.get("displayName"), it.get("active"),
            ))
        qs[role] = {"projections": projections}
    # sortDefinition của block trỏ field CŨ → bỏ để Desktop dùng sort mặc định
    # (muốn sort tùy chỉnh: đặt lại trong Desktop sau khi nghiệm thu trang)
    query.pop("sortDefinition", None)


def set_title(visual_obj: dict, title: str) -> None:
    """Đặt/ghi đè title text, GIỮ style title có sẵn của block (font/màu/size không đụng)."""
    vco = visual_obj.setdefault("visual", {}).setdefault("visualContainerObjects", {})
    titles = vco.setdefault("title", [{}])
    props = titles[0].setdefault("properties", {})
    escaped = title.replace("'", "''")
    props["text"] = {"expr": {"Literal": {"Value": f"'{escaped}'"}}}


# Khóa mang NHÃN HIỂN THỊ do người dùng đặt — KHÁC với tên kỹ thuật ở Entity/Property.
# Đây chính là lỗ hổng đã làm lộ tên measure nghiệp vụ thật ra một kit công khai:
# sanitize v1/v2 chỉ gom Entity/Property nên "ARPU bình quân (đ)", "Tỷ lệ rời mạng %"…
# không bao giờ vào map, và đi thẳng vào repo public.
LABEL_KEYS = ("nativeQueryRef", "displayName", "metadata", "NativeQueryRef")


def collect_field_names(obj) -> tuple[set, set]:
    """Gom mọi giá trị của khóa 'Entity' và 'Property' trong cả cây JSON."""
    entities, properties = set(), set()

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "Entity" and isinstance(v, str):
                    entities.add(v)
                elif k == "Property" and isinstance(v, str):
                    properties.add(v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for it in node:
                walk(it)

    walk(obj)
    return entities, properties


def collect_display_labels(obj) -> set:
    """Gom nhãn hiển thị (nativeQueryRef/displayName/metadata) — tên nghiệp vụ do user đặt.

    `metadata` có dạng `Bảng.Measure`; chỉ phần sau dấu chấm cuối mới là nhãn.
    """
    labels = set()

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in LABEL_KEYS and isinstance(v, str) and v.strip():
                    labels.add(v.rsplit(".", 1)[-1] if k.lower() == "metadata" else v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for it in node:
                walk(it)

    walk(obj)
    return labels


def build_sanitize_map(entities: set, properties: set, labels: set | None = None) -> dict[str, str]:
    """Map tên thật → placeholder ổn định (sort để deterministic).

    `labels` = nhãn hiển thị (xem collect_display_labels). Bỏ qua nhãn đã là placeholder,
    và bỏ qua nhãn TRÙNG tên kỹ thuật (đã có trong map rồi) để không ghi đè lẫn nhau.
    """
    mapping = {}
    for e in sorted(entities):
        mapping[e] = "TEMPLATE_TABLE"
    for i, p in enumerate(sorted(properties), start=1):
        mapping[p] = f"TEMPLATE_FIELD_{i}"
    n = 1
    for lb in sorted(labels or ()):
        # CHỈ bỏ qua khi nhãn đã sạch HOÀN TOÀN. Dùng startswith() là bẫy: nhãn ghép kiểu
        # "TEMPLATE_FIELD_29 Hủy/Rời" cũng startswith("TEMPLATE_") nên phần đuôi nghiệp vụ
        # sẽ sống sót — đúng lỗi đã làm lọt tên thật ra kit công khai.
        if lb in mapping or is_placeholder_only(lb):
            continue
        mapping[lb] = f"TEMPLATE_LABEL_{n}"
        n += 1
    return mapping


# Chuỗi "đã sạch" = chỉ gồm token TEMPLATE_*, số, dấu nháy và ký tự phân cách vô hại.
_SAFE_ONLY = re.compile(r"^[\s'\"\.\-_/#()0-9]*(?:TEMPLATE_[A-Z0-9_]+[\s'\"\.\-_/#()0-9]*)*$")


def is_placeholder_only(s: str) -> bool:
    """True nếu chuỗi KHÔNG còn mẩu văn bản nghiệp vụ nào."""
    return bool(_SAFE_ONLY.match(s or ""))


def deep_sanitize(visual_obj: dict, mapping: dict[str, str]) -> None:
    """Thay tên bảng/cột thật bằng placeholder Ở MỌI NƠI trong visual JSON — không chỉ
    queryState mà cả objects/visualContainerObjects (conditional color, dataPoint selector,
    sortDefinition, queryRef string...). Style giữ nguyên; apply_template sẽ rebind lại.

    Thay chuỗi theo tên DÀI TRƯỚC để tránh tên ngắn ăn mất một phần tên dài."""
    import re as _re
    keys_desc = sorted(mapping.keys(), key=len, reverse=True)
    # Tên file resource (logo/ảnh đăng ký trong registeredResources) cũng là thông tin
    # nguồn — thay luôn (resource không resolve được cross-report nên không mất gì)
    _img_re = _re.compile(r"[\w\-. %]+\.(png|jpe?g|gif|svg|bmp|webp)", _re.IGNORECASE)

    def repl_str(s: str) -> str:
        for k in keys_desc:
            if k in s:
                s = s.replace(k, mapping[k])
        s = _img_re.sub("TEMPLATE_IMAGE.png", s)
        return s

    def walk(node):
        if isinstance(node, dict):
            for k in list(node.keys()):
                v = node[k]
                if isinstance(v, str):
                    node[k] = repl_str(v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for i, it in enumerate(node):
                if isinstance(it, str):
                    node[i] = repl_str(it)
                else:
                    walk(it)

    # filter mức visual chứa field + giá trị lọc thật → bỏ hẳn
    visual_obj.pop("filterConfig", None)
    walk(visual_obj)

    # Literal Value dạng chuỗi ('Phân Tích:', 'Tổng tập đoàn'…) là VĂN BẢN NGHIỆP VỤ user gõ
    # vào tiêu đề/nhãn/shape. Không suy ra được từ map tên bảng/cột nên phải xoá riêng.
    # Chỉ đụng chuỗi trong nháy đơn — số/bool ("0L", "true") giữ nguyên vì là tham số layout.
    def scrub_literals(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "Value" and isinstance(v, str):
                    s = v.strip()
                    # Chỉ giữ khi chuỗi đã SẠCH HOÀN TOÀN; còn mẩu chữ nghiệp vụ nào là xoá.
                    if len(s) >= 2 and s[0] == "'" and s[-1] == "'" and not is_placeholder_only(s):
                        node[k] = "'TEMPLATE_TEXT'"
                else:
                    scrub_literals(v)
        elif isinstance(node, list):
            for it in node:
                scrub_literals(it)

    scrub_literals(visual_obj)

    # textbox: nội dung chữ là văn bản nghiệp vụ → thay bằng placeholder
    v = visual_obj.get("visual", {})
    if v.get("visualType") == "textbox":
        gen = v.get("objects", {}).get("general", [])
        for item in gen:
            paras = item.get("properties", {}).get("paragraphs", [])
            for p in paras:
                for run in p.get("textRuns", []):
                    if "value" in run:
                        run["value"] = "TEMPLATE_TEXT"


def roles_of(visual_obj: dict) -> list[str]:
    return sorted(visual_obj.get("visual", {}).get("query", {}).get("queryState", {}).keys())


def fields_of(visual_obj: dict) -> dict:
    """Rút gọn binding hiện tại: {Role: [queryRef,...]} — phục vụ blueprint."""
    out = {}
    qs = visual_obj.get("visual", {}).get("query", {}).get("queryState", {})
    for role, role_obj in qs.items():
        out[role] = [p.get("queryRef", "?") for p in role_obj.get("projections", [])]
    return out

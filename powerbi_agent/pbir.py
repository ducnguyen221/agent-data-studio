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
# Đây chính là lỗ hổng từng làm lộ tên measure nghiệp vụ ra một kit công khai: sanitize đời đầu
# chỉ gom Entity/Property, nên nhãn kiểu "Doanh thu BQ (đ)" không bao giờ vào map thay thế.
# So khớp KHÔNG phân biệt hoa thường: PBIR xuất hiện cả `displayName` lẫn `DisplayName`.
LABEL_KEYS = {"nativequeryref", "displayname", "metadata", "queryref"}


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

    def take(key: str, val: str) -> None:
        if not val.strip():
            return
        # `metadata`/`queryRef` là "Bảng.Cột" hoặc sâu hơn: LẤY TỪNG ĐOẠN, không chỉ đoạn cuối.
        # Chỉ lấy đoạn cuối thì "KH.Phân khúc.Chi tiết" còn sót "Phân khúc".
        if key in ("metadata", "queryref"):
            labels.update(p for p in val.split(".") if p.strip())
        else:
            labels.add(val)

    def walk(node, parent_key=""):
        if isinstance(node, dict):
            for k, v in node.items():
                lk = k.lower()
                if lk in LABEL_KEYS and isinstance(v, str):
                    take(lk, v)
                else:
                    walk(v, lk)
        elif isinstance(node, list):
            for it in node:
                # Chuỗi nằm TRỰC TIẾP trong mảng: collector cũ bỏ qua trong khi deep_sanitize
                # lại có xử lý — lệch nhau nghĩa là sanitizer sẵn sàng thay thứ nó chưa hề gom.
                if isinstance(it, str) and parent_key in LABEL_KEYS:
                    take(parent_key, it)
                else:
                    walk(it, parent_key)

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
        # "TEMPLATE_FIELD_29 <đuôi nghiệp vụ>" cũng startswith("TEMPLATE_") nên phần đuôi đó
        # sẽ sống sót — đúng lỗi đã làm lọt tên thật ra kit công khai.
        if lb in mapping or is_placeholder_only(lb):
            continue
        mapping[lb] = f"TEMPLATE_LABEL_{n}"
        n += 1
    return mapping


# NGỮ PHÁP ĐÓNG: chỉ đúng những placeholder mà build_sanitize_map/deep_sanitize sinh ra.
# Trước đây cho `TEMPLATE_[A-Z0-9_]+` là quá rộng — một measure tên "TEMPLATE_DOANHTHU" hay
# chuỗi "TEMPLATE_FIELD_1_TY_LE" tự nhận là "đã sạch" rồi đi thẳng vào bản public.
_PLACEHOLDER = r"TEMPLATE_(?:TABLE|TEXT|IMAGE\.png|(?:FIELD|LABEL)_[0-9]+)"
_SEP = r"[\s'\"\.\-_/#()0-9]*"
# PHAI co it nhat MOT placeholder. Cho phep 0 placeholder nghia la chuoi toan so/dau
# ("0912345678", "01/02/2024", ma khach hang) tu nhan la da sach va di thang ra ban public.
_SAFE_ONLY = re.compile(rf"^{_SEP}{_PLACEHOLDER}(?:{_SEP}{_PLACEHOLDER})*{_SEP}$")


def is_placeholder_only(s: str) -> bool:
    """True nếu chuỗi KHÔNG còn mẩu văn bản nghiệp vụ nào.

    Chỉ chấp nhận đúng bộ placeholder repo tự sinh — không nhận mọi thứ bắt đầu bằng
    "TEMPLATE_", vì tên nghiệp vụ có thể cố tình hoặc vô tình mang tiền tố đó.
    Chuỗi rỗng/toàn khoảng trắng xử riêng: không có gì để lộ.
    """
    if not (s or "").strip():
        return True
    return bool(_SAFE_ONLY.match(s))


def deep_sanitize(visual_obj: dict, mapping: dict[str, str]) -> None:
    """Thay tên bảng/cột thật bằng placeholder Ở MỌI NƠI trong visual JSON — không chỉ
    queryState mà cả objects/visualContainerObjects (conditional color, dataPoint selector,
    sortDefinition, queryRef string...). Style giữ nguyên; apply_template sẽ rebind lại.

    Thay MỘT LƯỢT bằng regex alternation (tên dài trước), KHÔNG lặp str.replace nhiều vòng:
    replace tuần tự thì placeholder do vòng trước chèn vào lại thành đầu vào của vòng sau, nên
    một bảng tên "T" hay cột tên "FIELD" sẽ ăn vào chính chữ TEMPLATE_TABLE/TEMPLATE_FIELD_n
    và sinh ra chuỗi rác kiểu "TEMPLATE_TABLEEMPLATEMPLATE_TABLEE_..." — hỏng kit chứ không
    phải sanitize. Một lượt thì mỗi ký tự chỉ bị tiêu thụ đúng một lần."""
    import re as _re
    _sub = None
    if mapping:
        keys_desc = sorted(mapping.keys(), key=len, reverse=True)
        _pat = _re.compile("|".join(_re.escape(k) for k in keys_desc))
        _sub = lambda s: _pat.sub(lambda m: mapping[m.group(0)], s)  # noqa: E731

    # Tên file resource (logo/ảnh khách hàng) là thông tin nguồn → thay TRỌN chuỗi.
    # Regex cũ chỉ khớp `[\w\-. %]+` nên tên có dấu ngoặc/&/+ chỉ bị cắt phần đuôi, để lại
    # phần đọc được: "revenue_(1)23578.png" -> "revenue_(1)TEMPLATE_IMAGE.png". Nay chuỗi nào
    # KẾT THÚC bằng đuôi ảnh thì thay nguyên chuỗi.
    # Cho phép chuỗi bọc nháy đơn: PBIR lưu tên ảnh cả ở `ItemName` (trần) lẫn trong
    # `Literal.Value` (dạng `'revenue (1).png'`). Không xử nháy thì bản trong Literal lọt.
    _img_re = _re.compile(r"^'?.*\.(png|jpe?g|gif|svg|bmp|webp)'?$", _re.IGNORECASE)

    def repl_str(s: str) -> str:
        if _img_re.match(s):
            return "'TEMPLATE_IMAGE.png'" if s.startswith("'") else "TEMPLATE_IMAGE.png"
        return _sub(s) if _sub else s

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

    # Literal Value dạng chuỗi user GÕ VÀO (tiêu đề, nhãn, chữ trên shape) là văn bản nghiệp vụ.
    # Phân loại theo VỊ TRÍ trong cây, KHÔNG theo ký tự.
    #
    # Bản trước lọc theo bộ ký tự cho phép (không chữ cái) nên nó xoá luôn `'#2B395B'`,
    # `'rectangle'`, `'Dropdown'`, `'Calibri'`… — tức là xoá sạch bảng màu và enum bố cục,
    # phá đúng cái mà kit sinh ra để giữ. Chỉ những Literal nằm trong Ô CHỮ mới là văn bản
    # người dùng; màu/enum/font nằm ở ô khác và phải giữ nguyên 100%.
    # Quyết định dựa trên TÊN PROPERTY chứa literal (khoá ngay dưới `properties`), vì PBIR
    # luôn có dạng  objects.<tênObject>[i].properties.<tênProp>.expr.Literal.Value.
    # So khớp theo CHỨA chữ, không khớp chính xác: thực tế là `titleText`, `referenceLabelTitle`,
    # `labelText`… nên khớp chính xác "title"/"text" sẽ trượt hết.
    # Trừ ra các property STYLE: `labelColor`, `titleFontSize`… cũng chứa "label"/"title"
    # nhưng giá trị là màu/size — xoá là mất style, đúng lỗi đã phá cả bảng màu của kit.
    TEXTISH = ("text", "title", "label", "caption", "paragraph", "tooltip")
    STYLISH = ("color", "colour", "size", "font", "weight", "align", "position",
               "style", "transparency", "bold", "italic", "underline", "display",
               "show", "visible", "shape", "width", "height", "padding", "margin")

    def is_user_text_prop(name: str) -> bool:
        n = name.lower()
        return any(t in n for t in TEXTISH) and not any(s in n for s in STYLISH)

    def scrub_literals(node, prop_name=""):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "Value" and isinstance(v, str) and is_user_text_prop(prop_name):
                    s = v.strip()
                    # PBIR ghi literal chuỗi bằng CẢ nháy đơn lẫn nháy kép — chỉ xử nháy đơn
                    # thì bản nháy kép đi thẳng ra ngoài.
                    q = s[0] if len(s) >= 2 and s[0] in "'\"" and s[-1] == s[0] else ""
                    if q and not is_placeholder_only(s):
                        node[k] = f"{q}TEMPLATE_TEXT{q}"
                else:
                    # `properties` mở ra một tầng tên property mới; các tầng khác giữ nguyên tên.
                    scrub_literals(v, k if prop_name == "__props__" else
                                   ("__props__" if k == "properties" else prop_name))
        elif isinstance(node, list):
            for it in node:
                scrub_literals(it, prop_name)

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

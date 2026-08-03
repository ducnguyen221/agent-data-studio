"""Template kit: distill trang mẫu → kit tái dùng, và apply kit → trang mới (clone-and-rebind).

Nguyên tắc lõi (đúc từ thất bại thật): layout agent tự dựng từ đầu LUÔN xấu;
clone block verbatim từ trang đã chứng minh + chỉ đổi binding thì đẹp.
=> apply_template chuyển luật đó thành CODE: giữ nguyên visualContainerObjects,
chỉ đổi name / position / queryState / visualType (+ title text nếu yêu cầu).
"""

import json
import os
from datetime import date

from powerbi_agent import pbir
from powerbi_agent.util import log, short_err

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _template_dirs() -> list[str]:
    dirs = [os.path.join(_REPO_ROOT, "report-templates")]
    env = os.getenv("POWERBI_TEMPLATES_DIR")
    if env:
        dirs.append(env)
    return [d for d in dirs if os.path.isdir(d)]


def _load_kits() -> list[tuple[str, dict]]:
    kits = []
    for root in _template_dirs():
        for name in sorted(os.listdir(root)):
            kj = os.path.join(root, name, "kit.json")
            if os.path.exists(kj):
                try:
                    kits.append((os.path.join(root, name), pbir.read_json(kj)))
                except Exception as e:
                    log.warning("kit.json hỏng ở %s: %s", kj, e)
    return kits


def register(mcp):
    """Đăng ký các tool template vào instance FastMCP."""

    @mcp.tool()
    def list_templates() -> str:
        """Liệt kê các template kit báo cáo có sẵn (repo report-templates/ + env POWERBI_TEMPLATES_DIR).
        Mỗi kit gồm: blocks (visual.json verbatim theo loại), blueprint, page settings, design tokens."""
        kits = _load_kits()
        if not kits:
            return "Chưa có template kit nào. Tạo bằng distill_template từ một trang báo cáo mẫu."
        out = ["# Template kits\n"]
        for kit_dir, kit in kits:
            out.append(f"## `{kit.get('name', os.path.basename(kit_dir))}`")
            out.append(f"- Đường dẫn: `{kit_dir}`")
            canvas = kit.get("canvas", {})
            out.append(f"- Canvas: {canvas.get('width', '?')}×{canvas.get('height', '?')}")
            if kit.get("source"):
                out.append(f"- Nguồn: {kit['source'].get('report', '?')} / trang '{kit['source'].get('page', '?')}'")
            blocks = kit.get("blocks", [])
            out.append(f"- Blocks ({len(blocks)}): " + ", ".join(f"`{b['visualType']}`" for b in blocks))
            out.append("")
        out.append("Dùng apply_template để dựng trang mới từ kit (clone-and-rebind).")
        return "\n".join(out)

    @mcp.tool()
    def distill_template(report_path: str, page: str, out_dir: str, kit_name: str = None,
                         sanitize: bool = True) -> str:
        """
        Chưng cất 1 trang báo cáo PBIR thành template kit tái dùng (blueprint.md + blocks/*.json
        verbatim mỗi loại visual + _page.json + kit.json).
        - report_path: file .pbip, folder *.Report, hoặc folder definition.
        - page: GUID trang hoặc displayName chính xác.
        - out_dir: thư mục ghi kit — mặc định nên là `templates/` trong THƯ MỤC DỰ ÁN (ngoài repo).
        - sanitize: **MẶC ĐỊNH True** — thay tên bảng/cột/nhãn thật bằng placeholder TEMPLATE_*.
          Đặt False chỉ khi user nói RÕ kit này dùng nội bộ và chấp nhận giữ tên nghiệp vụ thật.
          Mặc định phải an toàn: kit từng lọt tên measure thật của khách ra bản public vì
          an toàn phụ thuộc vào việc người gọi nhớ bật cờ.
        CHỈ ĐỌC — không sửa báo cáo nguồn.
        """
        try:
            definition = pbir.resolve_definition_dir(report_path)
            page_dir, page_json = pbir.find_page(definition, page)
            visuals = pbir.list_visuals(page_dir)
            if not visuals:
                return f"Trang '{page}' không có visual nào."

            # Kit CHUA sanitize la du lieu khach -> chan ghi vao repo.
            # report-templates/ duoc mien vi do la noi kit DA sanitize duoc phep nam.
            from powerbi_agent.knowledge import ensure_outside_repo
            out_dir = ensure_outside_repo(out_dir, "template kit")
            os.makedirs(out_dir, exist_ok=True)
            blocks_dir = os.path.join(out_dir, "blocks")

            # Khi sanitize: gom TÊN THẬT (Entity/Property) trên TOÀN trang trước → 1 map
            # nhất quán cho cả blocks lẫn blueprint
            san_map = {}
            if sanitize:
                all_e, all_p, all_lb = set(), set(), set()
                for _, vobj in visuals:
                    e, p = pbir.collect_field_names(vobj)
                    all_e |= e
                    all_p |= p
                    # Nhãn hiển thị (nativeQueryRef/displayName/metadata) là tên nghiệp vụ
                    # user tự đặt — KHÔNG suy ra được từ Entity/Property. Thiếu bước này
                    # từng làm lọt tên measure thật của khách hàng vào kit công khai.
                    all_lb |= pbir.collect_display_labels(vobj)
                san_map = pbir.build_sanitize_map(all_e, all_p, all_lb)

            # 1 exemplar / visualType — chọn file GIÀU style nhất (JSON dài nhất)
            exemplars: dict[str, tuple[str, dict, int]] = {}
            blueprint_rows = []
            for vid, vobj in visuals:
                vtype = vobj.get("visual", {}).get("visualType")
                pos = vobj.get("position", {})
                bp_obj = vobj
                if sanitize:
                    bp_obj = json.loads(json.dumps(vobj))
                    pbir.deep_sanitize(bp_obj, san_map)
                fields = pbir.fields_of(bp_obj)
                fields_str = "; ".join(f"{r}: {', '.join(v)}" for r, v in fields.items()) or "—"
                blueprint_rows.append(
                    f"| `{vid}` | {vtype or '*(group/container)*'} "
                    f"| {round(pos.get('x', 0))},{round(pos.get('y', 0))} z{pos.get('z', 0)} "
                    f"| {round(pos.get('width', 0))}×{round(pos.get('height', 0))} | {fields_str} |"
                )
                if not vtype:
                    continue  # visualGroup — không làm block
                size = len(json.dumps(vobj))
                if vtype not in exemplars or size > exemplars[vtype][2]:
                    exemplars[vtype] = (vid, vobj, size)

            block_meta = []
            for vtype, (vid, vobj, size) in sorted(exemplars.items()):
                block = json.loads(json.dumps(vobj))  # deep copy
                if sanitize:
                    pbir.deep_sanitize(block, san_map)
                pbir.write_json_no_bom(os.path.join(blocks_dir, f"{vtype}.json"), block)
                block_meta.append({
                    "file": f"blocks/{vtype}.json",
                    "visualType": vtype,
                    "roles": pbir.roles_of(vobj),
                    "source_visual": vid,
                })

            # _page.json: page settings + nền, BỎ filter/interaction đặc thù trang nguồn.
            # page_json CŨNG là dữ liệu khách (`displayName` là tên trang user đặt, nền có thể
            # tham chiếu ảnh của họ) — trước đây ghi thẳng, không qua sanitize.
            page_tpl = {k: v for k, v in page_json.items()
                        if k not in ("filterConfig", "visualInteractions", "name")}
            if sanitize:
                page_tpl = json.loads(json.dumps(page_tpl))
                pbir.deep_sanitize(page_tpl, san_map)
                page_tpl.pop("displayName", None)   # tên trang không suy ra được từ map
            pbir.write_json_no_bom(os.path.join(out_dir, "_page.json"), page_tpl)

            # blueprint.md
            src_name = page_json.get("displayName", page)
            bp_src = "(sanitized)" if sanitize else f"`{os.path.basename(os.path.dirname(definition))}`"
            bp_title = "(trang mẫu đã sanitize)" if sanitize else f"trang mẫu '{src_name}'"
            bp = [
                f"# Blueprint — {bp_title}",
                "",
                f"> Distill {date.today().isoformat()} từ {bp_src}. "
                f"{len(visuals)} visual, {len(exemplars)} loại block."
                + (" **Đã sanitize** — binding = placeholder TEMPLATE_*." if sanitize else
                   " Binding GỐC giữ nguyên làm tham chiếu."),
                "",
                "| Visual ID | Loại | Vị trí (x,y z) | Kích thước | Binding (Role: fields) |",
                "|---|---|---|---|---|",
                *blueprint_rows,
                "",
                "## Cách dùng",
                "Dùng tool `apply_template` với kit này: mỗi visual trong page_spec chọn 1 `block`,",
                "đặt vị trí theo bảng trên (hoặc layout mới), bind field thật của model đích.",
                "KHÔNG sửa tay `visualContainerObjects` trong blocks — đó là style làm trang đẹp.",
            ]
            with open(os.path.join(out_dir, "blueprint.md"), "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(bp) + "\n")

            # kit.json
            # kit_name do NGƯỜI GỌI đặt — có thể là "Telco Churn" hay tên khách. Khi sanitize
            # thì tên kit cũng phải sạch, nếu không thì cả kit ẩn danh mà nhãn lại chỉ đích danh.
            safe_name = kit_name or os.path.basename(out_dir.rstrip("\\/"))
            if sanitize and not pbir.is_placeholder_only(safe_name):
                import re as _re
                cleaned = _re.sub(r"[^A-Za-z0-9\-_]+", "-", safe_name).strip("-").lower()
                if _re.search(r"[^\x00-\x7F]", safe_name):
                    cleaned = "kit"          # có dấu ⇒ gần như chắc là tên nghiệp vụ
                safe_name = cleaned or "kit"
            kit = {
                "name": safe_name,
                "schema": "powerbi-agent/kit/v1",
                "created": date.today().isoformat(),
                "sanitized": sanitize,
                "source": {
                    "report": "(sanitized)" if sanitize else os.path.basename(os.path.dirname(definition)),
                    "page": "(sanitized)" if sanitize else src_name,
                },
                "canvas": {
                    "width": page_json.get("width", 1280),
                    "height": page_json.get("height", 720),
                    "displayOption": page_json.get("displayOption", "FitToPage"),
                },
                "blocks": block_meta,
            }
            pbir.write_json_no_bom(os.path.join(out_dir, "kit.json"), kit)

            return (
                f"Đã distill trang '{src_name}' thành kit tại `{out_dir}`:\n"
                f"- {len(block_meta)} block: " + ", ".join(b["visualType"] for b in block_meta) + "\n"
                f"- blueprint.md ({len(visuals)} visual) + _page.json + kit.json\n"
                + ("- ĐÃ sanitize (an toàn để chia sẻ/public)\n" if sanitize else
                   "- CHƯA sanitize — binding nghiệp vụ thật còn trong blocks, đừng public kit này\n")
            )
        except Exception as e:
            log.exception("distill_template thất bại")
            return f"Lỗi distill_template: {short_err(e)}"

    @mcp.tool()
    def apply_template(report_path: str, kit_dir: str, page_spec: str) -> str:
        """
        Dựng TRANG MỚI vào báo cáo PBIR từ template kit (clone-and-rebind — không dựng layout từ đầu).
        ⚠️ File .pbip phải ĐANG ĐÓNG trong Power BI Desktop (mở + Ctrl+S sẽ đè mất trang mới).
        - report_path: file .pbip, folder *.Report, hoặc folder definition (SẼ GHI vào đây).
        - kit_dir: thư mục kit (tạo bởi distill_template, hoặc report-templates/ có sẵn — xem list_templates).
        - page_spec: JSON string:
          {"displayName": "Tên trang", "visuals": [
              {"block": "cardVisual", "x": 30, "y": 100, "z": 1000, "width": 280, "height": 110,
               "visualType": "(tùy chọn — đổi loại chart, phải chỉnh roles khớp)",
               "title": "(tùy chọn — ghi đè text title, giữ style)",
               "fields": {"Data": [{"type": "Measure", "entity": "Công thức", "property": "Tổng TB"}]}}
          ]}
          Role theo loại: card/slicer=Values · cardVisual=Data · line/area/combo=Category/Y/Series ·
          pivotTable=Rows/Columns/Values. Field type: Measure | Column.
        Trả về: đường trang mới + việc cần làm tay (mở lại Power BI để nghiệm thu).
        """
        try:
            definition = pbir.resolve_definition_dir(report_path)
            kit_json_path = os.path.join(kit_dir, "kit.json")
            if not os.path.exists(kit_json_path):
                return f"Không thấy kit.json trong '{kit_dir}'. Dùng list_templates xem kit có sẵn."
            spec = json.loads(page_spec) if isinstance(page_spec, str) else page_spec
            if not spec.get("visuals"):
                return "page_spec phải có ít nhất 1 visual."

            # page mới từ _page.json của kit
            page_guid = pbir.new_guid()
            page_tpl_path = os.path.join(kit_dir, "_page.json")
            page_json = pbir.read_json(page_tpl_path) if os.path.exists(page_tpl_path) else {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
                "displayOption": "FitToPage", "height": 720, "width": 1280,
            }
            page_json["name"] = page_guid
            page_json["displayName"] = spec.get("displayName", "Trang mới")
            page_dir = os.path.join(definition, "pages", page_guid)
            pbir.write_json_no_bom(os.path.join(page_dir, "page.json"), page_json)

            created = []
            for i, vs in enumerate(spec["visuals"], start=1):
                block_file = os.path.join(kit_dir, "blocks", f"{vs['block']}.json")
                if not os.path.exists(block_file):
                    return f"Visual #{i}: block '{vs['block']}' không có trong kit (xem kit.json)."
                vobj = pbir.read_json(block_file)

                vid = pbir.new_guid()
                vobj["name"] = vid
                pos = vobj.setdefault("position", {})
                for k in ("x", "y", "z", "width", "height"):
                    if k in vs:
                        pos[k] = vs[k]
                vobj.pop("parentGroupName", None)  # block có thể từng nằm trong group nguồn

                if vs.get("visualType"):
                    vobj.setdefault("visual", {})["visualType"] = vs["visualType"]
                if vs.get("fields"):
                    pbir.rebind_query_state(vobj, vs["fields"])
                    # expansionStates (slicer) trỏ queryRef cũ — bỏ để Desktop tự dựng lại
                    vobj.get("visual", {}).pop("expansionStates", None)
                if vs.get("title"):
                    pbir.set_title(vobj, vs["title"])

                pbir.write_json_no_bom(os.path.join(page_dir, "visuals", vid, "visual.json"), vobj)
                created.append(f"{vs['block']}→`{vid}`")

            # đăng ký pages.json
            pages_meta_path = os.path.join(definition, "pages", "pages.json")
            pages_meta = pbir.read_json(pages_meta_path)
            if page_guid not in pages_meta.get("pageOrder", []):
                pages_meta.setdefault("pageOrder", []).append(page_guid)
            pbir.write_json_no_bom(pages_meta_path, pages_meta)

            return (
                f"Đã tạo trang '{page_json['displayName']}' (GUID `{page_guid}`) với {len(created)} visual:\n"
                + "\n".join(f"- {c}" for c in created) + "\n\n"
                "Việc tiếp theo (người dùng): mở lại file .pbip trong Power BI Desktop để nghiệm thu. "
                "Nếu file đang mở sẵn: Đóng KHÔNG LƯU rồi mở lại — Ctrl+S phiên cũ sẽ đè mất trang này."
            )
        except Exception as e:
            log.exception("apply_template thất bại")
            return f"Lỗi apply_template: {short_err(e)}"

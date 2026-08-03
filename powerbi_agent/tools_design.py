"""Quét TRỌN BỘ thiết kế 1 báo cáo Power BI (PBIR) → bộ hồ sơ thiết kế tái dùng (M5.1).

Đầu ra (mặc định vào Knowledge Dir `projects/<slug>/design/` — NGOÀI repo, riêng tư):
- REPORT_CATALOG.md — Report → Page → Visual (loại, vị trí, binding) toàn bộ các trang.
- DESIGN.md        — theme, palette, canvas, nền trang, kiểm kê visual, resource ảnh.
- theme/*.json     — file theme (custom + base) copy nguyên — import lại Desktop được.

Khác với distill_template (1 trang → kit APPLY được): tool này là HỒ SƠ THAM CHIẾU toàn dự án.
Muốn kit apply được cho trang đẹp cụ thể → dùng distill_template riêng cho trang đó.
"""

import os
import shutil
from datetime import date

from powerbi_agent import knowledge as kn
from powerbi_agent import pbir
from powerbi_agent.util import log, short_err


def _theme_summary(theme_path: str) -> dict:
    try:
        t = pbir.read_json(theme_path)
        return {
            "name": t.get("name", os.path.basename(theme_path)),
            "dataColors": t.get("dataColors", [])[:12],
            "background": t.get("background"),
            "foreground": t.get("foreground"),
            "tableAccent": t.get("tableAccent"),
        }
    except Exception:
        return {"name": os.path.basename(theme_path), "dataColors": []}


def register(mcp):
    """Đăng ký tool design-scan vào instance FastMCP."""

    @mcp.tool()
    def distill_report_design(report_path: str, project: str = None, out_dir: str = None) -> str:
        """
        Quét TOÀN BỘ báo cáo PBIR (mọi trang + theme + report settings) thành bộ hồ sơ thiết kế:
        REPORT_CATALOG.md (Report→Page→Visual) + DESIGN.md (theme/palette/canvas/nền/kiểm kê)
        + theme/*.json (import lại được). CHỈ ĐỌC báo cáo nguồn.
        - report_path: file .pbip, folder *.Report, hoặc folder definition.
        - project: tên dự án trong Knowledge Dir → ghi vào projects/<slug>/design/ (mặc định).
        - out_dir: ghi đè đích ra folder tùy ý (bỏ qua Knowledge Dir).
        Kết hợp distill_model_schema (model) = trọn bộ hồ sơ 1 project.
        LƯU Ý: hồ sơ chứa binding nghiệp vụ thật — mặc định lưu Knowledge Dir riêng tư, KHÔNG commit repo.
        """
        try:
            definition = pbir.resolve_definition_dir(report_path)
            report_root = os.path.dirname(definition)
            report_name = os.path.basename(report_root).replace(".Report", "")

            # đích ghi
            if not out_dir:
                root = kn.resolve_root()
                if not root:
                    return "CHƯA SETUP Knowledge Dir. " + kn.NOT_SETUP_MSG + " (Hoặc truyền out_dir tường minh.)"
                slug = kn.slugify(project or report_name)
                os.makedirs(os.path.join(root, "projects", slug), exist_ok=True)
                out_dir = os.path.join(root, "projects", slug, "design")
            out_dir = kn.ensure_outside_repo(out_dir, "hồ sơ thiết kế báo cáo")
            os.makedirs(out_dir, exist_ok=True)

            # ---- report.json + theme ----
            report_json = pbir.read_json(os.path.join(definition, "report.json"))
            tc = report_json.get("themeCollection", {})
            theme_dir = os.path.join(out_dir, "theme")
            os.makedirs(theme_dir, exist_ok=True)
            themes = []
            static = os.path.join(report_root, "StaticResources")
            for kind, sub in (("customTheme", "RegisteredResources"),
                              ("baseTheme", os.path.join("SharedResources", "BaseThemes"))):
                info = tc.get(kind)
                if not info:
                    continue
                name = info["name"]
                src = os.path.join(static, sub, name if name.endswith(".json") else name + ".json")
                if os.path.exists(src):
                    dst = os.path.join(theme_dir, os.path.basename(src))
                    shutil.copy2(src, dst)
                    themes.append((kind, _theme_summary(src)))

            # resource ảnh đăng ký (logo/icon)
            rr = os.path.join(static, "RegisteredResources")
            images = sorted(f for f in os.listdir(rr)
                            if f.lower().endswith((".png", ".jpg", ".jpeg", ".svg", ".gif"))) if os.path.isdir(rr) else []

            # ---- quét mọi trang ----
            pages_meta = pbir.read_json(os.path.join(definition, "pages", "pages.json"))
            catalog = [f"# REPORT CATALOG — {report_name}", "",
                       f"> Quét {date.today().isoformat()} · {len(pages_meta.get('pageOrder', []))} trang. "
                       f"Binding là THẬT (riêng tư — không commit repo public).", ""]
            inventory: dict[str, int] = {}
            page_summaries = []
            for pid in pages_meta.get("pageOrder", []):
                page_dir = os.path.join(definition, "pages", pid)
                pj = pbir.read_json(os.path.join(page_dir, "page.json"))
                visuals = pbir.list_visuals(page_dir)
                bg = ""
                try:
                    bg = pj["objects"]["background"][0]["properties"]["color"]["solid"]["color"]["expr"]["Literal"]["Value"].strip("'")
                except Exception:
                    pass
                page_summaries.append((pj.get("displayName", pid), pj.get("width"), pj.get("height"), bg, len(visuals)))
                catalog += [f"## {pj.get('displayName', pid)}",
                            f"`{pid}` · {pj.get('width')}×{pj.get('height')} · nền `{bg or 'theme'}` · {len(visuals)} visual", "",
                            "| Visual | Loại | Vị trí (x,y z) | Kích thước | Binding |", "|---|---|---|---|---|"]
                for vid, vobj in visuals:
                    vtype = vobj.get("visual", {}).get("visualType") or "(group)"
                    inventory[vtype] = inventory.get(vtype, 0) + 1
                    pos = vobj.get("position", {})
                    fields = pbir.fields_of(vobj)
                    fstr = "; ".join(f"{r}: {', '.join(v[:4])}" for r, v in fields.items()) or "—"
                    catalog.append(
                        f"| `{vid}` | {vtype} | {round(pos.get('x', 0))},{round(pos.get('y', 0))} z{pos.get('z', 0)} "
                        f"| {round(pos.get('width', 0))}×{round(pos.get('height', 0))} | {fstr} |")
                catalog.append("")
            with open(os.path.join(out_dir, "REPORT_CATALOG.md"), "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(catalog) + "\n")

            # ---- DESIGN.md ----
            design = [f"# DESIGN — {report_name}", "",
                      f"> Hồ sơ thiết kế quét {date.today().isoformat()}. Theme import lại được ở `theme/`.", "",
                      "## Theme"]
            for kind, ts in themes:
                design.append(f"### {kind}: `{ts['name']}`")
                if ts.get("dataColors"):
                    design.append("- Palette: " + " ".join(f"`{c}`" for c in ts["dataColors"]))
                for k in ("background", "foreground", "tableAccent"):
                    if ts.get(k):
                        design.append(f"- {k}: `{ts[k]}`")
                design.append("")
            design += ["## Trang", "", "| Trang | Canvas | Nền | Visual |", "|---|---|---|---|"]
            for name, w, h, bg, n in page_summaries:
                design.append(f"| {name} | {w}×{h} | `{bg or 'theme'}` | {n} |")
            design += ["", "## Kiểm kê visual toàn báo cáo", ""]
            for vtype, n in sorted(inventory.items(), key=lambda x: -x[1]):
                design.append(f"- `{vtype}`: {n}")
            if images:
                design += ["", "## Resource ảnh (RegisteredResources)", ""]
                design += [f"- `{i}`" for i in images]
            design += ["", "## Tái tạo",
                       "- Trang đẹp muốn APPLY lại → `distill_template` trang đó thành kit.",
                       "- Model → `distill_model_schema`. Theme → import `theme/*.json` trong Desktop.",
                       ]
            with open(os.path.join(out_dir, "DESIGN.md"), "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(design) + "\n")

            # timeline nếu có knowledge
            root = kn.resolve_root()
            if root and out_dir.startswith(root):
                rel = os.path.relpath(out_dir, root).replace("\\", "/")
                kn.append_timeline(root, project or report_name, "Quét thiết kế báo cáo",
                                   f"{len(page_summaries)} trang, {sum(inventory.values())} visual", rel)

            total_v = sum(inventory.values())
            return (
                f"Đã quét '{report_name}': {len(page_summaries)} trang / {total_v} visual / "
                f"{len(themes)} theme / {len(images)} ảnh resource.\n"
                f"Hồ sơ tại `{out_dir}`: REPORT_CATALOG.md · DESIGN.md · theme/\n"
                "Gợi ý tiếp: distill_model_schema (model) + distill_template cho trang muốn tái tạo."
            )
        except Exception as e:
            log.exception("distill_report_design thất bại")
            return f"Lỗi distill_report_design: {short_err(e)}"

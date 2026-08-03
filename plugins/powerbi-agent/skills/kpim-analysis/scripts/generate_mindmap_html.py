"""Sinh bản XEM HTML cho các mindmap trong bộ tài liệu KPIM.

NGUỒN DUY NHẤT là khối ```mermaid mindmap nằm ngay trong file .md tương ứng.
Script này chỉ dựng thêm một lớp hiển thị — không có nội dung riêng, nên hai bản
không bao giờ lệch nhau. Sửa mindmap = sửa file .md rồi chạy lại script.

Vì sao không dùng ảnh PNG như trước:
  - PNG cần graphviz + font tiếng Việt cài sẵn; máy thiếu là sinh ra ảnh hỏng hoặc mất dấu.
  - PNG không sửa được bằng tay, không diff được trong git, không tìm kiếm được.
  - Nội dung nghiệp vụ nằm trong ảnh thì không công cụ nào rà rò rỉ được (đã có tiền lệ).

Vì sao HTML tự chứa, không nhúng thư viện mermaid:
  - Chạy offline, mở bằng double-click, không cần mạng, không dính CSP.
  - File chỉ vài KB thay vì kéo theo cả bundle JS.

Chạy:
    python generate_mindmap_html.py            # sinh cho mọi file .md cạnh script
    python generate_mindmap_html.py PROJECT.md # chỉ 1 file
"""

from __future__ import annotations

import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.normpath(os.path.join(HERE, "..", "document-templates"))
OUT = os.path.join(DOCS, "mindmaps")

BLOCK = re.compile(r"```mermaid\s*\n(mindmap\s*\n.*?)```", re.DOTALL)
ROOT = re.compile(r"^\s*root\(\((?P<t>.+?)\)\)\s*$")


def parse_mindmap(src: str) -> tuple[str, list]:
    """mermaid mindmap (thụt lề = cấp) -> (tiêu đề gốc, cây lồng nhau).

    Trả về cây dạng [(text, [con...]), ...].
    """
    lines = [ln for ln in src.splitlines()[1:] if ln.strip()]
    title, rows = "MINDMAP", []
    for ln in lines:
        m = ROOT.match(ln)
        if m and not rows:
            title = m.group("t").strip()
            continue
        rows.append((len(ln) - len(ln.lstrip()), ln.strip()))
    if not rows:
        return title, []

    base = min(indent for indent, _ in rows)
    root: list = []
    # stack[i] = danh sách con đang mở ở độ sâu i
    stack = {base - 2: root}
    for indent, text in rows:
        node = (text, [])
        parent_key = max((k for k in stack if k < indent), default=base - 2)
        stack[parent_key].append(node)
        stack[indent] = node[1]
        for k in [k for k in stack if k > indent]:
            del stack[k]
    return title, root


def render_ul(nodes: list, depth: int = 0) -> str:
    if not nodes:
        return ""
    items = "".join(
        f'<li><span class="n l{min(depth, 3)}">{html.escape(t)}</span>{render_ul(kids, depth + 1)}</li>'
        for t, kids in nodes
    )
    return f"<ul>{items}</ul>"


PAGE = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — mindmap</title>
<style>
  :root{{--bg:#fbfcfe;--ink:#16202c;--muted:#5b6b7f;--line:#d6dee8;--accent:#1f6feb;--card:#fff}}
  @media (prefers-color-scheme:dark){{
    :root{{--bg:#0f151c;--ink:#e6edf5;--muted:#93a3b6;--line:#26303c;--accent:#5296ff;--card:#151d26}}
  }}
  *{{box-sizing:border-box}}
  body{{margin:0;padding:32px 20px;background:var(--bg);color:var(--ink);
    font:15px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif}}
  .wrap{{max-width:1100px;margin:0 auto}}
  h1{{font-size:20px;margin:0 0 4px}}
  .sub{{color:var(--muted);font-size:13px;margin-bottom:26px}}
  .sub code{{background:var(--card);border:1px solid var(--line);border-radius:5px;padding:1px 6px}}
  .root{{display:inline-block;background:var(--accent);color:#fff;font-weight:700;
    padding:9px 20px;border-radius:999px;margin-bottom:18px}}
  ul{{list-style:none;margin:0;padding-left:26px}}
  li{{position:relative;padding:3px 0 3px 18px}}
  li::before{{content:"";position:absolute;left:0;top:0;bottom:0;border-left:1px solid var(--line)}}
  li:last-child::before{{bottom:calc(100% - 17px)}}
  li::after{{content:"";position:absolute;left:0;top:16px;width:13px;border-top:1px solid var(--line)}}
  .n{{display:inline-block;background:var(--card);border:1px solid var(--line);
    border-radius:8px;padding:4px 12px}}
  .l0{{font-weight:700;border-color:var(--accent)}}
  .l1{{font-weight:600}}
  .l2,.l3{{color:var(--muted);font-size:14px}}
  @media print{{body{{background:#fff}}}}
</style>
<div class="wrap">
  <h1>{title}</h1>
  <p class="sub">Bản xem của khối <code>mermaid mindmap</code> trong <code>{src}</code>.
     Sửa nội dung ở file đó rồi chạy lại <code>generate_mindmap_html.py</code> — đừng sửa file HTML này.</p>
  <div class="root">{title}</div>
  {tree}
</div>
"""


def build(md_name: str) -> list[str]:
    path = os.path.join(DOCS, md_name)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    made = []
    for block in BLOCK.findall(text):
        title, tree = parse_mindmap(block)
        if not tree:
            continue
        slug = "key_" + re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_").replace("key_", "", 1)
        os.makedirs(OUT, exist_ok=True)
        out = os.path.join(OUT, f"{slug}.html")
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(PAGE.format(title=html.escape(title), src=html.escape(md_name), tree=render_ul(tree)))
        made.append(os.path.relpath(out, DOCS).replace(os.sep, "/"))
    return made


def main() -> int:
    names = sys.argv[1:] or sorted(f for f in os.listdir(DOCS) if f.endswith(".md"))
    total = []
    for n in names:
        total += build(n)
    if not total:
        print("Không tìm thấy khối ```mermaid mindmap nào.")
        return 1
    for f in total:
        print("  ->", f)
    print(f"Đã sinh {len(total)} mindmap HTML trong {os.path.relpath(OUT, DOCS)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

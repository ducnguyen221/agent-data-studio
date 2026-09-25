"""Đồng bộ kho template → trang web /template/.

Quét `report-templates/<kit>/` (kit.json + README.md + blueprint.md + ảnh preview*.png|jpg
hoặc assets/*.png|jpg) → sinh `docs/template/templates.json` + copy ảnh vào
`docs/template/assets/<kit>/`. Trang web fetch JSON này để render kho.

Chạy sau khi thêm/distill kit mới:
    .venv/Scripts/python.exe scripts/build_template_gallery.py
rồi commit docs/template/. (Kit distill có sanitize=True mới nên đưa vào repo public.)
"""

import json
import os
import re
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "report-templates")
OUT_DIR = os.path.join(REPO, "docs", "template")
OUT_ASSETS = os.path.join(OUT_DIR, "assets")
IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif")


def first_paragraph(md_path: str) -> str:
    if not os.path.exists(md_path):
        return ""
    txt = open(md_path, encoding="utf-8").read()
    # bỏ heading + blockquote đầu, lấy đoạn văn đầu tiên
    paras = [p.strip() for p in txt.split("\n\n")]
    for p in paras:
        if p and not p.startswith(("#", ">", "|", "```")):
            return re.sub(r"\s+", " ", re.sub(r"[*_`\[\]]", "", p))[:400]
    return ""


def main() -> int:
    kits = []
    os.makedirs(OUT_ASSETS, exist_ok=True)
    if not os.path.isdir(SRC):
        print("Không có report-templates/ — bỏ qua.")
        return 0
    for name in sorted(os.listdir(SRC)):
        kdir = os.path.join(SRC, name)
        kj = os.path.join(kdir, "kit.json")
        if not os.path.isfile(kj):
            continue
        kit = json.load(open(kj, encoding="utf-8-sig"))
        # ảnh preview: preview*.* ở gốc kit hoặc assets/
        previews = []
        cand_dirs = [kdir, os.path.join(kdir, "assets")]
        for d in cand_dirs:
            if not os.path.isdir(d):
                continue
            for f in sorted(os.listdir(d)):
                if f.lower().endswith(IMG_EXT) and ("preview" in f.lower() or d.endswith("assets")):
                    dst_dir = os.path.join(OUT_ASSETS, name)
                    os.makedirs(dst_dir, exist_ok=True)
                    shutil.copy2(os.path.join(d, f), os.path.join(dst_dir, f))
                    previews.append(f"assets/{name}/{f}")
        blocks = kit.get("blocks", [])
        kits.append({
            "name": kit.get("name", name),
            "dir": name,
            "description": first_paragraph(os.path.join(kdir, "README.md")),
            "canvas": kit.get("canvas", {}),
            "created": kit.get("created", ""),
            "sanitized": kit.get("sanitized", False),
            "blocks": [b.get("visualType", "?") for b in blocks],
            "n_blocks": len(blocks),
            "previews": previews,
            "readme_url": f"https://github.com/ducnguyen221/agent-data-studio/tree/main/report-templates/{name}",
        })
    out = os.path.join(OUT_DIR, "templates.json")
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"kits": kits}, f, ensure_ascii=False, indent=2)
    print(f"OK: {len(kits)} kit → {out}")
    for k in kits:
        print(f"  - {k['name']}: {k['n_blocks']} block, {len(k['previews'])} ảnh preview")
    return 0


if __name__ == "__main__":
    sys.exit(main())

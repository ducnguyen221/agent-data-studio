"""Tạo gallery chỉ từ kit có manifest quyền sử dụng ở ngoài repo.

Mặc định không ghi gì. Manifest phải liệt kê chính xác mọi file của từng kit,
SHA-256 của file, chủ sở hữu và giấy phép. Ví dụ cấu trúc manifest::

    {"schema_version": 1, "kits": [{"dir": "kit-name", "owner": "Owner",
     "license": "CC-BY-4.0", "files": {"kit.json": "<64 hex>"}}]}

Manifest là bằng chứng duyệt bên ngoài repo; việc có kit sanitize trong repo
không tự cấp quyền đưa ảnh hoặc metadata lên website.
"""

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "report-templates"
OUT_DIR = REPO / "docs" / "template"
KIT_NAME = re.compile(r"[a-z0-9][a-z0-9-]*\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class GalleryGateError(ValueError):
    """Manifest thiếu hoặc không đủ bằng chứng để phát hành."""


def _inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _is_reparse(path: Path) -> bool:
    """Chặn cả symlink và Windows junction trước khi đọc hoặc ghi."""
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    if is_junction is not None and is_junction():
        return True
    attrs = getattr(os.lstat(path), "st_file_attributes", 0)
    return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _safe_source(path: Path) -> bool:
    root = REPO.resolve()
    source = SRC.resolve()
    if not _inside(source, root) or not _inside(path.resolve(), source):
        return False
    current = path
    while current != SRC and _inside(current, SRC):
        if _is_reparse(current):
            return False
        current = current.parent
    return not _is_reparse(SRC)


def _safe_output() -> bool:
    root = REPO.resolve()
    if not _inside(OUT_DIR.resolve(), root):
        return False
    for path in (OUT_DIR, OUT_DIR.parent, OUT_DIR / "templates.json"):
        if path.exists() and _is_reparse(path):
            return False
    # Bản text-only không được âm thầm để lại ảnh public từ lần sinh trước.
    return not (OUT_DIR / "assets").exists()


def _paragraph(content: bytes | None) -> str:
    if content is None:
        return ""
    try:
        paragraphs = content.decode("utf-8").split("\n\n")
    except UnicodeDecodeError as exc:
        raise GalleryGateError("README của kit phải là UTF-8.") from exc
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if paragraph and not paragraph.startswith(("#", ">", "|", "```")):
            return re.sub(r"\s+", " ", re.sub(r"[*_`\[\]]", "", paragraph))[:400]
    return ""


def _file_map(directory: Path) -> dict[str, Path]:
    if not _safe_source(directory):
        raise GalleryGateError(f"Kit trỏ ra ngoài source hoặc là junction: {directory.name}")
    found = {}
    for path in directory.rglob("*"):
        if not _safe_source(path):
            raise GalleryGateError(f"File trỏ ra ngoài source hoặc là junction: {path}")
        if path.is_file():
            found[path.relative_to(directory).as_posix()] = path
    return found


def _validate(manifest_path: Path) -> list[tuple[str, dict, dict, dict[str, bytes]]]:
    if not manifest_path.is_file():
        raise GalleryGateError("Cần --approval-manifest trỏ tới file duyệt bên ngoài repo.")
    if _inside(manifest_path.resolve(), REPO.resolve()):
        raise GalleryGateError("Manifest duyệt phải nằm ngoài repo.")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GalleryGateError(f"Không đọc được manifest: {type(exc).__name__}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise GalleryGateError("Manifest phải có schema_version=1.")
    entries = manifest.get("kits")
    if not isinstance(entries, list) or not entries:
        raise GalleryGateError("Manifest phải duyệt ít nhất một kit.")
    validated = []
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise GalleryGateError("Mỗi kit trong manifest phải là object.")
        name = entry.get("dir")
        if not isinstance(name, str) or not KIT_NAME.fullmatch(name) or name in seen:
            raise GalleryGateError(f"Tên kit không hợp lệ hoặc trùng: {name!r}")
        seen.add(name)
        for field in ("owner", "license"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise GalleryGateError(f"Kit {name} thiếu {field}.")
        approved_files = entry.get("files")
        if not isinstance(approved_files, dict) or not approved_files:
            raise GalleryGateError(f"Kit {name} thiếu hash từng file.")
        directory = SRC / name
        if not directory.is_dir():
            raise GalleryGateError(f"Không tìm thấy kit {name}.")
        actual_files = _file_map(directory)
        if set(approved_files) != set(actual_files):
            raise GalleryGateError(f"Danh sách file của kit {name} không khớp manifest.")
        approved_bytes = {}
        for rel, path in actual_files.items():
            expected = approved_files[rel]
            if not isinstance(expected, str) or not SHA256.fullmatch(expected):
                raise GalleryGateError(f"SHA-256 không hợp lệ: {name}/{rel}")
            content = path.read_bytes()
            actual = hashlib.sha256(content).hexdigest()
            if actual != expected:
                raise GalleryGateError(f"Hash đã đổi: {name}/{rel}")
            approved_bytes[rel] = content
        if "kit.json" not in actual_files:
            raise GalleryGateError(f"Kit {name} thiếu kit.json.")
        try:
            kit = json.loads(approved_bytes["kit.json"].decode("utf-8-sig"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise GalleryGateError(f"kit.json không hợp lệ: {name}") from exc
        if not isinstance(kit, dict) or kit.get("sanitized") is not True:
            raise GalleryGateError(f"Kit {name} chưa xác nhận sanitized=true.")
        validated.append((name, entry, kit, approved_bytes))
    return validated


def build(manifest_path: Path) -> int:
    # Toàn bộ input phải qua gate trước khi tạo thư mục hoặc ghi bất kỳ file nào.
    validated = _validate(manifest_path)
    if not _safe_output():
        raise GalleryGateError("Đích là link, ngoài repo hoặc còn assets cũ; cần review thủ công.")
    kits = []
    for name, approval, kit, files in validated:
        blocks = kit.get("blocks", [])
        if not isinstance(blocks, list) or any(not isinstance(block, dict) for block in blocks):
            raise GalleryGateError(f"blocks không hợp lệ: {name}")
        kits.append({
            "name": kit.get("name", name),
            "dir": name,
            "description": _paragraph(files.get("README.md")),
            "canvas": kit.get("canvas", {}),
            "created": kit.get("created", ""),
            "sanitized": True,
            "blocks": [block.get("visualType", "?") for block in blocks],
            "n_blocks": len(blocks),
            "previews": [],
            "owner": approval["owner"].strip(),
            "license": approval["license"].strip(),
            "readme_url": f"https://github.com/ducnguyen221/agent-data-studio/tree/main/report-templates/{name}",
        })
    payload = json.dumps({"kits": kits}, ensure_ascii=False, indent=2) + "\n"
    # Chỉ xuất metadata text-only: một file JSON thay thế nguyên tử, không copy asset.
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=OUT_DIR, delete=False) as temp:
        temp.write(payload)
        temp_path = Path(temp.name)
    try:
        os.replace(temp_path, OUT_DIR / "templates.json")
    finally:
        temp_path.unlink(missing_ok=True)
    print(f"OK: {len(kits)} kit được duyệt → {OUT_DIR / 'templates.json'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval-manifest", type=Path, help="Manifest duyệt ngoài repo, có owner/license/SHA-256 từng file")
    args = parser.parse_args(argv)
    if args.approval_manifest is None:
        print("TỪ CHỐI: chưa có --approval-manifest bên ngoài repo; gallery giữ nguyên.", file=sys.stderr)
        return 2
    try:
        return build(args.approval_manifest)
    except GalleryGateError as exc:
        print(f"TỪ CHỐI: {exc}; gallery giữ nguyên.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

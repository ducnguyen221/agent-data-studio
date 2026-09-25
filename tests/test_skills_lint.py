"""Lint cây skills/ — khuôn skill của studio do MÁY kiểm, không phải mắt.

Luật (xem skills/README.md):
  - đúng 9 skill phẳng, tên thư mục có tiền tố `data-` hoặc `pbi-`;
  - SKILL.md có frontmatter: `name` = tên thư mục, `description` ≤ 1024 ký tự,
    `metadata.group` ∈ {data, powerbi};
  - SKILL.md ≤ 150 dòng;
  - mọi link Markdown tương đối trong SKILL.md trỏ tới file/thư mục có thật;
  - mọi `references/microsoft/SOURCE.lock.json` khớp sha256 + bytes của file nguyên văn,
    và không có file nguyên văn nào nằm ngoài lock.

Không dùng PyYAML (không có trong phụ thuộc của repo): frontmatter của studio viết theo
một tập con YAML cố định — `key: value`, chuỗi JSON trong ngoặc kép, khối `metadata:` thụt 2
khoảng trắng và danh sách `- item`. Viết sai tập con đó thì test báo đỏ, đúng ý đồ.
"""

import hashlib
import json
import os
import re

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(REPO, "skills")

EXPECTED = {
    "data-discovery", "data-mockup", "pbi-model", "pbi-analysis", "pbi-design",
    "pbi-build", "pbi-review", "pbi-publish", "pbi-knowledge",
}
MAX_LINES = 150
MAX_DESC = 1024
GROUPS = {"data", "powerbi"}


def skill_dirs() -> list[str]:
    return sorted(
        d for d in os.listdir(SKILLS)
        if os.path.isdir(os.path.join(SKILLS, d)) and not d.startswith((".", "_"))
    )


def _scalar(raw: str):
    raw = raw.strip()
    if raw.startswith('"'):
        return json.loads(raw)
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    return raw


def parse_frontmatter(text: str) -> dict:
    """Parse tập con YAML của studio. Ném ValueError khi không đúng khuôn."""
    if not text.startswith("---\n"):
        raise ValueError("thiếu dòng mở frontmatter '---'")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("thiếu dòng đóng frontmatter '---'")
    data: dict = {}
    block = None      # dict con hiện tại (vd metadata)
    list_key = None   # khoá danh sách hiện tại trong block
    for n, line in enumerate(text[4:end].split("\n"), 2):
        if not line.strip():
            continue
        if not line.startswith(" "):
            key, sep, val = line.partition(":")
            if not sep:
                raise ValueError(f"dòng {n}: không phải 'key: value'")
            key = key.strip()
            if val.strip():
                data[key] = _scalar(val)
                block = None
            else:
                data[key] = block = {}
            list_key = None
            continue
        if block is None:
            raise ValueError(f"dòng {n}: thụt lề nhưng không nằm trong khối")
        stripped = line.strip()
        if stripped.startswith("- "):
            if list_key is None:
                raise ValueError(f"dòng {n}: mục danh sách không có khoá cha")
            block[list_key].append(_scalar(stripped[2:]))
            continue
        key, sep, val = stripped.partition(":")
        if not sep:
            raise ValueError(f"dòng {n}: không phải 'key: value'")
        key = key.strip()
        if val.strip():
            block[key] = _scalar(val)
            list_key = None
        else:
            block[key] = []
            list_key = key
    return data


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def test_exactly_nine_prefixed_skills():
    dirs = set(skill_dirs())
    assert dirs == EXPECTED, f"thừa: {sorted(dirs - EXPECTED)} · thiếu: {sorted(EXPECTED - dirs)}"
    bad = [d for d in dirs if not d.startswith(("data-", "pbi-"))]
    assert not bad, f"tên skill thiếu tiền tố data-/pbi-: {bad}"


@pytest.mark.parametrize("skill", sorted(EXPECTED))
def test_skill_frontmatter(skill):
    path = os.path.join(SKILLS, skill, "SKILL.md")
    assert os.path.isfile(path), f"thiếu {skill}/SKILL.md"
    fm = parse_frontmatter(read(path))
    assert fm.get("name") == skill, f"name={fm.get('name')!r} phải = tên thư mục {skill!r}"
    desc = fm.get("description")
    assert isinstance(desc, str) and desc.strip(), "thiếu description"
    assert len(desc) <= MAX_DESC, f"description {len(desc)} > {MAX_DESC} ký tự"
    assert "Use when" in desc and "Not:" in desc, "description phải theo kiểu router 'Use when … Not: …'"
    meta = fm.get("metadata")
    assert isinstance(meta, dict), "thiếu khối metadata"
    assert meta.get("group") in GROUPS, f"metadata.group={meta.get('group')!r} ∉ {sorted(GROUPS)}"
    expected_group = "data" if skill.startswith("data-") else "powerbi"
    assert meta.get("group") == expected_group, "metadata.group phải khớp tiền tố thư mục"
    assert meta.get("status") in {"stable", "unverified"}, f"metadata.status={meta.get('status')!r}"
    assert isinstance(meta.get("sources"), list) and meta["sources"], "metadata.sources rỗng"
    assert "chain_position" in meta, "thiếu metadata.chain_position"


@pytest.mark.parametrize("skill", sorted(EXPECTED))
def test_skill_md_length(skill):
    n = len(read(os.path.join(SKILLS, skill, "SKILL.md")).rstrip("\n").split("\n"))
    assert n <= MAX_LINES, f"{skill}/SKILL.md dài {n} dòng > {MAX_LINES} — dời phần dài sang references/kpim/"


_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")


@pytest.mark.parametrize("skill", sorted(EXPECTED))
def test_relative_links_exist(skill):
    base = os.path.join(SKILLS, skill)
    text = read(os.path.join(base, "SKILL.md"))
    # Bỏ khối code: link minh hoạ trong ``` không phải link thật.
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    broken = []
    for m in _LINK.finditer(text):
        target = m.group(1)
        if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
            continue
        target = target.split("#", 1)[0]
        if not target:
            continue
        if os.path.isabs(target) or target.startswith("/"):
            broken.append(f"{target} (đường tuyệt đối bị cấm)")
            continue
        if not os.path.exists(os.path.normpath(os.path.join(base, target))):
            broken.append(target)
    assert not broken, f"{skill}/SKILL.md có link gãy:\n  " + "\n  ".join(broken)


def _locks() -> list[str]:
    out = []
    for skill in skill_dirs():
        lock = os.path.join(SKILLS, skill, "references", "microsoft", "SOURCE.lock.json")
        if os.path.isfile(lock):
            out.append(lock)
    return out


def test_microsoft_refs_have_lock():
    """Có thư mục references/microsoft/ thì phải có lock."""
    missing = [
        s for s in skill_dirs()
        if os.path.isdir(os.path.join(SKILLS, s, "references", "microsoft"))
        and not os.path.isfile(os.path.join(SKILLS, s, "references", "microsoft", "SOURCE.lock.json"))
    ]
    assert not missing, f"references/microsoft/ thiếu SOURCE.lock.json: {missing}"
    assert _locks(), "không tìm thấy SOURCE.lock.json nào"


@pytest.mark.parametrize("lock", _locks(), ids=lambda p: os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(p)))))
def test_source_lock_matches_files(lock):
    root = os.path.dirname(lock)
    with open(lock, encoding="utf-8") as fh:
        spec = json.load(fh)
    for key in ("upstream", "tag", "commit", "license", "files"):
        assert key in spec, f"lock thiếu khoá {key!r}"
    assert re.fullmatch(r"[0-9a-f]{40}", spec["commit"]), "commit phải là sha đầy đủ 40 ký tự"
    bad, listed = [], set()
    for entry in spec["files"]:
        for key in ("upstream_path", "path", "sha256", "bytes"):
            assert key in entry, f"mục lock thiếu {key!r}: {entry}"
        rel = entry["path"]
        listed.add(rel)
        p = os.path.join(root, *rel.split("/"))
        if not os.path.isfile(p):
            bad.append(f"{rel}: không tồn tại")
            continue
        with open(p, "rb") as fh:
            data = fh.read()
        if hashlib.sha256(data).hexdigest() != entry["sha256"] or len(data) != entry["bytes"]:
            bad.append(f"{rel}: sha256/bytes lệch lock (file nguyên văn bị sửa hoặc đổi xuống dòng)")
    actual = set()
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            rel = os.path.relpath(os.path.join(dirpath, f), root).replace(os.sep, "/")
            if rel != "SOURCE.lock.json":
                actual.add(rel)
    extra = sorted(actual - listed)
    assert not bad, "Reference Microsoft không khớp lock:\n  " + "\n  ".join(bad)
    assert not extra, "File trong references/microsoft/ không có trong lock:\n  " + "\n  ".join(extra)

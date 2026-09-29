"""Website `docs/`: header/footer chung, menu 4 mục, link nội bộ không gãy, redirect trang cũ.

Site tĩnh không có bước build nên header/footer được chép vào từng trang; test này bắt
mọi chỗ chép lệch. Kèm một phép đối chiếu số liệu: danh sách công cụ MCP trên trang Thiết kế
phải khớp đúng tập `@mcp.tool()` trong `powerbi_agent/`, để trang không trôi khỏi mã.
"""

import os
import posixpath
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(REPO, "docs")

MENU = [("about/", "Giới thiệu"), ("instruction/", "Hướng dẫn"), ("architecture/", "Thiết kế"), ("install/", "Cài đặt")]
# Trang chính → mục menu đang đứng (None = trang chủ, không mục nào active).
PAGES = {
    "index.html": None,
    "about/index.html": "about/",
    "instruction/index.html": "instruction/",
    "architecture/index.html": "architecture/",
    "install/index.html": "install/",
}
REDIRECTS = {
    "feature/index.html": "about/",
    "template/index.html": "architecture/",
}


def read(rel: str) -> str:
    with open(os.path.join(DOCS, rel.replace("/", os.sep)), encoding="utf-8") as fh:
        return fh.read()


class _Page(HTMLParser):
    """Gom link trong nav chính, link trong footer, mọi href/src và các mốc a11y."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.nav, self.footer, self.refs = [], [], []
        self.aria_current, self.h1, self.main_ids, self.skip = 0, 0, [], False
        self._in_nav = self._in_footer = False
        self._nav_depth = 0
        self._cur = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if tag == "nav" and "nav-links" in classes:
            self._in_nav, self._nav_depth = True, 1
        elif tag == "nav" and self._in_nav:
            self._nav_depth += 1
        if tag == "footer":
            self._in_footer = True
        if tag == "main":
            self.main_ids.append(a.get("id"))
        if tag == "h1":
            self.h1 += 1
        if a.get("aria-current") == "page":
            self.aria_current += 1
        for key in ("href", "src"):
            if a.get(key) is not None and tag in ("a", "link", "script", "img"):
                self.refs.append(a[key])
        if tag == "a":
            if "skip" in classes and a.get("href") == "#main":
                self.skip = True
            if self._in_nav:
                self._cur = {"href": a.get("href"), "current": a.get("aria-current") == "page", "text": ""}
            elif self._in_footer and a.get("href"):
                self.footer.append(a["href"])

    def handle_endtag(self, tag):
        if tag == "a" and self._cur is not None:
            self._cur["text"] = " ".join(self._cur["text"].split())
            self.nav.append(self._cur)
            self._cur = None
        if tag == "nav" and self._in_nav:
            self._nav_depth -= 1
            if self._nav_depth == 0:
                self._in_nav = False
        if tag == "footer":
            self._in_footer = False

    def handle_data(self, data):
        if self._cur is not None:
            self._cur["text"] += data


def parse(rel: str) -> _Page:
    p = _Page()
    p.feed(read(rel))
    return p


def is_internal(ref: str) -> bool:
    return not re.match(r"^(https?:|mailto:|data:|#|//)", ref) and ref != ""


def resolve(page_rel: str, ref: str) -> str:
    """Đường dẫn (so với docs/) mà `ref` trên trang `page_rel` trỏ tới; thư mục → index.html."""
    path = urlsplit(ref).path
    target = posixpath.join(posixpath.dirname(page_rel), path)
    if path in ("", ".") or path.endswith("/"):
        target = posixpath.join(target, "index.html")
    return posixpath.normpath(target)


@pytest.mark.parametrize("rel,active", PAGES.items())
def test_menu_has_four_items_in_fixed_order(rel, active):
    page = parse(rel)
    root = "" if rel == "index.html" else "../"
    labels = [item["text"] for item in page.nav]
    assert labels == [label for _, label in MENU], f"{rel}: menu phải là {[m[1] for m in MENU]}, đang là {labels}"
    for item, (slug, label) in zip(page.nav, MENU, strict=True):
        expected = "./" if slug == active else root + slug
        assert item["href"] == expected, f"{rel}: mục {label} phải trỏ {expected!r}, đang là {item['href']!r}"
        assert item["current"] == (slug == active), f"{rel}: aria-current của mục {label} sai"


@pytest.mark.parametrize("rel,active", PAGES.items())
def test_exactly_one_current_page_marker(rel, active):
    expected = 0 if active is None else 1
    assert parse(rel).aria_current == expected, f"{rel}: cần đúng {expected} aria-current=\"page\""


@pytest.mark.parametrize("rel", PAGES)
def test_skip_link_main_landmark_and_single_h1(rel):
    page = parse(rel)
    assert page.skip, f"{rel}: thiếu skip link <a class=\"skip\" href=\"#main\">"
    assert page.main_ids == ["main"], f"{rel}: cần đúng một <main id=\"main\">"
    assert page.h1 == 1, f"{rel}: cần đúng một <h1>, thấy {page.h1}"


@pytest.mark.parametrize("rel", PAGES)
def test_internal_links_point_to_existing_files(rel):
    missing = []
    for ref in parse(rel).refs:
        if not is_internal(ref):
            continue
        target = resolve(rel, ref)
        if not os.path.isfile(os.path.join(DOCS, target.replace("/", os.sep))):
            missing.append(f"{ref} -> docs/{target}")
    assert not missing, f"{rel}: link nội bộ gãy:\n  " + "\n  ".join(missing)


def test_footer_is_the_same_block_on_every_page():
    """Cùng tập đích (sau khi quy về docs/) và cùng thứ tự trên cả năm trang."""
    seen = {}
    for rel in PAGES:
        refs = parse(rel).footer
        seen[rel] = [resolve(rel, r) if is_internal(r) else r for r in refs]
    first = next(iter(seen.values()))
    assert first, "footer không có link nào"
    for rel, refs in seen.items():
        assert refs == first, f"{rel}: footer lệch khuôn chung\n  mong đợi {first}\n  đang là  {refs}"
    for slug, _ in MENU:
        assert slug + "index.html" in first, f"footer thiếu mục menu {slug}"


@pytest.mark.parametrize("rel", PAGES)
def test_main_pages_no_longer_link_retired_pages(rel):
    text = read(rel)
    for bad in ('href="../feature/', 'href="../template/', 'href="feature/', 'href="template/'):
        assert bad not in text, f"{rel}: còn link tới trang đã chuyển hướng ({bad})"
    assert "Power Agent" not in text, f"{rel}: còn tên cũ “Power Agent”"
    nav = re.search(r'<nav class="nav-links".*?</nav>', text, re.DOTALL)
    assert nav and "data-i18n" not in nav.group(0), f"{rel}: menu không còn dùng span data-i18n"


@pytest.mark.parametrize("rel,target", REDIRECTS.items())
def test_retired_pages_redirect_with_fallbacks(rel, target):
    text = read(rel)
    canonical = f'<link rel="canonical" href="https://ducnguyen.vn/agent-data-studio/{target}">'
    assert canonical in text, f"{rel}: thiếu canonical tới {target}"
    assert re.search(r'<meta http-equiv="refresh" content="0;url=\.\./' + re.escape(target), text), (
        f"{rel}: thiếu meta refresh dự phòng khi tắt JS"
    )
    assert "location.replace" in text and "location.hash" in text, f"{rel}: redirect bằng JS phải giữ fragment"
    assert f'href="../{target}' in text, f"{rel}: thiếu link bấm tay tới {target}"


def test_template_gallery_output_stays_in_place():
    """scripts/build_template_gallery.py ghi docs/template/templates.json — không được dời."""
    assert os.path.isfile(os.path.join(DOCS, "template", "templates.json"))


def _mcp_tools() -> set[str]:
    names = set()
    pkg = os.path.join(REPO, "powerbi_agent")
    for fn in os.listdir(pkg):
        if fn.startswith("tools_") and fn.endswith(".py"):
            with open(os.path.join(pkg, fn), encoding="utf-8") as fh:
                names |= set(re.findall(r"@mcp\.tool\(\)\s*\n\s*def\s+(\w+)", fh.read()))
    return names


def test_architecture_page_lists_exactly_the_mcp_tools_in_code():
    tools = _mcp_tools()
    assert len(tools) == 16, f"Số tool trong code đổi ({len(tools)}): cập nhật con số trên website"
    section = re.search(r'<section id="mcp".*?</section>', read("architecture/index.html"), re.DOTALL)
    assert section, "trang Thiết kế thiếu section #mcp"
    on_page = set()
    for row in re.findall(r"<tr>(.*?)</tr>", section.group(0), re.DOTALL):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
        if len(cells) >= 2:
            on_page |= set(re.findall(r"<code>(\w+)</code>", cells[1]))
    assert on_page == tools, (
        f"Danh sách tool trên trang lệch code. Thiếu: {sorted(tools - on_page)}; thừa: {sorted(on_page - tools)}"
    )


COUNT_PHRASES = {
    "about/index.html": ["<b>16</b>", "<b>9</b>", "<b>8</b>", "<b>2</b>", "<b>4</b>", "v0.7.1"],
    "architecture/index.html": ["16 công cụ", "9 skill", "8 lệnh và 2 agent", "Bốn host"],
}


@pytest.mark.parametrize("rel,phrases", COUNT_PHRASES.items())
def test_counts_on_pages_match_repo(rel, phrases):
    skills = [d for d in os.listdir(os.path.join(REPO, "skills"))
              if os.path.isfile(os.path.join(REPO, "skills", d, "SKILL.md"))]
    commands = [f for f in os.listdir(os.path.join(REPO, "commands")) if f.endswith(".md")]
    agents = [f for f in os.listdir(os.path.join(REPO, "agents")) if f.endswith(".md")]
    hosts = [d for d in os.listdir(os.path.join(REPO, "hosts")) if os.path.isdir(os.path.join(REPO, "hosts", d))]
    assert (len(skills), len(commands), len(agents), len(hosts)) == (9, 8, 2, 4), (
        "Số skill/lệnh/agent/host trong repo đổi: cập nhật con số trên website"
    )
    text = read(rel)
    for phrase in phrases:
        assert phrase in text, f"{rel}: thiếu con số “{phrase}”"

"""Kiểm tài liệu cài đặt agent-first: một prompt, một nguồn, không lệnh nguy hiểm.

`INSTALL.md` ở gốc repo là bản gốc của prompt copy-dán. README, START-HERE và trang
`/install/` của website chỉ chép lại; test này bắt mọi chỗ chép lệch. Test cũng khoá
luật an toàn của runbook: không tải-rồi-chạy, không đổi ExecutionPolicy phạm vi máy,
mọi lệnh gọi script của repo đều Bypass theo tiến trình.
"""

import html
import os
import re

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFFICIAL_REPO = "https://github.com/ducnguyen221/agent-data-studio"
RAW_INSTALL_URL = "https://raw.githubusercontent.com/ducnguyen221/agent-data-studio/main/INSTALL.md"
PROMPT_START = {
    "vi": "Hãy cài Agent Data Studio lên máy Windows này",
    "en": "Install Agent Data Studio on this Windows machine",
}
# Nơi chép prompt: file Markdown (khối ```text) hoặc trang web (<pre id="prompt-<lang>">).
COPIES = {
    "vi": ["README.vi.md", "START-HERE.md", "docs/install/index.html"],
    "en": ["README.md", "docs/install/index.html"],
}
INSTALL_HOSTS = {"codex", "claude", "claude-desktop", "antigravity"}
USER_DOCS = [
    "INSTALL.md", "START-HERE.md", "README.md", "README.vi.md", "hosts/README.md",
    "hosts/codex/README.md", "hosts/claude/README.md", "hosts/antigravity/README.md",
    "docs/install/index.html",
]


def read(rel: str) -> str:
    with open(os.path.join(REPO, rel.replace("/", os.sep)), encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip("\n").split("\n"))


def fenced_blocks(markdown: str) -> list[str]:
    return re.findall(r"^```[\w-]*\n(.*?)^```", markdown, flags=re.MULTILINE | re.DOTALL)


def html_pre_blocks(page: str) -> dict[str, str]:
    """Nội dung chữ của mọi <pre>, theo id (không id thì khoá rỗng + số thứ tự)."""
    blocks = {}
    for i, m in enumerate(re.finditer(r"<pre([^>]*)>(.*?)</pre>", page, flags=re.DOTALL)):
        ident = re.search(r'id="([^"]+)"', m.group(1))
        blocks[ident.group(1) if ident else f"#{i}"] = html.unescape(re.sub(r"<[^>]+>", "", m.group(2)))
    return blocks


def prompt_in(rel: str, lang: str) -> str:
    text = read(rel)
    if rel.endswith(".html"):
        found = html_pre_blocks(text).get(f"prompt-{lang}")
        assert found is not None, f"{rel}: thiếu <pre id=\"prompt-{lang}\">"
        return normalize(found)
    hits = [b for b in fenced_blocks(text) if b.startswith(PROMPT_START[lang])]
    assert len(hits) == 1, f"{rel}: cần đúng 1 khối prompt {lang}, thấy {len(hits)}"
    return normalize(hits[0])


def canonical(lang: str) -> str:
    return prompt_in("INSTALL.md", lang)


@pytest.mark.parametrize("lang,rel", [(lang, rel) for lang, rels in COPIES.items() for rel in rels])
def test_prompt_copies_match_install_md(lang, rel):
    assert prompt_in(rel, lang) == canonical(lang), (
        f"Prompt {lang} trong {rel} lệch bản gốc INSTALL.md — chép lại nguyên văn khối trong INSTALL.md."
    )


@pytest.mark.parametrize("lang", sorted(PROMPT_START))
def test_prompt_points_to_single_official_source(lang):
    prompt = canonical(lang)
    assert OFFICIAL_REPO in prompt
    assert RAW_INSTALL_URL in prompt
    urls = set(re.findall(r"https?://\S+", prompt))
    assert urls == {OFFICIAL_REPO, RAW_INSTALL_URL}, f"Prompt chỉ được trỏ repo chính thức: {sorted(urls)}"
    # Raw URL trỏ nhánh main tới đúng file ở gốc repo.
    assert os.path.isfile(os.path.join(REPO, RAW_INSTALL_URL.rsplit("/main/", 1)[1]))
    assert len(prompt.splitlines()) <= 16, "Prompt quá dài để dán vào ô chat hẹp"


def command_blocks(rel: str) -> list[str]:
    text = read(rel)
    if rel.endswith(".html"):
        return list(html_pre_blocks(text).values())
    return fenced_blocks(text)


@pytest.mark.parametrize("rel", USER_DOCS)
def test_no_download_and_execute_or_machine_policy(rel):
    bad = []
    for block in command_blocks(rel):
        for line in block.splitlines():
            if re.search(r"\biex\b|Invoke-Expression|DownloadString", line, re.IGNORECASE):
                bad.append(line.strip())
    text = read(rel)
    for m in re.finditer(r"Set-ExecutionPolicy[^\n]*", text, re.IGNORECASE):
        line = m.group(0)
        if re.search(r"LocalMachine", line, re.IGNORECASE) or not re.search(r"-Scope\s+(CurrentUser|Process)", line):
            bad.append(line.strip())
    assert not bad, f"{rel}: lệnh bị cấm trong tài liệu cài:\n  " + "\n  ".join(bad)


def test_install_md_never_changes_execution_policy():
    """Runbook cho agent không chứa lệnh đổi policy ở bất kỳ phạm vi nào."""
    assert "Set-ExecutionPolicy" not in read("INSTALL.md")


def test_install_md_runs_repo_scripts_with_process_bypass():
    bad = []
    powershell = re.findall(r"^```powershell\n(.*?)^```", read("INSTALL.md"), flags=re.MULTILINE | re.DOTALL)
    assert powershell, "INSTALL.md không có khối lệnh PowerShell nào"
    for block in powershell:
        for line in block.splitlines():
            if re.search(r"\b(install|doctor|uninstall|update)\.ps1\b", line):
                if "powershell -NoProfile -ExecutionPolicy Bypass -File" not in line:
                    bad.append(line.strip())
    assert not bad, "Lệnh gọi script trong INSTALL.md phải chạy qua Bypass theo tiến trình:\n  " + "\n  ".join(bad)


def test_install_md_relative_links_exist():
    missing = []
    for target in re.findall(r"\]\(([^)\s]+)\)", read("INSTALL.md")):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        path = target.split("#", 1)[0]
        if path and not os.path.exists(os.path.join(REPO, path.replace("/", os.sep))):
            missing.append(target)
    assert not missing, f"INSTALL.md có link tương đối gãy: {missing}"


def test_install_md_names_every_supported_host():
    text = read("INSTALL.md")
    for host in INSTALL_HOSTS:
        assert f"`{host}`" in text, f"INSTALL.md thiếu giá trị -Hosts `{host}`"


@pytest.mark.parametrize("script", ["install.ps1", "doctor.ps1", "uninstall.ps1"])
def test_documented_hosts_are_accepted_by_scripts(script):
    """Tài liệu hứa host nào thì script phải nhận host đó (bắt lệch docs ↔ code)."""
    text = read(script)
    missing = sorted(h for h in INSTALL_HOSTS if f"'{h}'" not in text and f'"{h}"' not in text)
    assert not missing, f"{script} chưa nhận host được INSTALL.md công bố: {missing}"


def test_doctor_supports_documented_preflight():
    assert re.search(r"\[switch\]\s*\$Preflight\b", read("doctor.ps1")), (
        "INSTALL.md dùng `doctor.ps1 -Preflight` nhưng doctor.ps1 chưa có cờ này"
    )


def test_entry_docs_point_to_install_md():
    for rel in ("README.md", "README.vi.md", "START-HERE.md", "INDEX.md"):
        assert "INSTALL.md" in read(rel), f"{rel} chưa trỏ tới INSTALL.md"


def test_install_page_is_host_neutral():
    page = read("docs/install/index.html")
    assert "Bắt đầu với Codex" not in page
    assert "Nhờ Codex cài" not in page
    for host in ("Codex", "Claude Code", "Claude Desktop", "Antigravity"):
        assert host in page, f"Trang cài đặt thiếu host {host}"

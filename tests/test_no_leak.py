"""Kiểm ranh giới source public và dữ liệu trạm basic/external."""

import json
import importlib.util
import os
import re
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Chỉ file do CHÍNH repo phát hành mới bị soi gắt. Artifact kế hoạch giữ nguyên vẹn làm lịch sử.
# docs/internal/ khong duoc track. docs/plans/ THI CO -> khong duoc mien,
# neu khong thi "file public duoc mien khoi quet file public".
SKIP_PREFIXES = ("docs/internal/", ".git/")


def tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "-C", REPO, "ls-files"], capture_output=True, text=True, check=True
    ).stdout
    return [f for f in out.splitlines() if f and not f.startswith(SKIP_PREFIXES)]


def read(rel: str) -> str:
    with open(os.path.join(REPO, rel.replace("/", os.sep)), encoding="utf-8") as fh:
        return fh.read()


class TestKitsAreSanitized:
    """Kit công khai chỉ được chứa placeholder — không một mẩu tên nghiệp vụ nào."""

    def _kit_files(self, ext: str) -> list[str]:
        return [f for f in tracked_files() if f.startswith("report-templates/") and f.endswith(ext)]

    def test_json_blocks_only_reference_placeholders(self):
        bad = []
        for rel in self._kit_files(".json"):
            obj = json.loads(read(rel))

            def walk(node, _rel=rel):
                if isinstance(node, dict):
                    for k, v in node.items():
                        if k in ("Entity", "Property") and isinstance(v, str):
                            if not v.startswith("TEMPLATE_"):
                                bad.append(f"{_rel}: {k}={v!r}")
                        else:
                            walk(v)
                elif isinstance(node, list):
                    for it in node:
                        walk(it)

            walk(obj)
        assert not bad, "Tên bảng/cột THẬT còn trong kit công khai:\n  " + "\n  ".join(bad)

    def test_blueprint_field_refs_are_placeholders(self):
        """`TEMPLATE_TABLE.<gì đó không phải TEMPLATE_*>` = tên thật lọt qua sanitize."""
        pat = re.compile(r"TEMPLATE_TABLE\.([^\s;,|<]+)")
        bad = []
        for rel in self._kit_files(".md"):
            for m in pat.finditer(read(rel)):
                if not m.group(1).startswith("TEMPLATE_"):
                    bad.append(f"{rel}: TEMPLATE_TABLE.{m.group(1)}")
        assert not bad, "Tên field THẬT còn trong blueprint kit:\n  " + "\n  ".join(bad)

    def test_no_contact_details_in_kit_data(self):
        """Nhãn tiếng Việt hợp lệ; chặn thông tin liên hệ trong giá trị kit."""
        email = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
        bad = []
        for rel in self._kit_files(".json"):
            obj = json.loads(read(rel))

            def walk(node):
                if isinstance(node, dict):
                    for value in node.values():
                        walk(value)
                elif isinstance(node, list):
                    for value in node:
                        walk(value)
                elif isinstance(node, str) and email.search(node):
                    bad.append(rel)

            walk(obj)
        assert not bad, "Kit chứa thông tin liên hệ; kiểm các file: " + ", ".join(sorted(set(bad)))


class TestNoPrivateArtifactsTracked:
    """Những thứ tuyệt đối không được vào git."""

    def test_secret_and_machine_files_untracked(self):
        forbidden = {".env", "policy.json", "knowledge.config.json"}
        tracked = set(tracked_files())
        hit = forbidden & tracked
        assert not hit, f"File riêng tư BỊ TRACK: {sorted(hit)}"

    def test_no_internal_docs_tracked(self):
        hit = [f for f in subprocess.run(
            ["git", "-C", REPO, "ls-files"], capture_output=True, text=True, check=True
        ).stdout.splitlines() if f.startswith("docs/internal/")]
        assert not hit, f"docs/internal/ là tài liệu nội bộ, không được track: {hit}"


class TestSourceBoundary:
    """Chỉ source được theo dõi; đầu ra nằm ở workspace/ bị ignore hoặc trạm ngoài."""

    # Danh sách file gốc repo được phép — mọi thứ khác là ứng viên "lỡ tay".
    ALLOWED_ROOT_FILES = {
        "README.md", "README.vi.md", "START-HERE.md", "INDEX.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md",
        "ROADMAP.md", "LICENSE", ".gitignore", ".gitattributes", ".env.example",
        "policy.example.json", "THIRD_PARTY_NOTICES.md", "NOTICE.md",
        "pyproject.toml", "requirements.txt", "requirements.loose.txt",
        "install.ps1", "uninstall.ps1", "doctor.ps1", "update.ps1", "pack.ps1", "mcp_server_powerbi.py",
    }
    ALLOWED_ROOT_DIRS = {
        ".claude-plugin", ".codex-plugin", ".claude", ".agents", ".github", "docs", "hosts", "plugins", "powerbi_agent",
        "report-templates", "samples", "scripts", "tests",
        "skills", "commands", "agents", "templates", "workflows", "upstream", "LICENSES",
    }

    def test_no_stray_files_at_repo_root(self):
        roots = {f.split("/")[0] for f in tracked_files()}
        stray = sorted(
            r for r in roots
            if r not in self.ALLOWED_ROOT_FILES and r not in self.ALLOWED_ROOT_DIRS
        )
        assert not stray, (
            "File/thư mục lạ ở gốc repo — sản phẩm làm việc phải ra thư mục dữ liệu "
            "(AGENTS.md §0). Nếu thật sự thuộc về repo, thêm vào ALLOWED_* trong test này:\n  "
            + "\n  ".join(stray)
        )

    def test_no_project_deliverables_committed(self):
        """Tên file bàn giao dự án (theo bộ mẫu KPIM) không được nằm ngoài templates/documents/."""
        deliverables = {
            "PROJECT.md", "RESEARCH_NOTES.md", "DATA_DICTIONARY.md",
            "METRICS_CALCULATION.md", "DOMAIN_DIMENSION.md", "REPORTS.md", "DESIGN.md",
        }
        allowed_prefix = "templates/documents/"
        bad = [
            f for f in tracked_files()
            if os.path.basename(f) in deliverables and not f.startswith(allowed_prefix)
        ]
        assert not bad, (
            "Tài liệu bàn giao dự án bị commit vào repo — chúng thuộc về thư mục dữ liệu:\n  "
            + "\n  ".join(bad)
        )


class TestNoPersonalPaths:
    """Docs công khai phải machine-agnostic (AGENTS.md)."""

    def test_no_real_home_directory(self):
        # Cho phép placeholder <you> / %USERPROFILE% / $env:USERPROFILE.
        pat = re.compile(r"[A-Z]:\\Users\\(?!<you>)[A-Za-z0-9._-]+", re.IGNORECASE)
        bad = []
        for rel in tracked_files():
            if not rel.endswith((".md", ".html", ".ps1", ".py", ".json", ".txt", ".example", ".toml", ".yml")):
                continue
            try:
                txt = read(rel)
            except (UnicodeDecodeError, FileNotFoundError):
                continue
            for i, line in enumerate(txt.splitlines(), 1):
                for m in pat.finditer(line):
                    bad.append(f"{rel}:{i}: {m.group(0)}")
        assert not bad, "Đường dẫn home THẬT trong file công khai:\n  " + "\n  ".join(bad)


class TestKitData:
    """Kiểm metadata kit bằng quy tắc chung; matcher dữ liệu riêng ở ngoài repo."""

    def test_kit_strings_are_style_or_placeholder(self):
        """Mọi chuỗi trong kit phải là placeholder, token style, hoặc từ khoá PBIR.

        Bắt được cả tên ASCII (`revenue_(1)…png`) mà bộ quét dấu tiếng Việt bỏ lọt.
        """
        import sys
        sys.path.insert(0, REPO)
        from powerbi_agent.pbir import is_placeholder_only

        style = re.compile(
            r"^'?#[0-9A-Fa-f]{3,8}'?$"           # màu hex
            r"|^'?[A-Za-z][A-Za-z0-9 ]{0,30}'?$"  # enum / tên font: 1 cụm chữ, không dấu
            r"|^[\d.,\-+eLD%]*$"                  # số / đơn vị
            r"|^blocks/[\w.\-]+$"                 # đường dẫn nội bộ kit
            r"|^https?://\S+$"                    # $schema và URL chuẩn của Microsoft
            r"|^'?[\w.\- /:]+'?$"                 # định danh kỹ thuật không dấu
            r"|^'?\(sanitized\)'?$"               # nhãn do chính distill_template ghi
            # Giá trị enum nhiều từ có sẵn của Power BI, vd nội dung nhãn donut
            # ("Category, data value, percent of total"). Thuần ASCII, không dấu.
            r"|^'?[A-Za-z][A-Za-z ,]{2,60}'?$"
        )
        # Lưu ý giới hạn: nhánh cuối chấp nhận cụm tiếng Anh, nên một measure đặt tên
        # tiếng Anh sẽ lọt qua CA NÀY. Lớp chặn cho trường hợp đó là
        # test_json_blocks_only_reference_placeholders (Entity/Property) và deny-list.
        bad = []
        for rel in [f for f in tracked_files()
                    if f.startswith("report-templates/") and f.endswith(".json")]:
            obj = json.loads(read(rel))

            def walk(node, _rel=rel):
                if isinstance(node, dict):
                    items = node.items()
                elif isinstance(node, list):
                    items = ((None, v) for v in node)
                else:
                    return
                for k, v in items:
                    if isinstance(v, str):
                        s = v.strip()
                        if s and not is_placeholder_only(s) and not style.match(s):
                            bad.append(f"{_rel}: {k} = {s[:60]!r}")
                    else:
                        walk(v)

            walk(obj)
        assert not bad, (
            "Chuỗi trong kit không phải placeholder cũng không phải token style "
            "— nghi là tên nghiệp vụ:\n  " + "\n  ".join(sorted(set(bad))[:25])
        )


class TestMindmapsStayInSync:
    """HTML mindmap sinh RA TỪ khối mermaid trong .md — hai bản không được lệch."""

    def test_cli_writes_project_mindmaps_from_repo_script(self, tmp_path):
        import shutil
        import sys

        docs = tmp_path / "project-docs"
        docs.mkdir()
        shutil.copy2(os.path.join(REPO, "templates", "documents", "PROJECT.md"), docs / "PROJECT.md")
        script = os.path.join(REPO, "skills", "data-discovery", "scripts", "generate_mindmap_html.py")
        result = subprocess.run(
            [sys.executable, script, "--docs", str(docs), "PROJECT.md"],
            cwd=REPO, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False, timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert list((docs / "mindmaps").glob("*.html"))

    def test_cli_rejects_parent_path(self, tmp_path):
        docs = tmp_path / "project-docs"
        docs.mkdir()
        outside = tmp_path / "outside.md"
        outside.write_text("```mermaid\nmindmap\n  root((Ngoài trạm))\n    Nhánh\n```", encoding="utf-8")
        script = os.path.join(REPO, "skills", "data-discovery", "scripts", "generate_mindmap_html.py")
        result = subprocess.run(
            [sys.executable, script, "--docs", str(docs), "../outside.md"],
            cwd=REPO, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False, timeout=30,
        )
        assert result.returncode != 0
        assert not (docs / "mindmaps").exists()

    def test_cli_rejects_linked_output_directory(self, tmp_path):
        docs = tmp_path / "project-docs"
        docs.mkdir()
        (docs / "PROJECT.md").write_text(
            "```mermaid\nmindmap\n  root((Dự án))\n    Nhánh\n```", encoding="utf-8"
        )
        outside = tmp_path / "outside"
        outside.mkdir()
        try:
            (docs / "mindmaps").symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("Máy không cho tạo symlink thư mục")
        script = os.path.join(REPO, "skills", "data-discovery", "scripts", "generate_mindmap_html.py")
        result = subprocess.run(
            [sys.executable, script, "--docs", str(docs), "PROJECT.md"],
            cwd=REPO, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False, timeout=30,
        )
        assert result.returncode != 0
        assert list(outside.iterdir()) == []


class TestSkillScriptOutputBoundary:
    def test_mockup_rejects_repo_output(self):
        script = os.path.join(REPO, "skills", "data-mockup", "scripts", "gen_skeleton.py")
        target = os.path.join(REPO, "data")
        result = subprocess.run(
            [sys.executable, script, "missing-spec.yaml", "-o", target],
            cwd=REPO, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False, timeout=30,
        )
        assert result.returncode == 2
        assert not os.path.exists(target)

    def test_planning_workbook_rejects_repo_output(self):
        script = os.path.join(REPO, "skills", "data-discovery", "scripts", "generate_project_management_xlsx.py")
        target = os.path.join(REPO, "Project_Management.xlsx")
        result = subprocess.run(
            [sys.executable, script, "--out", target],
            cwd=REPO, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False, timeout=30,
        )
        assert result.returncode == 2
        assert not os.path.exists(target)

    @pytest.mark.parametrize("command,target", [
        ("dict", "DATASET_SPEC.md"),
        ("verify", "DATA_QUALITY_REPORT.md"),
        ("pack", "Mockup.xlsx"),
    ])
    def test_mockpack_rejects_repo_output(self, command, target):
        script = os.path.join(REPO, "skills", "data-mockup", "scripts", "mockpack.py")
        output = os.path.join(REPO, target)
        source = os.path.join(REPO, "templates", "documents", "dataset", "dataset.template.yaml")
        args = [sys.executable, script, command, source]
        if command != "dict":
            args.append("missing-data")
        args.extend(["-o", output])
        result = subprocess.run(args, cwd=REPO, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False, timeout=30)
        assert result.returncode == 1
        assert "TỪ CHỐI" in result.stdout
        assert not os.path.exists(output)

    def test_mockpack_save_frames_rejects_traversal_and_hardlink(self, tmp_path):
        import pandas as pd

        script_dir = os.path.join(REPO, "skills", "data-mockup", "scripts")
        sys.path.insert(0, script_dir)
        spec = importlib.util.spec_from_file_location("mockpack_output_boundary_test", os.path.join(script_dir, "mockpack.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        out = tmp_path / "csv"
        frame = pd.DataFrame({"id": [1]})
        with pytest.raises(ValueError):
            module.save_frames({"../outside": frame}, str(out))
        assert not out.exists()
        out.mkdir()
        original = tmp_path / "original.txt"
        original.write_text("giữ nguyên", encoding="utf-8")
        try:
            os.link(original, out / "dim_khach_hang.csv")
        except OSError:
            pytest.skip("Máy không cho tạo hardlink")
        with pytest.raises(ValueError):
            module.save_frames({"dim_khach_hang": frame}, str(out))
        assert original.read_text(encoding="utf-8") == "giữ nguyên"

    def test_mockpack_rejects_quoted_hardlink_output(self, tmp_path):
        script = os.path.join(REPO, "skills", "data-mockup", "scripts", "mockpack.py")
        source = os.path.join(REPO, "templates", "documents", "dataset", "dataset.template.yaml")
        original = tmp_path / "original.md"
        original.write_text("giữ nguyên", encoding="utf-8")
        output = tmp_path / "DATASET_SPEC.md"
        try:
            os.link(original, output)
        except OSError:
            pytest.skip("Máy không cho tạo hardlink")
        result = subprocess.run(
            [sys.executable, script, "dict", source, "-o", f'"{output}"'],
            cwd=REPO, text=True, encoding="utf-8", errors="replace",
            capture_output=True, check=False, timeout=30,
        )
        assert result.returncode == 1
        assert "TỪ CHỐI" in result.stdout
        assert original.read_text(encoding="utf-8") == "giữ nguyên"

    def test_planning_workbook_rejects_quoted_hardlink_output(self, tmp_path):
        script = os.path.join(REPO, "skills", "data-discovery", "scripts", "generate_project_management_xlsx.py")
        original = tmp_path / "original.xlsx"
        original.write_text("giữ nguyên", encoding="utf-8")
        output = tmp_path / "Project_Management.xlsx"
        try:
            os.link(original, output)
        except OSError:
            pytest.skip("Máy không cho tạo hardlink")
        result = subprocess.run(
            [sys.executable, script, "--out", f'"{output}"'],
            cwd=REPO, text=True, encoding="utf-8", errors="replace",
            capture_output=True, check=False, timeout=30,
        )
        assert result.returncode == 2
        assert original.read_text(encoding="utf-8") == "giữ nguyên"

    def test_regenerating_html_produces_identical_files(self, tmp_path):
        import importlib.util
        import shutil
        skill = os.path.join(REPO, "skills", "data-discovery")
        docs = os.path.join(REPO, "templates", "documents")
        out = os.path.join(docs, "mindmaps")
        before = {f: open(os.path.join(out, f), encoding="utf-8").read()
                  for f in os.listdir(out) if f.endswith(".html")}
        assert before, "không có mindmap HTML nào"
        scratch_docs = tmp_path / "documents"
        scratch_docs.mkdir()
        for name in os.listdir(docs):
            if name.endswith(".md"):
                shutil.copy2(os.path.join(docs, name), scratch_docs / name)
        script = os.path.join(skill, "scripts", "generate_mindmap_html.py")
        spec = importlib.util.spec_from_file_location("mindmap_generator_test", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.DOCS = str(scratch_docs)
        module.OUT = str(scratch_docs / "mindmaps")
        made = []
        for name in sorted(os.listdir(scratch_docs)):
            if name.endswith(".md"):
                made.extend(module.build(name))
        assert made
        after = {f: (scratch_docs / "mindmaps" / f).read_text(encoding="utf-8")
                 for f in os.listdir(module.OUT) if f.endswith(".html")}
        assert after.keys() == before.keys(), (
            f"đổi tập file: {sorted(before)} -> {sorted(after)}")
        drift = [f for f in before if before[f] != after[f]]
        assert not drift, (
            "HTML đã lệch khỏi khối mermaid trong .md — chạy lại "
            f"generate_mindmap_html.py rồi commit: {drift}")

    def test_no_reference_to_deleted_png_mindmaps(self):
        bad = [f"{rel}" for rel in tracked_files()
               if rel.endswith((".md", ".html")) and "mindmaps/key_" in read(rel)
               and ".png" in read(rel).split("mindmaps/key_")[1][:40]]
        assert not bad, f"còn trỏ tới mindmap PNG đã xoá: {bad}"

"""Quét rò rỉ dữ liệu — repo này là PUBLIC.

Lý do tồn tại: kit `kpim-business-light` từng lọt 2 tên measure thật trong `blueprint.md`
suốt nhiều tháng, trong khi các file `blocks/*.json` đã sạch. Không ai soi ra bằng mắt.
Từ nay việc đó do máy kiểm, mỗi lần chạy test.

Luật của repo (xem AGENTS.md §0):
  - repo = hướng dẫn + hệ điều hành agent + MCP/skill. KHÔNG phải nơi làm việc.
  - tài liệu/báo cáo dự án luôn nằm ở Knowledge Dir NGOÀI repo.
  - chỉ template đã sanitize và tri thức NỀN TẢNG mới được đưa vào đây.
"""

import json
import os
import re
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Chỉ file do CHÍNH repo phát hành mới bị soi gắt. Artifact kế hoạch giữ nguyên vẹn làm lịch sử.
SKIP_PREFIXES = ("docs/plans/", "docs/internal/", ".git/")


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

    def test_no_business_labels_in_kit_data(self):
        """Chữ có dấu tiếng Việt trong DỮ LIỆU kit = tên nghiệp vụ thật sót lại.

        Đây là ca đã bắt được rò rỉ thật: `nativeQueryRef`/`displayName`/`metadata` và
        `Literal.Value` mang NHÃN HIỂN THỊ do user đặt, khác hoàn toàn tên kỹ thuật ở
        Entity/Property — nên sanitize đời đầu không đụng tới chúng.

        Chỉ soi phần DỮ LIỆU: mọi giá trị chuỗi trong JSON, và các dòng bảng của
        blueprint. Văn xuôi tài liệu (tiêu đề, mục "Cách dùng", README) được miễn.
        """
        viet = re.compile(
            r"[àáâãèéêìíòóôõùúăđĩũơưạảấầẩẫậắằẳẵặẹẻẽếềểễệốồổỗộớờởỡợụủứừửữựỳỵỷỹý]",
            re.IGNORECASE,
        )
        bad = []
        for rel in self._kit_files(".json"):
            obj = json.loads(read(rel))

            def walk(node, _rel=rel):
                if isinstance(node, dict):
                    for k, v in node.items():
                        if isinstance(v, str):
                            if viet.search(v):
                                bad.append(f"{_rel}: {k} = {v!r}")
                        else:
                            walk(v)
                elif isinstance(node, list):
                    for it in node:
                        if isinstance(it, str):
                            if viet.search(it):
                                bad.append(f"{_rel}: [] = {it!r}")
                        else:
                            walk(it)

            walk(obj)

        for rel in self._kit_files(".md"):
            if rel.endswith("README.md"):
                continue
            for i, line in enumerate(read(rel).splitlines(), 1):
                # chỉ dòng bảng (| … |) mới chứa binding; còn lại là văn xuôi hướng dẫn
                if line.lstrip().startswith("|") and "Visual ID" not in line and viet.search(line):
                    bad.append(f"{rel}:{i}: {line.strip()[:90]}")

        assert not bad, "Tên nghiệp vụ THẬT còn trong dữ liệu kit:\n  " + "\n  ".join(bad)


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


class TestRepoIsNotAWorkspace:
    """AGENTS.md §0 — repo giữ thứ đến từ GitHub, sản phẩm tạo ra đi ra ngoài.

    Luật này phải do MÁY kiểm. Một file `BAO_CAO_KHACH_A.md` lỡ tay commit vào gốc repo
    trông vô hại trong `git status` giữa hàng chục thay đổi khác — nhưng nó là dữ liệu
    khách hàng nằm trên repo public.
    """

    # Danh sách file gốc repo được phép — mọi thứ khác là ứng viên "lỡ tay".
    ALLOWED_ROOT_FILES = {
        "README.md", "README.vi.md", "INDEX.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md",
        "ROADMAP.md", "LICENSE", ".gitignore", ".env.example", "policy.example.json",
        "pyproject.toml", "requirements.txt", "requirements.loose.txt",
        "install.ps1", "uninstall.ps1", "pack.ps1", "mcp_server_powerbi.py",
    }
    ALLOWED_ROOT_DIRS = {
        ".claude-plugin", ".github", "docs", "hosts", "plugins", "powerbi_agent",
        "report-templates", "scripts", "tests",
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
        """Tên file bàn giao dự án (theo bộ mẫu KPIM) không được nằm ngoài document-templates/."""
        deliverables = {
            "PROJECT.md", "RESEARCH_NOTES.md", "DATA_DICTIONARY.md",
            "METRICS_CALCULATION.md", "DOMAIN_DIMENSION.md", "REPORTS.md", "DESIGN.md",
        }
        allowed_prefix = "plugins/powerbi-agent/skills/kpim-analysis/document-templates/"
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

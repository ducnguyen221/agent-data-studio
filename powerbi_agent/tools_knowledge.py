"""Tool Knowledge OS: setup Knowledge Dir (user chỉ định) · project folder · timeline.

Quy trình đầy đủ + luật riêng tư: skill `powerbi-knowledge` và ROADMAP §M5.
"""

import json
import os
from datetime import date

from powerbi_agent import knowledge as kn
from powerbi_agent.util import log, short_err


def register(mcp):
    """Đăng ký các tool Knowledge OS vào instance FastMCP."""

    @mcp.tool()
    def knowledge_status() -> str:
        """
        Kiểm tra Knowledge Dir (nơi lưu tri thức dự án NGOÀI repo) đã thiết lập chưa +
        tóm tắt hiện trạng. GỌI TOOL NÀY ĐẦU TIÊN trước mọi quy trình tri thức
        (/powerbi-new, /powerbi-scan, /powerbi-done, /powerbi-pack, /powerbi-recall).
        """
        root = kn.resolve_root()
        if not root:
            return "CHƯA SETUP. " + kn.NOT_SETUP_MSG
        if not os.path.isdir(root):
            return (
                f"Config trỏ tới '{root}' nhưng folder không tồn tại (đổi máy/di chuyển?). "
                "Hỏi user xác nhận lại đường dẫn rồi gọi setup_knowledge(path) lần nữa."
            )
        projects = sorted(os.listdir(os.path.join(root, "projects"))) if os.path.isdir(
            os.path.join(root, "projects")) else []
        n_knowledge = sum(
            len([f for f in os.listdir(os.path.join(root, "knowledge", ax)) if f.endswith(".md")])
            for ax in kn.KNOWLEDGE_AXES if os.path.isdir(os.path.join(root, "knowledge", ax))
        )
        return (
            f"Knowledge Dir: `{root}`\n"
            f"- Dự án ({len(projects)}): {', '.join(projects) or '(chưa có)'}\n"
            f"- Tri thức đã đóng gói: {n_knowledge} file (4 trục: {', '.join(kn.KNOWLEDGE_AXES)})\n"
            f"- Đọc bối cảnh: `{root}/INDEX.md` → `TIMELINE.md` → knowledge/ khớp domain.\n"
            "Nhắc: folder này là CỦA USER, ngoài repo — không commit vào git của repo."
        )

    @mcp.tool()
    def setup_knowledge(path: str) -> str:
        """
        Thiết lập Knowledge Dir tại `path` do USER CHỈ ĐỊNH (folder NGOÀI repo — ưu tiên
        knowledge base/Brain có sẵn của user; agent phải HỎI user trước, không tự chọn).
        Ghi knowledge.config.json (gitignored) + dựng skeleton (projects/ · knowledge/ 4 trục ·
        templates/ · INDEX.md · TIMELINE.md). Idempotent.
        """
        try:
            base = os.path.expanduser(path.strip().strip('"'))
            repo_root = os.path.dirname(kn.CONFIG_FILE)
            if os.path.commonpath([os.path.abspath(base), repo_root]) == repo_root:
                return (
                    "TỪ CHỐI: đường dẫn nằm TRONG repo. Tri thức cá nhân phải ở NGOÀI repo "
                    "public — hỏi user chọn folder khác (Brain có sẵn hoặc ~/powerbi-knowledge)."
                )
            os.makedirs(base, exist_ok=True)
            with open(kn.CONFIG_FILE, "w", encoding="utf-8", newline="\n") as f:
                json.dump({"knowledge_dir": base, "created": date.today().isoformat()}, f,
                          ensure_ascii=False, indent=2)
            root = os.path.join(base, "powerbi-agent")
            kn.ensure_skeleton(root)
            kn.append_timeline(root, "—", "Thiết lập Knowledge Dir", f"skeleton tại {root}")
            return (
                f"Đã thiết lập Knowledge Dir: `{root}` (config: knowledge.config.json — gitignored).\n"
                "Cấu trúc: projects/ · knowledge/{tech-stack,industry,business-domain,powerbi}/ · "
                "templates/ · INDEX.md · TIMELINE.md.\n"
                "Gợi ý thêm: đặt env POWERBI_TEMPLATES_DIR trỏ `templates/` trong này để dùng kit riêng."
            )
        except Exception as e:
            log.exception("setup_knowledge thất bại")
            return f"Lỗi setup_knowledge: {short_err(e)}"

    @mcp.tool()
    def init_project(name: str) -> str:
        """
        Tạo folder dự án mới `projects/<slug>/` trong Knowledge Dir (+ artifacts/ + design/),
        đăng ký INDEX + TIMELINE. MỌI file agent tạo trong dự án (tài liệu KPIM, artifact,
        distill) mặc định lưu vào folder này. Trả về đường dẫn để dùng cho các bước sau.
        """
        try:
            root = kn.resolve_root()
            if not root:
                return "CHƯA SETUP. " + kn.NOT_SETUP_MSG
            slug = kn.slugify(name)
            pdir = os.path.join(root, "projects", slug)
            existed = os.path.isdir(pdir)
            os.makedirs(os.path.join(pdir, "artifacts"), exist_ok=True)
            os.makedirs(os.path.join(pdir, "design"), exist_ok=True)
            kn.ensure_skeleton(root)
            if not existed:
                kn.register_project_in_index(root, slug, name)
                kn.append_timeline(root, name, "Khởi tạo dự án", "", f"projects/{slug}/")
            return (
                f"{'Dự án đã tồn tại' if existed else 'Đã tạo dự án'}: `{pdir}`\n"
                "- Tài liệu KPIM (PROJECT.md, DATA_DICTIONARY.md…) ghi thẳng vào đây\n"
                "- Artifact (PLAN/CHANGESET/VERIFICATION/HANDOFF) → artifacts/\n"
                "- Distill model/report design → design/\n"
                "Bước tiếp: skill kpim-analysis (pha Research NÊN đọc knowledge/ khớp domain trước khi hỏi user)."
            )
        except Exception as e:
            log.exception("init_project thất bại")
            return f"Lỗi init_project: {short_err(e)}"

    @mcp.tool()
    def log_timeline(project: str, event: str, lesson: str = "", link: str = "") -> str:
        """
        Ghi 1 dòng vào TIMELINE.md (append-only): dự án + sự kiện + bài học/sản phẩm + link.
        Dùng khi: đóng dự án, sinh kit mới, rút bài học, mốc quan trọng.
        """
        try:
            root = kn.resolve_root()
            if not root:
                return "CHƯA SETUP. " + kn.NOT_SETUP_MSG
            kn.append_timeline(root, project, event, lesson, link)
            return f"Đã ghi TIMELINE: {project} — {event}"
        except Exception as e:
            log.exception("log_timeline thất bại")
            return f"Lỗi log_timeline: {short_err(e)}"

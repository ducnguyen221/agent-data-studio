"""Tool Knowledge OS: setup Knowledge Dir (user chỉ định) · project folder · timeline.

Quy trình đầy đủ + luật riêng tư: skill `powerbi-knowledge` và ROADMAP §M5.
"""

import os

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
        Thiết lập THƯ MỤC DỰ ÁN tại `path` do USER CHỈ ĐỊNH — luôn NẰM NGOÀI repo.
        Agent phải HỎI user trước, gợi ý mặc định `~/powerbi-project`, không tự chọn.

        Con trỏ ghi vào %LOCALAPPDATA%\\powerbi-agent\\config.json (ngoài repo, nên sống sót
        khi repo bị xoá/clone lại và không thể bị commit nhầm). Dựng skeleton:
        projects/ · knowledge/ 4 trục · templates/ · INDEX.md · TIMELINE.md. Idempotent.
        """
        try:
            base = os.path.abspath(os.path.expanduser(path.strip().strip('"')))
            repo_root = os.path.dirname(os.path.dirname(os.path.abspath(kn.__file__)))
            if os.path.commonpath([base, repo_root]) == repo_root:
                return (
                    "TỪ CHỐI: đường dẫn nằm TRONG repo. Repo là git working tree — chỉ một lệnh "
                    "`git add -A` là tài liệu khách hàng bị commit, và `git pull`/cài lại có thể "
                    f"xoá đè. Hỏi user chọn nơi khác, mặc định `{kn.default_project_dir()}`."
                )
            os.makedirs(base, exist_ok=True)
            root = kn.set_project_dir(base)
            kn.ensure_skeleton(root)
            kn.append_timeline(root, "—", "Thiết lập thư mục dự án", f"skeleton tại {root}")
            return (
                f"Đã thiết lập thư mục dự án: `{root}`\n"
                f"Con trỏ ghi tại: `{kn.CONFIG_FILE}` (ngoài repo).\n"
                "Cấu trúc: projects/ · knowledge/{tech-stack,industry,business-domain,powerbi}/ · "
                "templates/ · INDEX.md · TIMELINE.md.\n"
                "Muốn dùng kit riêng: đặt env POWERBI_TEMPLATES_DIR trỏ vào `templates/` trong này."
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
            # Sổ ghi nhớ nằm ngoài repo: sau này truy vết được tài liệu dự án nằm ở đâu,
            # kể cả khi user cho ghi ra một thư mục khác hoàn toàn.
            kn.register_project(slug, name, pdir)
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

---
name: powerbi-knowledge
description: >
  Knowledge OS của powerbi-agent — cơ chế lưu trữ & học hỏi tri thức dự án Power BI vào
  Knowledge Dir do USER CHỈ ĐỊNH ngoài repo (ưu tiên folder Brain/knowledge base có sẵn).
  Kích hoạt khi: bắt đầu/kết thúc dự án Power BI, user nói "lưu tri thức", "đóng gói kiến thức",
  "dự án cũ làm thế nào", "đã từng làm gì tương tự", "quét thiết kế báo cáo này", "setup knowledge",
  hoặc bất kỳ lúc nào cần ghi/đọc kinh nghiệm dự án. Các host không có slash command (Codex,
  Antigravity) dùng skill này thay cho bộ lệnh /powerbi-*.
---

# powerbi-knowledge — Knowledge OS (dự án · tri thức · timeline)

**Nguyên tắc:** repo public sạch — MỌI tri thức làm việc (tài liệu dự án, kinh nghiệm, kit riêng)
sống trong **Knowledge Dir ngoài repo, do user chỉ định**. Agent giỏi dần theo từng dự án của
chính user; không tri thức nào của ai bị đẩy lên git.

## Luồng chuẩn (= bộ lệnh /powerbi-* trên Claude; host khác làm theo bảng này)

| Lệnh | Khi nào | Agent làm gì |
|---|---|---|
| `/powerbi-setup` | Lần đầu, hoặc `knowledge_status` báo chưa setup | HỎI user chỉ định folder NGOÀI repo (**ưu tiên Brain/knowledge base có sẵn**; chưa có → đề xuất `~/powerbi-knowledge`) → `setup_knowledge(path)` |
| `/powerbi-new <tên>` | Bắt đầu dự án Power BI mới | `init_project(tên)` → nhận đường dẫn `projects/<slug>/` → chạy skill `kpim-analysis` (pha Research **ĐỌC `knowledge/` khớp domain trước khi hỏi user**) — mọi file sinh ra ghi vào folder dự án |
| `/powerbi-scan <path>` | Có file .pbip/.Report cần lưu hồ sơ thiết kế | `distill_report_design(path, project)` → REPORT_CATALOG + DESIGN + theme/ vào `projects/<slug>/design/`; kèm `distill_model_schema` nếu model đang mở |
| `/powerbi-done` | Kết thúc dự án | Checklist đóng: đủ 4 artifact? design/ đã quét? → đề xuất trang đẹp đáng `distill_template` thành kit (bản thô → `templates/` của Knowledge Dir; muốn public → sanitize=True + user duyệt) → `log_timeline` → gọi curator đóng gói |
| `/powerbi-pack [dự án]` | Sau /powerbi-done hoặc định kỳ | Giao agent **`powerbi-knowledge-curator`**: rút bài học TÁI DÙNG từ projects/ → phân loại 4 trục `knowledge/{tech-stack,industry,business-domain,powerbi}/` — **dedup: cập nhật file cũ thay vì tạo trùng**, mỗi bài học có `**Why:**` + `**How to apply:**` → cập nhật INDEX + TIMELINE |
| `/powerbi-recall [từ khóa]` | "Đã từng làm gì tương tự?" | Đọc `INDEX.md` → `TIMELINE.md` → grep `knowledge/` + `projects/*/PROJECT.md` theo từ khóa → tóm tắt kinh nghiệm liên quan |

**Trước MỌI quy trình trên: gọi tool `knowledge_status` trước.** Chưa setup → dừng, chạy luồng /powerbi-setup.

## Cấu trúc Knowledge Dir (tool tự dựng)

```
<KNOWLEDGE_DIR>/powerbi-agent/
  INDEX.md          # mục lục — agent đọc ĐẦU TIÊN
  TIMELINE.md       # lịch sử append-only: | ngày | dự án | sự kiện | bài học | link |
  projects/<slug>/  # 1 dự án 1 folder: tài liệu KPIM + artifacts/ + design/
  knowledge/        # tri thức ĐÃ đóng gói: tech-stack/ industry/ business-domain/ powerbi/
  templates/        # kit visual riêng CHƯA sanitize (POWERBI_TEMPLATES_DIR trỏ vào đây)
```

## Luật riêng tư (CỨNG)

1. `knowledge.config.json` + toàn bộ Knowledge Dir **KHÔNG BAO GIỜ commit** vào repo.
2. Đường DUY NHẤT đưa tri thức riêng → repo public: user chủ động ra lệnh + `sanitize=True` + user review.
3. User này trỏ Knowledge Dir vào Brain riêng của họ — user khác clone repo sẽ **không có** config đó
   và phải tự khai báo qua /powerbi-setup. Đừng bao giờ gợi ý commit config.

## Chuẩn 1 file tri thức trong knowledge/

```markdown
# <tên bài học ngắn>
> Nguồn: projects/<slug> · <ngày> · trục: <tech-stack|industry|business-domain|powerbi>

<sự thật/bài học 2-5 câu>

**Why:** <vì sao đúng/đáng nhớ — bằng chứng từ dự án>
**How to apply:** <lần sau gặp tình huống X thì làm Y>
Liên quan: [<dự án>](../../projects/<slug>/PROJECT.md) · <link kit/file khác nếu có>
```

## 🔗 Liên quan
- Quy trình nghiệp vụ sinh tài liệu: [`../kpim-analysis/SKILL.md`](../kpim-analysis/SKILL.md)
- Pipeline kỹ thuật 9 khâu: [`../powerbi-pipeline/SKILL.md`](../powerbi-pipeline/SKILL.md)
- Tool MCP (knowledge_status/setup/init/log + distill_*): [`../powerbi-mcp/SKILL.md`](../powerbi-mcp/SKILL.md)

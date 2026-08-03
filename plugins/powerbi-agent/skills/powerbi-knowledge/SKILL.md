---
name: powerbi-knowledge
x-generated-by: powerbi-agent
description: >
  Knowledge OS của powerbi-agent — cơ chế lưu trữ & học hỏi tri thức dự án Power BI vào
  thư mục dự án do USER CHỈ ĐỊNH ngoài repo (mặc định `~/powerbi-project`).
  Kích hoạt khi: bắt đầu/kết thúc dự án Power BI, user nói "lưu tri thức", "đóng gói kiến thức",
  "dự án cũ làm thế nào", "đã từng làm gì tương tự", "quét thiết kế báo cáo này", "setup knowledge",
  hoặc bất kỳ lúc nào cần ghi/đọc kinh nghiệm dự án. Các host không có slash command (Codex,
  Antigravity) dùng skill này thay cho bộ lệnh /powerbi-*.
---

# powerbi-knowledge — Knowledge OS (dự án · tri thức · timeline)

**Nguyên tắc:** repo public sạch — MỌI tri thức làm việc (tài liệu dự án, kinh nghiệm, kit riêng)
sống trong **thư mục dự án ngoài repo, do user chỉ định**. Agent giỏi dần theo từng dự án của
chính user; không tri thức nào của ai bị đẩy lên git.

## Luồng chuẩn (= bộ lệnh /powerbi-* trên Claude; host khác làm theo bảng này)

| Lệnh | Khi nào | Agent làm gì |
|---|---|---|
| `/powerbi-help` | Chưa rõ nên dùng gì, hoặc vừa cài xong trên máy mới | Gọi `knowledge_status` + `list_templates` báo trạng thái THẬT → liệt kê 8 lệnh · 4 skill · 16 tool → định tuyến yêu cầu của user vào đúng quy trình |
| `/powerbi-setup` | Lần đầu, hoặc `knowledge_status` báo chưa setup | HỎI user chỉ định folder NGOÀI repo (**mặc định ~/powerbi-project**; chưa có → đề xuất `~/powerbi-project`) → `setup_knowledge(path)` |
| `/powerbi-new <tên>` | Bắt đầu dự án Power BI mới | `init_project(tên)` → nhận đường dẫn `projects/<slug>/` → chạy skill `kpim-analysis` (pha Research **ĐỌC `knowledge/` khớp domain trước khi hỏi user**) — mọi file sinh ra ghi vào folder dự án |
| `/powerbi-scan <path>` | Có file .pbip/.Report cần lưu hồ sơ thiết kế | `distill_report_design(path, project)` → REPORT_CATALOG + DESIGN + theme/ vào `projects/<slug>/design/`; kèm `distill_model_schema` nếu model đang mở |
| `/powerbi-kit <path>` | Có báo cáo đẹp muốn TÁI DÙNG thiết kế (khác /powerbi-scan chỉ ghi hồ sơ) | `distill_report_design` để chọn trang → `distill_template(..., sanitize=True)` cho TỪNG trang đáng giữ → gom thành bộ có `theme.json` + README mô tả hệ thiết kế; mặc định ghi vào `templates/` của thư mục dự án |
| `/powerbi-done` | Kết thúc dự án | Checklist đóng: đủ 4 artifact? design/ đã quét? → đề xuất trang đẹp đáng `distill_template` thành kit (bản thô → `templates/` của thư mục dự án; muốn public → sanitize=True + user duyệt) → `log_timeline` → gọi curator đóng gói |
| `/powerbi-pack [dự án]` | Sau /powerbi-done hoặc định kỳ | Giao agent **`powerbi-knowledge-curator`**: rút bài học TÁI DÙNG từ projects/ → phân loại 4 trục `knowledge/{tech-stack,industry,business-domain,powerbi}/` — **dedup: cập nhật file cũ thay vì tạo trùng**, mỗi bài học có `**Why:**` + `**How to apply:**` → cập nhật INDEX + TIMELINE |
| `/powerbi-recall [từ khóa]` | "Đã từng làm gì tương tự?" | Đọc `INDEX.md` → `TIMELINE.md` → grep `knowledge/` + `projects/*/PROJECT.md` theo từ khóa → tóm tắt kinh nghiệm liên quan |

**Trước MỌI quy trình trên: gọi tool `knowledge_status` trước.** Chưa setup → dừng, chạy luồng /powerbi-setup.

## Cấu trúc thư mục dự án (tool tự dựng)

```
<KNOWLEDGE_DIR>/
  INDEX.md          # mục lục — agent đọc ĐẦU TIÊN
  TIMELINE.md       # lịch sử append-only: | ngày | dự án | sự kiện | bài học | link |
  projects/<slug>/  # 1 dự án 1 folder: tài liệu KPIM + artifacts/ + design/
  knowledge/        # tri thức ĐÃ đóng gói: tech-stack/ industry/ business-domain/ powerbi/
  templates/        # kit visual riêng CHƯA sanitize (POWERBI_TEMPLATES_DIR trỏ vào đây)
```

## Luật riêng tư (CỨNG)

1. `.env` (chứa con trỏ + secret) + toàn bộ thư mục dự án **KHÔNG BAO GIỜ commit** vào repo.
2. Đường DUY NHẤT đưa tri thức riêng → repo public: user chủ động ra lệnh + `sanitize=True` + user review.
3. Con trỏ thư mục nằm trong `.env` của TỪNG BẢN CLONE — user khác clone repo sẽ **không có** config đó
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

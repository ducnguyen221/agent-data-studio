---
title: Knowledge OS — cấu trúc Knowledge Dir, luồng 8 lệnh, chuẩn file tri thức, luật riêng tư
source: KPIM practice — gộp skill powerbi-knowledge (repo) và pbi-knowledge (OpcOS data-bi)
updated: 2026-09-17
---

# Knowledge OS

**Nguyên tắc:** repo công khai sạch — MỌI tri thức làm việc (tài liệu dự án, kinh nghiệm, kit riêng) sống trong
**Knowledge Dir ngoài repo, do user chỉ định**. Agent giỏi dần theo từng dự án của chính user.

## 1. Luồng chuẩn (= 8 lệnh `/pbi-*`; host không có slash-command làm theo bảng)

| Lệnh | Khi nào | Agent làm gì |
|---|---|---|
| `/pbi-help` | Chưa rõ dùng gì / vừa cài xong | `knowledge_status` + `list_templates` → báo trạng thái thật → bản đồ 9 skill → định tuyến |
| `/pbi-setup` | Lần đầu, hoặc `knowledge_status` báo chưa setup | HỎI user folder NGOÀI repo (ưu tiên knowledge base có sẵn của họ) → `setup_knowledge(path)` |
| `/pbi-new <tên>` | Bắt đầu dự án | `init_project` → đọc `knowledge/` + `TIMELINE.md` khớp domain **trước khi hỏi user** → skill `data-discovery`; chuỗi ở `workflows/data-to-report.md` |
| `/pbi-scan <path>` | Có `.pbip` / `.Report` cần hồ sơ thiết kế | `distill_report_design` → `projects/<slug>/design/`; kèm `distill_model_schema` nếu model đang mở |
| `/pbi-kit <path>` | Muốn **tái dùng** thiết kế | Chọn trang → `distill_template(sanitize=True)` từng trang, `out_dir` riêng → gom bộ + theme + README |
| `/pbi-done` | Kết thúc dự án | Checklist 4 artifact + design/ + schema → đề xuất kit → `log_timeline` → `/pbi-pack` |
| `/pbi-pack [dự án]` | Sau `/pbi-done` hoặc định kỳ | Agent **`pbi-knowledge-curator`**: rút bài học tái dùng → 4 trục → dedup → INDEX + TIMELINE |
| `/pbi-recall [từ khoá]` | "Đã từng làm gì tương tự?" | `INDEX.md` → `TIMELINE.md` → grep `knowledge/` + `projects/*/PROJECT.md` → tóm tắt |

**Trước MỌI luồng: gọi `knowledge_status`.** Chưa setup → dừng, chạy `/pbi-setup`.

## 2. Cấu trúc Knowledge Dir (tool tự dựng)

```
<KNOWLEDGE_DIR>/
  INDEX.md          mục lục — agent đọc ĐẦU TIÊN
  TIMELINE.md       lịch sử append-only: | ngày | dự án | sự kiện | bài học | link |
  projects/<slug>/  1 dự án 1 thư mục: tài liệu KPIM + artifacts/ + design/
  knowledge/        tri thức ĐÃ đóng gói: tech-stack/ industry/ business-domain/ powerbi/
  templates/        kit visual riêng CHƯA sanitize (POWERBI_TEMPLATES_DIR trỏ vào đây)
```

Con trỏ tới Knowledge Dir là dòng `POWERBI_PROJECT_DIR` trong `.env` của **thư mục dữ liệu máy** (`$ADS_DATA`),
không phải của repo. Thư mục user chọn CHÍNH LÀ root (không có cấp con).

## 3. Luật riêng tư (CỨNG)
1. `.env` + toàn bộ Knowledge Dir **không bao giờ commit** vào repo.
2. Đường DUY NHẤT đưa tri thức riêng vào repo công khai: user chủ động ra lệnh + `sanitize=True` + user review.
3. Mỗi máy tự khai báo Knowledge Dir qua `/pbi-setup`; không bao giờ gợi ý commit cấu hình.
4. Schema model, audit, kit chưa sanitize: chỉ ở Knowledge Dir / thư mục dữ liệu, không ở thư mục đồng bộ công khai.

## 4. Chuẩn một file tri thức trong `knowledge/`

```markdown
# <tên bài học ngắn>
> Nguồn: projects/<slug> · <ngày> · trục: <tech-stack|industry|business-domain|powerbi>

<sự thật/bài học 2–5 câu>

**Why:** <vì sao đúng/đáng nhớ — bằng chứng từ dự án>
**How to apply:** <lần sau gặp tình huống X thì làm Y>
Liên quan: [<dự án>](../../projects/<slug>/PROJECT.md) · <link kit/file khác>
```

Ngưỡng cao: chỉ bài học **tái dùng**; không lưu thứ tra lại được từ tài liệu dự án, chi tiết một lần, số liệu cụ thể.
Dedup trước khi ghi — trùng chủ đề thì cập nhật file cũ. Mỗi file ≤ ~40 dòng.

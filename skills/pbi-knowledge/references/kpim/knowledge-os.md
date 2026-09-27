---
title: Knowledge OS — cấu trúc Knowledge Dir, luồng 8 lệnh, chuẩn file tri thức, luật riêng tư
source: Agent Data Studio practice
updated: 2026-09-17
---

# Knowledge OS

**Nguyên tắc:** phần source được Git theo dõi luôn sạch. Tri thức làm việc nằm trong trạm dữ liệu:
`workspace/` bị Git bỏ qua cho basic, hoặc thư mục `ADS_DATA` ngoài repo do người dùng chọn.

## 1. Luồng chuẩn (= 8 lệnh `/pbi-*`; host không có slash-command làm theo bảng)

| Lệnh | Khi nào | Agent làm gì |
|---|---|---|
| `/pbi-help` | Chưa rõ dùng gì / vừa cài xong | `knowledge_status` + `list_templates` → báo trạng thái thật → bản đồ 9 skill → định tuyến |
| `/pbi-setup` | Lần đầu, hoặc `knowledge_status` báo chưa setup | Basic: `setup_knowledge()` tại `workspace/`; trạm riêng: xác nhận đường ngoài repo rồi gọi `setup_knowledge(path)` |
| `/pbi-new <tên>` | Bắt đầu dự án | `init_project` → đọc `knowledge/` + `TIMELINE.md` khớp domain **trước khi hỏi user** → skill `data-discovery`; chuỗi ở `workflows/data-to-report.md` |
| `/pbi-scan <path>` | Có `.pbip` / `.Report` cần hồ sơ thiết kế | `distill_report_design` → `projects/<slug>/design/`; kèm `distill_model_schema` nếu model đang mở |
| `/pbi-kit <path>` | Muốn **tái dùng** thiết kế | Chọn trang → `distill_template(sanitize=True)` từng trang, `out_dir` riêng → gom bộ + theme + README |
| `/pbi-done` | Kết thúc dự án | Checklist 4 artifact + design/ + schema → đề xuất kit → `log_timeline` → `/pbi-pack` |
| `/pbi-pack [dự án]` | Sau `/pbi-done` hoặc định kỳ | Agent **`pbi-knowledge-curator`**: rút bài học tái dùng → 4 trục → dedup → INDEX + TIMELINE |
| `/pbi-recall [từ khoá]` | "Đã từng làm gì tương tự?" | `INDEX.md` → `TIMELINE.md` → grep `knowledge/` + `projects/*/PROJECT.md` → tóm tắt |

**Trước luồng tri thức: gọi `knowledge_status`.** Nếu chưa có cấu trúc, thiết lập ở trạm mặc định; chỉ hỏi đường dẫn khi trạm riêng chưa rõ hoặc cấu hình xung đột.

## 2. Cấu trúc Knowledge Dir (tool tự dựng)

```
<KNOWLEDGE_DIR>/
  INDEX.md          mục lục — agent đọc ĐẦU TIÊN
  TIMELINE.md       lịch sử append-only: | ngày | dự án | sự kiện | bài học | link |
  projects/<slug>/  1 dự án 1 thư mục: tài liệu dự án + artifacts/ + design/
  knowledge/        tri thức ĐÃ đóng gói: tech-stack/ industry/ business-domain/ powerbi/
  templates/        kit visual riêng CHƯA sanitize (POWERBI_TEMPLATES_DIR trỏ vào đây)
```

Con trỏ tới thư mục dự án là dòng `POWERBI_PROJECT_DIR` trong `<trạm>/config.env` (không chứa credential).
Không có con trỏ thì engine dùng chính trạm đã chọn. Thư mục người dùng chọn là gốc, không tự thêm cấp con.

## 3. Luật riêng tư (CỨNG)
1. `config.env`, binding và toàn bộ dữ liệu trong trạm **không bao giờ commit** vào phần source; `workspace/` phải bị Git bỏ qua.
2. Chỉ đưa kit vào bản công khai khi người dùng chủ động yêu cầu, có quyền phân phối từng tài sản, dùng `sanitize=True` và tự kiểm lại kết quả.
3. Basic dùng `workspace/` sẵn có; trạm ngoài dùng `ADS_DATA`. Không gợi ý commit cấu hình trạm.
4. Schema model, audit, kit riêng: chỉ ở trạm dữ liệu, không ở thư mục đồng bộ công khai.

## 4. Chuẩn một file tri thức trong `knowledge/`

```markdown
# <tên bài học ngắn>
> Nguồn: projects/<slug> · <ngày> · trục: <tech-stack|industry|business-domain|powerbi>

<sự thật/bài học 2–5 câu>

**Vì sao:** <vì sao đúng/đáng nhớ — bằng chứng từ dự án>
**Cách áp dụng:** <lần sau gặp tình huống X thì làm Y>
Liên quan: [<dự án>](../../projects/<slug>/PROJECT.md) · <link kit/file khác>
```

Ngưỡng cao: chỉ bài học **tái dùng**; không lưu thứ tra lại được từ tài liệu dự án, chi tiết một lần, số liệu cụ thể.
Dedup trước khi ghi — trùng chủ đề thì cập nhật file cũ. Mỗi file ≤ ~40 dòng.

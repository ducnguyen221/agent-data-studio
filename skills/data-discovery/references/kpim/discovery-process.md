---
title: Quy trình khảo sát KPIM — Research → Key Information → Planning (→ Implementation → Monitoring)
source: KPIM practice — gộp skill kpim-analysis (repo, bản mindmap HTML) + kpim-analysis (OpcOS data-bi, description router) + 5 pha của pbi-project-delivery
updated: 2026-09-17
---

# Quy trình khảo sát & tài liệu hoá dữ liệu (KPIM)

Nguyên tắc: **Chuẩn hoá trước — Tự động hoá sau — Phân tích sau cùng.** Không gắn với công cụ BI: làm được
khi chưa có Power BI; bàn giao cho `pbi-model` (có Power BI) hoặc `data-mockup` (chưa có dữ liệu).

Mọi đầu ra ghi vào `projects/<slug>/` của Knowledge Dir (skill `pbi-knowledge`), **không** vào repo.

## Pha −1 — KHỞI TẠO
- `knowledge_status` → `init_project(<tên>)` (hoặc `/pbi-new`).
- Đọc `INDEX.md`, `TIMELINE.md`, `knowledge/` khớp domain → tóm tắt kinh nghiệm cũ **trước khi** hỏi user.

## Pha 0 — RESEARCH (đọc – hiểu – hỏi ngược)
1. Đọc mọi tài liệu + bộ dữ liệu (schema, mẫu, nguồn) → `RESEARCH_NOTES.md` (tổng quan tài liệu, dữ liệu, domain).
2. Suy luận + tra cứu bổ sung (tài liệu chính thức, kiến thức domain) → chuẩn bị tư vấn.
3. **Hỏi ngược user** theo lô (tối đa ~3 vòng): mỗi câu kèm phương án + khuyến nghị; user không biết thì tự
   quyết theo mặc định ngành và ghi **Giả định**. Bộ câu hỏi bám 5 thành phần ở Pha 1 + câu hỏi PII.
- ✅ Cổng: có `RESEARCH_NOTES.md` + user đã trả lời (hoặc xác nhận giả định).

## Pha 1 — KEY INFORMATION (5 thành phần cốt lõi)

| Thành phần | Câu hỏi phải trả lời | Tài liệu |
|---|---|---|
| Requirements & Objectives | Báo cáo phục vụ ai, quyết định gì? | `PROJECT.md` §1 |
| Analytics Questions | Câu hỏi phân tích cụ thể nào phải trả lời được? | `PROJECT.md` §2 |
| Data Required | Nguồn nào, bảng nào, grain nào, tần suất? | `DATA_DICTIONARY.md` |
| Metrics & Dimensions | Chỉ số tính thế nào, cắt theo chiều nào? | `METRICS_CALCULATION.md` · `DOMAIN_DIMENSION.md` |
| Result & Delivery | Báo cáo/trang nào, ai nhận, khi nào? | `REPORTS.md` |

Đầu ra:
- `PROJECT.md` — mỗi thành phần 1 bảng chuẩn hoá + khối ` ```mermaid mindmap `.
- **6 mindmap HTML** (`mindmaps/`): key_objectives, key_questions, key_data_dictionary, key_measures, key_dimensions,
  key_reports. **Nguồn là khối mermaid trong file `.md`**; script `generate_mindmap_html.py` chỉ sinh bản xem HTML
  tự chứa (không graphviz, không mạng). Sửa mindmap = sửa `.md` rồi chạy lại script.
- `DATA_DICTIONARY.md`, `METRICS_CALCULATION.md`, `DOMAIN_DIMENSION.md`, `REPORTS.md`.
- `PROJECT.docx` — proposal Word sinh từ `PROJECT.md` (python-docx), khi user cần.
- ✅ Cổng: PROJECT.md đủ 5 bảng + 6 mindmap (+ Word nếu cần); user duyệt.

## Pha 2 — PLANNING
- `Project_Management.xlsx` ≥ 6 sheet: KEY INFORMATION · PLANNING · DATA DICTIONARY · METRICS_CALCULATION ·
  DOMAIN_DIMENSION · REPORT — sinh bằng `generate_project_management_xlsx.py` (openpyxl).
- Sheet PLANNING = task 2 cấp (Giai đoạn → task con): Khảo sát → Xác nhận nguồn & kiến trúc → Kết nối / làm sạch /
  load → DAX measure → Thiết kế báo cáo.
- Báo cáo phân cấp **Report Group → Report (file) → Report Page**.
- ✅ Cổng: Excel có PLANNING + user duyệt.

## Pha 3 — IMPLEMENTATION (bàn giao, không làm ở skill này)
- Có Power BI + dữ liệu → `pbi-model` (rồi `pbi-analysis` → `pbi-design` → `pbi-build`); trọn gói theo
  `workflows/data-to-report.md`.
- Chưa có dữ liệu → `data-mockup` sinh bộ mẫu từ chính `DATA_DICTIONARY` / `METRICS_CALCULATION`.
- Cập nhật song song `DATA_DICTIONARY` / `METRICS_CALCULATION` / `DOMAIN_DIMENSION` / `REPORTS` + `DESIGN.md` / `theme.json`.
- ✅ Cổng: từng báo cáo pass nghiệm thu số liệu + hiển thị.

## Pha 4 — MONITORING
Tiến độ, bàn giao, cảnh báo, đào tạo, mở rộng — ghi mốc bằng `log_timeline`; đóng dự án bằng `/pbi-done`.

## Bộ mẫu tài liệu — `templates/documents/` ở gốc repo
`PROJECT.md` · `RESEARCH_NOTES.md` · `DATA_DICTIONARY.md` · `METRICS_CALCULATION.md` · `DOMAIN_DIMENSION.md` ·
`REPORTS.md` · `DESIGN.md` + `theme.json` (theme Power BI import chạy ngay) · `Project_Management.xlsx` (6 sheet) ·
`mindmaps/*.html`. Đây là **worked example trên bộ bán lẻ "KPIM Mart"** — nhân bản sang `projects/<slug>/` rồi
thay nội dung; không sửa bản mẫu trong repo cho dự án cụ thể.

Yêu cầu: `pip install openpyxl python-docx` (xlsx, docx). Mindmap HTML chỉ cần thư viện chuẩn Python.

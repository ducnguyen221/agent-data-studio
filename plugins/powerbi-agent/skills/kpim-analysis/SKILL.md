---
name: kpim-analysis
description: >
  Quy trình phân tích KPIM để AI Agent triển khai một dự án báo cáo Power BI trọn vẹn từ
  một bộ dữ liệu + tài liệu đầu vào — tự khảo sát, hỏi ngược người dùng, dựng tài liệu nghiệp
  vụ chuẩn hóa (5 mindmap + bảng), lập kế hoạch (Excel), rồi bàn giao cho powerbi-pipeline thực thi.
  Kích hoạt khi user: "phân tích bộ dữ liệu này thành báo cáo", "triển khai báo cáo Power BI từ
  đầu", "làm dự án Power BI", "khảo sát dữ liệu để làm dashboard", "tài liệu hóa & chuẩn hóa dữ
  liệu để xây báo cáo", hoặc cung cấp 1 dataset mẫu cần biến thành hệ thống báo cáo.
license: MIT — process & templates by Duc Nguyen (ducnguyen221)
---

# kpim-analysis — Quy trình phân tích KPIM (Research → Key Information → Planning → Implementation → Monitoring)

Bộ quy trình + template biến AI Agent thành **chuyên gia phân tích dữ liệu KPIM**: nhận dữ liệu → tài liệu hóa nghiệp vụ → chuẩn hóa → tự động hóa việc xây báo cáo Power BI. Kết hợp với skill [`../powerbi-pipeline/SKILL.md`](../powerbi-pipeline/SKILL.md) (thực thi kỹ thuật 9 khâu) và hướng dẫn tool [`../powerbi-mcp/SKILL.md`](../powerbi-mcp/SKILL.md) (11 tool MCP + policy an toàn dữ liệu).

## 5 pha (làm theo THỨ TỰ, mỗi pha có cổng kiểm)

### Pha -1 — KHỞI TẠO (Knowledge OS)
0. Gọi tool `knowledge_status` → `init_project(<tên dự án>)` — MỌI output của quy trình này ghi vào
   `projects/<slug>/` trong Knowledge Dir. Đọc `knowledge/` khớp domain + `TIMELINE.md` để NẠP KINH
   NGHIỆM CŨ trước khi hỏi user (luồng: [`../powerbi-knowledge/SKILL.md`](../powerbi-knowledge/SKILL.md)).

### Pha 0 — RESEARCH (Đọc – Hiểu – Hỏi ngược)
1. Đọc mọi tài liệu + bộ dữ liệu (schema, sample, nguồn) → ghi `RESEARCH_NOTES.md` (tổng quan tài liệu + dữ liệu + domain).
2. Suy luận + research bổ sung (internet, Microsoft Learn, domain) → chuẩn bị tư vấn.
3. **Hỏi ngược user** một bộ câu hỏi khảo sát (bám khung sheet KHẢO SÁT) để chốt điểm mấu chốt + xin ngữ cảnh còn thiếu.
- ✅ Cổng kiểm: có `RESEARCH_NOTES.md` + user đã trả lời (hoặc xác nhận giả định).

### Pha 1 — KEY INFORMATION (5 thành phần cốt lõi)
Requirements · Analytics Questions · Data Required · Metrics & Dimensions · Result & Delivery.
**Đầu ra:**
- `PROJECT.md` — mỗi thành phần 1 bảng chuẩn hóa + mindmap mermaid.
- **5 mindmap ảnh** (`document-templates/mindmaps/`): key_objectives, key_questions, key_data_dictionary, key_analysis, key_report → sinh bằng `scripts/generate_mindmaps.py` (graphviz, font "DejaVu Sans" render tiếng Việt; render vào ./out rồi copy).
- File chi tiết: `DATA_DICTIONARY.md`, `METRICS_CALCULATION.md`, `DOMAIN_DIMENSION.md`, `REPORTS.md`.
- `PROJECT.docx` — Word proposal (từ `PROJECT.md` + gộp 5 mindmap; dùng python-docx).
- ✅ Cổng kiểm: PROJECT.md đủ 5 bảng + 5 mindmap + Word; user duyệt.

### Pha 2 — PLANNING
`Project_Management.xlsx` (≥6 sheet: KEY INFORMATION, PLANNING, DATA DICTIONARY, METRICS_CALCULATION, DOMAIN_DIMENSION, REPORT) — sinh bằng `scripts/generate_project_management_xlsx.py`. Sheet PLANNING = task 2 cấp (Giai đoạn → task con): Khảo sát → Xác nhận nguồn & kiến trúc → Kết nối/làm sạch/load → DAX Measure → Thiết kế báo cáo.
Báo cáo phân cấp **Report Group → Report (file .pbix) → Report Page**.
- ✅ Cổng kiểm: Excel có PLANNING + user duyệt.

### Pha 3 — IMPLEMENTATION
Bàn giao cho **`powerbi-pipeline` 9 khâu** (Power Query → M → star schema + Date Table → DAX → truy vấn tổng hợp → visual từ template → nâng cao → đóng dự án) + `references/` (DAX/M/SQL). Cập nhật `DATA_DICTIONARY`/`METRICS_CALCULATION`/`DOMAIN_DIMENSION`/`REPORTS` + `DESIGN.md`/`theme.json` song song.
- ✅ Cổng kiểm: từng báo cáo pass UAT số liệu + hiển thị (user nghiệm thu Desktop).

### Pha 4 — MONITORING
Tiến độ, bàn giao, cảnh báo, đào tạo, mở rộng.

## Bộ mẫu tài liệu (thư mục `document-templates/`)
`PROJECT.md` · `RESEARCH_NOTES.md` · `DATA_DICTIONARY.md` · `METRICS_CALCULATION.md` · `DOMAIN_DIMENSION.md` · `REPORTS.md` · `DESIGN.md` + `theme.json` (theme Power BI import chạy ngay) · `Project_Management.xlsx` (6 sheet) · `mindmaps/*.png`. **Đây là worked-example trên dataset bán lẻ "KPIM Mart"** — agent nhân bản & thay nội dung cho dự án mới.

## Scripts (`scripts/`)
- `generate_mindmaps.py` — sinh 4 mindmap PNG (graphviz).
- `generate_data_dictionary_img.py` — sinh ảnh bảng data dictionary (matplotlib).
- `generate_project_management_xlsx.py` — sinh Excel 6 sheet (openpyxl).
Yêu cầu: `pip install graphviz matplotlib openpyxl python-docx` + `graphviz` (apt/`dot`).

## Nguyên tắc KPIM
Chuẩn hóa trước — Tự động hóa sau — Phân tích sau cùng · Data model dùng chung theo chủ đề · clone-and-rebind báo cáo (không dựng layout từ 0) · dữ liệu thô ở lại engine (policy).

---
*Quy trình, công cụ & kỹ thuật do **Duc Nguyen (ducnguyen221)** xây dựng để AI Agent làm phân tích dữ liệu như chuyên gia. MIT License.*

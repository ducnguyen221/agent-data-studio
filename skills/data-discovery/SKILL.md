---
name: data-discovery
description: "Business and data discovery before any BI tool: read the documents and dataset, interview the user back with options and recommendations, and produce the KPIM standard project documents (RESEARCH_NOTES, PROJECT.md with 5 key tables, 6 mindmaps, DATA_DICTIONARY, METRICS_CALCULATION, DOMAIN_DIMENSION, REPORTS) plus a planning workbook (Project_Management.xlsx). Works without Power BI. Use when: survey a dataset, turn a dataset into a reporting plan, document business requirements, define metrics and dimensions, plan reports, start an analytics project. Not: no data yet and a sample dataset is needed -> data-mockup; Power Query, model or DAX -> pbi-model; querying a model -> pbi-analysis; saving or recalling project knowledge -> pbi-knowledge."
metadata:
  group: data
  chain_position: 1
  status: stable
  sources:
    - "kpim: repo skill kpim-analysis (body, document templates, HTML mindmap and xlsx generators)"
    - "kpim: OpcOS data-bi skill kpim-analysis (router description)"
    - "kpim: OpcOS kpim-skills pbi-project-delivery phases 1-3"
---

# data-discovery — khảo sát, tài liệu hoá, lập kế hoạch

## Mục đích
Nhận dữ liệu + tài liệu → hiểu nghiệp vụ → hỏi ngược cho đủ → **tài liệu chuẩn hoá** và **kế hoạch** mà mọi bước
sau dựa vào. Không cần Power BI.

## Trước / Sau trong chuỗi

| | Skill | Khi nào |
|---|---|---|
| Trước | [`pbi-knowledge`](../pbi-knowledge/SKILL.md) | `/pbi-new`: mở dự án, nạp kinh nghiệm cũ |
| Sau (có dữ liệu + Power BI) | [`pbi-model`](../pbi-model/SKILL.md) | PROJECT.md + PLANNING đã duyệt |
| Sau (chưa có dữ liệu) | [`data-mockup`](../data-mockup/SKILL.md) | Cần bộ dữ liệu mẫu theo dictionary |

Trọn gói: `workflows/data-to-report.md` (gốc repo).

## Must / Prefer / Avoid
- **Must** — làm theo **thứ tự pha**, mỗi pha có cổng; không sang pha sau khi user chưa duyệt.
- **Must** — đọc kinh nghiệm cũ trong Knowledge Dir **trước khi** hỏi user.
- **Must** — hỏi ngược có phương án + khuyến nghị; điều user không biết → tự quyết theo mặc định ngành và ghi **Giả định**.
- **Must** — hỏi cột nhạy cảm (PII) ngay từ đầu; ghi vào tài liệu để `pbi-analysis` khai `policy.json`.
- **Must** — mọi đầu ra ghi vào `projects/<slug>/` của Knowledge Dir, không vào repo.
- **Prefer** — nhân bản bộ mẫu `templates/documents/` (gốc repo) rồi thay nội dung, thay vì viết từ trắng.
- **Prefer** — mindmap nguồn là khối mermaid trong `.md`; HTML chỉ là bản xem sinh lại.
- **Avoid** — phỏng vấn thụ động ("bạn cần gì?"); hỏi rời rạc từng câu nhiều vòng.
- **Avoid** — nhảy vào model/DAX khi chưa có Analytics Questions và Metrics được duyệt.
- **Avoid** — sửa tay mindmap HTML hoặc sửa bộ mẫu trong repo cho một dự án cụ thể.

## Quy trình

| Pha | Việc | Đọc | Cổng kiểm |
|---|---|---|---|
| −1 Khởi tạo | `knowledge_status` → `init_project` → recall | [discovery-process](references/kpim/discovery-process.md) §−1 | Có `projects/<slug>/` + tóm tắt kinh nghiệm cũ |
| 0 Research | Đọc tài liệu + dữ liệu → `RESEARCH_NOTES.md` → hỏi ngược theo lô | §0 · mẫu `templates/documents/RESEARCH_NOTES.md` | User trả lời / xác nhận giả định |
| 1 Key Information | `PROJECT.md` (5 bảng + mermaid) → 6 mindmap HTML → dictionary, metrics, dimension, reports | §1 · mẫu `templates/documents/PROJECT.md` … | PROJECT.md đủ 5 bảng + 6 mindmap; user duyệt |
| 2 Planning | `Project_Management.xlsx` ≥ 6 sheet, task 2 cấp, Report Group → Report → Page | §2 | Excel có PLANNING; user duyệt |
| 3 Bàn giao | Có dữ liệu → [`pbi-model`](../pbi-model/SKILL.md); chưa có → [`data-mockup`](../data-mockup/SKILL.md) | §3 | Tài liệu đủ để bước sau không phải hỏi lại |
| 4 Monitoring | Tiến độ, cảnh báo, đào tạo; `log_timeline` | §4 | Mốc ghi trong TIMELINE |

## Scripts — `scripts/`

| Script | Làm gì | Chạy |
|---|---|---|
| `generate_mindmap_html.py` | Sinh 6 bản xem HTML tự chứa từ khối mermaid trong các `.md` của bộ mẫu `templates/documents/` | `python scripts/generate_mindmap_html.py` (hoặc tên 1 file `.md`); cho dự án: chép script cạnh bộ tài liệu dự án và chỉnh `DOCS` |
| `generate_project_management_xlsx.py` | Sinh `Project_Management.xlsx` 6 sheet (worked example KPIM Mart) | `pip install openpyxl` rồi chạy trong thư mục dự án; thay nội dung theo dự án |

## Bộ mẫu tài liệu — `templates/documents/` ở gốc repo
`PROJECT.md` · `RESEARCH_NOTES.md` · `DATA_DICTIONARY.md` · `METRICS_CALCULATION.md` · `DOMAIN_DIMENSION.md` ·
`REPORTS.md` · `DESIGN.md` · `theme.json` · `Project_Management.xlsx` · `mindmaps/*.html` — worked example "KPIM Mart".

## References — `references/kpim/`

| File | Đọc khi |
|---|---|
| [discovery-process.md](references/kpim/discovery-process.md) | Mọi pha — chi tiết từng pha, 5 thành phần Key Information, đầu ra, cổng kiểm, bộ mẫu |

Microsoft `powerbi-report-planning` (phần requirements) chưa chép vào studio; khi có sẽ nằm ở skill này.

---
*Quy trình, công cụ & mẫu tài liệu: KPIM practice (Duc Nguyen), MIT.*

---
name: pbi-analysis
description: "Query and explore Power BI data safely: run aggregate DAX against Power BI Desktop or Service through the studio engine, discover tables/columns/measures, check numbers before design, choose the lightest tool tier (CLI, skill, studio MCP, Microsoft Modeling MCP), and respect the aggregate-only, PII and audit policy. Use when: list open reports, run a DAX query, inspect model metadata with INFO functions, answer a data question from a model, ADOMD connection errors, decide which Power BI tool to call. Not: business discovery and project documents -> data-discovery; creating or fixing measures, relationships, Power Query -> pbi-model; page layout -> pbi-design / pbi-build; formal review of SQL/DAX/model -> pbi-review."
metadata:
  group: powerbi
  chain_position: 3
  status: stable
  sources:
    - "kpim: repo skill powerbi-mcp (16 tools + policy)"
    - "kpim: OpcOS data-bi skill powerbi-mcp + references/operations.md"
---

# pbi-analysis — truy vấn & khai thác dữ liệu an toàn

## Mục đích
Lấy số và cấu trúc thật từ model mà **dữ liệu thô không rời engine**: truy vấn tổng hợp mặc định,
PII bị chặn, mọi truy vấn có audit. Chọn đúng tầng công cụ để không đốt context.

## Trước / Sau trong chuỗi

| | Skill | Khi nào |
|---|---|---|
| Trước | [`pbi-model`](../pbi-model/SKILL.md) | Model đã chốt, measure đã kiểm |
| Sau | [`pbi-design`](../pbi-design/SKILL.md) | Số đã soát → thiết kế trang |
| Liên quan | [`pbi-review`](../pbi-review/SKILL.md) · [`pbi-knowledge`](../pbi-knowledge/SKILL.md) | Số không khớp → review · distill schema vào dự án |

## Must / Prefer / Avoid
- **Must** — gọi `list_local_reports` trước khi truy vấn Desktop; nhiều instance → hỏi user chọn.
- **Must** — mọi truy vấn đi qua `execute_dax_*` (có policy + audit). Không chạy DAX bằng script trần.
- **Must** — hỏi user cột nhạy cảm (PII) **đầu dự án** → ghi `policy.json` trước khi chạm dữ liệu.
- **Must** — read-only mặc định: không refresh/process/XMLA ghi trừ khi user yêu cầu rõ và xác nhận lại.
- **Prefer** — `SUMMARIZECOLUMNS` / `TOPN` / measure thay cho `EVALUATE` cả bảng.
- **Prefer** — metadata bằng `INFO.TABLES()` / `INFO.COLUMNS()` / `INFO.MEASURES()`; engine cũ mới lùi về DMV `$SYSTEM.TMSCHEMA_*`.
- **Prefer** — tầng nhẹ nhất đủ dùng (T0 CLI → T1 skill → T2 MCP studio → T3 Modeling MCP).
- **Avoid** — `max_rows=0` khi user chưa được cảnh báo; kéo bảng fact lớn chỉ để đếm/tổng.
- **Avoid** — tắt `POWERBI_AGGREGATE_ONLY` để "cho nhanh"; đó là quyết định của user, có ghi lại.
- **Avoid** — mở `.env`, `secrets.env`, `policy.json` để đọc bằng agent — engine tự đọc.

## Quy trình

| # | Bước | Đọc | Cổng kiểm |
|---|---|---|---|
| 1 | Xác định nguồn: Desktop (`list_local_reports`) hay Service (`dataset_id`) | [mcp-tools](references/kpim/mcp-tools.md) | Đúng port + `model_id` / dataset; user xác nhận khi có nhiều |
| 2 | Khám phá: `list_tables` → `describe_table`, hoặc `INFO.*` | [operations](references/kpim/operations.md) | Biết bảng fact/dim, measure sẵn có; bỏ `LocalDateTable_*` |
| 3 | Chính sách: hỏi cột PII → `policy.json`; nhắc aggregate-only | [mcp-tools](references/kpim/mcp-tools.md) §an toàn | User đã trả lời (hoặc xác nhận không có PII) |
| 4 | Truy vấn tổng hợp: viết DAX theo grain của câu hỏi | [operations](references/kpim/operations.md) | Bảng Markdown; audit không có verdict `blocked` bất thường |
| 5 | Soát số trước thiết kế: đối chiếu 1–2 con số biết trước với `METRICS_CALCULATION` | — | Khớp → [`pbi-design`](../pbi-design/SKILL.md); lệch → [`pbi-review`](../pbi-review/SKILL.md) hoặc quay lại [`pbi-model`](../pbi-model/SKILL.md) |
| 6 | (Tuỳ chọn) `distill_model_schema` vào `projects/<slug>/` của Knowledge Dir | [mcp-tools](references/kpim/mcp-tools.md) | Blueprint + ERD nằm NGOÀI repo |

Truy vấn bị chặn → viết lại theo gợi ý của engine, **không** tìm cách lách (vd `TOPN` cực lớn).

## Định dạng kết quả
Bảng Markdown chuẩn, giữ đúng tiếng Việt/Unicode; nói rõ khi kết quả bị siết trần dòng. Lỗi ADOMD
(`FileNotFoundException`) → hướng dẫn cài *Analysis Services client libraries* hoặc đặt `ADOMD_LIB_DIR`;
kiểm Desktop đã mở file chưa.

## References — `references/kpim/`

| File | Đọc khi |
|---|---|
| [mcp-tools.md](references/kpim/mcp-tools.md) | Chọn tool, tham số, policy, phân vai với Modeling MCP, tầng T0–T3 |
| [operations.md](references/kpim/operations.md) | Luồng theo tình huống (liệt kê, truy vấn, metadata `INFO.*` + DMV), định dạng output, lỗi ADOMD |

Tra cứu Microsoft liên quan nằm ở skill chủ, đọc theo tên: `metadata-discovery.md`, `dax-guidelines.md`,
`dax-perf-decision-guide.md` trong [`pbi-model`](../pbi-model/SKILL.md) → `references/microsoft/`.

---
*Nguồn: KPIM practice (engine studio 16 tool + chính sách an toàn dữ liệu).*

---
title: Sổ tay 16 tool của engine studio (bridge Power BI) + phân vai với Modeling MCP của Microsoft
skill: pbi-analysis
source: KPIM practice — gộp bản skill powerbi-mcp (repo) và bản vận hành (OpcOS data-bi)
updated: 2026-09-17
---

# 16 tool của engine studio

Engine chạy từ gói đã cài (`$ADS_DATA/.venv`), bật MCP **theo nhu cầu**. Mặc định làm việc tiết kiệm
context: chỉ gọi tool khi cần số liệu/cấu trúc thật.

| Nhóm | Tool | Chức năng | Ghi chú |
|---|---|---|---|
| Khám phá | `list_local_reports()` | Liệt kê Power BI Desktop đang mở: port + `model_id` (catalog) | Gọi **đầu tiên**; nhiều instance → hỏi user chọn, không đoán |
| | `list_tables(port, model_id)` | Bảng trong model | |
| | `describe_table(port, model_id, table_name)` | Cột + kiểu + measure + biểu thức | Kiểm field tồn tại trước khi bind visual |
| Truy vấn 🛡️ | `execute_dax_local(port, model_id, dax_query, max_rows=1000)` | DAX lên Desktop | **Luôn qua policy** |
| | `execute_dax_service(dataset_id, dax_query, max_rows=1000)` | DAX lên Power BI Service qua REST | Cần app Entra ID; secret đọc từ `ADS_SECRETS_FILE`, agent không đọc |
| Ghi model | `add_measure_local(...)` | Tạo/sửa 1 measure qua TOM | Chỉ để **thử** — TOM không làm file dirty (xem `pbi-model`) |
| | `add_relationship_local(...)` | Tạo quan hệ Many→One qua TOM | Lẻ 1–2 cái; bulk → Modeling MCP |
| Template | `list_templates()` | Kit có sẵn (`report-templates/` + `POWERBI_TEMPLATES_DIR`) | |
| | `apply_template(report_path, kit_dir, page_spec)` | Dựng trang mới từ kit (clone-and-rebind) | File `.pbip` phải **đóng**; luật ở `pbi-design` / `pbi-build` |
| | `distill_template(report_path, page, out_dir, kit_name?, sanitize=True)` | Trang đẹp → kit tái dùng | `out_dir` khác nhau cho từng trang |
| Distill | `distill_model_schema(port?, model_id?, output_filename?, output_dir?)` | Model → blueprint Markdown + ERD Mermaid | Schema có thể nhạy cảm — không ghi vào repo/thư mục đồng bộ công khai |
| | `distill_report_design(report_path, project?, out_dir?)` | Quét trọn báo cáo: mọi trang + theme + DESIGN.md + REPORT_CATALOG.md | Mặc định vào Knowledge Dir |
| Knowledge OS | `knowledge_status()` | Trạng thái Knowledge Dir | Gọi trước mọi quy trình tri thức |
| | `setup_knowledge(path)` · `init_project(name)` · `log_timeline(project, event, lesson?, link?)` | Thiết lập · mở dự án · ghi mốc | Luồng: skill `pbi-knowledge` |

## Chính sách an toàn dữ liệu (engine cưỡng chế, không phải lời nhắc)

| Luật | Hành vi | Cấu hình |
|---|---|---|
| Aggregate-only (mặc định BẬT) | `EVALUATE 'Bảng'` / `EVALUATE ALL(...)` bị từ chối kèm gợi ý viết lại | Tắt có chủ đích: `POWERBI_AGGREGATE_ONLY=0` |
| PII blocklist | Cột khai trong `policy.json` bị cấm project | `POWERBI_POLICY_FILE`; hỏi user cột nhạy cảm **đầu dự án** |
| Trần dòng | Kết quả có cột dimension siết còn 200 dòng (thuần measure thì không) | `POWERBI_DIMENSION_ROW_CAP` |
| Audit | Mọi truy vấn ghi JSONL (verdict + số dòng, không lưu dữ liệu) | `POWERBI_AUDIT_DIR`; mặc định thư mục dữ liệu, không bao giờ trong repo |

Trung thực về giới hạn: đây là lớp chặn rò **vô ý**; bảo mật cứng là RLS + service principal quyền tối thiểu.

## Phân vai với Modeling MCP của Microsoft (`@microsoft/powerbi-modeling-mcp`, EULA preview — không phân phối)

| Việc | Dùng |
|---|---|
| Truy vấn/tổng hợp DAX, khám phá schema, đọc báo cáo đang mở | Engine studio |
| Tạo/sửa hàng loạt measure, cột, quan hệ, bảng; refactor; TMDL; validate DAX | Modeling MCP (bật on-demand) |
| Trang báo cáo / visual (PBIR) | Engine studio (template/clone) + CLI `powerbi-report-author` — Modeling MCP không làm report layer |

Không interleave thao tác GHI từ hai server lên cùng một model: xong `SaveChanges` bên này rồi mới quay lại bên kia.

## Tầng thực thi — chọn cái nhẹ nhất đủ dùng

| Tầng | Công cụ | Khi nào |
|---|---|---|
| T0 | CLI (`powerbi-desktop`, `powerbi-report-author` của Microsoft; CLI engine khi có) | Mặc định cho thao tác đơn: status, validate, screenshot |
| T1 | Skill (đọc quy trình, không gọi gì) | Quyết định có nhánh, cần luật |
| T2 | MCP engine studio | Cần phiên truy vấn có policy, template, distill, Knowledge OS |
| T3 | Modeling MCP của Microsoft | Chỉ khi ghi model hàng loạt |

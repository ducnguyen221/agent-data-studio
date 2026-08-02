---
name: powerbi-mcp
description: Kết nối và tương tác trực tiếp với Power BI Desktop (Local) và Power BI Service (Cloud) qua MCP Server.
---
# powerbi-mcp

Kỹ năng này cho phép Trợ lý AI tự động nhận diện và sử dụng các công cụ MCP để kết nối, truy vấn dữ liệu từ mô hình Power BI Desktop cục bộ hoặc Power BI Service trên đám mây bằng ngôn ngữ DAX và DMV, thay vì yêu cầu người dùng chạy các script thủ công.

## Các Công cụ Khả dụng (MCP Tools)

Khi kỹ năng này được kích hoạt thông qua cấu hình MCP Server, các công cụ sau sẽ sẵn sàng để sử dụng:

1. `list_local_reports()`
   - **Mô tả:** Quét hệ thống Windows và liệt kê toàn bộ các file báo cáo Power BI Desktop (`.pbix`) đang mở kèm theo cổng (port) kết nối cục bộ và tên Database Model (Catalog).
   - **Cách dùng:** Gọi công cụ này trước tiên để lấy thông tin cổng và mã model khi làm việc với báo cáo cục bộ.

2. `execute_dax_local(port: str, model_id: str, dax_query: str, max_rows: int = 1000)`
   - **Mô tả:** Chạy truy vấn DAX trực tiếp lên file Power BI Desktop đang mở qua cổng kết nối cục bộ.
   - **Cách dùng:** Truyền vào cổng kết nối và model_id lấy từ `list_local_reports`, cùng câu lệnh DAX (ví dụ: `EVALUATE TableName`).
   - **`max_rows`:** Mặc định cắt còn 1000 dòng để tránh tràn context. Đặt `0` chỉ khi user thực sự cần toàn bộ dữ liệu.

3. `execute_dax_service(dataset_id: str, dax_query: str, max_rows: int = 1000)`
   - **Mô tả:** Chạy truy vấn DAX lên Power BI Service Cloud thông qua Microsoft REST API (yêu cầu cấu hình Azure Entra ID App).
   - **Cách dùng:** Truyền vào GUID Dataset ID và câu lệnh DAX cần truy vấn.
   - **`max_rows`:** Tương tự, mặc định 1000 dòng.

4. `distill_model_schema(port?, model_id?, output_filename?, output_dir?)`
   - **Mô tả:** Chưng cất cấu trúc model (bảng/cột/measure/relationship) thành Markdown blueprint kèm Mermaid ERD — để Agent tham chiếu khi viết DAX/thiết kế báo cáo.
   - **Đích ghi:** mặc định `~/.powerbi-agent/distilled/` (đổi qua `output_dir` hoặc env `POWERBI_DISTILL_DIR`). ⚠️ Schema model có thể nhạy cảm — KHÔNG ghi vào repo public/thư mục sync chia sẻ.

5. `add_measure_local(port, model_id, table_name, measure_name, expression, format_string?, description?)` — tạo/sửa 1 measure qua TOM (GHI model).
6. `add_relationship_local(port, model_id, from_table, from_column, to_table, to_column, is_active?)` — tạo relationship Many-to-One qua TOM (GHI model).
   - **Cả 5 & 6:** là fallback đơn lẻ. Thao tác modeling hàng loạt/phức tạp (bulk rename, transaction, TMDL, validate) → dùng MCP `powerbi-modeling` của Microsoft (xem Phân vai bên dưới). Sau khi GHI, nhắc user model đã đổi (Desktop thấy ngay, refresh visual nếu cần).

7. `list_tables(port, model_id)` / `describe_table(port, model_id, table_name)` — khám phá schema (bảng, cột + kiểu, measure + expression) không cần thuộc DMV.

8. **Template kit (report layer — PBIR, file .pbip ĐÓNG):**
   - `list_templates()` — kit có sẵn (repo `report-templates/` + env `POWERBI_TEMPLATES_DIR`).
   - `apply_template(report_path, kit_dir, page_spec)` — dựng TRANG MỚI từ kit theo luật clone-and-rebind (giữ style `visualContainerObjects`, chỉ đổi name/position/fields/visualType/title). KHÔNG BAO GIỜ tự dựng layout PBIR từ đầu.
   - `distill_template(report_path, page, out_dir, sanitize?)` — chưng cất trang đẹp thành kit tái dùng; `sanitize=True` TRƯỚC khi chia sẻ/public (xóa tên bảng/cột nghiệp vụ).
9. **Distill & Knowledge OS:**
   - `distill_report_design(report_path, project?, out_dir?)` — quét TRỌN báo cáo: mọi trang + theme + DESIGN.md + REPORT_CATALOG.md (hồ sơ thiết kế toàn dự án, mặc định vào Knowledge Dir).
   - `knowledge_status()` — GỌI ĐẦU TIÊN trước mọi quy trình tri thức; chưa setup thì hỏi user chỉ định folder.
   - `setup_knowledge(path)` / `init_project(name)` / `log_timeline(project, event, lesson?, link?)` — thiết lập Knowledge Dir, mở dự án, ghi timeline. Luồng đầy đủ: [`../pbi-knowledge/SKILL.md`](../pbi-knowledge/SKILL.md).

   - Quy trình dự án trọn gói: pha nghiệp vụ [`../kpim-analysis/SKILL.md`](../kpim-analysis/SKILL.md) → pha kỹ thuật 9 khâu [`../pbi-pipeline/SKILL.md`](../pbi-pipeline/SKILL.md).

## Chính sách an toàn dữ liệu (server enforce — không phải chỉ lời nhắc)

- `aggregate_only` **mặc định BẬT**: `EVALUATE 'Bảng'` / `EVALUATE ALL(...)` bị server TỪ CHỐI kèm hint viết lại (SUMMARIZECOLUMNS/TOPN/measure). Tắt khi user chủ đích: env `POWERBI_AGGREGATE_ONLY=0`.
- **PII blocklist**: `policy.json` cạnh server (hoặc env `POWERBI_POLICY_FILE`) liệt kê cột cấm project. Đầu dự án dữ liệu nhạy cảm → hỏi user và ghi file này.
- **Audit log**: mọi truy vấn ghi `~/.powerbi-agent/audit/*.jsonl` (verdict + số dòng) — dùng chứng minh "không dump dữ liệu thô".
- Kết quả có cột dimension bị siết trần 200 dòng (thuần measure thì không).
- Trung thực: đây là guard chống rò rỉ SƠ Ý — bảo mật cứng vẫn là RLS + service principal quyền tối thiểu.

---

## Nguyên tắc Kích hoạt & Luồng Xử lý của Agent

Trợ lý AI (Antigravity, Claude, Codex) phải tự động áp dụng kỹ năng này khi người dùng đưa ra các yêu cầu sau:

### 1. Khi người dùng muốn xem/kiểm tra các báo cáo đang mở cục bộ:
- **Hành động:** Tự động gọi công cụ `list_local_reports` thông qua kết nối MCP. Không yêu cầu người dùng mở terminal hay chạy file python kiểm thử.
- **Nếu có NHIỀU instance:** liệt kê kèm port + model_id và hỏi user chọn báo cáo nào trước khi truy vấn (đừng tự đoán).

### 2. Khi người dùng muốn truy vấn dữ liệu hoặc viết DAX trên Power BI Desktop:
- **Hành động:**
  1. Nếu chưa biết cổng kết nối, tự động gọi `list_local_reports`.
  2. Dùng cổng và model_id tìm được để gọi `execute_dax_local` với câu lệnh DAX tương ứng.
  3. Trình bày kết quả dữ liệu trả về dưới dạng bảng Markdown hoàn chỉnh và đẹp mắt.

### 3. Khi người dùng muốn kiểm tra cấu trúc bảng hoặc Metadata của Model:
- **Hành động:** Ưu tiên dùng các hàm DAX `INFO.*` (chuẩn cho model Tabular hiện đại của Power BI, trả về bảng sạch qua `EVALUATE`) thông qua `execute_dax_local`:
  - *Danh sách bảng:* `EVALUATE INFO.TABLES()`
  - *Danh sách cột:* `EVALUATE INFO.COLUMNS()`
  - *Danh sách measure + biểu thức:* `EVALUATE SELECTCOLUMNS(INFO.MEASURES(), "Name", [Name], "Expression", [Expression])`
- **Fallback (engine cũ không có `INFO.*`):** dùng DMV Tabular `$SYSTEM.TMSCHEMA_*`:
  - *Bảng:* `SELECT [Name] FROM $SYSTEM.TMSCHEMA_TABLES`
  - *Cột:* `SELECT [ExplicitName], [DataType] FROM $SYSTEM.TMSCHEMA_COLUMNS`
  - *Measure:* `SELECT [Name], [Expression] FROM $SYSTEM.TMSCHEMA_MEASURES`
  - Lưu ý: bỏ qua các bảng hệ thống tên `LocalDateTable_*` / `DateTableTemplate_*`.

---

## Phân vai với `powerbi-modeling` (MCP chính chủ Microsoft — nếu máy có cài)

Hai server chạy song song, KHÔNG giẫm chân:

| Việc | Dùng server |
|---|---|
| Truy vấn/tổng hợp dữ liệu bằng DAX, khám phá schema, đọc báo cáo đang mở | **powerbi-mcp-bridge** (server này) |
| Tạo/sửa measure, calculated column, relationship, table; bulk rename/refactor; TMDL/PBIP; validate DAX | **powerbi-modeling** (`npx @microsoft/powerbi-modeling-mcp`) |
| Trang báo cáo / visual (PBIR) | Server này (roadmap M2) — modeling-mcp KHÔNG làm report layer |

Quy tắc: không interleave thao tác GHI từ 2 server cùng lúc lên 1 model; modeling ops xong (SaveChanges) rồi mới quay lại query.

---

## Nguyên tắc An toàn (Bắt buộc)

- **Read-only mặc định:** chỉ chạy truy vấn đọc (`EVALUATE`, `INFO.*`, `SELECT ... $SYSTEM`). KHÔNG chạy lệnh có thể thay đổi/refresh/process model (XMLA/TMSL) trừ khi user yêu cầu rõ và xác nhận lại.
- **Luôn giới hạn dữ liệu khám phá:** khi chưa biết độ lớn của bảng, bọc truy vấn bằng `TOPN`, ví dụ `EVALUATE TOPN(50, 'Sales')`. Để `max_rows` ở mặc định; chỉ đặt `max_rows=0` khi user thực sự cần kéo toàn bộ và đã được cảnh báo.
- **Không kéo bảng fact lớn không lý do:** nếu chỉ cần tổng/đếm, dùng measure hoặc `SUMMARIZECOLUMNS` thay vì `EVALUATE` cả bảng.

---

## Định dạng Kết quả đầu ra (Output Formatting)

- **Bảng dữ liệu:** Luôn định dạng bảng kết quả trả về dưới dạng bảng Markdown chuẩn. Tránh hiển thị dữ liệu thô dạng JSON hay chuỗi văn bản không định dạng.
- **Xử lý Unicode:** Đảm bảo hiển thị đúng font Tiếng Việt và các ký tự đặc biệt có trong dữ liệu của mô hình Power BI.
- **Thông báo lỗi:** Nếu xảy ra lỗi kết nối ADOMD.NET (do thiếu driver), hãy hướng dẫn người dùng tải thư viện ADOMD.NET từ trang chủ Microsoft hoặc kiểm tra lại xem Power BI Desktop đã được mở chưa.

---

## Hướng dẫn Khắc phục Sự cố nhanh cho Agent

- **Lỗi `System.IO.FileNotFoundException` (Không tìm thấy DLL ADOMD.NET):**
  - Bản MCP Server portable tự động dò ADOMD.NET ở nhiều vị trí (mọi phiên bản SSMS, ADOMD.NET standalone, GAC). Nếu vẫn lỗi, hướng dẫn user trỏ thủ công bằng biến môi trường `ADOMD_LIB_DIR` tới thư mục chứa `Microsoft.AnalysisServices.AdomdClient.dll`, hoặc cài "Analysis Services client libraries" từ trang Microsoft.

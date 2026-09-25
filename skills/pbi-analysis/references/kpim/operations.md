---
title: "pbi-analysis — luồng xử lý, định dạng output, khắc phục sự cố"
skill: pbi-analysis
source: KPIM practice (bản vận hành tool bridge)
updated: 2026-09-17
---

# Nguyên tắc Kích hoạt & Luồng Xử lý của Agent

Agent (Antigravity, Claude, Codex) phải tự động áp dụng kỹ năng này khi người dùng đưa ra các yêu cầu sau:

## 1. Khi người dùng muốn xem/kiểm tra các báo cáo đang mở cục bộ
- **Hành động:** Tự động gọi công cụ `list_local_reports` thông qua kết nối MCP. Không yêu cầu người dùng mở terminal hay chạy file python kiểm thử.
- **Nếu có NHIỀU instance:** liệt kê kèm port + model_id và hỏi user chọn báo cáo nào trước khi truy vấn (đừng tự đoán).

## 2. Khi người dùng muốn truy vấn dữ liệu hoặc viết DAX trên Power BI Desktop
- **Hành động:**
  1. Nếu chưa biết cổng kết nối, tự động gọi `list_local_reports`.
  2. Dùng cổng và model_id tìm được để gọi `execute_dax_local` với câu lệnh DAX tương ứng.
  3. Trình bày kết quả dữ liệu trả về dưới dạng bảng Markdown hoàn chỉnh và đẹp mắt.

## 3. Khi người dùng muốn kiểm tra cấu trúc bảng hoặc Metadata của Model
- **Hành động:** Ưu tiên dùng các hàm DAX `INFO.*` (chuẩn cho model Tabular hiện đại của Power BI, trả về bảng sạch qua `EVALUATE`) thông qua `execute_dax_local`:
  - *Danh sách bảng:* `EVALUATE INFO.TABLES()`
  - *Danh sách cột:* `EVALUATE INFO.COLUMNS()`
  - *Danh sách measure + biểu thức:* `EVALUATE SELECTCOLUMNS(INFO.MEASURES(), "Name", [Name], "Expression", [Expression])`
- **Fallback (engine cũ không có `INFO.*`):** dùng DMV Tabular `$SYSTEM.TMSCHEMA_*`:
  - *Bảng:* `SELECT [Name] FROM $SYSTEM.TMSCHEMA_TABLES`
  - *Cột:* `SELECT [ExplicitName], [DataType] FROM $SYSTEM.TMSCHEMA_COLUMNS`
  - *Measure:* `SELECT [Name], [Expression] FROM $SYSTEM.TMSCHEMA_MEASURES`
  - Lưu ý: bỏ qua các bảng hệ thống tên `LocalDateTable_*` / `DateTableTemplate_*`.

# Định dạng Kết quả đầu ra (Output Formatting)

- **Bảng dữ liệu:** Luôn định dạng bảng kết quả trả về dưới dạng bảng Markdown chuẩn. Tránh hiển thị dữ liệu thô dạng JSON hay chuỗi văn bản không định dạng.
- **Xử lý Unicode:** Đảm bảo hiển thị đúng font Tiếng Việt và các ký tự đặc biệt có trong dữ liệu của mô hình Power BI.
- **Thông báo lỗi:** Nếu xảy ra lỗi kết nối ADOMD.NET (do thiếu driver), hướng dẫn người dùng tải thư viện ADOMD.NET từ trang chủ Microsoft hoặc kiểm tra lại xem Power BI Desktop đã được mở chưa.

# Hướng dẫn Khắc phục Sự cố nhanh cho Agent

- **Lỗi `System.IO.FileNotFoundException` (Không tìm thấy DLL ADOMD.NET):**
  - Bản MCP Server portable tự động dò ADOMD.NET ở nhiều vị trí (mọi phiên bản SSMS, ADOMD.NET standalone, GAC). Nếu vẫn lỗi, hướng dẫn user trỏ thủ công bằng biến môi trường `ADOMD_LIB_DIR` tới thư mục chứa `Microsoft.AnalysisServices.AdomdClient.dll`, hoặc cài "Analysis Services client libraries" từ trang Microsoft.

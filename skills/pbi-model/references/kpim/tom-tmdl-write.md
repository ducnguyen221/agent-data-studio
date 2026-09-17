---
title: Ghi measure / cột tính / quan hệ vào model Power BI — TOM để thử, TMDL để lưu
measured_on: 2026-09-16 · Power BI Desktop 2.157 · Windows · pythonnet + AMO/TOM
source: KPIM practice (chưng cất phần kỹ thuật, bỏ đường máy)
---

# Ghi vào semantic model: TOM để THỬ, TMDL để LƯU

Tầng truy vấn của studio (`execute_dax_*`) chỉ **đọc**. Muốn tạo/sửa measure, cột tính, quan hệ có hai
đường; chọn sai đường là mất việc.

## 1. Quy tắc chọn đường

| Tình huống | Đường đúng | Vì sao |
|---|---|---|
| Thử nhanh công thức trên file đang mở | **TOM** (AMO/TOM qua pythonnet, hoặc tool `add_measure_local`) | Desktop thấy ngay, không cần đóng file |
| Lưu bền vào dự án `.pbip` | **Sửa TMDL khi file ĐÃ ĐÓNG** | TOM **không làm file "dirty"**: user Ctrl+S → Desktop không ghi lại → đóng file là **mất** measure |
| Thao tác hàng loạt, refactor, validate DAX | Modeling MCP của Microsoft (on-demand) hoặc TMDL | Có transaction + validate; xem reference Microsoft `tmdl-guidelines.md` |
| TMSL `createOrReplace` ở mức từng measure qua ADOMD | **Không dùng** | Engine Desktop từ chối ("Unrecognized JSON property: measure") |

## 2. Thủ tục TOM (thử công thức)

1. Lấy `port` + `model_id` (catalog GUID) từ `list_local_reports`.
2. Nạp thư viện: thư mục chứa `Microsoft.AnalysisServices.Tabular.dll` (thường đi kèm SSMS, trong
   `Common7\IDE`) → `clr.AddReference("Microsoft.AnalysisServices.Tabular")`. Engine của studio đã có
   hàm tự dò thư mục này; biến `ADOMD_LIB_DIR` dùng khi dò không ra.
3. `Server().Connect("Data Source=localhost:<port>")` → chọn database có `.ID == model_id` → `db.Model`.
4. Mỗi measure: `Measure()` → đặt `Name`, thêm vào `table.Measures`, rồi `Expression`, `DisplayFolder`,
   `FormatString` (tiền `#,0`, phần trăm `0.0%`).
5. `model.SaveChanges()` **một lần ở cuối** — engine validate cả lô nên thứ tự phụ thuộc giữa các
   measure không quan trọng.
6. Kiểm bằng `EVALUATE ROW("kq", [Measure])`.

Script kiểu này là dùng-một-lần: đặt ở thư mục tạm của hệ điều hành, xoá sau khi chạy.

## 3. Thủ tục TMDL (lưu bền)

1. User **đóng** file `.pbip` trong Desktop.
2. Mở `<Tên>.SemanticModel/definition/tables/<bảng measure>.tmdl`.
3. Chèn khối `measure` **trước dòng `partition`**: thụt lề bằng **tab**, xuống dòng **CRLF**, file
   **UTF-8 không BOM**, `lineageTag` là UUID mới, `formatString` và `displayFolder` đặt tường minh.
4. User mở lại file → kiểm bằng DAX.

## 4. Cột tính, bảng tính, quan hệ qua TOM

- **Calculated column**: `CalculatedColumn()` + `Expression` + `DataType` chỉ tạo metadata → truy vấn báo
  "column does not hold data" cho tới khi `Model.RequestRefresh(RefreshType.Calculate)` + `SaveChanges()`.
- **Bảng tính** (vd `CALENDAR`): sửa `partition.Source.Expression` rồi refresh `Full`.
- Collection TOM duyệt bằng `for x in table.Partitions` / `model.Relationships`, **không** index `[0]`.
- Gỡ quan hệ gây "blank member": `Model.Relationships.Remove(...)`.

## 5. Bẫy dữ liệu gặp khi viết measure

| Bẫy | Dấu hiệu | Cách xử lý |
|---|---|---|
| Tên cột chứa **ký tự vô hình** (zero-width space U+200B) | So khớp tên cột trượt, `describe_table` thấy tên "giống hệt" | Dò cột theo pattern, hoặc chép đúng ký tự ẩn |
| Ngày từ Excel thành **số serial** (45292…) | `DATEDIFF` lỗi, trục thời gian là số | Ép kiểu Date ở Power Query; tạm thời `DATE(1899,12,30) + [serial]` |
| **Blank member** trên slicer ngày | Cột khoá có giá trị rỗng (vd ngày kết thúc của đối tượng chưa kết thúc) | `FILTER(ALL('Date'), 'Date'[Date] <= MAX(...))` phải thêm `NOT ISBLANK('Date'[Date])`; date table phủ TOÀN BỘ phạm vi dữ liệu |
| **STOCK vs FLOW** trên fact snapshot tháng | Tồn/số dư gộp N tháng phồng N lần | Tồn cuối kỳ: `CLOSINGBALANCEMONTH(SUM(col), 'Date'[Date])`; đầu kỳ `OPENINGBALANCEMONTH`; cột phát sinh trong kỳ mới `SUM` |
| Time-intelligence lọc qua cột năm của fact | Cùng kỳ / đầu kỳ ra blank hoặc sai | Mọi time-intel lọc qua **date table**; quan hệ fact → date qua cột cuối tháng là đủ |

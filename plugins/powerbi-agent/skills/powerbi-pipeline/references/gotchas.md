# Gotchas & Bẫy kinh nghiệm (agent reference)

> Bẫy đã trả giá khi làm Power BI end-to-end. Đọc để tránh lặp lại.

## Data / Power Query
- **Date thành serial 45292**: Excel ngày về số → ép kiểu Date tường minh ở bước cuối.
- **Bước làm gãy query folding** (Index, một số custom step, merge với nguồn khác) → refresh chậm; kiểm bằng View Native Query.
- **Cột khóa có blank** → xuất hiện "blank member" ở mọi slicer/quan hệ.
- Nhiều sheet Excel (mỗi năm 1 sheet) → **append** thành 1 bảng dài trước khi model.
- Mã SP/khu vực **không đồng nhất** giữa nguồn → phải mapping về 1 mã chuẩn (Unify Code).

## Data Model
- **Auto date/time** phình model → tắt, dùng Date Table riêng.
- Snapshot fact nối date qua **cột cuối tháng** là đủ (đừng ép ngày chính xác).
- Quan hệ Many-to-many/ngược chiều → soi Mermaid ERD (`distill_model_schema`) đảm bảo hình sao.

## DAX
- **Cột tồn kho/số dư KHÔNG SUM qua tháng** → `CLOSINGBALANCEMONTH`.
- Time-intel lọc qua **date table**, không qua cột năm của fact.
- Lặp biểu thức không dùng VAR → chậm gấp đôi.
- Chia bằng `/` không guard → lỗi/‑∞ khi mẫu 0 → dùng `DIVIDE`.

## Report / PBIR
- **KHÔNG dựng layout từ số 0** (luôn xấu) → `apply_template` clone-and-rebind, giữ `visualContainerObjects`.
- Field bind phải **tồn tại** trong model → `describe_table` trước khi bind.
- Ghi REPORT (PBIR) chỉ khi file **.pbip ĐÓNG**; ghi model thì lúc nào cũng được (engine live).
- **Bookmark để tay** — clone bookmark từng vỡ báo cáo; dựng stacked visuals + nhờ user bấm tạo.
- Agent **không thấy render** → bắt buộc user nghiệm thu mắt trên Desktop.

## Policy / bảo mật
- Hỏi **cột PII đầu dự án** → ghi `policy.json` trước khi chạm dữ liệu.
- `EVALUATE 'Bảng'`/`ALL(...)` bị policy chặn → viết lại `SUMMARIZECOLUMNS`/`TOPN`/measure.
- Đừng interleave write 2 MCP (powerbi-agent + powerbi-modeling) cùng lúc — modeling SaveChanges xong mới quay lại query/report.

## Vận hành
- SQL Server **Developer** = free đủ tính năng (kèm Report Server) nhưng vẫn là rủi ro pháp lý — nói rõ với khách.
- Power BI Pro **$14/user/th** (từ 4/2025); RLS chỉ từ Pro; Fabric F64 → viewer Free.

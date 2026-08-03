# Power Query (M) — Best Practices & Techniques (agent reference)

> Nguồn: Microsoft Learn (Power Query best practices, query folding, Value.NativeQuery) + kinh nghiệm KPIM. Agent đọc ở Khâu 1–2 của `powerbi-pipeline`.

## 1. Query Folding — nguyên tắc số 1 về hiệu năng
**Query folding** = đẩy transform về data source thực thi (SQL native) thay vì kéo hết dữ liệu về engine Power Query. Với **DirectQuery/Dual** BẮT BUỘC fold; với **Import** nên fold tối đa để refresh nhanh.
- **Đẩy càng nhiều xử lý về nguồn càng tốt.** Tìm bước làm gãy fold; **đưa các bước fold-được lên trước** trong sequence.
- Kiểm tra bằng **query folding indicators** + **View Native Query** (nếu mờ = bước đó gãy fold) + **query plan** (node khác `Value.NativeQuery`/data-source = không fold).
- Filter & giảm cột (`Table.SelectColumns`) SỚM để giảm dữ liệu truyền.
(MS: "Query folding guidance", "Query folding examples" — full-fold lấy 10 dòng vs no-fold lấy 3.6M dòng.)

## 2. Native SQL query giữ được fold — `Value.NativeQuery`
Khi cần SQL thô nhưng vẫn muốn các bước sau fold, dùng `Value.NativeQuery(Source, "SELECT ...", null, [EnableFolding=true])`:
```m
let
  Source = Sql.Database("server","db"),
  q = Value.NativeQuery(Source, "SELECT A.id, A.name FROM account A", null, [EnableFolding=true])
in q
```
- Lợi ích lớn khi lấy **subset của bảng lớn**. MS: đổi measure từ `COUNTDISTINCT` sang `SUMX` giúp fold → nhanh **97%**.
- Lưu ý: DirectQuery chỉ nhận `SELECT` (không CTE/stored proc); **incremental refresh KHÔNG dùng native query** (buộc kéo hết rồi lọc).
- Hỗ trợ fold cho: SQL Server, PostgreSQL, Snowflake, BigQuery, Redshift, SAP HANA, Dataverse (enhanced compute).

## 3. Chọn đúng connector
Dùng connector chuyên dụng (VD **SQL Server** thay vì ODBC) → có fold + trải nghiệm Get Data tốt. Chỉ dùng ODBC/OLEDB khi không có connector.

## 4. Kiểu dữ liệu & staging
- **Ép kiểu tường minh ở cuối** query, đặc biệt Date (bẫy kinh điển: ngày Excel thành serial `45292`).
- Tách **staging query** (nguồn thô) khỏi query cuối; đặt tên bước rõ nghĩa.
- Không hardcode path máy cá nhân → dùng **M parameter**; credential KHÔNG nằm trong M code.

## 5. Tối ưu evaluation & privacy
- Với Dataverse thêm `CreateNavigationProperties=false` để bỏ qua dò relationship (nhanh hơn) — trừ khi cần cột expand.
- Chú ý **Data Privacy Firewall**: nhiều nguồn khác privacy level có thể chặn fold/gây lỗi; set privacy level hợp lý.
- Lazy evaluation: bước không cần cho output sẽ không chạy.

## 6. Incremental refresh
Với bảng lớn → **incremental refresh + query folding** (RangeStart/RangeEnd param fold thành `WHERE date BETWEEN ...`). Tránh timeout truy vấn dài.

## Nguồn
- https://learn.microsoft.com/power-query/best-practices
- https://learn.microsoft.com/power-bi/guidance/power-query-folding
- https://learn.microsoft.com/power-query/query-folding-basics
- https://learn.microsoft.com/power-query/native-query-folding
- https://learn.microsoft.com/power-bi/guidance/powerbi-modeling-guidance-for-power-platform

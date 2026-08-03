# SQL (T-SQL / nguồn quan hệ) — Best Practices cho BI (agent reference)

> Nguồn: Microsoft Learn (SQL Server index design, T-SQL performance, high-CPU SARGability) + kinh nghiệm KPIM. Áp dụng khi agent viết SQL cho nguồn (Value.NativeQuery, View, stored proc, staging DW).

## 1. SARGable predicates (điều kiện dùng được index)
**SARGable** = predicate cho phép **index seek** thay vì table scan. Đừng bọc hàm/biểu thức lên cột trong `WHERE`/`JOIN`/`HAVING`/`GROUP BY`/`ORDER BY`.
- ❌ `WHERE SUBSTRING(ProductNumber,0,4)='HN-'` → scan. ✅ `WHERE Name LIKE 'Hex%'`.
- ❌ `WHERE UnitPrice*0.10 > 300` → non-SARGable. ✅ chuyển vế: `WHERE UnitPrice > 300/0.10`.
- ❌ `WHERE ABS(ProductID)=771`, `WHERE UPPER(LastName)='SMITH'` → scan.
- ❌ `LIKE '%Smith'` (wildcard đầu) → scan. ✅ `LIKE 'Smith%'` → seek.
- Tránh **implicit conversion** (varchar↔nvarchar, int↔varchar) trong JOIN/WHERE → gãy index (tìm `CONVERT_IMPLICIT` trong execution plan). Khai báo biến/tham số **đúng kiểu** cột.
- Không sửa được query → tạo **computed column có index** dùng cùng hàm.
(MS: "Troubleshoot high-CPU" Step 6; "Post-migration optimization".)

## 2. Index design
- Tạo **nonclustered index** trên cột hay dùng ở predicate/join (SARGable). Bỏ index không dùng (`sys.dm_db_index_usage_stats`).
- **Covering index**: đưa mọi cột query cần (WHERE/JOIN/GROUP BY + SELECT) vào index (key SARGable + `INCLUDE` cột còn lại) → chỉ đọc index, giảm I/O.
- Window function: index khớp `PARTITION BY` rồi `ORDER BY` (+ `INCLUDE` cột đo). Tận dụng **batch mode** (columnstore hoặc compat level ≥150).
- IN với cột không index → scan; index cột đó hoặc giới hạn cột đã index.

## 3. Viết query cho BI
- **Không `SELECT *`** — chỉ lấy cột cần (giảm I/O, hỗ trợ covering index, fold tốt hơn).
- Pre-aggregate fact lớn bằng **View / Stored Procedure / indexed view** trước khi vào Power BI (giảm tải model).
- Tránh full-scan cho bảng lớn: lọc sớm, dùng `TOP`/phân trang khi khám phá.
- CTE cho dễ đọc; nhưng nhớ DirectQuery native query không nhận CTE/stored proc.
- Đối chiếu kết quả tổng hợp với số biết trước trước khi tin.

## 4. DW / staging (khi xây kho)
- Tách **Transient staging** (`*_TST`, tạm cho ETL) vs **Persistent staging** (`*_PST`, làm sạch, lưu lâu).
- Fact lưu sẵn cột lũy kế `VALUE_MTD/QTD/YTD` (tránh tính runtime); **MD5 hashkey** cho change-detection/incremental.
- Surrogate key + xử lý **SCD** (Type 2 giữ lịch sử) thay vì sửa mã gốc.
- Idempotent pipeline (MERGE/upsert theo khóa + watermark) — chạy lại không nhân đôi.

## 5. Bảo mật
- Bảo mật cứng ở nguồn: **RLS** trên model + **service principal quyền tối thiểu**; không để credential trong M/SQL.
- Cột PII (SĐT/CMND/email) khai báo vào `policy.json` của powerbi-agent (aggregate-only chặn project cột thô).

## Nguồn
- https://learn.microsoft.com/sql/relational-databases/sql-server-index-design-guide
- https://learn.microsoft.com/troubleshoot/sql/database-engine/performance/troubleshoot-high-cpu-usage-issues
- https://learn.microsoft.com/sql/tools/sql-database-projects/concepts/sql-code-analysis/t-sql-performance-issues
- https://learn.microsoft.com/sql/t-sql/queries/select-over-clause-transact-sql

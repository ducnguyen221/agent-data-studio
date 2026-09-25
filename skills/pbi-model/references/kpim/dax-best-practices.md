# DAX — Best Practices & Techniques (agent reference)

> Nguồn: Microsoft Learn (DAX best practices, Analysis Services, Power BI transform-model) + kinh nghiệm KPIM. Agent đọc file này ở bước 4–5 của skill `pbi-model` (measure + truy vấn thử).

## 1. VAR — luôn dùng biến để tránh tính lặp
Lặp cùng một biểu thức khiến engine tính nhiều lần. Gán vào `VAR` → tính 1 lần, nhanh ~2×, dễ đọc, dễ debug.
```dax
Sales YoY % =
VAR SalesPriorYear = CALCULATE([Sales], SAMEPERIODLASTYEAR('Date'[Date]))
RETURN DIVIDE([Sales] - SalesPriorYear, SalesPriorYear)
```
Biến có thể là scalar hoặc **table**. (MS: "Use variables to improve your DAX formulas".)

## 2. DIVIDE thay cho toán tử `/`
`DIVIDE(num, den [,alt])` xử lý chia 0 / BLANK an toàn, tối ưu hơn `IF(den=0,...)`. 
- Dùng `DIVIDE` khi mẫu số **có thể** = 0/BLANK.
- Dùng `/` khi mẫu số là hằng số (đảm bảo ≠ 0) → nhanh hơn vì bỏ kiểm tra.
- Measure nên trả **BLANK** (không truyền alt) để visual tự ẩn nhóm rỗng.
(MS: "DIVIDE function vs. divide operator".)

## 3. Date table riêng + time-intelligence
- **Không dùng Auto date/time** cho model lớn (tạo nhiều bảng ẩn, phình model). Tạo **Date Table riêng**, "Mark as Date Table".
- Date table phải **liên tục** (không thiếu ngày giữa min–max) với classic time-intelligence, nếu không `SAMEPERIODLASTYEAR`/`DATESYTD` báo lỗi.
- Time-intel LỌC QUA date table, KHÔNG qua cột năm/tháng của fact.
- Ưu tiên hàm chuẩn: `TOTALYTD`/`DATESYTD`, `SAMEPERIODLASTYEAR`, `DATEADD`, `PREVIOUSMONTH`, `PARALLELPERIOD`.
- Tránh kỹ thuật "cộng cột offset vào date table" cho model lớn (phình semantic model, refresh chậm) — MS khuyến cáo.
- (Mới) **Calendar-based time intelligence** (preview): `TOTALYTD([Sales], 'Fiscal Calendar')` — hỗ trợ lịch bất kỳ (retail 445/454/544, 13-month), sparse dates, week-based, hiệu năng tốt hơn.

## 4. Calculation Groups — chống bùng nổ measure
Thay vì tạo tay hàng trăm measure MTD/YTD/YoY cho mỗi base measure, định nghĩa **1 lần** các calculation item áp cho mọi measure qua `SELECTEDMEASURE()`:
```dax
-- YTD item
CALCULATE(SELECTEDMEASURE(), DATESYTD('Date'[Date]))
-- YOY item
SELECTEDMEASURE() - CALCULATE(SELECTEDMEASURE(), 'Time Intelligence'[Time Calc]="PY")
```
Sửa qua Tabular Editor hoặc **Modeling MCP của Microsoft** (bước bulk, xem `pbi-model`). (MS: Analysis Services "Calculation groups".)

## 5. Measure family pattern (KPIM)
1 KPI gốc → viết 1 **base measure**, các biến thể là `CALCULATE(base, <time filter>)`. Không lặp logic. Bộ phái sinh chuẩn: base → MTD → YTD → SPLY → %YoY → chênh lệch → đánh giá (đèn giao thông) → phân loại → format.

## 6. Aggregation & filter context
- Cột STOCK/tồn kho/số dư cuối kỳ **KHÔNG SUM qua tháng** → dùng `CLOSINGBALANCEMONTH`/`LASTNONBLANKVALUE`.
- Tránh `FILTER('Bảng lớn', ...)` khi có thể dùng điều kiện cột trực tiếp trong `CALCULATE`.
- Ưu tiên `SUMMARIZECOLUMNS` (không `SUMMARIZE` + `ADDCOLUMNS` kiểu cũ) để truy vấn tổng hợp.
- Hiểu **context transition**: measure trong row context tự bọc `CALCULATE`.
- Dùng `KEEPFILTERS`, `REMOVEFILTERS`/`ALL`, `ALLSELECTED` có chủ đích.

## 7. Quản trị & format
- Explicit measure (không dùng implicit auto-aggregate); ẩn cột số gốc.
- `DisplayFolder` theo nhóm; `FormatString` (`#,0` tiền, `0.0%` %); prefix nhất quán.
- DAX user-defined functions (UDF) cho logic tái dùng nhiều nơi.
- Verify từng measure: `EVALUATE ROW("kq", [Measure])` đối chiếu 1 số biết trước.

## Nguồn
- https://learn.microsoft.com/dax/best-practices/dax-variables
- https://learn.microsoft.com/dax/best-practices/dax-divide-function-operator
- https://learn.microsoft.com/power-bi/transform-model/desktop-time-intelligence
- https://learn.microsoft.com/analysis-services/tabular-models/calculation-groups

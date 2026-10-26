# DAX — cách viết và tối ưu cho agent

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

## 3b. Tạo bảng Date khi model chưa có
Thứ tự ưu tiên (khớp `modeling-guidelines.md` của Microsoft trong skill này):
1. **Nguồn đã có bảng lịch** → nhập nó, đừng dựng lại.
2. Chưa có → tạo bằng **Power Query / M**.
3. Chỉ khi không làm được ở nguồn hay Power Query → **bảng tính DAX**, phạm vi lấy từ chính dữ liệu, không gõ cứng năm bắt đầu/kết thúc (gõ cứng thì dữ liệu mới vượt mốc sẽ rơi khỏi mọi time-intelligence).
```dax
Date =
VAR _MinDate = MIN('Sales'[Order Date])
VAR _MaxDate = MAX('Sales'[Order Date])
RETURN
    ADDCOLUMNS(
        CALENDAR(DATE(YEAR(_MinDate), 1, 1), DATE(YEAR(_MaxDate), 12, 31)),
        "Year", YEAR([Date]),
        "Month Number", MONTH([Date]),
        "Month Name", FORMAT([Date], "MMMM")
    )
```
- Nhiều bảng fact có ngày: lấy ngày nhỏ nhất và lớn nhất qua **mọi** cột ngày liên quan (phép `MIN`/`MAX` hai đối số), để bảng Date phủ trọn phạm vi.
- Đánh dấu **bảng** Date là date table (Mark as date table; trong TMDL là `dataCategory: Time` đặt ở **bảng**, không phải trên cột); cột `Date` là khoá (`isKey`), duy nhất và liên tục, không hở ngày.
- **Sort by column**: sắp `Month Name` theo `Month Number`; nếu không, tháng xếp theo bảng chữ cái.
- Quan hệ Một→Nhiều từ `Date[Date]` sang cột ngày của fact. Cột ngày của fact có phần giờ thì tạo cột chỉ-ngày để khớp. Tắt auto date/time.
- Thêm cột chỉ khi báo cáo cần (quý, tuần, năm tài chính...); ghi `displayFolder` và `formatString` như mục 7.

## 4. Calculation Groups — chống bùng nổ measure
Thay vì tạo tay hàng trăm measure MTD/YTD/YoY cho mỗi base measure, định nghĩa **1 lần** các calculation item áp cho mọi measure qua `SELECTEDMEASURE()`:
```dax
-- YTD item
CALCULATE(SELECTEDMEASURE(), DATESYTD('Date'[Date]))
-- YOY item
SELECTEDMEASURE() - CALCULATE(SELECTEDMEASURE(), 'Time Intelligence'[Time Calc]="PY")
```
Sửa qua Tabular Editor hoặc **Modeling MCP của Microsoft** (bước bulk, xem `pbi-model`). (MS: Analysis Services "Calculation groups".)

## 5. Mẫu nhóm measure (KPIM)
1 KPI gốc → viết 1 **base measure**, các biến thể là `CALCULATE(base, <time filter>)`. Không lặp logic. Bộ phái sinh chuẩn: base → MTD → YTD → SPLY → %YoY → chênh lệch → đánh giá (đèn giao thông) → phân loại → format.

## 6. Tổng hợp và ngữ cảnh lọc
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
- Trình bày: xuống dòng ngay sau dấu `=` và sau `RETURN`, mỗi `VAR` một dòng, thụt lề một cấp cho biểu thức trả về; tên biến bắt đầu bằng `_` (theo `dax-guidelines.md` của Microsoft).

## 7b. Mẫu DAX hay gặp
Tên bảng/cột trong ví dụ (`Sales`, `Date`, `Product`, `Account`) chỉ minh họa; thay bằng tên thật của model.

**Xếp hạng động — `RANKX`.** Hàm chuyên dụng cho xếp hạng; `ALLSELECTED` giữ phạm vi mà slicer đang chọn, nên thứ hạng tính trong tập đang hiển thị.
```dax
Product Rank =
IF(
    HASONEVALUE('Product'[Product Name]),
    RANKX(ALLSELECTED('Product'[Product Name]), [Total Sales], , DESC, DENSE)
)
```
- `HASONEVALUE` để dòng tổng cộng không hiện một thứ hạng vô nghĩa. Đối số cuối quyết định cách xếp khi hòa (`DENSE` không nhảy bậc, `SKIP` có nhảy).
- Top N: dùng bộ lọc Top N của visual theo `[Total Sales]`, hoặc lọc trên measure thứ hạng; nhớ ca hòa có thể cho nhiều hơn N dòng.

**Lũy kế (running total).** Lọc qua bảng Date, không qua cột ngày của fact.
```dax
Sales Running Total =
VAR _LastDate = MAX('Date'[Date])
RETURN
    CALCULATE([Total Sales], DATESBETWEEN('Date'[Date], BLANK(), _LastDate))
```
- Lũy kế từ đầu năm: `CALCULATE([Total Sales], DATESYTD('Date'[Date]))` (hoặc `TOTALYTD`, mục 3). `DATESBETWEEN` với đầu mút `BLANK()` lấy từ ngày sớm nhất của bảng Date.
- Cần date table liên tục và **đã được đánh dấu** là date table (mục 3, 3b); nếu chưa đánh dấu, bộ lọc trên cột Năm/Tháng vẫn giữ và lũy kế bị cắt theo từng tháng trên trục. Nếu bắt buộc dùng điều kiện tùy ý, có thể dùng `FILTER(ALL('Date'[Date]), 'Date'[Date] <= _LastDate)`; ở đây `ALL` là **hàm trả bảng** (danh sách ngày) chứ không phải bộ sửa ngữ cảnh nên `REMOVEFILTERS` không thay máy móc được. Chỉ `ALL` trên cột/bảng Date, **không** trên bảng fact. Bẫy blank member khi dùng cách này: `tom-tmdl-write.md`, mục 5.

**Số dư / tồn cuối kỳ (semi-additive).** Cộng qua tháng làm số phồng; lấy giá trị ở cuối kỳ.
```dax
Closing Balance =
CLOSINGBALANCEMONTH(SUM('Account Balance'[Balance]), 'Date'[Date])
```
- Snapshot thưa (ngày cuối kỳ không có dòng) thì dùng `LASTNONBLANKVALUE('Date'[Date], SUM('Account Balance'[Balance]))`: lấy giá trị ở ngày gần nhất có dữ liệu trong kỳ.
- Bẫy hụt tổng: `LASTNONBLANKVALUE` lấy **một** ngày chung gần nhất; khi nhiều thực thể (tài khoản, kho) có ngày chụp cuối khác nhau, thực thể không có dòng ở ngày đó bị bỏ nên tổng bị hụt. Tính theo từng thực thể rồi cộng, ví dụ `SUMX(VALUES('Account'[Account ID]), LASTNONBLANKVALUE('Date'[Date], SUM('Account Balance'[Balance])))`, và đối chiếu số biết trước.
- Bẫy: bọc `LASTDATE` trần trong `CALCULATE` trả `BLANK` khi ngày cuối kỳ không có dòng; luôn đối chiếu một con số biết trước (mục 7) cho tháng cuối cùng và tháng đầu tiên.
- Phần "không SUM qua tháng" đã ghi ở mục 6.

**Phân cấp cha–con (sơ đồ tài khoản, tổ chức).** `PATH` bắt buộc là **cột tính trong bảng dimension** — đây là ngoại lệ có chủ đích với nguyên tắc ưu tiên measure hơn cột tính (checklist `pbi-review`, mục C).
```dax
Account Path =
PATH('Account'[Account ID], 'Account'[Parent Account ID])

Level 1 =
LOOKUPVALUE('Account'[Account Name], 'Account'[Account ID], PATHITEM('Account'[Account Path], 1, INTEGER))
```
- Mỗi cấp một cột tính (`PATHITEM(..., 2, INTEGER)`, ...); số cột bằng độ sâu lớn nhất (`PATHLENGTH` để đo), rồi dựng hierarchy từ các cột đó.
- Khóa cha rỗng là gốc; vòng lặp trong dữ liệu (A là cha của B, B là cha của A) gây lỗi — kiểm khi nạp.

**Chọn measure bằng slicer — field parameter trước.**
- **Field parameter** (Modeling → New parameter → Fields trong Desktop) tạo bảng tham số chứa các field/measure; slicer cho người xem đổi measure hiển thị mà không cần viết measure chuyển đổi. Đây là cách ưu tiên (khớp DAX013 trong `dax-perf-patterns.md` của Microsoft).
- Khi cần logic riêng (định dạng, điều kiện theo lựa chọn) mới dùng `SWITCH`:
```dax
Selected Metric =
SWITCH(
    SELECTEDVALUE('Metric Selector'[Metric]),
    "Revenue", [Total Sales],
    "Profit", [Total Profit],
    BLANK()
)
```
  Giữ mỗi nhánh đơn giản và cùng kiểu số; `SELECTEDVALUE` trả `BLANK` khi người xem chọn nhiều giá trị nên nhánh mặc định phải tường minh.
- Cùng một phép biến đổi áp cho mọi measure (YTD, so cùng kỳ) thì dùng calculation group (mục 4), không phải hai cách trên.

## 7c. Debug measure sai hoặc blank bất ngờ
1. **Ngữ cảnh lọc**: slicer, bộ lọc visual/trang, `ALL`/`REMOVEFILTERS` có xóa nhầm không. Tách measure thành từng phần, trả riêng từng biến ở `RETURN` (hoặc `EVALUATE ROW(...)` qua `pbi-analysis`) để thấy bước nào lệch.
2. **Quan hệ**: chiều lọc, cardinality, quan hệ không hoạt động cần `USERELATIONSHIP`, khóa có blank member.
3. **Kiểu dữ liệu**: text lệch number, Date lẫn DateTime, ngày thành số serial — lệch kiểu làm khớp quan hệ trượt âm thầm.
4. **Blank**: để measure trả `BLANK` theo mục 2; chỉ dùng `ISBLANK`/`COALESCE` ở chỗ nghiệp vụ thật sự cần số. Ép về 0 cho "đẹp" làm visual hiện mọi nhóm rỗng.
5. **Hiệu năng** (khi chậm chứ không sai): đo trong DAX Studio — Server Timings tách thời gian engine lưu trữ và engine công thức; hướng dẫn ở `dax-perf-decision-guide.md` (Microsoft).
6. **Biến để tách, không để thay**: dùng `VAR` tách `CALCULATE` lồng nhau cho dễ đọc và dễ soi từng bước. Biến được tính **một lần** ở ngữ cảnh nơi nó khai báo, nên không thay được `CALCULATE` (vốn đổi ngữ cảnh).

## Nguồn
- https://learn.microsoft.com/dax/best-practices/dax-variables
- https://learn.microsoft.com/dax/best-practices/dax-divide-function-operator
- https://learn.microsoft.com/power-bi/transform-model/desktop-time-intelligence
- https://learn.microsoft.com/analysis-services/tabular-models/calculation-groups
- https://learn.microsoft.com/dax/rankx-function-dax
- https://learn.microsoft.com/dax/allselected-function-dax
- https://learn.microsoft.com/dax/datesbetween-function-dax
- https://learn.microsoft.com/dax/datesytd-function-dax
- https://learn.microsoft.com/dax/closingbalancemonth-function-dax
- https://learn.microsoft.com/dax/lastnonblankvalue-function-dax
- https://learn.microsoft.com/dax/path-function-dax
- https://learn.microsoft.com/dax/pathitem-function-dax
- https://learn.microsoft.com/dax/parent-and-child-functions-dax
- https://learn.microsoft.com/dax/switch-function-dax
- https://learn.microsoft.com/dax/selectedvalue-function-dax
- https://learn.microsoft.com/power-bi/create-reports/power-bi-field-parameters
- https://learn.microsoft.com/dax/calendar-function-dax
- https://learn.microsoft.com/power-bi/transform-model/desktop-date-tables

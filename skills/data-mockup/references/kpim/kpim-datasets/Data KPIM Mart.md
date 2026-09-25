# Data KPIM Mart — bán lẻ chuỗi cửa hàng

> Hồ sơ tham chiếu (distill 2026-08-18) từ một bộ dữ liệu dạy học nội bộ KPIM — bộ gốc không kèm trong repo.
> Dùng cho khoá Power BI Cơ Bản. Có kèm bản `(after query)` đã dọn để đối chiếu trước/sau Power Query.

## 1. Tóm tắt

| | |
|---|---|
| Ngành | Bán lẻ tiêu dùng nhanh, chuỗi cửa hàng tại Hà Nội |
| Khoảng thời gian | 2020-01-01 → 2022-12-31 (đúng 3 năm, 1.096 ngày) |
| Ngôn ngữ cột | Tiếng Anh, snake_case |
| Kiểu | Star schema kinh điển, 1 file Excel nhiều sheet |
| Điểm mạnh để tái dùng | Mẫu chuẩn nhất trong 5 bộ — học star schema, plan vs actual, RFM |

## 2. Cấu trúc bảng

| Sheet | Loại | Grain | Dòng | Cột |
|---|---|---|---|---|
| `dim_date` | dim | 1 ngày | 1.096 | 6 |
| `dim_store` | dim | 1 cửa hàng | 29 | 10 |
| `dim_product` | dim | 1 SKU | 353 | 21 |
| `dim_customer` | dim | 1 khách hàng | 18.484 | 12 |
| `dim_promotion` | dim | 1 chương trình KM | 16 | 8 |
| `fact_sales` | fact | 1 dòng hàng trong đơn | 58.414 | 14 |
| `fact_sales_plan` | fact | 1 cửa hàng × tháng | 1.044 | 3 |
| `segment` | tra cứu | 1 tổ hợp R-F-M | 23 | 4 |

## 3. Cột đáng chú ý

| Cột | Bảng | Ghi chú thiết kế |
|---|---|---|
| `order_number` + `order_line_number` | fact_sales | Khoá tổ hợp: đơn nhiều dòng hàng — grain là dòng, không phải đơn |
| `order_date` / `ship_date` / `payment_date` | fact_sales | **Ba mốc thời gian trên một fact** → phân tích lead time giao hàng, kỳ thu tiền. Giao/thu kéo dài sang 2023, vượt khỏi kỳ đặt hàng — đúng thực tế |
| `unit_price` / `unit_cost` / `unit_discount` | fact_sales | Đơn giá là **non-additive** (không SUM); `sales_amount` mới là additive |
| `sales_plan` | fact_sales_plan | Kế hoạch ở grain **thô hơn** fact (cửa hàng × tháng) — mẫu chuẩn cho so sánh KH/TH |
| `loyal_group` | dim_customer | Hạng thẻ (WHITE…) — chiều phân khúc chính |
| `latitude` / `longitude` | dim_store | Cho phép bản đồ; `manager_image` cho ảnh đại diện trong report |
| `brand`, `suplier_name`, `product_category/subcategory` | dim_product | Phân cấp ngành hàng 2 cấp + nhãn hàng + nhà cung cấp |
| `R-F-M`, `Segment`, `Sort` | segment | Bảng tra RFM: 23 tổ hợp → tên phân khúc + thứ tự sắp xếp |

## 4. KPI tiêu biểu

Doanh thu · Giá vốn · Lợi nhuận gộp và biên gộp · AOV · Số đơn / số dòng hàng · % đạt kế hoạch theo cửa hàng-tháng · Doanh thu theo ngành hàng / khu vực / hạng thẻ · Phân tích RFM · Lead time giao hàng · Kỳ thu tiền bình quân.

## 5. Hình mẫu đáng tái dùng

1. **Kế hoạch tách bảng riêng, grain thô hơn fact** — đừng nhét cột `target` vào fact. Cửa hàng × tháng là mức kế hoạch tự nhiên của bán lẻ.
2. **dim_date dựng sẵn phủ đúng khoảng fact** — 1.096 dòng = 3 năm tròn, không thừa không thiếu.
3. **Nhiều mốc thời gian trên một fact** để sinh ra chỉ số độ trễ mà không cần thêm bảng.
4. **Bảng tra cứu phục vụ phân tích** (`segment`) tách khỏi dim — quy tắc phân nhóm thay đổi thì sửa một chỗ.
5. **Dim khách hàng lớn hơn nhiều lần các dim khác** (18k so với 29 và 353) — đúng hình dạng bán lẻ thật.

## 6. Cạm bẫy — KHÔNG chép sang bộ mới

- `first_name` / `last_name` **tách sai**: một cột giữ gần như cả họ tên (`'Đăng'` + `'Đặng Bá Trần Hải'`). Tiếng Việt nên để một cột `ho_ten`.
- Tên cột lỗi: `'country '` (thừa khoảng trắng cuối), `heigth`, `uom_volumn`, `suplier_name`.
- `dim_promotion` có `start_date`/`end_date` rơi vào 2010–2014, **nằm ngoài hẳn khoảng fact 2020–2022** → khuyến mãi không khớp giao dịch nào. Bộ mới phải cho hiệu lực khuyến mãi nằm trong kỳ dữ liệu.
- Tên nhãn hàng/nhà cung cấp có dùng **thương hiệu FMCG có thật** — cân nhắc lại theo chính sách thương hiệu ở `design-playbook.md` Nhóm 6.

## 7. Khi user nói "giống bộ này nhưng…"

| Yêu cầu | Đổi gì |
|---|---|
| Ngành khác (F&B, dược, thời trang) | Giữ nguyên 8 bảng và grain; chỉ thay danh mục `product_category` và tên hàng |
| Có thương mại điện tử | Thêm cột `kenh_ban` vào fact + dim kênh; cho tỉ trọng online tăng dần theo thời gian (mix shift) |
| Có trả hàng | Thêm `trang_thai` cho dòng hàng và fact trả hàng riêng, hoặc số lượng âm — chốt với user trước, hai cách không trộn được |
| Nhiều tỉnh thành | Mở rộng `dim_store` thêm cấp vùng/miền; nhớ luật "quận phải thuộc đúng tỉnh" |
| Nhẹ hơn để dạy nhập môn | Giữ `dim_date`, `dim_store`, `dim_product`, `fact_sales`; bỏ promotion/segment/plan |

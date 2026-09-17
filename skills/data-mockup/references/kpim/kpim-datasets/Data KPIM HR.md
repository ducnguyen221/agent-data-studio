# Data KPIM HR — nhân sự

> Hồ sơ tham chiếu (distill 2026-08-18) từ một bộ dữ liệu dạy học nội bộ KPIM — bộ gốc không kèm trong repo.
> Bối cảnh nhân sự của chính KPIM Bank — dùng chung thương hiệu với `Data KPIM Bank`.

## 1. Tóm tắt

| | |
|---|---|
| Ngành | Nhân sự ngân hàng, nhiều chi nhánh trên cả nước |
| Khoảng thời gian | 2020-01 → 2025-12 (chấm công 2020-01-13 → 2025-12-19) |
| Ngôn ngữ cột | Tiếng Việt có dấu, có khoảng trắng (`ID Nhân Sự`, `Ngày Vào Làm`) |
| Kiểu | Dim rất nhỏ + fact lớn, 1 file nhiều sheet |
| Điểm mạnh để tái dùng | Vòng đời nhân sự vào–ra, quan hệ phân cấp tự trỏ, tỉ lệ dim:fact chênh lệch lớn |

## 2. Cấu trúc bảng

| Sheet | Loại | Grain | Dòng | Cột |
|---|---|---|---|---|
| `Nhân Sự` | dim | 1 nhân viên | 60 | 14 |
| `Phòng Ban` | dim | 1 phòng ban | 8 | 4 |
| `Data Chấm Công` | fact | 1 nhân viên × ngày | 16.735 | 9 |
| `Data Lương` | fact | 1 nhân viên × kỳ lương | 1.842 | 10 |
| `Data Nghỉ Phép` | fact | 1 đơn nghỉ phép | 79 | 8 |
| `Data Đào Tạo` | fact | 1 nhân viên × khoá học | 96 | 10 |

## 3. Cột đáng chú ý

| Cột | Bảng | Ghi chú thiết kế |
|---|---|---|
| `Ngày Vào Làm` / `Ngày Nghỉ Việc` / `Trạng Thái` | Nhân Sự | Vòng đời nhân sự — nền tảng của headcount, turnover, thâm niên. `Ngày Nghỉ Việc` rỗng = đang làm |
| `ID Quản Lý` | Nhân Sự | **Khoá tự trỏ** về chính bảng → cây tổ chức, tính span of control |
| `Bậc Lương`, `Loại Hợp Đồng`, `Chức Danh` | Nhân Sự | Chiều phân tích cho chênh lệch lương và cơ cấu lao động |
| `Giờ Vào` / `Giờ Ra` / `Giờ Làm` / `Giờ Tăng Ca` | Chấm Công | Giờ làm là cột dẫn xuất từ vào–ra; tăng ca tách riêng để nối sang lương |
| `Cuối Tuần`, `Ngày Lễ` | Chấm Công | Cờ ngày đặc biệt → hệ số lương tăng ca khác nhau |
| `Kỳ Công` | Lương | Grain theo kỳ (tháng), không phải ngày |
| `Lương Cơ Bản`, `Phụ Cấp`, `Lương Tăng Ca`, `Thưởng`, `Khấu Trừ`, `Bảo Hiểm`, `Thuế`, `Thực Lĩnh` | Lương | **Chuỗi cộng trừ ra `Thực Lĩnh`** — ràng buộc số học kiểm được bằng rule `expression` |
| `Duyệt` | Nghỉ Phép | Trạng thái phê duyệt → phân biệt đơn xin và ngày nghỉ thực tế |
| `Hạn Chứng Chỉ` | Đào Tạo | Ngày trong tương lai (tới 2027) — hợp lệ vì là hạn hiệu lực |
| `Lãnh Đạo` | Phòng Ban | Ghi **tên người** thay vì mã nhân viên → liên kết mềm, dễ lệch |

## 4. KPI tiêu biểu

Headcount đầu/cuối kỳ · Tuyển mới, nghỉ việc, tỉ lệ turnover · Thâm niên bình quân · Cơ cấu theo phòng ban/chức danh/giới tính · Quỹ lương và lương bình quân · Tỉ lệ tăng ca · Chi phí đào tạo và số giờ đào tạo/người · Tỉ lệ nghỉ phép · Span of control theo `ID Quản Lý`.

## 5. Hình mẫu đáng tái dùng

1. **Dim cực nhỏ, fact lớn** (60 nhân viên → 16.735 dòng chấm công). Không phải bộ nào cũng cần dim to; đúng grain quan trọng hơn số dòng.
2. **Khoá tự trỏ** cho cây tổ chức — mẫu tốt cho mọi quan hệ phân cấp trong cùng một bảng.
3. **Chuỗi thành phần lương cộng trừ ra một số cuối** — mẫu chuẩn cho mọi bảng có công thức nội bộ, kiểm được tự động.
4. **Cờ ngày đặc biệt trên fact** (cuối tuần, ngày lễ) thay vì bắt tra `dim_date` — tiện cho lớp nghiệp vụ.
5. **Vòng đời có kết thúc**: có người đã nghỉ việc, nên turnover ra số thật chứ không bằng 0.

## 6. Cạm bẫy — KHÔNG chép sang bộ mới

- `Lãnh Đạo` ở `Phòng Ban` là **tên người**, không phải `ID Nhân Sự` → trùng tên là gán sai. Dùng khoá.
- Tên cột tiếng Việt **có dấu và có khoảng trắng** → phải bọc ngoặc trong SQL/DAX. Bộ mới nên dùng tên kỹ thuật không dấu + nhãn tiếng Việt trong Data Dictionary.
- Chấm công tới 2025-12-19 nhưng lương chỉ 1.842 dòng (~31 kỳ) — kiểm lại độ phủ hai fact có khớp kỳ nhau không trước khi so sánh.
- Không có `dim_date`, nên phân tích theo tuần/quý phải tự dựng.

## 7. Khi user nói "giống bộ này nhưng…"

| Yêu cầu | Đổi gì |
|---|---|
| Doanh nghiệp lớn hơn | Nhân số nhân viên lên; giữ nguyên grain. Chấm công phình theo cấp số nhân — cân nhắc chỉ giữ tổng hợp theo tháng |
| Theo dõi biến động phòng ban | Chuyển `Nhân Sự` sang SCD2 (`valid_from`/`valid_to`/`is_current`) hoặc bảng chụp theo tháng |
| Có tuyển dụng | Thêm fact tuyển dụng grain 1 ứng viên × vị trí, để tính time-to-hire và tỉ lệ chuyển đổi qua từng vòng |
| Có đánh giá hiệu suất | Thêm fact grain nhân viên × kỳ đánh giá; cài tương quan điểm đánh giá ↔ thưởng ↔ nghỉ việc |
| Ngành sản xuất/bán lẻ | Giữ nguyên khung; đổi `Chi Nhánh` thành nhà máy/cửa hàng, thêm ca kíp vào chấm công |

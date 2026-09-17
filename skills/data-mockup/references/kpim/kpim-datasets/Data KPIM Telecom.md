# Data KPIM Telecom — telecom, thuê bao & doanh thu

> Hồ sơ tham chiếu (distill 2026-08-18) từ một bộ dữ liệu dạy học nội bộ KPIM — bộ gốc không kèm trong repo.
> Bộ mô phỏng theo mô hình quản trị của một nhà mạng hư cấu.

## 1. Tóm tắt

| | |
|---|---|
| Ngành | Telecom, quản trị theo đơn vị hành chính (tỉnh/TP → khu vực) |
| Khoảng thời gian | 12 kỳ năm 2025, chốt cuối mỗi tháng |
| Ngôn ngữ cột | Tiếng Việt có dấu, tên cột dạng nhãn báo cáo |
| Kiểu | **Hỗn hợp**: 2 bảng phẳng máy-đọc + 1 danh mục cây + 144 file báo cáo người-đọc phân mảnh theo tháng |
| Điểm mạnh để tái dùng | Bộ giàu nhất về **cân bằng dòng vào–ra**, **cây đơn vị nhiều cấp**, **so kế hoạch/thực hiện/cùng kỳ**, và **bất thường có chủ đích được ghi thành tài liệu** |

## 2. Cấu trúc

| File / sheet | Loại | Grain | Dòng | Cột |
|---|---|---|---|---|
| `Báo cáo Thuê Bao.xlsx` → `Data` | fact | 1 kỳ × đơn vị × sản phẩm | 13.320 | 29 |
| `Báo cáo KH Hợp Nhát.xlsx` → `Data` | fact/dim khách | 1 khách hàng (ẩn danh) | 4.201 | 41 |
| `Danh Mục Đơn Vị.xlsx` → `PhanCap_Demo` | dim cây | 1 đơn vị trong cây | 148 | 9 |
| `1.1._Kế_hoạch_doanh_thu/` | báo cáo | đơn vị × tháng | 149/file | 14 |
| `1.2._Doanh_thu_PTM/` | báo cáo | đơn vị × tháng | 149/file | 12 |
| `1.3._Doanh_thu_duy_trì/` | báo cáo | đơn vị × tháng | 149/file | 12 |

Ba thư mục báo cáo đều phân mảnh: `<thư mục>/MM-DD-YYYY/<tên>_<dòng sản phẩm>.xlsx`, 12 kỳ × 4 dòng sản phẩm = 48 file mỗi loại, **144 file** tổng cộng.

Hai file fact **có sẵn sheet `Từ điển dữ liệu`** (Trường / Mô tả / Kiểu-Miền giá trị) — đúng tinh thần sheet `01_Data_Dictionary` của skill này.

## 3. Cột đáng chú ý

| Cột | Bảng | Ghi chú thiết kế |
|---|---|---|
| `TB đầu kỳ`, `TB PTM mới`, `TB hủy/rời mạng`, `TB kết thúc HĐ`, `TB tạm ngưng`, `TB cuối kỳ (active)` | Thuê Bao | **Cân bằng dòng vào–ra**: cuối kỳ = đầu kỳ + PTM − hủy − kết thúc − tạm ngưng, và cuối kỳ tháng N = đầu kỳ tháng N+1. Ràng buộc quan trọng nhất của bộ này |
| `Tỷ lệ rời bỏ %`, `Tỷ lệ PTM %`, `Tăng trưởng thuần %` | Thuê Bao | Tỉ lệ tính sẵn — non-additive, tuyệt đối không SUM |
| `TB PTM lũy kế`, `TB hủy lũy kế` | Thuê Bao | Luỹ kế từ đầu năm theo đơn vị × sản phẩm |
| `Doanh thu bình quân/TB (đồng)`, `Doanh thu tháng (triệu)` | Thuê Bao | Doanh thu lấy từ báo cáo kế hoạch để định cỡ, doanh thu bình quân/thuê bao dẫn xuất — **hai nguồn phải khớp nhau** |
| `Chỉ số cảnh báo sớm churn`, `Nhóm cảnh báo sớm` | Thuê Bao | Điểm 0–100 + nhóm Xanh/Vàng/Đỏ |
| `Internet_Co_Dinh`, `IPTV`, `Mesh`, `Camera`, `Di_Dong` (0/1) + `Số dịch vụ` | KH Hợp Nhất | **Cờ sở hữu từng dịch vụ + tổng cờ** → độ sâu bán chéo. Ràng buộc: `Số dịch vụ` = tổng 5 cờ |
| `Tháng kích hoạt` / `Tháng rời mạng` / `Thâm niên (tháng)` | KH Hợp Nhất | Vòng đời thuê bao; rỗng ở cột rời mạng = còn hoạt động |
| `Loại rời mạng`, `Lý do rời mạng` | KH Hợp Nhất | Chủ động / bị động / chuyển mạng + mã lý do |
| `Thay đổi sử dụng 3T %`, `Thay đổi doanh thu bình quân/thuê bao 3T %`, `Sự cố 3T`, `Khiếu nại 3T` | KH Hợp Nhất | **Tín hiệu hành vi cửa sổ 3 tháng** — đầu vào cho mô hình cảnh báo sớm |
| `Sản phẩm gợi ý`, `Lý do gợi ý`, `Điểm cơ hội`, `Hành động khuyến nghị` | KH Hợp Nhất | Lớp next-best-offer nằm ngay trong dữ liệu |
| `Cấp`, `Tên cấp`, `Là dòng chi tiết` | Danh Mục Đơn Vị | Cây 4 cấp Công ty mẹ → Khối → Tỉnh/TP → Khu vực; **cờ dòng chi tiết để tổng không cộng trùng** |
| `DT KH tháng (1)`, `DT TH tháng (2)`, `So T-1 (3)`, `TL tháng % (4)=(2)/(1)` | báo cáo | Header có **chú thích công thức bằng số thứ tự** — đặc trưng báo cáo quản trị |

## 4. KPI tiêu biểu

Thuê bao cuối kỳ · Phát triển mới, rời mạng, tăng trưởng thuần · Tỉ lệ rời mạng · doanh thu bình quân/thuê bao · Doanh thu thực hiện so kế hoạch (tháng, luỹ kế, năm) · So tháng trước và cùng kỳ năm trước · Độ sâu bán chéo · Điểm rủi ro churn theo nhóm cảnh báo · Chất lượng dịch vụ (báo hỏng, khiếu nại trên 1.000 thuê bao) · Tỉ lệ thanh toán trễ, SLA quá hạn.

## 5. Hình mẫu đáng tái dùng

1. **Cân bằng dòng vào–ra** cho mọi đại lượng có đầu kỳ/cuối kỳ. Áp dụng được cho tồn kho, nhân sự, dư nợ, thuê bao — và là lỗi hay gặp nhất khi sinh dữ liệu kiểu này.
2. **Cây đơn vị có `cấp` + `tên cấp` + cờ dòng chi tiết** — cách xử lý phân cấp gọn hơn nhiều so với mã hoá bằng thụt đầu dòng.
3. **Bất thường được ghi thành tài liệu**: từ điển dữ liệu ghi rõ "churn vọt tháng 6–8 do sự cố mạng", "~6% khách đang hoạt động nhưng tín hiệu xấu dần". Đây chính là nguyên tắc "sự kiện bất thường phải có lý do" — và người ra đề có sẵn đáp án.
4. **So sánh nhiều trục trong cùng một báo cáo**: kế hoạch/thực hiện, tháng/luỹ kế/năm, so tháng trước, so cùng kỳ.
5. **Tín hiệu cửa sổ trượt 3 tháng** làm đầu vào cho điểm cảnh báo — cách tạo dữ liệu "có thể mô hình hoá được".
6. **Phân mảnh file theo kỳ** giống hệ thống thật xuất ra, để dạy Power Query gộp thư mục.
7. **Sheet từ điển dữ liệu đi kèm ngay trong workbook** — user KPIM đã quen định dạng này.

## 6. Cạm bẫy — KHÔNG chép sang bộ mới

- Tên cột chứa **ký tự vô hình** (zero-width space) và xuống dòng, ví dụ `"So T​-1 [triệu]\n(3)"` → so khớp chuỗi sẽ trượt. Phải làm sạch khi nạp.
- Phân cấp đơn vị ở cột `Đơn vị gốc` mã hoá bằng **thụt đầu dòng** (`"            - KV TP Cao Bằng"`). Không dùng khoảng trắng làm dữ liệu.
- Báo cáo có **header hai tầng** nên `pandas`/Power Query đọc thẳng sẽ ra `Unnamed: 2`… Phải bỏ qua số dòng đầu và tự đặt tên cột.
- Tên file gốc có lỗi chính tả (`Báo cáo KH Hợp Nhát`) — sửa ở bộ mới.
- Đơn vị tính lẫn lộn: doanh thu tính bằng **triệu đồng**, doanh thu bình quân/thuê bao bằng **đồng**. Bắt buộc ghi `unit` trong dictionary.

## 7. Khi user nói "giống bộ này nhưng…"

| Yêu cầu | Đổi gì |
|---|---|
| Ngành khác có thuê bao (truyền hình, SaaS, phòng gym) | Giữ nguyên khung cân bằng đầu kỳ–cuối kỳ và bộ chỉ số churn/doanh thu bình quân/thuê bao; chỉ đổi danh mục sản phẩm |
| Không cần phân mảnh file | Giữ một bảng phẳng duy nhất grain kỳ × đơn vị × sản phẩm — đơn giản hơn nhiều |
| Cần cấp huyện/xã | Thêm cấp vào `Danh Mục Đơn Vị`, giữ nguyên cờ dòng chi tiết để không cộng trùng |
| Cần dữ liệu ngày thay vì tháng | Đổi grain sang ngày; cân bằng dòng vào–ra vẫn giữ nguyên nhưng khối lượng ×30 |
| Cần dạy Power Query dọn dữ liệu | Giữ đúng dạng báo cáo người-đọc (header 2 tầng, file phân mảnh) — đây là giá trị dạy học chính của bộ này |

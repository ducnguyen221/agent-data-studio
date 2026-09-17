# Data KPIM Bank — ngân hàng, dư nợ & tiền gửi

> Hồ sơ tham chiếu (distill 2026-08-18) từ một bộ dữ liệu dạy học nội bộ KPIM — bộ gốc không kèm trong repo.
> Thư mục nguồn còn có `sqlserver_schema.xlsx` (lược đồ SQL Server) và `Dữ liệu dư nợ và tiền gửi.xlsx`.

## 1. Tóm tắt

| | |
|---|---|
| Ngành | Ngân hàng bán lẻ, địa bàn TP HCM |
| Khoảng thời gian | Fact: 2025-01-01 → 2025-11-30 (số dư **cuối mỗi ngày**); tài khoản mở từ 1994, đáo hạn tới 2060 |
| Ngôn ngữ cột | Tiếng Việt không dấu, snake_case; tên sheet có dấu |
| Kiểu | Dim + fact snapshot hằng ngày, khối lượng lớn |
| Điểm mạnh để tái dùng | Mẫu duy nhất cho **đại lượng semi-additive** (số dư) và snapshot theo ngày |

## 2. Cấu trúc bảng

| Sheet | Loại | Grain | Dòng | Cột |
|---|---|---|---|---|
| `Khách Hàng` | dim | 1 khách (CIF) | 3.807 | 13 |
| `Cán Bộ` | dim | 1 cán bộ | 225 | 6 |
| `Sản Phẩm` | dim | 1 mã sản phẩm | 115 | 4 |
| `Phòng Ban` | dim | 1 phòng ban | 18 | 2 |
| `Khu Vực` | dim | 1 quận | 17 | 6 |
| `Phân Khúc` | dim | 1 phân khúc | 17 | 4 |
| `Tài Khoản Nợ` | dim/bridge | 1 tài khoản vay | 5.124 | 13 |
| `Tài khoản tiền gửi` | dim/bridge | 1 tài khoản tiền gửi | 4.515 | 13 |
| `Fact Dư Nợ` | fact | 1 tài khoản × ngày | ~200k+ | 7 |
| `Fact Tiền Gửi` | fact | 1 tài khoản × ngày | ~200k+ | 6 |

## 3. Cột đáng chú ý

| Cột | Bảng | Ghi chú thiết kế |
|---|---|---|
| `du_no_ngay_quy_doi`, `du_no_bq_quy_quy_doi`, `du_no_bq_nam_quy_doi` | Fact Dư Nợ | Số dư ngày + **bình quân quý/năm tính sẵn**. Số dư là semi-additive: cộng ngang tài khoản thì được, cộng dọc thời gian thì sai — nên bình quân phải tính trước ở tầng dữ liệu |
| `nguyen_te` vs `quy_doi` | cả 2 fact | Song song nguyên tệ và quy đổi VND — chuẩn khi có `loai_tien` |
| `nhom_no` | Fact Dư Nợ | Nhóm nợ 1–5 → nền tảng tính NPL, trích lập dự phòng |
| `ngay_mo_tai_khoan` / `ngay_dao_han` / `ngay_dong_tai_khoan` | tài khoản | Vòng đời hợp đồng; đáo hạn tới 2060 (vay dài hạn) — dữ liệu tương lai hợp lệ ở cột đáo hạn |
| `ma_can_bo`, `ma_phong_ban` | tài khoản | Gắn sở hữu để xếp hạng cán bộ/đơn vị |
| `dien_tich_km2`, `dan_so`, `mat_do`, `lat`, `long` | Khu Vực | **Dim kèm số liệu nền** → tính được thị phần, dư nợ/đầu người, bản đồ nhiệt |
| `ten_san_pham` + `ten_viet_gom` | Sản Phẩm | Tên đầy đủ để hiểu + tên viết gọn không dấu để hiển thị chật chỗ |
| `ma_phan_khuc`, `ten_phan_khuc`, `loai_phan_khuc` | Phân Khúc | Phân khúc dạng `KHCN HANG GOLD` — mã viết hoa không dấu |
| `diem_rui_ro` | Khách Hàng | Điểm rủi ro sẵn để phân nhóm |

## 4. KPI tiêu biểu

Dư nợ cuối kỳ / bình quân · Số dư tiền gửi cuối kỳ / bình quân · CASA · Tỷ lệ NPL theo nhóm nợ · Lãi suất bình quân · Dư nợ theo sản phẩm / phòng ban / cán bộ / quận · Số tài khoản mở mới và đóng theo tháng · Thị phần theo dân số địa bàn · Cơ cấu kỳ hạn.

## 5. Hình mẫu đáng tái dùng

1. **Snapshot hằng ngày** cho đại lượng tồn: mỗi tài khoản mỗi ngày một dòng. Khối lượng lớn nhưng là cách duy nhất tính đúng bình quân và biến động.
2. **Tính sẵn cột bình quân quý/năm** thay vì bắt người dùng viết DAX phức tạp — đánh dấu rõ `semi_additive` trong dictionary.
3. **Dim địa bàn có số liệu nền** (diện tích, dân số, toạ độ) để mở ra cả nhóm chỉ số tương đối.
4. **Tách bảng tài khoản khỏi bảng khách hàng**: một khách nhiều tài khoản, mỗi tài khoản một sản phẩm — tránh nhồi hết vào dim khách hàng.
5. **Ngày mở tài khoản trải rất dài** (1994→2025) tạo ra phân bố thâm niên thật, không phải ai cũng mới vào.

## 6. Cạm bẫy — KHÔNG chép sang bộ mới

- `CIF` để **kiểu số** (`3000000001`). Mã định danh phải là text, nếu không Excel/Power Query sẽ tự cộng, làm tròn, cắt số 0 đầu.
- Tên cột sai chính tả: `loai_phan_lhuc`, `du_no_bq_quy_quy_doi` (lặp "quy").
- Tên sheet không nhất quán hoa/thường: `Tài Khoản Nợ` vs `Tài khoản tiền gửi`.
- File 64 MB — mở chậm. Bộ mới nếu vượt ~200k dòng/bảng thì tách CSV/Parquet cho lớp chi tiết.

## 7. Khi user nói "giống bộ này nhưng…"

| Yêu cầu | Đổi gì |
|---|---|
| Chỉ cần tiền gửi (hoặc chỉ vay) | Bỏ hẳn nhánh còn lại — hai nhánh độc lập, không phá cấu trúc |
| Nhẹ hơn, không cần snapshot ngày | Đổi grain fact sang **cuối tháng**: ~1/30 khối lượng, vẫn tính được tăng trưởng, nhưng mất bình quân ngày |
| Thêm giao dịch | Thêm fact giao dịch (1 dòng = 1 giao dịch) song song fact số dư; giữ ràng buộc số dư cuối = số dư đầu + phát sinh |
| Ngành bảo hiểm / tài chính tiêu dùng | Giữ nguyên khung: khách → hợp đồng → snapshot số dư; đổi `nhom_no` thành trạng thái hợp đồng |
| Có kế hoạch giao chỉ tiêu | Thêm bảng kế hoạch grain phòng ban × tháng, so với dư nợ bình quân |

# Data KPIM Marketing — marketing đa kênh & outreach

> Hồ sơ tham chiếu (distill 2026-08-18) từ một bộ dữ liệu dạy học nội bộ KPIM — bộ gốc không kèm trong repo.
> Hai nhánh độc lập: `01_MASS_MEDIA` (nội dung đăng công khai) và `02_CUSTOMER_OUTREACH` (gửi tới từng khách).

## 1. Tóm tắt

| | |
|---|---|
| Ngành | Marketing ngân hàng (KPIM Bank), mốc "hiện tại" ≈ 2026-10-01 |
| Ngôn ngữ cột | Tiếng Việt không dấu, snake_case |
| Kiểu | Nhiều file: 1 workbook kế hoạch + file export nền tảng + 1 file fact cho mỗi chiến dịch |
| Điểm mạnh để tái dùng | Duy nhất có **phễu nhiều bước** và **nối kế hoạch ↔ kết quả từ nền tảng ngoài** |

## 2. Cấu trúc

### Nhánh A — `01_MASS_MEDIA`

| File / sheet | Loại | Grain | Dòng | Cột |
|---|---|---|---|---|
| `MassMedia_Campaigns.xlsx` → `Campaign` | dim | 1 chiến dịch | 6 | 16 |
| `MassMedia_Campaigns.xlsx` → `Post` | fact kế hoạch | 1 bài đăng | 261 | 15 |
| `Facebook Post Summary.csv` | kết quả nền tảng | 1 bài đăng | ~215 | 41 |
| `Youtube Video Summary.csv` | kết quả nền tảng | 1 video (+ dòng Total) | ~68 | 14 |

Khoá nối: `Post.id_bai_dang` = cột ID bài viết trong file export của nền tảng.

### Nhánh B — `02_CUSTOMER_OUTREACH`

| File / sheet | Loại | Grain | Dòng | Cột |
|---|---|---|---|---|
| `danh_sach.xlsx` → `khach_hang` | dim | 1 khách hàng | 2.000 | 32 |
| `danh_sach.xlsx` → `chien_dich` | dim | 1 đợt gửi (chiến dịch × kênh × mẫu) | 36 | 28 |
| `OC-yyyy-nn.xlsx` (5 file) | fact | **1 tin nhắn gửi tới 1 khách** | ~1.400/file | 22 |

Mã chiến dịch theo khuôn `OC-<năm>-<số thứ tự trong năm>`.

## 3. Cột đáng chú ý

| Cột | Bảng | Ghi chú thiết kế |
|---|---|---|
| `target_view` / `target_reach` / `target_interaction` | Post | Chỉ tiêu đặt trước cho từng bài → so với kết quả thật lấy từ export nền tảng |
| `pheu_tiep_can` | Post | Giai đoạn phễu của nội dung (nhận biết → cân nhắc → chuyển đổi) |
| `da_mo` / `ngay_mo`, `da_click` / `ngay_click`, `da_kich_hoat` / `ngay_kich_hoat` | fact OC | **Cặp cờ + mốc thời gian** cho mỗi bước phễu — vừa đếm được tỉ lệ, vừa tính được độ trễ |
| `ngay_giao_dich`, `gia_tri_thu_ve` | fact OC | Chuyển đổi cuối cùng ra tiền → tính được ROI thật của chiến dịch |
| `nhan_email`, `nhan_sms`, `nhan_app_push`, `nhan_cuoc_goi`, `nhan_zalo` | khach_hang | **Cờ đồng ý nhận tin theo từng kênh** — điều kiện lọc bắt buộc trước khi gửi |
| `diem_uu_tien`, `nhom_uu_tien` | khach_hang + fact | Điểm ưu tiên và nhóm High/Medium/Low, mang xuống cả fact để phân tích hiệu quả theo nhóm |
| `so_du_casa_bq`, `so_du_tien_gui_bq`, `so_du_no_bq` | khach_hang | Giá trị khách hàng lấy từ nghiệp vụ ngân hàng → nối được với `Data KPIM Bank` |
| `so_luong_gui/mo/click/kich_hoat`, `gia_tri_thu_ve` | chien_dich | **Số tổng hợp phải bằng tổng từ fact** — ràng buộc `sum_match` |
| `tong_budget`, `chi_phi` | Campaign / fact | Chi phí ở cả hai cấp → dựng được nghịch lý "kênh lãi nhưng tổng lỗ" |

## 4. KPI tiêu biểu

Tỉ lệ gửi thành công · Tỉ lệ mở · CTR và CTOR · Tỉ lệ kích hoạt · Tỉ lệ chuyển đổi ra giao dịch · Chi phí trên mỗi chuyển đổi · ROI theo chiến dịch/kênh/nhóm ưu tiên · Đạt chỉ tiêu view/tương tác theo bài đăng · Hiệu quả theo mẫu nội dung (A/B).

## 5. Hình mẫu đáng tái dùng

1. **Phễu nhiều bước bằng cặp cờ + mốc thời gian** trên cùng một dòng — đơn giản hơn bảng sự kiện, vẫn đủ để tính tỉ lệ và độ trễ. Ràng buộc: đã click thì phải đã mở; mốc sau ≥ mốc trước.
2. **Giữ nguyên định dạng export của nền tảng thật** thay vì tự đặt lại tên cột — người học gặp đúng file như ngoài đời và phải tự nối khoá.
3. **Số tổng hợp ở bảng chiến dịch = tổng từ fact**, không nhập tay — kiểm bằng rule.
4. **Cờ đồng ý theo từng kênh** — bất kỳ bộ dữ liệu marketing nào cũng phải có, nếu không thì phân tích sẽ dạy sai nghiệp vụ.
5. **Mã chiến dịch có khuôn** `OC-yyyy-nn` — nhìn mã biết năm và thứ tự.
6. **Một file fact cho mỗi chiến dịch** — dễ bàn giao từng đợt, nhưng phải append khi phân tích.

## 6. Cạm bẫy — KHÔNG chép sang bộ mới

- `khach_hang` chứa `email` và `dien_thoai` **dạng thô**. Bộ mới phải dùng `email_masked` / `sdt_masked`.
- Hai nhánh dùng quy ước mã khác nhau (`ma_bai_dang` vs `ma_khach_hang`) và bản gốc tiếng Anh còn tồn tại song song → dễ lẫn. Bộ mới chọn **một** ngôn ngữ và giữ đến cùng.
- Chiến dịch trạng thái "Đề xuất/Duyệt" có fact mẫu nhưng cột kết quả để trống — hợp lý về nghiệp vụ nhưng phải ghi rõ trong dictionary, nếu không người phân tích tưởng thiếu dữ liệu.
- Số liệu tổng ở `chien_dich` chỉ đúng nếu tất cả file fact đều được nạp; thiếu một file là lệch ngay.

## 7. Khi user nói "giống bộ này nhưng…"

| Yêu cầu | Đổi gì |
|---|---|
| Chỉ cần mass media | Bỏ hẳn nhánh outreach; giữ Campaign → Post → kết quả nền tảng |
| Chỉ cần outreach | Bỏ nhánh mass media; giữ khách hàng → đợt gửi → fact tin nhắn |
| Thương mại điện tử | Đổi "kích hoạt" thành "đặt hàng"; thêm giỏ hàng bỏ quên vào phễu |
| Cần A/B testing rõ hơn | Tách bảng mẫu nội dung riêng với `variant_code`, mỗi khách gán đúng một biến thể |
| Cần bảng sự kiện thay vì cờ | Đổi sang grain **1 dòng = 1 sự kiện** (gửi/mở/click/…) — phân tích linh hoạt hơn nhưng khối lượng lớn hơn nhiều |

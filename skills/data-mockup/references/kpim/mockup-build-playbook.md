# Build playbook — P3 SINH SỐ · P4 VERIFY · P5 ĐÓNG GÓI

Đọc file này khi đã có spec và bắt đầu **sinh dữ liệu**. Phần hỏi nghiệp vụ & thiết kế ở `mockup-design-playbook.md`.

---

## PHẦN 1 — Sinh số liệu "biết nói" (P3)

### Thứ tự sinh bắt buộc
`cfg_*` (tham số) → `dim_*` (danh mục) → `bridge_*` → `fact_*` → lớp nghiệp vụ (chiếu từ lớp DB).

Sinh ngược thứ tự này là tự tạo FK mồ côi.

### Seed
Một seed cho cả bộ, khai trong `dataset.yaml`. Trong generator dùng đúng một đối tượng random khởi tạo từ seed đó (`rng = mockpack.rng(SEED)`), không gọi `random.*` toàn cục xen kẽ — trộn hai nguồn ngẫu nhiên là mất tính tái lập.

Kiểm tra seed hoạt động: chạy generator 2 lần, `diff` hai lần xuất phải rỗng.

### Chống dữ liệu phẳng — dùng đúng phân phối

| Loại đại lượng | Phân phối nên dùng | Vì sao |
|---|---|---|
| Giá trị đơn hàng, doanh thu/khách | **lognormal** | Đuôi dài phải: nhiều đơn nhỏ, ít đơn rất lớn |
| Số lần mua / tần suất | **Poisson** hoặc geometric | Đếm sự kiện rời rạc |
| Tuổi, điểm số | **normal** cắt biên | Tập trung quanh trung bình |
| Chọn sản phẩm / khách VIP | **Pareto 80/20** | 20% mã chiếm ~80% doanh số — đúng thực tế bán lẻ |
| Tỉ lệ chuyển đổi từng bước | **phễu suy giảm** có nhiễu | Mỗi bước rơi, tỉ lệ dao động theo phân khúc |
| Thời điểm trong ngày | **đa đỉnh** (sáng/trưa/tối) | Hành vi người dùng không đều |

`mockpack.py` có sẵn helper cho tất cả các dạng trên — đọc docstring trong file.

### CÂU CHUYỆN TRONG SỐ LIỆU — 8 hình dạng bắt buộc cài

Tiêu chuẩn nghiệm thu của một bộ mockup không phải "đủ dòng" mà là: **mở dashboard lên là có chuyện để kể**. Dữ liệu đúng cấu trúc nhưng phẳng lì thì mọi biểu đồ đều vô nghĩa và người học/người xem không rút ra được kết luận nào.

| # | Hình dạng | Phải thấy được gì trên dashboard | Cách cài |
|---|---|---|---|
| 1 | **Xu hướng dài hạn** | Đường doanh thu năm nay cao/thấp hơn năm ngoái rõ rệt | Hệ số tăng trưởng tuyến tính 10–40%/năm áp lên trọng số ngày (`date_series(trend=…)`) |
| 2 | **Mùa vụ lặp lại** | Đỉnh Tết, đỉnh cuối năm, trũng sau Tết; cuối tuần cao hơn ngày thường | Trọng số theo tháng + theo thứ; **lặp lại được ở mọi năm** để so cùng kỳ có ý nghĩa |
| 3 | **Tăng và GIẢM xen kẽ** | Có tháng tăng, có tháng giảm so tháng trước — không phải tháng nào cũng tăng | Nhiễu ±10–15% đủ lớn để đảo chiều MoM ở vài tháng; tránh đơn điệu tăng |
| 4 | **Kế hoạch vs thực hiện** | Có đơn vị/tháng **đạt**, có đơn vị/tháng **hụt** kế hoạch | Sinh actual trước, rồi đặt target = actual × hệ số ngẫu nhiên quanh 1 (0,85–1,15) → tỉ lệ đạt rơi vào 50–70%. **Đừng** sinh target rồi ép actual bám sát |
| 5 | **So sánh kỳ** | MoM, QoQ, YoY, luỹ kế đều tính được và ra số khác nhau | Phủ **tối thiểu 24 tháng liền mạch** (lý tưởng 36) — dưới 13 tháng là không có YoY |
| 6 | **Chênh lệch giữa các chiều** | Có cửa hàng/sản phẩm/kênh dẫn đầu và có nhóm tụt hậu rõ rệt | Gán hệ số hiệu suất riêng cho từng thành viên dim (0,6–1,6), giữ cố định theo seed |
| 7 | **Dịch chuyển cơ cấu (mix shift)** | Tỉ trọng kênh Online tăng dần, Offline giảm dần theo thời gian | Cho tỉ lệ chọn kênh/nhóm hàng thay đổi tuyến tính theo thời gian, không cố định |
| 8 | **Sự kiện bất thường có lý do** | 2–5 điểm gãy giải thích được (campaign lớn, đứt hàng, viral, sự cố) | Nhân hệ số đột biến vào một khoảng ngày cụ thể và **ghi lại vào §1 của spec** để người phân tích tìm ra thì có đáp án |

Kiểm tra nhanh trước khi đóng gói — pivot doanh thu theo tháng rồi tự hỏi:
- Năm sau có khác năm trước không? · Có tháng nào giảm so tháng trước không? · Tỉ lệ đạt kế hoạch có nằm giữa 40–80% không? · Top 5 và bottom 5 có cách biệt không? · Cơ cấu kênh đầu kỳ và cuối kỳ có khác nhau không?

Trả lời "không" cho câu nào thì quay lại sửa generator — đó là lỗi thiết kế, không phải chuyện thẩm mỹ.

### Tương quan cài sẵn — sinh theo nhân quả, không ghép cột độc lập
Chọn phân khúc khách trước → phân khúc quyết định tần suất mua và giá trị đơn → giá trị đơn quyết định mức chiết khấu → chiết khấu ăn vào biên lợi nhuận. Chuỗi nhân quả này là thứ làm cho việc "slice theo phân khúc" ra được kết luận. Cài tối thiểu 2 chuỗi như vậy, và **1 nghịch lý dạy được** nếu là lab (ROI từng kênh dương nhưng tổng âm khi tính đủ chi phí cố định; chi nhánh doanh thu cao nhất lại có biên thấp nhất).

### Ràng buộc nhất quán khi có dòng vào–dòng ra
Bất cứ đại lượng nào có "đầu kỳ / tăng / giảm / cuối kỳ" (thuê bao, tồn kho, nhân sự, dư nợ) đều phải **cân bằng**: `cuối kỳ = đầu kỳ + phát triển mới − rời bỏ − kết thúc − tạm ngưng`, và **cuối kỳ tháng N = đầu kỳ tháng N+1**. Khai thành rule `expression` khi các cột nằm cùng dòng. Đây là lỗi phổ biến nhất khi sinh dữ liệu kiểu này và người phân tích phát hiện ngay lập tức.

### Lỗi cài cắm có chủ đích (chỉ khi mục đích là dạy học)
Khai báo TRƯỚC trong `rules:` với `intentional_fail: true` kèm `note` giải thích. Các dạng hay dùng:
- Trùng bản ghi (cùng nghiệp vụ, khác ID) — dạy dedup.
- Thiếu giá trị ở cột không bắt buộc — dạy xử lý null.
- Sai chính tả danh mục ("Hà Nội" / "Ha Noi" / "HN") — dạy chuẩn hoá.
- Ngoại lai cực đoan — dạy phát hiện outlier.
- Lệch tổng giữa bảng chi tiết và bảng tổng hợp — dạy đối soát.

Số lỗi cài cắm nên ≤ 5% số dòng, và **luôn** liệt kê trong `DATA_QUALITY_REPORT.md` để người chấm biết đâu là chủ đích.

### Không PII
Không lấy dữ liệu người thật. Họ tên ghép từ danh sách họ/tên đệm/tên phổ biến; email/SĐT sinh theo khuôn rồi che (`ng***@gm***.com`, `09*****678`). Nếu cần khoá định danh, dùng hash giả lập, không hash từ dữ liệu thật.

---

## PHẦN 1B — Cơ chế đặt tên đối tượng

Tên là thứ người xem nhìn thấy đầu tiên. `Sản phẩm 001`, `Khách hàng A`, `Cửa hàng 3` làm cả bộ dữ liệu trông giả ngay lập tức và không slice được theo chiều nào có ý nghĩa. Quy tắc chung: **tên riêng của tổ chức thì hư cấu, mọi thứ còn lại lấy theo thực tế** (xem chính sách thương hiệu ở `mockup-design-playbook.md` Nhóm 6).

| Loại đối tượng | Công thức đặt tên | Ví dụ thật đang dùng |
|---|---|---|
| **Điểm bán / chi nhánh** | `<Thương hiệu> <địa danh thật>` — lấy tên đường/khu/toà nhà có thật trong quận đó | `KPIM Mart Lĩnh Nam`, `KPIM Mart CT1A Hateco Apolo`, `Chi nhánh Hải Phòng`, `Phòng Giao dịch Đắk Lắk` |
| **Địa bàn** | Danh mục hành chính THẬT, **kèm thuộc tính nền**: diện tích, dân số, toạ độ | `Quận Phú Nhuận` (4,18 km², 203.767 dân, lat/long) — nhờ có dân số mới tính được mật độ, thị phần, doanh thu/đầu người |
| **Hàng hoá tiêu dùng** | Tên hàng thông dụng theo ngành hàng, không đánh số | `Tiêu xay`, `Ngũ vị hương`, `Bột nếp` trong `Gia vị – nguyên liệu nấu ăn` |
| **Sản phẩm dịch vụ** | Tên đầy đủ mô tả đúng nghiệp vụ **+ tên viết gọn không dấu** để hiển thị | `Tiền gửi thanh toán KHCN gói KPIM-Super (VND)` ↔ `TG TT KHCN KPIM-Super VND` |
| **Người** | Họ + đệm + tên ghép từ danh sách phổ biến, giữ phân bố họ gần thực tế | `Nguyễn Quang Đức`, `Phan Tuấn Yến` |
| **Mã định danh** | Prefix + số thứ tự zero-pad, hoặc dải số bắt đầu từ mốc nhận diện được | `KH-000123`, `NV0001`, `CUS-000001`, CIF bắt đầu từ `3000000001` |
| **Danh mục nội bộ** | Mã ngắn viết hoa không dấu + tên đầy đủ có dấu | `KHCN` / "Khách hàng Cá nhân"; `QLRR` / "Quản lý rủi ro"; `KHCN HANG GOLD` |
| **Đơn vị nhiều cấp** | Bảng cây riêng: `cấp` (số) + `tên cấp` + **cờ dòng chi tiết** | Tập đoàn → Khối → Tỉnh/TP → Khu vực; cờ "là dòng chi tiết" để tổng không bị cộng trùng |

Bốn luật kèm theo:

1. **Tên ổn định theo seed** — sinh tên một lần vào dim, fact chỉ tham chiếu khoá. Sinh tên lại ở nhiều chỗ là mỗi bảng một tên khác nhau cho cùng một thực thể.
2. **Tên phải phân bố không đều** — vài cửa hàng/sản phẩm phải nổi bật hẳn (xem hình dạng #6), nếu không mọi bảng xếp hạng đều vô nghĩa.
3. **Địa bàn phải khớp cụm** — quận phải thuộc đúng tỉnh/thành, chi nhánh phải nằm đúng khu vực. Trộn "Quận Phú Nhuận, Hà Nội" là người trong ngành phát hiện ngay.
4. **Đừng tách tên người thành họ/tên nếu không cần** — bộ Mart hiện có `first_name`/`last_name` tách sai (một cột giữ gần như cả họ tên). Tiếng Việt tách họ–đệm–tên rất dễ sai; giữ một cột `ho_ten` là an toàn nhất.

---

## PHẦN 2 — Catalog rule verify (P4)

### Rule cơ bản — TỰ SUY từ spec, không cần khai
`mockpack.py verify` tự sinh các rule sau từ `tables:` trong YAML:

| Rule | Nội dung |
|---|---|
| `pk_unique` | Cột `key: PK` không trùng, không rỗng |
| `fk_subset` | Giá trị FK ⊆ tập PK bảng đích (bỏ qua null nếu cột nullable) |
| `not_null` | Cột `nullable: false` không có ô trống |
| `dtype` | Ép được về đúng `type` đã khai (kể cả `bool` — giá trị rác ở cột bool cũng bị bắt) |
| `enum_values` | Giá trị ∈ `values:` đã liệt kê |
| `range` | Trong `min`/`max` nếu có khai |
| `as_of` | Không có `date`/`timestamp` vượt `as_of_date` |
| `no_pii` | Không có tên cột nằm trong danh sách PII cấm (email, phone, cccd, full_name... trừ bản `*_masked`/`*_hash`) |
| `row_count` | Số dòng khớp `rows:` (±10% nếu khai `rows_tolerance`) |

Ngoài PASS/FAIL/WAIVED còn mức **WARN** — nhắc nhở, không chặn exit code: cột khai `pii: true` luôn ra WARN `pii_declared` để nhắc "phải là dữ liệu giả lập/đã che, không lấy từ người thật".

### Rule nghiệp vụ — PHẢI khai trong `rules:`

| `kind` | Dùng cho | Tham số |
|---|---|---|
| `expression` | Ràng buộc số học trên từng dòng | `table`, `expr` (biểu thức pandas, phải trả về boolean) |
| `funnel` | Phễu đơn điệu giảm dần | `table`, `steps` (danh sách cột đếm hoặc điều kiện) |
| `sum_match` | Tổng bảng chi tiết = cột tổng ở bảng cha | `child`, `child_col`, `parent`, `parent_col`, `on`, `tolerance` |
| `ratio` | Tỉ lệ nằm trong khoảng hợp lý | `table`, `numerator`, `denominator`, `min`, `max` |
| `unique` | Bộ cột duy nhất (khoá tổ hợp) | `table`, `columns` |
| `row_count` | Chốt số dòng chính xác | `table`, `expected` |

### Cổng P4
0 FAIL ngoài rule `intentional_fail`. Có FAIL thật → quay lại P3, hoặc P2 nếu chính spec sai. **Không bao giờ sửa tay dữ liệu để rule xanh** — đó là che lỗi, lần re-gen sau lỗi quay lại.

---

## PHẦN 3 — Đóng gói Excel (P5)

### Thứ tự sheet chuẩn
1. `00_README` — tên bộ dữ liệu, mục đích, seed, `as_of_date`, ngày sinh, danh sách sheet, cảnh báo "dữ liệu giả lập".
2. `01_Data_Dictionary` — mỗi dòng 1 cột dữ liệu, đủ 20 thuộc tính (xem dưới).
3. `02_Relationships` — from → to, cardinality, mô tả quan hệ.
4. `03_Metrics` — KPI, công thức, đơn vị, bảng nguồn, định nghĩa.
5. Các sheet dữ liệu, theo thứ tự cfg → dim → fact.

### Cột chuẩn của sheet Data Dictionary
`table` · `table_label` · `table_type` · `grain` · `sheet` · `column_order` · `column` · `column_label` · `data_type` · `format` · `nullable` · `key` · `allowed_values` · `unit` · `definition` · `calc_rule` · `additive` · `pii` · `source_system` · `example`

Sinh tự động từ YAML — không viết tay, không sửa tay trong Excel.

### Bẫy Excel — `mockpack.py` đã cưỡng chế, đừng tự làm lại bằng tay

| Bẫy | Hậu quả | Cách xử lý trong pack |
|---|---|---|
| Mã dạng `0123`, `KH-000123` | Excel cắt số 0 đầu, đổi thành số | Ghi dạng text, format `@` |
| Ngày thành `45292` | Người mở file không đọc được | Ghi kiểu date thật + number_format `dd/mm/yyyy` |
| Số lưu dạng text | Pivot/SUM ra 0 | Ép numeric trước khi ghi |
| Merge cell trong vùng dữ liệu | Pivot và Power Query gãy | Cấm merge, chỉ dùng ở README |
| Không freeze header | Bảng dài không đọc được | Freeze dòng 1 + autofilter |
| Tên sheet > 31 ký tự hoặc có `[ ] : * ? / \` | Excel từ chối tạo | Tự cắt & thay ký tự cấm |
| Số quá lớn (> 15 chữ số) | Mất độ chính xác | Để dạng text nếu là mã, không phải số đo |
| Ô bắt đầu bằng `=`, `+`, `-`, `@` | Excel hiểu là công thức / rủi ro CSV injection | Prefix `'` khi ghi |

Thêm bốn bẫy gặp trong dữ liệu thật của KPIM — **kiểm khi nhận file mẫu từ user**, đừng bê nguyên vào bộ mới:

| Bẫy | Dấu hiệu ngoài đời | Xử lý |
|---|---|---|
| Khoảng trắng thừa / ký tự vô hình trong tên cột | `'country '`, header chứa zero-width space `​` | `strip()` + gỡ ký tự điều khiển khi nạp; đặt lại tên chuẩn trong spec |
| Sai chính tả tên cột lan ra cả hệ thống | `heigth`, `uom_volumn`, `loai_phan_lhuc` | Sửa ở spec ngay từ đầu — đã lỡ phát hành thì giữ nguyên và ghi chú, đổi tên giữa chừng làm gãy báo cáo hạ nguồn |
| Phân cấp mã hoá bằng thụt đầu dòng | `"            - KV TP Cao Bằng"` | Không dùng khoảng trắng làm dữ liệu. Tách thành cột `cấp` + `mã cha` + cờ dòng chi tiết |
| Mã định danh để kiểu số | CIF `3000000001` là số nguyên | Mã là text. Để số thì Excel/Power Query sẽ tự cộng, tự làm tròn, tự cắt số 0 đầu |

### Hai định dạng bàn giao — đừng trộn vào nhau

| | **Bảng máy đọc** (mặc định) | **Báo cáo người đọc** |
|---|---|---|
| Hình dạng | 1 dòng tiêu đề, 1 dòng = 1 bản ghi, không merge | Tiêu đề nhiều tầng, nhóm cột (Tháng / Luỹ kế / Năm), chú thích công thức `(4)=(2)/(1)` |
| Dùng để | Nạp Power BI, pivot, phân tích | In ra họp, ký duyệt |
| Ví dụ thật | `Data KPIM Mart` các sheet `fact_*`/`dim_*` | `Kế hoạch doanh thu.xlsx` của Mart |

Luật: **luôn sinh bảng máy đọc trước** làm nguồn sự thật. Báo cáo người đọc chỉ là bản trình bày dựng thêm từ đó — và chỉ làm khi user yêu cầu rõ (thường là để dạy Power Query dọn dữ liệu thô). Không bao giờ để báo cáo người đọc làm nguồn dữ liệu duy nhất.

### Khi user muốn "giống hệ thống thật xuất ra"
Hệ thống thật thường xuất **nhiều file cùng cấu trúc, phân mảnh theo kỳ** — ví dụ thư mục `MM-DD-YYYY` × loại báo cáo × dòng sản phẩm. Nếu user cần đúng cảm giác đó: giữ một bảng nguồn duy nhất trong spec, rồi **cắt ra file theo kỳ ở bước cuối**, đặt tên theo khuôn cố định. Đừng sinh riêng từng file — sẽ lệch số giữa các mảnh.

### Cổng P5
Mở file: mọi sheet dữ liệu có số cột khớp Data Dictionary; chạy lại `verify` trên chính file `.xlsx` vẫn PASS (kiểm tra khâu ghi không làm hỏng kiểu dữ liệu).

### Khi dữ liệu quá lớn
Excel chịu được ~1.048.576 dòng/sheet nhưng file > 50MB mở rất chậm. Vượt ~200.000 dòng/bảng: giữ Excel cho lớp nghiệp vụ + dictionary, xuất lớp chi tiết ra CSV/Parquet trong thư mục `_detail/`, và ghi rõ trong `00_README`.

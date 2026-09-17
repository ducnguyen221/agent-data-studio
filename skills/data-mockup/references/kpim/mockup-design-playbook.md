# Design playbook — P1 INTERVIEW & P2 THIẾT KẾ

Đọc file này khi đang **hỏi nghiệp vụ** và **thiết kế cấu trúc**. Phần sinh số & đóng gói ở `mockup-build-playbook.md`.

---

## PHẦN 0 — Cách hỏi: agent DẪN DẮT, không phỏng vấn thụ động

Người dùng hầu như không bao giờ mô tả đủ. Nhiệm vụ của agent **không phải** chép lại yêu cầu mơ hồ rồi sinh bừa, mà là **làm rõ tới mức dựng được**. Sáu luật:

1. **Không hỏi câu trống.** Mỗi câu hỏi kèm 2–4 phương án + khuyến nghị của bạn. Hỏi "bạn muốn bao nhiêu dòng?" là đẩy việc cho user; hỏi "tôi đề xuất 6.000 dòng phủ 2 năm — đủ thấy mùa vụ và so cùng kỳ; muốn nhẹ hơn thì 2.000/1 năm" mới là tư vấn.
2. **Suy diễn trước, hỏi để xác nhận.** Từ một câu "làm data bán lẻ", bạn đã suy được star schema, grain, 6 KPI. Trình bản nháp đó ra và hỏi "đúng hướng chưa?", đừng bắt user kể lại từ đầu.
3. **Hỏi theo lô, tối đa 3 vòng.** Vòng 1: mục đích + phạm vi + grain. Vòng 2: KPI + khối lượng + thời gian. Vòng 3: ràng buộc + tên gọi + lỗi cài cắm. Hỏi lắt nhắt từng câu làm user nản và bỏ ngang.
4. **Mỗi vòng phải thu hẹp không gian thiết kế.** Câu hỏi nào mà trả lời kiểu gì cũng không đổi thiết kế thì đừng hỏi.
5. **User không biết / không trả lời → agent tự quyết.** Chọn mặc định hợp lý theo ngành, nói rõ "tôi giả định X", và ghi vào §1.6 Giả định của `DATASET_SPEC.md`. Không được đứng im chờ.
6. **Không hỏi thứ tra được.** User đã đưa file mẫu/ảnh chụp báo cáo → đọc trước rồi hỏi phần còn thiếu. Hỏi lại thứ họ vừa đưa là mất uy tín ngay vòng đầu.

### Yêu cầu mơ hồ → phải làm rõ ngay (kèm mặc định để user chỉ cần gật)

| User nói | Cái đang thiếu | Hỏi lại thế nào |
|---|---|---|
| "Làm data bán hàng" | grain, trả hàng, kế hoạch, kênh | "1 dòng = 1 dòng hàng trong đơn (khuyến nghị) hay 1 đơn? Có cần bảng kế hoạch để so đạt/không đạt không? Có đơn huỷ/trả hàng không?" |
| "Data nhân sự" | ảnh chụp hay lịch sử, có nghỉ việc, có lương | "Cần theo dõi biến động (vào/ra, đổi phòng ban) hay chỉ danh sách hiện tại? Có gộp chấm công + lương không?" |
| "Data ngân hàng" | dư nợ là số dư ngày hay cuối kỳ | "Dư nợ/tiền gửi lấy **số dư cuối ngày** (khuyến nghị — tính được bình quân) hay chỉ số cuối tháng? Có cần nhóm nợ để tính NPL không?" |
| "Data marketing" | mass media hay outreach từng KH | "Đo hiệu quả **nội dung đăng** (post/campaign) hay **chiến dịch gửi tới từng khách** (email/SMS)? Hai hướng khác hẳn nhau về bảng." |
| "Data telecom" | thuê bao hay doanh thu, cấp đơn vị | "Trọng tâm là **biến động thuê bao** (đầu kỳ/phát triển mới/rời mạng) hay **doanh thu theo kế hoạch**? Cắt tới cấp tỉnh hay cấp huyện/khu vực?" |
| "Khoảng 1.000 dòng" | dòng của bảng nào | "1.000 dòng đó là giao dịch, hay khách hàng? Fact thường phải lớn hơn dim 10–100 lần mới ra biểu đồ đẹp." |
| "Dữ liệu 3 năm" | mốc kết thúc | "Ba năm tới **hôm nay** (số liệu năm hiện tại còn dở) hay tới **hết năm trước** (năm nào cũng đủ 12 tháng)?" |
| "Cho giống thật" | giống ở mức nào | "Giống về **hình dạng số** (mùa vụ, tăng trưởng, 80/20) là mặc định. Có cần giống cả **tên thương hiệu/địa bàn thật** không?" |
| "Để dựng dashboard cho đẹp" | chưa có KPI | "Kể tôi nghe 5 câu hỏi sếp bạn sẽ hỏi khi mở dashboard — tôi thiết kế dữ liệu để trả lời đúng 5 câu đó." |
| "Dữ liệu giống hệ thống X" | định dạng export | "Bạn export được 1 file mẫu (kể cả rỗng, chỉ cần dòng tiêu đề) không? Có mẫu thì tôi bám đúng cột, khỏi đoán." |

### 12 điểm phải có câu trả lời trước khi thiết kế (giả định cũng được, nhưng phải ghi ra)

Mục đích · ngành/tổ chức · grain bảng chính · danh sách bảng · khoảng thời gian · mốc "hiện tại" · khối lượng từng bảng · 5–15 câu hỏi phân tích · có kế hoạch để so sánh không · ngôn ngữ & quy ước tên · chính sách PII · có lỗi cài cắm không.

### Chốt bằng tóm tắt ngược
Trước khi viết spec, đọc lại cho user một đoạn ngắn: *"Tôi sẽ dựng &lt;N bảng&gt; cho &lt;tổ chức&gt;, 1 dòng fact = &lt;grain&gt;, phủ &lt;khoảng thời gian&gt; tới mốc &lt;as_of&gt;, trả lời được &lt;3 câu tiêu biểu&gt;. Giả định: &lt;danh sách&gt;."* Sai chỗ nào user sẽ sửa ngay ở đây — rẻ hơn sửa sau khi đã sinh 60.000 dòng.

---

## PHẦN 1 — Bộ câu hỏi interview (6 nhóm)

Hỏi theo nhóm, mỗi lần 2–4 câu, ưu tiên câu hỏi trắc nghiệm để user chốt nhanh. Câu nào user không biết → đề xuất mặc định hợp lý và nói rõ "tôi giả định X, sai thì báo".

### Nhóm 1 — Bối cảnh
- Ngành/lĩnh vực? Tổ chức giả lập tên gì, quy mô nào (số chi nhánh/cửa hàng/nhân sự/khách)?
- Bộ dữ liệu này mô phỏng **một phòng ban** hay **cả doanh nghiệp**?
- Có hệ thống nguồn nào cần giả lập không (CRM, ERP, Core Banking, POS, LMS, web analytics)?

### Nhóm 2 — Mục đích sử dụng  *(quyết định độ khó và độ "bẩn" của data)*

| Mục đích | Hệ quả thiết kế |
|---|---|
| Dạy học / practice lab | Cần lỗi cài cắm có chủ đích, cần "câu chuyện" ẩn trong số (kênh lãi nhưng tổng lỗ...) |
| Demo BI / dựng dashboard mẫu | Data sạch, đủ chiều để slice, đủ dài để thấy xu hướng |
| Test hệ thống / seed database | Ưu tiên biên & ca lạ: null, chuỗi dài, unicode, trùng, ngày biên |
| POC / pitch khách hàng | Số phải đẹp và hợp lý theo ngành; nhãn tiếng Việt chuẩn |

### Nhóm 3 — Quy trình, thực thể, sự kiện
- Kể lại quy trình từ đầu đến cuối: ai làm gì, theo thứ tự nào?
- **Danh từ** trong lời kể → ứng viên bảng dim. **Động từ/sự kiện** → ứng viên bảng fact.
- Sự kiện xảy ra **một lần** (đơn hàng) hay **nhiều lần theo trạng thái** (mở → click → đăng ký → kích hoạt)?
- Có phễu (funnel) không? Các bước và tỉ lệ rơi ước lượng?

### Nhóm 4 — Grain, khối lượng, thời gian
- **1 dòng của bảng chính là gì?** (câu quan trọng nhất của cả pha — bắt user nói thành lời)
- Bao nhiêu dòng mỗi bảng? (gợi ý mặc định: dim 200–5.000, fact 5.000–200.000 — vượt 200k thì cân nhắc CSV thay Excel)
- Khoảng thời gian phủ (từ ngày → đến ngày)? Có cần so sánh cùng kỳ năm trước không?
- **Mốc "hiện tại" của bộ mock** (`as_of_date`) — mọi dữ liệu phải ≤ mốc này; kế hoạch tương lai để trạng thái `scheduled/planned`, không có số thực tế.

### Nhóm 5 — KPI & câu hỏi phân tích
- Bộ data này phải trả lời được **câu hỏi nào**? (liệt kê 5–15 câu)
- Mỗi KPI: công thức, đơn vị, tính trên bảng nào, kỳ vọng khoảng giá trị.
- Có so sánh kế hoạch ↔ thực tế không? (nếu có → cần bảng target riêng)
- Chiều phân tích nào chắc chắn phải có (thời gian, địa lý, sản phẩm, kênh, phân khúc KH, nhân sự)?

### Nhóm 6 — Ràng buộc
- Ngôn ngữ tên cột: tiếng Việt không dấu / tiếng Anh snake_case / nhãn Việt + tên kỹ thuật Anh (khuyến nghị: tên kỹ thuật Anh + nhãn Việt trong dictionary).
- Tiền tệ, đơn vị, định dạng ngày, múi giờ.
- PII: cột nào cần masked, cột nào cấm xuất hiện.
- **Lỗi cài cắm có chủ đích**: cần bao nhiêu, loại gì (trùng, thiếu, sai chính tả danh mục, ngoại lai, lệch tổng)?
- Lớp bàn giao: `business` (mặc định) / `database` / `both`.
- **Tên thương hiệu**: xem chính sách ngay dưới.

### Chính sách tên thương hiệu — hỏi rõ trước khi đặt

Người dùng hay nói "làm giống Vinamilk", "data cho Thế Giới Di Động". Ba hướng, phải chốt hướng nào trước khi sinh:

| Hướng | Khi nào dùng | Rủi ro |
|---|---|---|
| **Thương hiệu nhà KPIM** (khuyến nghị mặc định) | Lab đào tạo, demo, POC nội bộ | Không có. Dùng `KPIM Mart`, `KPIM Bank`, `KPIM Telecom`… — xem Phụ lục B |
| **Thương hiệu hư cấu riêng** | User muốn không dính KPIM | Phải đặt tên nghe thật mà không đụng doanh nghiệp có thật — kiểm tra bằng một lượt tìm kiếm nhanh |
| **Thương hiệu có thật** | Chỉ khi user là chính chủ, hoặc chỉ dùng nội bộ và user khẳng định chấp nhận | Số liệu bịa gắn tên hãng thật = có thể bị hiểu là dữ liệu thật của họ. Nếu buộc phải dùng, **bắt buộc** ghi cảnh báo ở `00_README` và đề nghị user không phát tán ra ngoài |

Ranh giới thực dụng: **tên riêng của tổ chức** (chuỗi, ngân hàng, nhà mạng) thì hư cấu; **danh mục ngành hàng, tên hàng hoá thông dụng, địa danh hành chính** thì dùng tên thật cho tự nhiên ("Gia vị – nguyên liệu nấu ăn", "Tiêu xay", "Quận Phú Nhuận", "Cao Bằng"). Nếu bộ dữ liệu cần **tên nhà cung cấp/nhãn hàng**, ưu tiên nhãn hư cấu; dùng nhãn có thật thì phải là thông tin phổ thông (tên nhãn) chứ không gắn số liệu kinh doanh nhạy cảm cho họ.

### Cổng P1
Không đi tiếp nếu chưa trả lời được:
1. 1 dòng của bảng chính là gì?
2. Bộ data trả lời được câu hỏi nào?

---

## PHẦN 2 — Thiết kế qua 3 lăng kính

Làm theo thứ tự BA → DE → DA. Mỗi lăng kính có sản phẩm riêng ghi vào spec.

### Lăng kính 1 — Chuyên gia nghiệp vụ (BA)
Mục tiêu: cấu trúc phải **kể đúng câu chuyện nghiệp vụ**.

- Vẽ chuỗi sự kiện theo dòng thời gian trước khi nghĩ tới bảng.
- Mỗi bảng phải trả lời được: *bảng này ghi lại chuyện gì trong đời thực?* Không trả lời được = bảng thừa.
- Định nghĩa nghiệp vụ từng cột viết cho **người không biết kỹ thuật** đọc hiểu ("Doanh thu thuần sau chiết khấu, chưa gồm VAT"), không diễn giải lại tên cột bằng lời.
- Danh mục (enum) phải là danh mục **có thật trong ngành**, đóng và hữu hạn: trạng thái đơn hàng, nhóm sản phẩm, kênh bán, lý do huỷ.
- Ghi rõ quy tắc nghiệp vụ dạng câu: "đơn huỷ không tính doanh thu", "1 khách chỉ có 1 hạng thẻ tại 1 thời điểm".

### Lăng kính 2 — Data engineer (DE)
Mục tiêu: cấu trúc **chịu được** khi nạp vào DB / Power BI.

- **Grain trước, cột sau.** Viết grain thành câu, rồi mới liệt kê cột. Cột nào không được xác định bởi grain → thuộc bảng khác.
- **Star schema** là mặc định: fact ở giữa (số đo + khoá), dim xung quanh (thuộc tính mô tả). Snowflake chỉ khi dim quá lớn và thật sự dùng lại.
- **Khoá**: PK là surrogate dạng chuỗi có prefix (`KH-000123`, `DH-0000451`) — dễ đọc, không lẫn kiểu số, không mất số 0 đầu. FK phải là tập con của PK bảng đích, không có bản ghi mồ côi.
- **Kiểu dữ liệu** khai tường minh: `text | int | decimal | date | timestamp | bool | enum`. Không để Excel tự đoán.
- **Cột kỹ thuật**: mọi fact có `load_ts`; bảng có phiên bản dùng `valid_from/valid_to/is_current` (SCD2) hoặc `snapshot_date` (bảng chụp).
- **Naming**: snake_case, tiền tố `dim_ / fact_ / bridge_ / cfg_ / log_`, tên bảng số ít, không viết tắt tuỳ hứng, cột khoá cùng tên ở cả hai bảng.
- **Additive**: đánh dấu từng số đo là `additive` (cộng được mọi chiều: số lượng, doanh thu), `semi_additive` (cộng theo chiều khác nhưng không theo thời gian: số dư, tồn kho), `non_additive` (không cộng được: đơn giá, tỉ lệ, %). Sai chỗ này là dashboard cộng bậy.
- **Bảng thời gian**: luôn có `dim_date` phủ từ min→max ngày (kể cả khi lớp nghiệp vụ không xuất ra).

### Lăng kính 3 — Data analyst (DA)
Mục tiêu: số liệu **có ý nghĩa khi vẽ lên biểu đồ**.

- Với mỗi KPI trong `metrics`, tự hỏi: vẽ theo tháng thì thấy gì? Không thấy gì thú vị = thiết kế còn thiếu biến động.
- Cài sẵn **ít nhất 2 tương quan** đọc ra được (khách phân khúc cao chi tiêu nhiều hơn; kênh A rẻ hơn nhưng chất lượng lead thấp hơn).
- Cài sẵn **1 nghịch lý dạy được** nếu là practice lab (ROI từng kênh dương nhưng tổng âm khi tính đủ chi phí cố định).
- Đảm bảo mọi chiều phân tích có **đủ độ phủ**: mỗi giá trị danh mục phải có đủ dòng để không bị mẫu quá nhỏ.
- Kiểm tra lại "câu hỏi phân tích" ở Nhóm 5: từng câu phải chỉ ra được **cột nào + phép tính nào** trả lời. Câu nào không chỉ ra được → thiếu bảng/cột.

### Cổng P2
Mọi bảng có `grain` bằng lời · mọi cột có `type` + `definition` · mọi FK trỏ PK có thật · mọi KPI tính được từ cột đã khai · mọi enum liệt kê hết giá trị.

---

## PHỤ LỤC A — 8 domain gợi ý sẵn

Dùng khi user chưa có yêu cầu rõ: đưa danh sách này cho chọn, rồi hỏi tiếp Nhóm 4–6. Mỗi domain là **điểm khởi đầu**, không phải khuôn cứng.

| # | Domain | Bảng lõi | Grain fact chính | KPI tiêu biểu | Điểm dạy được |
|---|---|---|---|---|---|
| 1 | **Bán lẻ / chuỗi cửa hàng** | dim_khach_hang, dim_san_pham, dim_cua_hang, dim_date, fact_don_hang, fact_ke_hoach | 1 dòng / dòng hàng trong đơn | Doanh thu, biên gộp, AOV, đạt kế hoạch | Giá vốn vs giá bán, mùa vụ lễ Tết |
| 2 | **Ngân hàng — marketing/outreach** | dim_khach_hang, dim_san_pham, dim_chien_dich, dim_mau_tin, fact_gui_tin, fact_su_kien, fact_chuyen_doi | 1 dòng / tin nhắn gửi tới 1 KH | Delivery/Open/CTOR, Lead rate, ROI | Phễu nhiều bước, consent, tần suất gửi |
| 3 | **Nhân sự (HR)** | dim_nhan_vien, dim_phong_ban, dim_chuc_danh, fact_cham_cong, fact_luong, fact_tuyen_dung | 1 dòng / nhân viên × tháng | Headcount, turnover, chi phí/đầu người, time-to-hire | SCD2 khi đổi phòng ban/chức danh |
| 4 | **Kho vận / chuỗi cung ứng** | dim_kho, dim_hang_hoa, dim_ncc, fact_nhap, fact_xuat, fact_ton_kho | 1 dòng / phiếu × mặt hàng | Vòng quay tồn, tỉ lệ hết hàng, OTIF | Tồn kho là semi-additive |
| 5 | **F&B / nhà hàng** | dim_mon, dim_chi_nhanh, dim_ca_lam, fact_hoa_don, fact_chi_tiet_hoa_don | 1 dòng / món trong hoá đơn | Doanh thu/giờ, món bán chạy, tỉ lệ huỷ món | Mùa vụ theo giờ và ngày trong tuần |
| 6 | **SaaS / thuê bao** | dim_khach_hang, dim_goi_cuoc, fact_dang_ky, fact_thanh_toan, fact_su_dung | 1 dòng / thuê bao × kỳ | MRR, churn, LTV, ARPU | Cohort, churn theo tháng gia nhập |
| 7 | **Đào tạo / LMS** | dim_hoc_vien, dim_khoa_hoc, dim_giang_vien, fact_ghi_danh, fact_diem, fact_tuong_tac | 1 dòng / học viên × khoá | Tỉ lệ hoàn thành, điểm TB, drop-off theo bài | Phễu tiến độ học, tương quan tương tác ↔ điểm |
| 8 | **Phòng khám / y tế** | dim_benh_nhan, dim_bac_si, dim_dich_vu, fact_lich_hen, fact_kham, fact_thanh_toan | 1 dòng / lượt khám | Lượt khám/ngày, no-show rate, doanh thu/bác sĩ | PII nặng → bắt buộc masked, no-show theo khung giờ |

**Ánh xạ đề xuất riêng của user vào khung này:** tìm domain gần nhất trong bảng, giữ nguyên cấu trúc lõi, thay danh từ/động từ theo ngành của user, rồi hỏi bù Nhóm 4–6.

---

## PHỤ LỤC B — Thư viện bộ dữ liệu KPIM có sẵn

Năm bộ đã dựng và đang dùng dạy học, đã được **distill thành hồ sơ tham chiếu ngay trong skill này**: `references/kpim/kpim-datasets/`. Mỗi hồ sơ có: cấu trúc bảng + grain + số dòng, các cột đáng chú ý, KPI tiêu biểu, hình mẫu đáng tái dùng, cạm bẫy không nên chép, và bảng "giống bộ này nhưng…" để biến thể nhanh.

| Tên chuẩn | Ngành | Đọc khi user cần |
|---|---|---|
| **Data KPIM Mart** | Bán lẻ chuỗi cửa hàng | Star schema kinh điển, kế hoạch vs thực hiện, RFM |
| **Data KPIM Bank** | Ngân hàng — dư nợ & tiền gửi | Số dư semi-additive, snapshot hằng ngày, khối lượng lớn |
| **Data KPIM HR** | Nhân sự | Vòng đời vào–ra, cây tổ chức tự trỏ, chấm công & lương |
| **Data KPIM Marketing** | Marketing đa kênh & outreach | Phễu nhiều bước, nối kế hoạch ↔ kết quả nền tảng, consent |
| **Data KPIM Telecom** | Telecom — thuê bao & doanh thu | Cân bằng đầu kỳ–cuối kỳ, cây đơn vị nhiều cấp, so kế hoạch/cùng kỳ, file phân mảnh theo tháng |

**Cách dùng:** user chưa rõ yêu cầu → đưa 5 tên cho chọn ("gần giống bộ nào nhất?") → đọc **đúng một** hồ sơ → lấy khung bảng/grain/KPI làm điểm xuất phát → hỏi bù Nhóm 4–6.

Hồ sơ là **bản distill, không phải dữ liệu**; bộ gốc là tài sản khoá học nội bộ, không kèm trong repo. Giới hạn: `kpim-datasets/README.md`.

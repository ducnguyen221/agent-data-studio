# Câu hỏi gợi ý KPI theo ngành và gợi ý màu

> Nguồn: từ vựng chỉ tiêu phổ biến trong từng ngành, viết lại thành **câu hỏi gợi ý**. Đây là **gợi ý để hỏi ngược khách ở Pha 0** của `discovery-process.md`, **không phải chuẩn, không phải luật**. Định nghĩa chính xác của mọi chỉ tiêu do khách xác nhận rồi ghi vào `METRICS_CALCULATION`.

## 1. Cách dùng
- Chọn hàng gần nhất với ngành của khách, hỏi các câu bên phải, ghi câu trả lời hoặc **Giả định** vào tài liệu dự án.
- Chỉ tiêu dạng **tồn / số dư / NAV** là cột STOCK: không cộng qua kỳ — xem mục 7b (Mẫu DAX hay gặp) trong `dax-best-practices.md` của `pbi-model`.

## 2. Câu hỏi gợi ý theo ngành

| Ngành | Nên hỏi để làm rõ |
|---|---|
| Ngân hàng | Báo cáo chủ yếu để theo dõi quy mô và cơ cấu tín dụng/huy động, hay chất lượng tín dụng? Có theo dõi tỷ lệ nợ xấu (NPL) không và nhóm nợ được định nghĩa theo quy chế nào? Có cần biên lãi thuần (NIM) và tỷ trọng tiền gửi không kỳ hạn (CASA) không, tính theo bình quân hay cuối kỳ? Doanh thu phí chia theo sản phẩm hay kênh? |
| Bán lẻ | Doanh thu cắt theo cửa hàng, ngành hàng hay kênh? Biên lợi nhuận tính trên giá vốn nào? Tồn kho đo bằng vòng quay, số ngày tồn hay tỷ lệ bán ra so với tồn? Tồn lấy ở cuối ngày hay cuối tháng? |
| Sản xuất | Sản lượng đếm ở công đoạn nào? Tỷ lệ lỗi tính trên sản phẩm hay lô? Hiệu suất thiết bị tổng thể (OEE) tính theo ca, dây chuyền hay máy, và dữ liệu thời gian dừng máy đến từ đâu? |
| Quản lý quỹ | Giá trị tài sản ròng (NAV) và tài sản quản lý (AUM) được chốt theo tần suất nào? Hiệu quả danh mục so với chỉ số tham chiếu nào? Rủi ro đo bằng những chỉ tiêu nào và nguồn giá là gì? |
| Nhân sự / đào tạo | Quy mô nhân sự đếm theo người hay quy đổi toàn thời gian (FTE)? Tỷ lệ nghỉ việc tính trên nhân sự bình quân hay đầu kỳ? Hoàn thành đào tạo đo theo khóa, theo giờ hay theo mục tiêu năng lực? |

## 3. Gợi ý màu theo ngữ cảnh (cũng chỉ là gợi ý)
- Bối cảnh ngân hàng và doanh nghiệp tại Việt Nam: tông **xanh dương** và **xanh lục-lam (teal)** thường được khách chấp nhận. Dùng như điểm khởi đầu để **hỏi**, không áp. Bộ nhận diện thương hiệu của khách quyết định.
- Nguyên tắc chung (vài màu, màu gắn với ý nghĩa chỉ số, xám cho mốc tham chiếu) nằm ở `design-standard.md` của `pbi-design` và `color.md` trong `references/microsoft/` của skill đó.
- **Lưu ý văn hóa:** ý nghĩa của đỏ/xanh khác nhau theo thị trường (ở một số thị trường Đông Á, đỏ là tăng). Xác nhận với khách trước khi gắn màu "tốt/xấu"; xem cảnh báo trong `color.md` nói trên.

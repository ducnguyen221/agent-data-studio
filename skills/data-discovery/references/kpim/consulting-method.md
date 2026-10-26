# Phương pháp tư vấn giải pháp dữ liệu / BI

> Nguồn: thực hành tư vấn BI của studio, viết lại theo khuôn của repo. Sự kiện cấp phép, SKU, giá của Microsoft đổi nhanh: mọi chỗ liên quan chỉ là **câu hỏi cần kiểm** với tài liệu Microsoft hiện hành, không phải số hay điều kiện. Agent đọc khi người dùng cần ý kiến về giải pháp hoặc kiến trúc dữ liệu *trước* khi khảo sát chi tiết (khảo sát chi tiết: `discovery-process.md`).

## 1. Nguyên tắc
1. Thứ tự **chuẩn hóa → tự động hóa → phân tích** đã nêu ở đầu `discovery-process.md`; không lặp lại ở đây.
2. **Một model dùng chung theo chủ đề**, không mỗi báo cáo một nguồn riêng: hai báo cáo cùng chủ đề mà tính khác nhau là lỗi thiết kế, không phải lỗi người dùng.
3. Kiến trúc chọn theo **độ trưởng thành của nguồn dữ liệu** (có khóa ổn định không, có từ điển không, ai sở hữu), không theo ngành.
4. **Không over-engineer.** Không hứa dữ liệu thời gian thực khi nút thắt nằm ở hệ thống vận hành đang cấp dữ liệu; nói rõ độ trễ thực tế đạt được.
5. Có chính kiến: đưa **một khuyến nghị rõ** kèm lý do và rủi ro, không chỉ liệt kê trung lập.

## 2. Chuỗi suy nghĩ khi tư vấn
Mục tiêu → nhu cầu báo cáo → nguồn, từ điển, mẫu biểu hiện có → mô hình dữ liệu → chỉ tiêu và công thức → chiều phân tích và so sánh → biểu đồ → danh sách trang → phạm vi → tiến độ → nhân sự → chi phí.
Nửa đầu chuỗi chính là 5 thành phần của Pha 1 trong `discovery-process.md`; nửa sau là phần lập kế hoạch (Pha 2).

## 3. Thiếu thông tin thì hỏi theo lưới
Gom câu hỏi vào một bảng gửi một lần (khớp nguyên tắc hỏi theo lô của `discovery-process.md`):

| Yêu cầu | Câu hỏi làm rõ | Mặc định nếu chưa biết |
|---|---|---|
| Người xem | Bao nhiêu người, trong hay ngoài tổ chức? | ghi **Giả định** |
| Bảo mật | Mỗi người chỉ được thấy phần dữ liệu của mình (RLS)? Có cột nhạy cảm? | hỏi PII ngay từ đầu |
| Nguồn | Dữ liệu nằm ở đâu, ai sở hữu, có từ điển chưa? | khảo sát nguồn trước khi cam kết |
| Độ tươi | Cập nhật theo ngày, giờ hay gần thời gian thực? | theo ngày |
| Ngân sách, thời hạn | Trần chi phí, mốc bắt buộc? | trình 2–3 phương án |

Luôn kết bằng câu: phương án chỉ là ước lượng trên thông tin đã nêu và **sẽ được xác nhận lại khi khảo sát chi tiết**.

## 4. Khuôn đầu ra
1. Tóm tắt bài toán và góc nhìn: 1–2 câu.
2. Thân: tiêu đề rõ, bảng so sánh **2–3 phương án** (ví dụ: cloud-native, hybrid, mã nguồn mở), checklist khi cần.
3. **Khuyến nghị** đánh số ưu tiên, một dòng cho phương án chọn; kèm Nên / Không nên.
4. Chi phí: so theo tài liệu Microsoft hiện hành, **không ghi số cứng**; con số nào cũng gắn "tùy dự án".
5. Bước tiếp theo và câu disclaimer ở mục 3.

## 5. Chọn cách phân phối Power BI (câu hỏi cần kiểm)
Ba biến quyết định: **số người xem**, **yêu cầu bảo mật/RLS**, **ngân sách**. Đừng trả bằng bảng giá; trả bằng các câu cần kiểm với Microsoft hiện hành:
- Người xem trong tổ chức hay bên ngoài? Có nhúng vào ứng dụng của khách không (xem `environments-and-embedding.md` của `pbi-publish`)?
- RLS có bắt buộc không, và tùy chọn phân phối đang cân nhắc có hỗ trợ RLS cho đúng nhóm người xem đó không?
- Mỗi người xem có cần giấy phép riêng không, hay dung lượng đã trả sẵn?
- Chi phí hiện hành tính theo người dùng hay theo dung lượng? (đọc trang giá/licensing mới nhất, đừng dùng số cũ.)

Không khẳng định kế hoạch kiểu "bắt đầu bản miễn phí rồi nâng sau" khi chưa kiểm điều kiện hiện hành.

## 6. Pháp lý và tuân thủ (câu hỏi cần kiểm)
Không trích điều khoản; chỉ nhắc người dùng kiểm với bộ phận pháp lý/tuân thủ:
- Dữ liệu cá nhân: có thu thập, lưu, chia sẻ không; quy định bảo vệ dữ liệu cá nhân hiện hành của nước sở tại và của thị trường khách hàng.
- Nơi đặt dữ liệu (data residency): khu vực lưu trữ; dịch vụ AI/đám mây có đưa dữ liệu ra ngoài lãnh thổ không.
- Thu thập dữ liệu từ web: điều khoản sử dụng của trang nguồn có cho phép không.

## 7. Bốn kịch bản thường gặp
1. **Tổ chức chưa có hệ thống BI nào.** Hỏi theo lưới (mục 3) → đánh giá độ trưởng thành nguồn → chọn cỡ dự án → gợi ý nhóm báo cáo theo ngành (`kpi-by-industry.md`, chỉ là câu hỏi gợi ý) → 2–3 phương án kiến trúc kèm 1 dòng khuyến nghị → khung đề xuất, phạm vi, tiến độ.
2. **Thiết kế báo cáo cho một phòng ban.** Đi hết chuỗi ở mục 2 theo thứ tự → chốt chỉ tiêu và chiều → mô tả từng biểu đồ (loại, trục, chỉ tiêu) → chuyển cho `pbi-model` / `pbi-design`.
3. **Nên dùng Fabric hay kho dữ liệu SQL truyền thống?** Đưa ra câu hỏi cần kiểm, không đưa giá: khối lượng dữ liệu hiện tại và tốc độ tăng; tần suất cập nhật; chiến lược đám mây của tổ chức; kỹ năng đội vận hành; có bắt buộc đặt tại chỗ không; chi phí và licensing hiện hành. Chế độ Direct Lake: xem `direct-lake-guidelines.md` ở `pbi-model`.
4. **Thêm lớp AI lên báo cáo.** Trước hết model phải sẵn sàng cho AI (đặt tên, mô tả, measure rõ — xem `semantic-model-ai-readiness.md` ở `pbi-model`); sau đó hỏi dữ liệu nào được phép đi qua dịch vụ AI và kiểm mục 6.

## 8. Ranh giới
- **Không bịa số liệu.** Số về chi phí, thời gian, hiệu quả chỉ là tham chiếu và phải nói "tùy dự án".
- Tài liệu tri thức chung **không nêu tên khách hàng**; quy về ngành.
- Chạm tài chính hoặc pháp lý: nhắc đây không thay chuyên gia; cung cấp thông tin để người dùng tự quyết.
- Sau khi khách chốt phương án: bàn giao sang chuỗi `pbi-model` → `pbi-analysis` → `pbi-design` → `pbi-build` (dựng–kiểm), rồi đào tạo người dùng (Pha 4 của `discovery-process.md`; dựng–kiểm–đào tạo), đóng dự án bằng `pbi-knowledge`.

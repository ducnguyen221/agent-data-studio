# Thư viện bộ dữ liệu mẫu KPIM — bản distill

Năm bộ dữ liệu đã dựng và đang dùng dạy học tại KPIM Academy, được **rút gọn thành hồ sơ tham chiếu** để dùng làm điểm xuất phát khi thiết kế bộ mockup mới.

## Quy ước tên chuẩn

`Data KPIM <Domain>` — dùng tên này trong mọi tài liệu, spec và trao đổi với user, kể cả khi tên file/thư mục ở nguồn khác đi.

| Tên chuẩn | Ngành | Hồ sơ |
|---|---|---|
| **Data KPIM Mart** | Bán lẻ chuỗi cửa hàng | [Data KPIM Mart.md](<Data KPIM Mart.md>) |
| **Data KPIM Bank** | Ngân hàng — dư nợ & tiền gửi | [Data KPIM Bank.md](<Data KPIM Bank.md>) |
| **Data KPIM HR** | Nhân sự | [Data KPIM HR.md](<Data KPIM HR.md>) |
| **Data KPIM Marketing** | Marketing đa kênh + outreach | [Data KPIM Marketing.md](<Data KPIM Marketing.md>) |

## Cách dùng

1. **User chưa rõ yêu cầu** → đưa 5 tên trên cho chọn: "bộ bạn cần gần giống bộ nào nhất?".
2. **Chọn xong** → đọc đúng một hồ sơ, lấy cấu trúc bảng + grain + KPI làm khung, rồi hỏi bù Nhóm 4–6 của `../mockup-design-playbook.md`.
3. **User nói "giống bộ X nhưng ngành khác"** → giữ nguyên khung bảng/grain/KPI, chỉ thay danh mục và tên gọi. Mục 7 của mỗi hồ sơ ghi sẵn cách biến thể.
4. **Viết spec mới** → theo `templates/documents/dataset/dataset.template.yaml` (gốc repo), **không** sao chép nguyên quy ước đặt tên của bộ cũ.

## Ba giới hạn phải nhớ

- Đây là **bản distill**, không phải dữ liệu. Số dòng và khoảng thời gian ghi theo thời điểm khảo sát (2026-08-18); bộ nguồn có thể đã đổi.
- Bộ gốc là **tài sản khoá học nội bộ, không kèm trong repo** — hồ sơ chỉ giữ cấu trúc và ý đồ. Không dẫn đường tới file gốc trong tài liệu công khai.
- Các bộ này phục vụ dạy học nên **có chủ đích để thô**: nhiều file cùng cấu trúc phải append, dữ liệu xuất từ nền tảng khác nhau, có cả lỗi thật lẫn lỗi cài cắm. Lấy **cấu trúc và ý đồ**, đừng bê nguyên khuyết điểm sang bộ mới — mục 6 của mỗi hồ sơ liệt kê rõ cái gì không nên chép.

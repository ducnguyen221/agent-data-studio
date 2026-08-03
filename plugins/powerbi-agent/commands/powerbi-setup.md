---
description: Thiết lập thư mục dự án — nơi lưu tri thức dự án Power BI NGOÀI repo (lần đầu bắt buộc)
---

Thiết lập Knowledge OS cho powerbi-agent:

1. Gọi tool `knowledge_status`. Nếu đã setup → báo trạng thái, hỏi user có muốn đổi folder không; không thì dừng.
2. Chưa setup → HỎI user (bắt buộc, đừng tự chọn): *"Bạn muốn lưu tri thức dự án Power BI ở folder nào (NGOÀI repo)? Mặc định tôi dùng `~/powerbi-project`, bạn muốn nơi khác thì dán đường dẫn."*
3. Gọi `setup_knowledge(path)` với đường dẫn user chọn.
4. Đọc lại `knowledge_status` xác nhận, giải thích ngắn cấu trúc (projects/ · knowledge/ 4 trục · templates/ · INDEX · TIMELINE) và các lệnh tiếp theo: `/powerbi-new`, `/powerbi-scan`, `/powerbi-done`, `/powerbi-pack`, `/powerbi-recall`.

Tham số user đưa kèm (nếu có, coi như path): $ARGUMENTS

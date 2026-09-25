---
description: Thiết lập Knowledge Dir — nơi lưu tri thức dự án Power BI NGOÀI repo (lần đầu bắt buộc)
---

Thiết lập Knowledge OS của agent-data-studio:

1. Gọi tool `knowledge_status`. Nếu đã setup → báo trạng thái, hỏi user có muốn đổi folder không; không thì dừng.
2. Chưa setup → HỎI user (bắt buộc, đừng tự chọn): *"Bạn muốn lưu tri thức dự án Power BI ở folder nào (NGOÀI repo)? Ưu tiên knowledge base có sẵn của bạn. Chưa có thì tôi dùng mặc định `~/powerbi-project`."*
3. Gọi `setup_knowledge(path)` với đường dẫn user chọn (con trỏ ghi vào `.env` của thư mục dữ liệu máy `$ADS_DATA`, không vào repo).
4. Đọc lại `knowledge_status` xác nhận, giải thích ngắn cấu trúc (projects/ · knowledge/ 4 trục · templates/ · INDEX · TIMELINE) và các lệnh tiếp theo: `/pbi-new`, `/pbi-scan`, `/pbi-kit`, `/pbi-done`, `/pbi-pack`, `/pbi-recall`.

Tham số user đưa kèm (nếu có, coi như path): $ARGUMENTS

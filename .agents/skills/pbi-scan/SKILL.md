---
name: pbi-scan
description: Quét thiết kế báo cáo PBIP vào trạm dữ liệu đang dùng
---

# pbi-scan — adapter quy trình

Đọc toàn bộ [quy trình gốc](../../../commands/pbi-scan.md) trong repo trước khi làm. Thay `$ARGUMENTS` bằng nội dung người dùng cung cấp; nếu thiếu mục tiêu thì hỏi ngắn gọn. Đọc skill và workflow được dẫn tới trực tiếp từ repo; không lấy bản cache hoặc bản trong trạm. Nếu file gốc không mở được, báo thiếu source và dừng quy trình này.

---
description: Đóng gói tri thức từ dự án vào knowledge/ 4 trục (tech-stack · industry · business-domain · powerbi)
---

Đóng gói tri thức: $ARGUMENTS (để trống = quét các dự án chưa pack)

1. `knowledge_status` → lấy đường dẫn Knowledge Dir root.
2. Giao agent **`pbi-knowledge-curator`** (subagent) với prompt: đường dẫn root + slug dự án (nếu có). Host không hỗ trợ subagent → tự thực hiện đúng quy trình trong định nghĩa agent (`agents/pbi-knowledge-curator.md` của studio): đọc INDEX/TIMELINE/knowledge hiện có → đọc dự án → rút bài học TÁI DÙNG (ngưỡng cao) → DEDUP (cập nhật file cũ) → ghi theo chuẩn Why/How-to-apply → cập nhật INDEX + TIMELINE.
3. Trình user danh sách bài học mới/cập nhật để xác nhận chất lượng.

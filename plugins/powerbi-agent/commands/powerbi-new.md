---
description: Bắt đầu dự án Power BI mới — tạo folder dự án trong Knowledge Dir + khởi động quy trình phân tích
---

Bắt đầu dự án Power BI mới tên: $ARGUMENTS

1. `knowledge_status` — chưa setup thì chạy luồng /powerbi-setup trước.
2. `init_project("$ARGUMENTS")` → ghi nhớ đường dẫn `projects/<slug>/` — MỌI file của dự án này (tài liệu, artifact, distill) lưu vào đó.
3. **Đọc kinh nghiệm cũ trước khi hỏi user**: `INDEX.md` + `TIMELINE.md` + grep `knowledge/` theo domain/từ khóa của dự án — tóm tắt những gì đã biết.
4. Kích hoạt skill `kpim-analysis` (pha Research → Key Information → Planning), output ghi vào folder dự án.
5. Khi sang thực thi kỹ thuật → skill `powerbi-pipeline` (9 khâu); artifact vào `projects/<slug>/artifacts/`.

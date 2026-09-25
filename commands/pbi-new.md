---
description: Bắt đầu dự án Power BI / dữ liệu mới — tạo folder dự án trong Knowledge Dir + khởi động chuỗi skill
---

Bắt đầu dự án mới tên: $ARGUMENTS

1. `knowledge_status` — chưa setup thì chạy luồng `/pbi-setup` trước.
2. `init_project("$ARGUMENTS")` → ghi nhớ đường dẫn `projects/<slug>/` — MỌI file của dự án (tài liệu, artifact, distill) lưu vào đó, không bao giờ vào repo.
3. **Đọc kinh nghiệm cũ trước khi hỏi user**: `INDEX.md` + `TIMELINE.md` + grep `knowledge/` theo domain/từ khoá của dự án — tóm tắt những gì đã biết.
4. Kích hoạt skill `data-discovery` (Research → Key Information → Planning), output ghi vào folder dự án. Chưa có dữ liệu → skill `data-mockup`.
5. Thực thi theo chuỗi `workflows/data-to-report.md` của studio: `pbi-model` → `pbi-analysis` → `pbi-design` → `pbi-build` → `pbi-review` → `pbi-publish`; artifact vào `projects/<slug>/artifacts/`. Kết thúc bằng `/pbi-done`.

---
description: Mở dự án dữ liệu và chọn bước phù hợp với nguồn hiện có
---

Bắt đầu dự án: $ARGUMENTS

1. Gọi `knowledge_status`; nếu chưa thiết lập, làm theo `commands/pbi-setup.md` trong repo.
2. Gọi `init_project("$ARGUMENTS")`; ghi mọi tài liệu và artifact dự án vào `projects/<slug>/` của trạm đang dùng (`workspace/` hoặc `ADS_DATA`). Không ghi dữ liệu dự án vào phần source được Git theo dõi.
3. Đọc `INDEX.md`, `TIMELINE.md` và tri thức liên quan trong trạm; tóm tắt kinh nghiệm có thể dùng lại.
4. Dùng skill `data-discovery` từ repo để khảo sát. Nếu chỉ có CSV, bắt đầu kiểm cấu trúc và chất lượng dữ liệu từ CSV; chưa cần Power BI Desktop hoặc MCP. Nếu chưa có dữ liệu, cân nhắc `data-mockup`.
5. Khi đã có mục tiêu và dữ liệu phù hợp, đi tiếp theo `workflows/data-to-report.md` trong repo. Chỉ dùng bước model, báo cáo hoặc publish khi người dùng cần và công cụ thực sự có sẵn.

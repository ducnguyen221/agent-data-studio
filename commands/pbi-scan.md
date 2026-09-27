---
description: Quét thiết kế báo cáo PBIP vào trạm dữ liệu đang dùng
---

Quét hồ sơ thiết kế báo cáo Power BI: $ARGUMENTS

1. `knowledge_status` — chưa thiết lập thì theo `commands/pbi-setup.md` trong repo. Trạm là `workspace/` hoặc đường `ADS_DATA` đã chọn.
2. Xác định `report_path` từ tham số (file `.pbip` hoặc folder `*.Report`). File `.pbix` → bảo user Save As `.pbip` trước (Power BI Desktop → File → Save as → Power BI project; xem skill `pbi-model`, mục PBIP-first).
3. `distill_report_design(report_path, project=<tên dự án nếu đang có, không thì tên báo cáo>)` → REPORT_CATALOG.md + DESIGN.md + theme/ vào `projects/<slug>/design/`.
4. Nếu MCP và model Desktop đang sẵn sàng (`list_local_reports`) → chạy thêm `distill_model_schema` cùng đích.
5. Tóm tắt hồ sơ và gợi ý trang có thể chưng cất bằng quy trình `commands/pbi-kit.md`. Kit riêng lưu ở `templates/` của trạm; chỉ đưa vào source công khai sau khi sanitize và người dùng duyệt. Redesign dùng skill `pbi-design` từ repo.

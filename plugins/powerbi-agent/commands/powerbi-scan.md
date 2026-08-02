---
description: Quét trọn thiết kế 1 báo cáo Power BI (.pbip) — mọi trang + theme + hồ sơ DESIGN vào Knowledge Dir
---

Quét hồ sơ thiết kế báo cáo Power BI: $ARGUMENTS

1. `knowledge_status` — chưa setup thì chạy luồng /powerbi-setup trước.
2. Xác định `report_path` từ tham số (file .pbip hoặc folder *.Report). File .pbix → bảo user Save As .pbip trước (xem skill powerbi-pipeline).
3. `distill_report_design(report_path, project=<tên dự án nếu đang có, không thì tên báo cáo>)` → REPORT_CATALOG.md + DESIGN.md + theme/ vào `projects/<slug>/design/`.
4. Nếu model đang mở trong Desktop (`list_local_reports`) → chạy thêm `distill_model_schema` cùng đích.
5. Tóm tắt hồ sơ + gợi ý: trang nào đẹp/đặc trưng thì `distill_template` thành kit (bản thô → `templates/` của Knowledge Dir; muốn đưa vào repo public → `sanitize=True` + user duyệt).

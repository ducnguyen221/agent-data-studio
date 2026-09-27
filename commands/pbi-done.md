---
description: Đóng dự án Power BI — checklist bàn giao, distill thiết kế/kit, ghi timeline, đóng gói tri thức
---

Đóng dự án Power BI hiện tại (hoặc: $ARGUMENTS)

1. `knowledge_status` → xác định `projects/<slug>/` trong trạm `workspace/` hoặc `ADS_DATA`.
2. **Checklist đóng** (thiếu cái nào thì làm nốt):
   - [ ] `artifacts/` đủ 4: PLAN · CHANGESET · VERIFICATION · HANDOFF
   - [ ] Đã qua skill `pbi-review` (không còn Blocker/Major); nếu đã publish, HANDOFF ghi cách refresh + quyền (skill `pbi-publish`)
   - [ ] Nếu có báo cáo PBIP, `design/` đã có REPORT_CATALOG + DESIGN + theme (chưa → `distill_report_design`)
   - [ ] Nếu có model, blueprint đã distill (`distill_model_schema`)
   - [ ] Nếu có trang đẹp được duyệt, đề xuất quy trình `commands/pbi-kit.md` (kit riêng → `templates/` của trạm; đưa vào source công khai → `sanitize=True` + người dùng duyệt)
3. Nếu MCP có sẵn, gọi `log_timeline` cho mốc đóng dự án; nếu chưa có, ghi mốc vào artifact dự án và báo rõ chưa đồng bộ qua tool.
4. Theo `commands/pbi-pack.md` và skill `pbi-knowledge` từ repo để xét bài học tái dùng; giao agent khi host hỗ trợ.
5. Báo cáo bàn giao ngắn cho user: làm được gì, tri thức mới đóng gói, việc tay còn lại.

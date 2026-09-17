---
description: Đóng dự án Power BI — checklist bàn giao, distill thiết kế/kit, ghi timeline, đóng gói tri thức
---

Đóng dự án Power BI hiện tại (hoặc: $ARGUMENTS)

1. `knowledge_status` → xác định `projects/<slug>/` của dự án.
2. **Checklist đóng** (thiếu cái nào thì làm nốt):
   - [ ] `artifacts/` đủ 4: PLAN · CHANGESET · VERIFICATION · HANDOFF
   - [ ] Đã qua skill `pbi-review` (không còn Blocker/Major); nếu đã publish, HANDOFF ghi cách refresh + quyền (skill `pbi-publish`)
   - [ ] `design/` đã có REPORT_CATALOG + DESIGN + theme (chưa → `distill_report_design`)
   - [ ] Model blueprint đã distill (`distill_model_schema`)
   - [ ] Trang đẹp được user duyệt → đề xuất `/pbi-kit` thành kit (thô → `templates/` của Knowledge Dir; đưa vào repo công khai → `sanitize=True` + user duyệt)
3. `log_timeline(project, "Đóng dự án", <1 câu kết quả>, projects/<slug>/)`.
4. Chạy luồng `/pbi-pack` cho dự án này (giao agent `pbi-knowledge-curator` nếu host hỗ trợ subagent, không thì tự làm theo skill `pbi-knowledge`).
5. Báo cáo bàn giao ngắn cho user: làm được gì, tri thức mới đóng gói, việc tay còn lại.

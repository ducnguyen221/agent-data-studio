---
description: Đóng dự án Power BI — checklist bàn giao, distill thiết kế/kit, ghi timeline, đóng gói tri thức
---

Đóng dự án Power BI hiện tại (hoặc: $ARGUMENTS)

1. `knowledge_status` → xác định `projects/<slug>/` của dự án.
2. **Checklist đóng** (thiếu cái nào thì làm nốt):
   - [ ] `artifacts/` đủ 4: PLAN · CHANGESET · VERIFICATION · HANDOFF
   - [ ] `design/` đã có REPORT_CATALOG + DESIGN + theme (chưa → `distill_report_design`)
   - [ ] Model blueprint đã distill (`distill_model_schema`)
   - [ ] Trang đẹp được user duyệt → đề xuất `distill_template` thành kit (thô → Knowledge Dir templates/; public → sanitize + duyệt)
3. `log_timeline(project, "Đóng dự án", <1 câu kết quả>, projects/<slug>/)`.
4. Chạy luồng /powerbi-pack cho dự án này (giao agent `powerbi-knowledge-curator` nếu host hỗ trợ subagent, không thì tự làm theo skill `powerbi-knowledge` §curator).
5. Báo cáo bàn giao ngắn cho user: làm được gì, tri thức mới đóng gói, việc tay còn lại.

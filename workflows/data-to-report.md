---
name: data-to-report
description: Quy trình từ dữ liệu và yêu cầu nghiệp vụ tới báo cáo được kiểm tra
skills: [pbi-knowledge, data-discovery, data-mockup, pbi-model, pbi-analysis, pbi-design, pbi-build, pbi-review, pbi-publish]
gates: [project-opened, discovery-approved, model-verified, numbers-checked, brief-approved, page-validated, review-clean, project-closed]
---

# Quy trình dữ liệu → báo cáo

Đọc `SKILL.md` của bước đang làm từ `skills/` trong repo; chỉ mở reference liên quan. Source, script và workflow ở repo; artifact dự án ở `workspace/` (basic, bị Git bỏ qua) hoặc trạm ngoài do `ADS_DATA` chỉ định. Mỗi bước có cổng kiểm trước khi chuyển tiếp.

Nếu đầu vào chỉ là CSV, thực hiện bước 0–1 để khảo sát và đánh giá dữ liệu; có thể phân tích CSV mà chưa cần Power BI Desktop hoặc MCP. Chỉ đi tới model và trang báo cáo khi mục tiêu dự án đòi hỏi và công cụ đã sẵn sàng. Publish chỉ khi người dùng yêu cầu rõ và đường tích hợp thực tế được kiểm.

| # | Bước | File đọc từ gốc repo | Cổng kiểm |
|---|---|---|---|
| 0 | Mở dự án, tra kinh nghiệm | `skills/pbi-knowledge/SKILL.md`, `commands/pbi-setup.md`, `commands/pbi-new.md` | `projects/<slug>/` trong trạm; kinh nghiệm liên quan đã được xem. Nếu chưa có MCP, tạo tài liệu khảo sát trong trạm và ghi rõ tool chưa chạy. |
| 1 | Khảo sát và lập kế hoạch | `skills/data-discovery/SKILL.md`, `skills/data-discovery/references/kpim/discovery-process.md`, `templates/documents/` | Yêu cầu, nguồn, grain, chỉ số, cột nhạy cảm và kế hoạch được ghi rõ; người dùng duyệt phạm vi. |
| 1′ | Tạo dữ liệu mẫu khi thiếu dữ liệu | `skills/data-mockup/SKILL.md`, hai playbook trong `skills/data-mockup/references/kpim/` | Bộ mẫu kiểm được, có dictionary và lỗi dự kiến được giải thích. |
| 2 | Kết nối và dựng model khi cần Power BI | `skills/pbi-model/SKILL.md`, reference trong `skills/pbi-model/references/` | Row count, kiểu cột, quan hệ và measure được kiểm với số đối chiếu; trạng thái lưu được xác nhận. |
| 3 | Soát số và chính sách truy vấn | `skills/pbi-analysis/SKILL.md`, `skills/pbi-analysis/references/kpim/mcp-tools.md` | Policy PII phù hợp, số đối chiếu khớp và audit được xem khi tool có sẵn. |
| 4 | Thiết kế trang | `skills/pbi-design/SKILL.md`, reference trong `skills/pbi-design/references/` | Design Brief có nguồn thiết kế và field thật; người dùng duyệt. |
| 5 | Dựng và xem ảnh render | `skills/pbi-build/SKILL.md`, `agents/pbi-render-reviewer.md` | Validate, reload, screenshot và kiểm mắt; thiếu ảnh thì chưa nghiệm thu trang. |
| 6 | Review độc lập | `skills/pbi-review/SKILL.md`, `skills/pbi-review/references/kpim/review-checklist.md` | Không còn lỗi nghiêm trọng, số tie-out khớp. |
| 7 | Publish nếu được yêu cầu | `skills/pbi-publish/SKILL.md` | Kiểm quyền, đích, kết quả triển khai, binding và refresh bằng bằng chứng của host/Service. Đường publish chưa được nghiệm thu tổng quát. |
| 8 | Đóng dự án | `skills/pbi-knowledge/SKILL.md`, `commands/pbi-done.md`, `agents/pbi-knowledge-curator.md` | Artifact bàn giao đầy đủ theo phạm vi thực tế; bài học tái dùng được đối chiếu và lưu trong trạm. |

Các tệp `commands/pbi-*.md` có thể được gọi bằng `/pbi-*` khi host nhận lệnh. Host không hỗ trợ thì yêu cầu bằng ngôn ngữ tự nhiên với tên quy trình. Tệp adapter tồn tại chưa chứng minh host đã chạy được lệnh.

Số không khớp thì quay lại định nghĩa chỉ số hoặc model. Visual trống hay rebind sai thì quay lại bước dựng. Thiết kế không đạt thì sửa Brief rồi kiểm trang lại. Mỗi cổng ghi bằng chứng vào `projects/<slug>/artifacts/VERIFICATION` của trạm.

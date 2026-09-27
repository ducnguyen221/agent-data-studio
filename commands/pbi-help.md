---
description: Chọn quy trình dữ liệu và Power BI theo nhu cầu và công cụ hiện có
---

Hỗ trợ chọn bước tiếp theo: $ARGUMENTS

Đọc skill và workflow từ repo đang chạy. Dữ liệu dự án ở `workspace/` (basic, bị Git bỏ qua) hoặc trạm ngoài do `ADS_DATA` chỉ định. Không chép skill, engine hay workflow sang trạm.

Nếu người dùng đã nêu việc cụ thể, trả lời thẳng quy trình phù hợp. Nếu chưa, hỏi họ muốn khảo sát dữ liệu, tạo dữ liệu mẫu, phân tích CSV, làm Power BI hay tra lại kinh nghiệm cũ.

| Nhu cầu | Bước đầu |
|---|---|
| Chỉ có CSV hoặc tài liệu nghiệp vụ | `data-discovery`: đọc cấu trúc, chất lượng dữ liệu, câu hỏi và chỉ số; chưa cần MCP hoặc Power BI |
| Chưa có dữ liệu | `data-mockup`: thiết kế và kiểm bộ mẫu |
| Có Power BI Desktop/PBIP | `pbi-model` → `pbi-analysis` → `pbi-design` → `pbi-build` → `pbi-review` theo nhu cầu |
| Có báo cáo PBIP cần hiểu hoặc tái dùng | Quy trình `pbi-scan` hoặc `pbi-kit` |
| Cần dự án và tri thức có lưu vết | `pbi-setup` → `pbi-new`; cuối dự án dùng `pbi-done`/`pbi-pack` |
| Muốn tìm kinh nghiệm cũ | `pbi-recall` |
| Muốn phát hành lên Service/Fabric | `pbi-publish` sau khi người dùng yêu cầu rõ; kiểm năng lực và quyền thực tế của host trước khi thao tác |

Các tệp lệnh `/pbi-*` trong `commands/` là nguồn hướng dẫn. Dùng cú pháp slash chỉ khi host hiện tại thực sự nhận lệnh đó; nếu không, yêu cầu bằng ngôn ngữ tự nhiên, ví dụ “chạy quy trình pbi-new theo repo này”. Adapter project-local cần được kiểm trên từng host, chưa coi là đã nghiệm thu chỉ vì tệp tồn tại.

Khi MCP đã bật, gọi `knowledge_status` và `list_templates` để báo trạng thái thật. Nếu tool chưa có, nói rõ giới hạn hiện tại và tiếp tục với bước chỉ cần file/CSV. Công cụ Microsoft MCP là tích hợp riêng; không mặc định có sẵn hoặc tự kế thừa chính sách an toàn dữ liệu của studio.

Danh mục skill: `skills/README.md`. Chuỗi đầy đủ: `workflows/data-to-report.md`. Hai agent tùy chọn ở `agents/`; khả năng gọi agent phụ thuộc host.

# Cài Agent Data Studio cho Claude Code

Cần Git, Python 3.11 trở lên và Windows cho các tính năng Power BI Desktop. Mở PowerShell:

```powershell
git clone https://github.com/ducnguyen221/agent-data-studio "$env:USERPROFILE\agent-data-studio"
cd "$env:USERPROFILE\agent-data-studio"
.\install.ps1 -Hosts claude
```

Script tạo môi trường Python và trạm `workspace/`, kiểm adapter skill trong repo, đăng ký MCP `powerbi-mcp-bridge` cho Claude Code ở cấp người dùng (`~/.claude.json`). Nó sao lưu cấu hình hiện có trước khi thay đổi và giữ các server khác. Mọi thư mục mở trong Claude Code dùng chung server của checkout này; mỗi máy chỉ trỏ một checkout — xem [giới hạn](../README.md#mcp-được-đăng-ký-ở-cấu-hình-người-dùng). Khởi động lại Claude Code và mở folder repo; dùng `claude mcp list` để xem trạng thái server. Nếu chưa kết nối, xem dòng lỗi của installer và thử chạy lại sau khi sửa nguyên nhân.

Claude Code đọc [`.claude/skills/`](../../.claude/skills/) trong project. Mỗi adapter trỏ tới skill gốc ở [`skills/`](../../skills/); script và reference cũng được đọc trực tiếp từ repo. Bộ cài không sao chép skill, lệnh hoặc agent vào thư mục Claude toàn máy. Muốn chạy một quy trình, bảo Claude đọc file tương ứng ở [`commands/`](../../commands/), ví dụ `commands/pbi-help.md`.

Bài thử đầu tiên dùng [CSV tổng hợp](../../samples/README.md), chưa cần Power BI. Khi làm việc với Power BI Desktop, mở báo cáo trước rồi thử `list_local_reports`; tool Desktop cần ADOMD.NET. Power BI Service có cấu hình đăng nhập riêng, chỉ làm khi cần Service.

Bạn có thể chọn trạm dữ liệu ngoài repo bằng `ADS_DATA` trước khi cài ([hướng dẫn](../../START-HERE.md)). Sau `git pull`, mở lại Claude Code để nhận thay đổi skill trong repo. `install.ps1 -Only plugin` chỉ kiểm adapter.

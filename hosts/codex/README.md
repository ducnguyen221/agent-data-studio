# Cài Agent Data Studio cho Codex

Đây là lựa chọn mặc định của bộ cài. Cần Git, Python 3.11 trở lên và Windows cho các tính năng Power BI Desktop.

```powershell
git clone https://github.com/ducnguyen221/agent-data-studio "$env:USERPROFILE\agent-data-studio"
cd "$env:USERPROFILE\agent-data-studio"
.\install.ps1
```

Script tạo `.venv/`, `workspace/`, kiểm adapter skill trong repo và đăng ký `powerbi-mcp-bridge` vào cấu hình người dùng của Codex (`~/.codex/config.toml`, CLI và desktop cùng đọc file này). Nó sao lưu file cấu hình trước khi thay đổi và giữ các server khác. Mọi thư mục mở trong Codex dùng chung server của checkout này; mỗi máy chỉ trỏ một checkout — xem [giới hạn](../README.md#mcp-được-đăng-ký-ở-cấu-hình-người-dùng). Mở lại Codex tại folder repo sau khi cài; kiểm tra MCP trong danh sách công cụ của Codex hoặc hỏi agent gọi `knowledge_status`.

Codex tìm skill ở [`.agents/skills/`](../../.agents/skills/). Mỗi adapter yêu cầu đọc bản gốc tại [`skills/`](../../skills/); script và tài liệu hỗ trợ cũng lấy tại repo. Không cần copy skill vào `~/.codex/skills/` hay cài plugin để dùng checkout này. Cần đọc một quy trình `pbi-*` thì yêu cầu agent mở file tương ứng trong [`commands/`](../../commands/).

**Việc đầu tiên:** bảo Codex đọc [CSV mẫu](../../samples/README.md), kiểm tra dữ liệu và lưu báo cáo vào `workspace/outputs/first-report.md`. Bài này không cần Power BI. Sau đó, nếu có Power BI Desktop, mở báo cáo và thử `list_local_reports`; các tool Desktop cần thư viện ADOMD.NET. Thông tin Power BI Service chỉ cần khi dùng Service.

Nếu đã có trạm dữ liệu ngoài repo, đặt `ADS_DATA` trước khi cài (xem [START-HERE.md](../../START-HERE.md)). Cập nhật skill sau này bằng `git pull` trong repo rồi khởi động lại Codex. `install.ps1 -Only plugin` chỉ kiểm adapter, không cập nhật MCP hoặc môi trường Python.

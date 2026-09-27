# Cài Agent Data Studio cho Antigravity

Muốn agent cài giúp: dán prompt trong [INSTALL.md](../../INSTALL.md#prompt-copy-dán) vào Antigravity. Tự cài thì cần Git, Python 3.11–3.14 và Windows cho các tính năng Power BI Desktop. Mở PowerShell:

```powershell
git clone https://github.com/ducnguyen221/agent-data-studio "$env:USERPROFILE\agent-data-studio"
cd "$env:USERPROFILE\agent-data-studio"
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Hosts antigravity
```

`-ExecutionPolicy Bypass` chỉ áp cho lệnh đó, không đổi chính sách của máy. Script tạo `.venv/` và `workspace/`, kiểm adapter skill trong repo, rồi đăng ký MCP `powerbi-mcp-bridge` trong cấu hình người dùng của Antigravity (`~/.gemini/antigravity/mcp_config.json`). File cấu hình hiện có được sao lưu trước khi sửa; các server khác được giữ. Mọi thư mục mở trong Antigravity dùng chung server của checkout này; mỗi máy chỉ trỏ một checkout — xem [giới hạn](../README.md#mcp-được-đăng-ký-ở-cấu-hình-người-dùng). Khởi động lại Antigravity, mở folder repo và kiểm tra server trong mục MCP của ứng dụng hoặc yêu cầu agent gọi `knowledge_status`.

Antigravity đọc adapter tại [`.agents/skills/`](../../.agents/skills/) trong project. Adapter dẫn về [`skills/`](../../skills/); script, template và reference cũng nằm trong repo. Bộ cài không chép skill vào thư mục Antigravity toàn máy. Để dùng quy trình như `pbi-help`, yêu cầu agent đọc [`commands/pbi-help.md`](../../commands/pbi-help.md) rồi làm theo.

Bạn có thể bắt đầu với [CSV mẫu](../../samples/README.md) mà chưa cần Power BI. Khi có Power BI Desktop, mở báo cáo và thử `list_local_reports`; công cụ Desktop cần ADOMD.NET. Power BI Service là lựa chọn riêng và chỉ cần đăng nhập khi sử dụng.

Nếu có trạm dữ liệu ngoài repo, đặt `ADS_DATA` trước khi cài ([hướng dẫn](../../START-HERE.md)). Sau `git pull`, khởi động lại Antigravity để đọc skill mới. `install.ps1 -Only plugin` chỉ kiểm adapter.

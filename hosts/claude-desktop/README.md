# Cài Agent Data Studio cho Claude Desktop (tab chat)

Claude Desktop chỉ nhận **16 công cụ MCP** của Agent Data Studio (truy vấn Power BI, thiết kế, Knowledge Dir…). Tab chat **không có** skill project hay lệnh `/pbi-*`, và không có cửa sổ lệnh để tự chạy bộ cài. Muốn dùng đủ skill, dùng [Claude Code](../claude/README.md), [Codex](../codex/README.md) hoặc [Antigravity](../antigravity/README.md); có thể cài cả hai: Claude Desktop cho hỏi đáp, host kia cho quy trình.

## Cài đặt

Cần Git, Python 3.11–3.14 (khuyên dùng 3.12 hoặc 3.13) và Windows. Bước cài do **bạn chạy trong PowerShell**, hoặc nhờ Claude Code / Codex / Antigravity làm theo [`INSTALL.md`](../../INSTALL.md) với host `claude-desktop`:

```powershell
git clone https://github.com/ducnguyen221/agent-data-studio "$env:USERPROFILE\agent-data-studio"
cd "$env:USERPROFILE\agent-data-studio"
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Hosts claude-desktop
powershell -NoProfile -ExecutionPolicy Bypass -File .\doctor.ps1 -Hosts claude-desktop
```

`-ExecutionPolicy Bypass` chỉ áp cho lần chạy đó, không đổi chính sách của máy. Bộ cài tạo môi trường Python và trạm `workspace/`, rồi gộp server `powerbi-mcp-bridge` vào `%APPDATA%\Claude\claude_desktop_config.json` (khoá `mcpServers`, dạng `command`/`args`/`env` như tài liệu MCP). Nó sao lưu file cũ thành `.bak.*` trước khi ghi, giữ các server và thiết lập khác, và từ chối ghi đè nếu đã có server cùng tên trỏ checkout khác. `-Hosts claude` (Claude Code) **không** tự đăng ký Claude Desktop; cần cả hai thì cài bằng `-Hosts claude,claude-desktop` (chạy được cả qua `-File`), còn `doctor.ps1`/`uninstall.ps1` qua `-File` thì chạy riêng cho từng host.

## Khởi động lại và kiểm tra

Thoát hẳn Claude Desktop từ biểu tượng ở khay hệ thống (đóng cửa sổ chưa đủ), rồi mở lại. Trong ô chat, bấm nút thêm tệp/kết nối → **Connectors** → xem `powerbi-mcp-bridge` và danh sách công cụ. Hỏi thử: "Gọi `knowledge_status`". Chưa thấy server thì xem log `%APPDATA%\Claude\logs\mcp*.log` và chạy lại `doctor.ps1 -Hosts claude-desktop`.

Dòng `host` của doctor kiểm ứng dụng đã cài (bản tải từ claude.ai hoặc gói Microsoft Store). Nếu doctor báo gói Store có bản cấu hình riêng trong `LocalCache\Roaming\Claude`, ứng dụng có thể không đọc file vừa đăng ký: mở **Settings → Developer → Edit Config** trong Claude Desktop để biết file nó thật sự dùng.

## Dùng và gỡ

Bài thử đầu tiên dùng [CSV tổng hợp](../../samples/README.md), chưa cần Power BI. Làm việc với Power BI Desktop thì mở báo cáo trước rồi hỏi `list_local_reports`; công cụ Desktop cần ADOMD.NET. Gỡ đăng ký: `powershell -NoProfile -ExecutionPolicy Bypass -File .\uninstall.ps1 -Hosts claude-desktop` (chỉ xoá mục trỏ đúng checkout này).

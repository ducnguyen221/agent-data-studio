# Chọn ứng dụng AI để cài

“Host” là ứng dụng chạy AI Agent. Cách dễ nhất: dán prompt trong [INSTALL.md](../INSTALL.md#prompt-copy-dán) vào ứng dụng bạn đang dùng, agent tự chọn đúng host. Tự cài thì mở PowerShell tại gốc repo đã clone và chạy `powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Hosts <giá trị>` (Bypass chỉ áp cho lệnh đó, không đổi chính sách máy). Không truyền `-Hosts` thì bộ cài chọn `codex`.

| Bạn dùng | `-Hosts` | Có gì | Hướng dẫn |
|---|---|---|---|
| Codex (CLI và desktop) | `codex` | MCP + skill + quy trình | [Codex](codex/README.md) |
| Claude Code | `claude` | MCP + skill + quy trình | [Claude Code](claude/README.md) |
| Claude Desktop (tab chat) | `claude-desktop` | **Chỉ 16 công cụ MCP**, không có skill | [Claude Desktop](claude-desktop/README.md) |
| Antigravity | `antigravity` | MCP + skill + quy trình | [Antigravity](antigravity/README.md) |

Cần Git và Python 3.11–3.14 ([chuẩn bị máy](../START-HERE.md#chuẩn-bị-máy)). Kiểm máy trước khi cài: `powershell -NoProfile -ExecutionPolicy Bypass -File .\doctor.ps1 -Preflight` in 7 dòng `prereq` (PowerShell, ExecutionPolicy, Git, Python, ADOMD.NET, Node, `az`), chưa cần `.venv`, thoát mã 1 nếu có dòng `FAIL`. Muốn đăng ký nhiều host trong một lượt: `install.ps1 -Hosts codex,claude,antigravity` (chạy được cả qua `-File`); `doctor.ps1` và `uninstall.ps1` gọi qua `-File` thì mỗi lần một host. `-Hosts claude` không tự đăng ký Claude Desktop; cần cả hai thì ghi `-Hosts claude,claude-desktop`. Sau cài, khởi động lại các ứng dụng đã chọn và mở **thư mục repo**. Trạm cơ bản là `workspace/` trong repo, bị Git bỏ qua; `ADS_DATA` chọn trạm ngoài trước lúc cài. [Bài thử đầu tiên](../START-HERE.md) dùng CSV mẫu.

Skill gốc ở [`../skills/`](../skills/), script ở [`../scripts/`](../scripts/), quy trình ở [`../commands/`](../commands/). Repo có adapter `.agents/skills/` cho Codex và Antigravity, `.claude/skills/` cho Claude. Bộ cài chỉ kiểm tra adapter và đăng ký MCP; không sao chép skill vào thư mục chung của các host. Sau khi cập nhật repo, host cần mở lại để đọc nội dung mới.

## MCP được đăng ký ở cấu hình người dùng

Bộ cài ghi mục `powerbi-mcp-bridge` vào cấu hình **của người dùng** trên máy, không vào file trong repo:

| Host | File cấu hình |
|---|---|
| Codex (CLI và desktop) | `~/.codex/config.toml` |
| Claude Code | `~/.claude.json` (mục `mcpServers` cấp người dùng) |
| Claude Desktop | `%APPDATA%\Claude\claude_desktop_config.json` (mục `mcpServers`) |
| Antigravity | `~/.gemini/antigravity/mcp_config.json` |

Hệ quả cần biết:

- **Mỗi máy trỏ một checkout.** Mọi thư mục và workspace bạn mở trong host đều dùng chung một server, chạy engine của checkout đã cài và trạm dữ liệu đã liên kết lúc cài. Công cụ MCP vì thế xuất hiện cả khi bạn mở thư mục khác; skill và adapter thì chỉ có khi mở thư mục repo. Đây không phải cô lập theo project.
- **Không ghi đè checkout khác.** Nếu `powerbi-mcp-bridge` đã trỏ tới checkout khác, installer báo lỗi và giữ nguyên. Muốn chuyển sang checkout mới, chạy `.\uninstall.ps1 -Hosts <host>` ở checkout cũ trước.
- **Gộp, không thay cả file.** Installer sao lưu file cấu hình trước khi ghi, chỉ thêm mục của mình, giữ nguyên các server khác và tuỳ chỉnh bạn đã thêm vào mục trỏ đúng checkout này.
- **Gỡ đúng phần của mình.** `uninstall.ps1` chỉ xoá mục trỏ tới checkout đang chạy lệnh, sao lưu trước khi xoá, giữ mục cùng tên của checkout khác và không đụng `workspace/` hay trạm ngoài.

Tám quy trình `pbi-*` là file trong `commands/`; tab chat của Claude Desktop không nạp skill hay quy trình từ repo nên chỉ dùng công cụ MCP. Cách chắc chắn trên Codex, Claude Code và Antigravity: bảo agent “đọc `commands/pbi-help.md` trong repo rồi thực hiện theo đó”. Cách gọi bằng lệnh tắt của từng host có thể khác nhau.

# hosts/ — Hướng dẫn đăng ký RIÊNG từng MCP host

> "Host" = thuật ngữ chuẩn MCP chỉ ứng dụng agent chạy bên trong (Claude Code, Codex CLI,
> Antigravity). Folder này KHÔNG chứa skill — skill (nguồn duy nhất) nằm ở
> [`../skills/`](../skills/) (lệnh ở [`../commands/`](../commands/), agent ở
> [`../agents/`](../agents/)), installer copy sang thư mục skill của từng host khi cài.

Mỗi thư mục = 1 host, chứa cách cài trọn bộ + snippet cấu hình tay + vai gợi ý trong tổ đa-agent:

| Host | File | Skills nằm ở | MCP config |
|---|---|---|---|
| Claude Code | [`claude/README.md`](claude/README.md) | `~/.claude/skills/` | `~/.claude.json` |
| Codex CLI | [`codex/README.md`](codex/README.md) | `~/.codex/skills/` | `~/.codex/config.toml` |
| Antigravity | [`antigravity/README.md`](antigravity/README.md) | `~/.gemini/antigravity/skills/` | `~/.gemini/antigravity/mcp_config.json` |

Bình thường KHÔNG cần đọc từng file — `install.ps1` ở gốc repo đăng ký cả 3 host tự động.
Vào đây khi: cấu hình tay, gỡ rối 1 host, hoặc chỉ muốn cài 1 host (`-Hosts <tên>`).
Luật điều phối nhiều agent cùng lúc: [`../AGENTS.md`](../AGENTS.md) §4.

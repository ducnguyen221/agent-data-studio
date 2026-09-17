# Claude Code — cài & đăng ký powerbi-agent

## Cách 1 — Trọn bộ (MCP + venv + skills) — khuyến nghị

```powershell
git clone https://github.com/ducnguyen221/powerbi-agent "$env:USERPROFILE\.mcp\powerbi-mcp"
cd "$env:USERPROFILE\.mcp\powerbi-mcp"
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Hosts claude
```

Installer merge server `powerbi-mcp-bridge` vào `~/.claude.json` (user scope, backup `.bak`,
không đụng server khác), copy 9 skill từ [`skills/`](../../skills/) vào `~/.claude/skills/`, 8 lệnh `/pbi-*` từ
[`commands/`](../../commands/) vào `~/.claude/commands/` và agent từ [`agents/`](../../agents/) vào `~/.claude/agents/`. **Restart Claude Code** sau cài.

Verify: `claude mcp list` → `powerbi-mcp-bridge … ✔ Connected`.

## Cách 2 — Cài dạng PLUGIN (hiện trong trình quản lý plugin của Claude Desktop)

```bash
claude plugin marketplace add ducnguyen221/powerbi-agent
claude plugin install powerbi-agent@powerbi-agent
```

Plugin `powerbi-agent` xuất hiện trong danh sách plugin của app; nạp **9 skill + 8 lệnh /pbi-* +
agent `pbi-knowledge-curator`** (Claude tự auto-discover `commands/` + `agents/`). Dùng khi chỉ cần
quy trình/kiến thức mà chưa cần 16 tool DAX.

> Chỉ cài plugin = CHƯA có MCP server (16 tool). Muốn đủ tool → Cách 1.
> Đừng chạy CẢ Cách 1 (copy skill) LẪN Cách 2 (plugin) — skill sẽ bị nạp 2 lần.

## Khuyến nghị kèm theo

```bash
claude mcp add powerbi-modeling -s user -- npx -y "@microsoft/powerbi-modeling-mcp@latest" --start
```

Phân vai 2 server + luật multi-agent: xem [`AGENTS.md`](../../AGENTS.md) §3–§4.

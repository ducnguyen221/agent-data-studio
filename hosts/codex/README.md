# Codex CLI — cài & đăng ký powerbi-agent

Codex đọc **`AGENTS.md`** ở gốc repo một cách native — mọi luật làm việc nằm ở đó.

## Cách 1 — Trọn bộ (MCP + venv + skills) — khuyến nghị

```powershell
git clone https://github.com/ducnguyen221/powerbi-agent "$env:USERPROFILE\.mcp\powerbi-mcp"
cd "$env:USERPROFILE\.mcp\powerbi-mcp"
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Hosts codex
```

Installer làm 3 việc:
1. Thêm block `[mcp_servers.powerbi-mcp-bridge]` vào `~/.codex/config.toml` (backup `.bak`).
2. Copy 4 skill vào `~/.codex/skills/`.
3. **Copy 8 lệnh vào `~/.codex/prompts/`** → gõ `/powerbi-help`, `/powerbi-setup`… ngay trong Codex.
   *(Từ v0.5.0 — trước đó chỉ Claude Code mới có lệnh.)*

**Restart phiên Codex** sau cài.

Chỉ muốn cập nhật phần quy trình (skill + lệnh), không đụng venv/MCP:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Hosts codex -Only plugin
```

Đăng ký tay (nếu muốn tự làm):

```toml
# ~/.codex/config.toml
[mcp_servers.powerbi-mcp-bridge]
command = "C:/Users/<you>/.mcp/powerbi-mcp/.venv/Scripts/python.exe"
args    = ["C:/Users/<you>/.mcp/powerbi-mcp/mcp_server_powerbi.py"]
env     = { PYTHONUNBUFFERED = "1" }
```

## Cách 2 — Cài dạng PLUGIN (hiện trong `codex plugin list` / app)

Codex đọc **cùng một `.claude-plugin/marketplace.json`** với Claude — không cần manifest riêng.
Cài để plugin xuất hiện trong trình quản lý plugin của Codex (4 skill + 8 lệnh `/powerbi-*` + agent
`powerbi-knowledge-curator` được nạp tự động):

```bash
codex plugin marketplace add https://github.com/ducnguyen221/powerbi-agent
codex plugin add powerbi-agent@powerbi-agent
codex plugin list   # thấy: powerbi-agent@powerbi-agent  installed, enabled  0.5.0
```

> Chỉ cài plugin = có skill/lệnh, CHƯA có 16 tool MCP. Muốn đủ tool → chạy install.ps1 (Cách 1).
> Đừng chạy CẢ Cách 1 (copy skill) LẪN Cách 2 (plugin) cùng lúc — skill sẽ bị nạp 2 lần.

## Khuyến nghị kèm theo

Đăng ký thêm `powerbi-modeling` (Microsoft) cho modeling ops — xem [`AGENTS.md`](../../AGENTS.md) §2.
Vai gợi ý cho Codex trong tổ đa-agent: **Reviewer/second-opinion** (chỉ đọc) — §4.2.

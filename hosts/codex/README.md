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
2. Copy 9 skill từ [`skills/`](../../skills/) vào `~/.codex/skills/`.
3. **Cài 8 quy trình thành SKILL** (từ [`commands/`](../../commands/)) trong `~/.codex/skills/` — mỗi lệnh
   thành skill `pbi-<lệnh>`, gọi bằng tên: *"chạy pbi-help"*, *"chạy pbi-setup"*…
   *(Từ v0.6 — trước đó đặt nhầm vào `~/.codex/prompts/`, mà file ở đó phải gọi bằng
   `/prompts:<tên>` chứ không phải `/<tên>` — nên tên lệnh lệch hẳn so với Claude.)*

Sau cài, Codex có **17 skill**: 9 quy trình chuyên môn + 8 quy trình lệnh. Installer tự dọn các
skill tên cũ (`powerbi-*`…) do bản trước sinh ra.

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
Cài để plugin xuất hiện trong trình quản lý plugin của Codex (9 skill + 8 quy trình `pbi-*` (gọi theo tên, Codex không có slash-command) + agent
`pbi-knowledge-curator` được nạp tự động):

```bash
codex plugin marketplace add https://github.com/ducnguyen221/powerbi-agent
codex plugin add agent-data-studio@agent-data-studio
codex plugin list   # thấy: agent-data-studio@agent-data-studio  installed, enabled  0.7.0
```

> Chỉ cài plugin = có skill/lệnh, CHƯA có 16 tool MCP. Muốn đủ tool → chạy install.ps1 (Cách 1).
> Đừng chạy CẢ Cách 1 (copy skill) LẪN Cách 2 (plugin) cùng lúc — skill sẽ bị nạp 2 lần.

## Khuyến nghị kèm theo

Đăng ký thêm `powerbi-modeling` (Microsoft) cho modeling ops — xem [`AGENTS.md`](../../AGENTS.md) §2.
Vai gợi ý cho Codex trong tổ đa-agent: **Reviewer/second-opinion** (chỉ đọc) — §4.2.

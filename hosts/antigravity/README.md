# Google Antigravity — cài & đăng ký powerbi-agent

Antigravity đọc **`GEMINI.md`** (trỏ về `AGENTS.md`) — mọi luật làm việc ở [`AGENTS.md`](../../AGENTS.md).

> ℹ️ **Antigravity KHÔNG có trình quản lý plugin/marketplace** (khác Claude & Codex). Vì vậy
> "plugin" ở đây = **skill nạp từ thư mục** `~/.gemini/antigravity/skills/`. Installer copy skill
> vào đó; Antigravity tự hiện chúng khi khởi động (không có mục "plugin" riêng trong app).

## Cài (Antigravity không có plugin store — dùng installer)

```powershell
git clone https://github.com/ducnguyen221/agent-data-studio "$env:USERPROFILE\.mcp\powerbi-mcp"
cd "$env:USERPROFILE\.mcp\powerbi-mcp"
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Hosts antigravity
```

Installer làm 2 việc:
1. Merge server vào `~/.gemini/antigravity/mcp_config.json` (backup `.bak`, giữ server khác):

```json
{
  "mcpServers": {
    "powerbi-mcp-bridge": {
      "command": "C:/Users/<you>/.mcp/powerbi-mcp/.venv/Scripts/python.exe",
      "args": ["C:/Users/<you>/.mcp/powerbi-mcp/mcp_server_powerbi.py"],
      "env": { "PYTHONUNBUFFERED": "1" }
    }
  }
}
```

2. Copy 9 skill từ [`skills/`](../../skills/) (kèm `references/` + `scripts/`) vào `~/.gemini/antigravity/skills/`.
3. Vì Antigravity **không có slash-command**, installer đặt 8 lệnh (từ [`commands/`](../../commands/)) vào
   `~/.gemini/antigravity/skills/pbi-knowledge/commands/` — agent đọc được quy trình và
   bạn gọi bằng lời: *"chạy quy trình pbi-setup"*, *"chạy pbi-help"*.
   *(Từ v0.6.0.)*

**Restart Antigravity** sau cài để nhận tool + skill.

Chỉ cập nhật phần quy trình, không đụng venv/MCP:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Hosts antigravity -Only plugin
```

Vai gợi ý cho Antigravity trong tổ đa-agent: **Analyst/Documenter** (pha data-discovery,
soạn page_spec, artifact bàn giao) — xem `AGENTS.md` §4.2.

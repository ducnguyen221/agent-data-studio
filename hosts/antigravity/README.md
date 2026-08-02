# Google Antigravity — cài & đăng ký powerbi-agent

Antigravity đọc **`GEMINI.md`** (trỏ về `AGENTS.md`) — mọi luật làm việc ở [`AGENTS.md`](../../AGENTS.md).

> ℹ️ **Antigravity KHÔNG có trình quản lý plugin/marketplace** (khác Claude & Codex). Vì vậy
> "plugin" ở đây = **skill nạp từ thư mục** `~/.gemini/antigravity/skills/`. Installer copy skill
> vào đó; Antigravity tự hiện chúng khi khởi động (không có mục "plugin" riêng trong app).

## Cài (Antigravity không có plugin store — dùng installer)

```powershell
git clone https://github.com/ducnguyen221/powerbi-agent "$env:USERPROFILE\.mcp\powerbi-mcp"
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

2. Copy 4 skill (kèm `references/` + `document-templates/` + `scripts/`) vào `~/.gemini/antigravity/skills/`.

**Restart Antigravity** sau cài để nhận tool + skill.

Vai gợi ý cho Antigravity trong tổ đa-agent: **Analyst/Documenter** (pha kpim-analysis,
soạn page_spec, artifact bàn giao) — xem `AGENTS.md` §4.2.

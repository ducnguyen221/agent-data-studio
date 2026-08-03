# scripts/ — Tiện ích dev của REPO (không phải một phần của skill)

| File | Dùng khi |
|---|---|
| `cli.py` | Debug DAX **không cần MCP host**: `.venv\Scripts\python.exe scripts\cli.py list \| tables \| query <port> <model> "<dax>"` — hữu ích khi host chưa restart hoặc cần kiểm tra kết nối nhanh. |
| `test_mcp_local.py` | Smoke test kết nối ADOMD → Power BI Desktop đang mở. |

> ≠ `plugins/powerbi-agent/skills/kpim-analysis/scripts/` — đó là **generator thuộc skill**
> (mindmap/xlsx), đi theo skill khi installer copy sang host. Scripts ở đây ở lại repo.
- `build_template_gallery.py` — sinh `docs/template/templates.json` từ `report-templates/` (chạy sau khi thêm/sửa kit).

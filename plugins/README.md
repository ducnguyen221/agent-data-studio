# plugins/ — chỗ tạm của manifest plugin cũ

> Nội dung thật **không còn ở đây**. Từ v0.7, skill · lệnh · agent nằm phẳng ở gốc repo:
>
> - [`../skills/`](../skills/) — **9 skill**: `data-discovery` · `data-mockup` · `pbi-model` ·
>   `pbi-analysis` · `pbi-design` · `pbi-build` · `pbi-review` · `pbi-publish` · `pbi-knowledge`
> - [`../commands/`](../commands/) — **8 lệnh** `/pbi-*`: `help` · `setup` · `new` · `scan` · `kit` ·
>   `done` · `pack` · `recall`
> - [`../agents/`](../agents/) — agent phụ (`pbi-knowledge-curator`)
> - Mẫu tài liệu dự án: [`../templates/documents/`](../templates/documents/)

Thư mục này chỉ còn giữ **tạm** manifest cũ `powerbi-agent/.claude-plugin/plugin.json` (khai báo
plugin cho `/.claude-plugin/marketplace.json` ở gốc repo) tới bước đóng gói plugin. **Đừng thêm
skill/lệnh/agent vào đây** — sửa ở thư mục gốc; installer copy từ đó sang
`~/.claude/`, `~/.codex/skills/`, `~/.gemini/antigravity/skills/`.

Chưa biết bắt đầu từ đâu → chạy **`/pbi-help`**. Bản đồ toàn repo: [`../INDEX.md`](../INDEX.md) ·
luật làm việc: [`../AGENTS.md`](../AGENTS.md).

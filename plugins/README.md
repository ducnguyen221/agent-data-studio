# plugins/ — Trụ cột 2: chuyên môn đã số hóa

> Tên thư mục nói về **cách đóng gói**; nội dung bên trong mới là thứ đáng giá. Đây là phần
> lớn nhất của repo: quy trình làm việc của một chuyên gia Power BI, viết ra để AI Agent
> đọc và làm theo — **4 skill · 8 lệnh · 1 agent**.

| Thành phần | Là gì | Ở đâu |
|---|---|---|
| [`kpim-analysis`](powerbi-agent/skills/kpim-analysis/SKILL.md) | Pha **nghiệp vụ**: khảo sát → hỏi ngược → tài liệu hóa → lập kế hoạch. Kèm **bộ mẫu tài liệu** (trụ cột 4). | `powerbi-agent/skills/kpim-analysis/` |
| [`powerbi-pipeline`](powerbi-agent/skills/powerbi-pipeline/SKILL.md) | Pha **kỹ thuật**: 9 khâu Power Query → model → DAX → trang báo cáo. Kèm `references/` best-practice. | `powerbi-agent/skills/powerbi-pipeline/` |
| [`powerbi-mcp`](powerbi-agent/skills/powerbi-mcp/SKILL.md) | **Sổ tay tra cứu** 16 tool + luật policy + phân vai với `powerbi-modeling`. | `powerbi-agent/skills/powerbi-mcp/` |
| [`powerbi-knowledge`](powerbi-agent/skills/powerbi-knowledge/SKILL.md) | **Knowledge OS**: dự án, đóng gói tri thức 4 trục, timeline, luật riêng tư. | `powerbi-agent/skills/powerbi-knowledge/` |
| [8 lệnh](powerbi-agent/commands/) | `/powerbi-help` · `setup` · `new` · `scan` · `kit` · `done` · `pack` · `recall` | `powerbi-agent/commands/` |
| [1 agent](powerbi-agent/agents/powerbi-knowledge-curator.md) | `powerbi-knowledge-curator` — đóng gói bài học khi đóng dự án | `powerbi-agent/agents/` |

Chưa biết bắt đầu từ đâu → chạy **`/powerbi-help`**, agent sẽ tự định tuyến.
Bản đồ toàn repo: [`../INDEX.md`](../INDEX.md) · luật làm việc: [`../AGENTS.md`](../AGENTS.md).

---

## Cơ chế đóng gói

`powerbi-agent/` là plugin theo chuẩn Claude/Codex marketplace:

- `powerbi-agent/.claude-plugin/plugin.json` — **manifest của plugin** (tên, version, skills ở đâu).
  ≠ `/.claude-plugin/marketplace.json` ở gốc repo (= **danh mục chợ**, khai báo repo này phân phối
  plugin nào). Hai file này là 2 tầng của cùng một hệ thống — KHÔNG trùng lặp, thiếu 1 là hỏng
  flow `claude plugin marketplace add` → `plugin install`.
- `powerbi-agent/skills/` — 4 skill dùng chung mọi host. **Sửa skill Ở ĐÂY** — installer copy
  đi `~/.claude/skills/`, `~/.codex/skills/`, `~/.gemini/antigravity/skills/`; đừng sửa bản copy.

Chi tiết từng thư mục & file: [`../INDEX.md`](../INDEX.md).

## Plugin này chạy trên host nào?

| Host | Cách hiện dạng plugin | Lệnh |
|---|---|---|
| **Claude Code** | Trình quản lý plugin của app | `claude plugin marketplace add ducnguyen221/powerbi-agent` → `claude plugin install powerbi-agent@powerbi-agent` |
| **Codex CLI** | `codex plugin list` (đọc CÙNG `marketplace.json`) | `codex plugin marketplace add ...` → `codex plugin add powerbi-agent@powerbi-agent` |
| **Antigravity** | Không có store → skill nạp từ `~/.gemini/antigravity/skills/` (installer copy) | `install.ps1 -Hosts antigravity` |

Từ v0.5.0 installer cấp **lệnh cho cả 3 host**: Claude → `~/.claude/commands/`,
Codex → mỗi lệnh thành 1 skill trong `~/.codex/skills/`, Antigravity → trong skill `powerbi-knowledge/commands/`
(host này không có cơ chế slash-command). Cập nhật riêng phần này: `install.ps1 -Only plugin`.

Đã verify: cùng 1 `.claude-plugin/marketplace.json` cài sạch trên cả Claude lẫn Codex; commands/agents được auto-discover (KHÔNG khai báo trong plugin.json — Claude từ chối field `agents`).
